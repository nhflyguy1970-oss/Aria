"""Multi-step coding agent: plan → context → edit → verify → retry."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from jarvis import fs, llm
from jarvis.code_context import _is_sandbox_script, format_context, gather_context
from jarvis.coding_verify import verify_file_changes
from jarvis.diff_util import make_diff
from jarvis.patch_util import merge_file_change
from jarvis.router import infer_script_path, py_path_from_message
from jarvis.sandbox import run_sandboxed
from jarvis.syntax_check import format_diagnostics

_PYTHON = sys.executable
DEFAULT_MAX_STEPS = 5


@dataclass
class AgentStep:
    step: int
    action: str
    detail: str
    ok: bool = True


@dataclass
class AgentResult:
    ok: bool
    message: str
    files: list[dict] = field(default_factory=list)
    explanation: str = ""
    diff: str = ""
    steps: list[AgentStep] = field(default_factory=list)
    mode: str = "agent"
    diagnose_only: bool = False


class CodingAgent:
    """Iterative coding agent with read/search/run/verify tools."""

    def __init__(self, base: Path, *, max_steps: int = DEFAULT_MAX_STEPS):
        self.base = base
        self.max_steps = max_steps
        self.steps: list[AgentStep] = []

    def _log(self, action: str, detail: str, ok: bool = True) -> None:
        self.steps.append(AgentStep(len(self.steps) + 1, action, detail, ok))

    def _read(self, path: str) -> str:
        content = fs.read_file(path, base=self.base)
        self._log("read", path, not content.startswith("ERROR:"))
        return content

    def _search(self, query: str) -> list[tuple[str, int, str]]:
        hits = fs.search_files(query, self.base)
        self._log("search", f"'{query}' → {len(hits)} hits")
        return hits

    def _semantic_search(self, query: str) -> list[dict]:
        try:
            from jarvis import code_index
            hits = code_index.search(query, limit=6)
            self._log("semantic_search", f"'{query}' → {len(hits)} chunks")
            return hits
        except Exception as e:
            self._log("semantic_search", str(e), ok=False)
            return []

    def _run_file(self, path: str) -> tuple[int, str]:
        resolved = fs.resolve_path(path, base=self.base)
        result = run_sandboxed([_PYTHON, str(resolved)], cwd=str(self.base), timeout=30)
        out = ((result.stdout or "") + (result.stderr or "")).strip()
        self._log("run", path, result.returncode == 0)
        return result.returncode, out

    def _compile_check(self, path: str, content: str) -> str | None:
        from jarvis.syntax_check import check_file, has_errors
        resolved = fs.resolve_path(path, base=self.base)
        if path.endswith(".py"):
            diags = check_file(resolved, content=content, deep=False)
            if has_errors(diags):
                return format_diagnostics(diags, max_items=5)
            return None
        if path.endswith((".js", ".mjs", ".cjs")):
            diags = check_file(resolved, content=content, deep=False)
            if has_errors(diags):
                return format_diagnostics(diags, max_items=5)
        return None

    def _load_test_errors(self, path: str) -> str:
        if not path.endswith(".py"):
            return ""
        from jarvis.coding_verify import collect_test_failures
        resolved = fs.resolve_path(path, base=self.base)
        return collect_test_failures(resolved, self.base)

    def _verify_passed(self, verify: str) -> bool:
        if not verify.strip():
            return True
        lower = verify.lower()
        if "syntax check failed" in lower or "verify failed" in lower:
            return False
        if "**pytest:** failed" in lower:
            return False
        if "run failed" in lower:
            return False
        if "verification incomplete" in lower:
            return False
        if "**pytest:** passed" in lower or "pytest passed" in lower:
            return True
        if "**syntax:** ok" in lower and "**pytest:**" not in lower:
            return True
        return False

    def _verify_file_items(self, file_items: list[dict], *, mode: str = "agent") -> str:
        ok, msg = verify_file_changes(file_items, self.base, mode=mode)
        if not ok:
            return msg
        return msg

    def diagnose(self, path: str, task: str = "") -> AgentResult:
        """Explain issues without proposing code changes."""
        content = self._read(path)
        if content.startswith("ERROR:"):
            return AgentResult(False, content)

        ctx = gather_context(path, self.base, task=task or "diagnose errors")
        self._log("gather_context", f"{len(ctx.get('related', []))} related files")

        stderr = ""
        if path.endswith(".py"):
            resolved = fs.resolve_path(path, base=self.base)
            compile_check = subprocess.run(
                [_PYTHON, "-m", "py_compile", str(resolved)],
                capture_output=True, text=True, timeout=15,
            )
            if compile_check.returncode != 0:
                stderr = compile_check.stderr or compile_check.stdout
            else:
                rc, out = self._run_file(path)
                if rc != 0:
                    stderr = out

        explanation = llm.diagnose_code(
            task or "Explain what is wrong and how to fix it.",
            path=path,
            content=content,
            context=format_context(ctx),
            errors=stderr,
        )
        return AgentResult(
            ok=True,
            message=explanation,
            explanation=explanation,
            diagnose_only=True,
            steps=self.steps,
        )

    def _create_new_files(self, task: str, script_path: str) -> AgentResult:
        """Generate script + pytest when the target path does not exist yet."""
        self._log("plan", f"{script_path} missing → create")
        explanation, files = llm.generate_script_with_test(task, script_path)
        if not files or not any(f.get("code", "").strip() for f in files):
            return AgentResult(False, "Could not generate script for new file.", steps=self.steps)
        self._log("generate", f"{len(files)} file(s)")
        verify = self._verify_file_items(files, mode="create")
        if verify and not self._verify_passed(verify):
            return AgentResult(
                False,
                f"Generated files failed verification:\n\n{verify}",
                files=[],
                steps=self.steps,
            )
        combined_diff = ""
        for f in files:
            combined_diff += make_diff("", f["code"]) + "\n"
        msg = (
            f"**New script proposal** ({len(files)} file(s))\n\n"
            f"{explanation}\n\n"
        )
        if verify:
            msg += f"{verify}\n\n"
        msg += "Review the diff and say **apply it** to save changes."
        return AgentResult(
            ok=True,
            message=msg,
            files=files,
            explanation=explanation,
            diff=combined_diff.strip(),
            steps=self.steps,
            mode="create",
        )

    def run(
        self,
        task: str,
        *,
        path: str | None = None,
        mode: str = "agent",
        diagnose_first: bool = False,
        initial_errors: str = "",
    ) -> AgentResult:
        """Execute agent loop and return proposed file changes."""
        self.steps = []
        target_paths: list[str] = []

        if path:
            target_paths = [path]
            resolved = fs.resolve_path(path, base=self.base)
            if not resolved.exists():
                return self._create_new_files(task, path)
        else:
            # Infer paths from semantic search + task keywords
            self._log("plan", task[:120])
            for hit in self._semantic_search(task)[:3]:
                src = hit.get("source", "")
                if src and src not in target_paths:
                    target_paths.append(src)
            if not target_paths:
                # Grep for likely symbols
                words = re.findall(r"\b[\w./-]+\.(?:py|js|ts|sh)\b", task)
                for w in words:
                    if fs.resolve_path(w, base=self.base).exists():
                        target_paths.append(w)
                        break

        if not target_paths:
            # Create mode — no existing path
            if mode == "create" or re.search(r"\b(create|write|new|implement|build|add)\b", task, re.I):
                script_path = py_path_from_message(task) or infer_script_path(task)
                return self._create_new_files(task, script_path)

            return AgentResult(False, "No target file found. Specify a path or index the project first.")

        if diagnose_first and len(target_paths) == 1:
            return self.diagnose(target_paths[0], task)

        all_files: dict[str, dict] = {}
        last_errors = initial_errors or ""
        explanation = ""
        if last_errors:
            self._log("resume", "prior errors loaded")
        elif path and len(target_paths) == 1:
            test_err = self._load_test_errors(path)
            if test_err:
                last_errors = test_err
                self._log("pytest", "failures loaded")

        for step in range(self.max_steps):
            self._log("step", f"{step + 1}/{self.max_steps}")

            for target in target_paths:
                content = self._read(target)
                if content.startswith("ERROR:"):
                    continue

                ctx = gather_context(target, self.base, task=task)
                self._log("context", f"{target}: {len(ctx.get('related', []))} related")
                ctx_text = format_context(ctx)
                if _is_sandbox_script(target):
                    # Small scripts: file + its test only — skip unrelated context
                    from jarvis.code_context import _find_test_files
                    slim = [f"FILE: {target}\n{content}"]
                    for rel_test in _find_test_files(target, self.base):
                        t = fs.read_file(rel_test, base=self.base)
                        if not t.startswith("ERROR:"):
                            slim.append(f"--- {rel_test} (test) ---\n{t[:4000]}")
                    ctx_text = "\n".join(slim)

                if mode == "refactor" or len(target_paths) > 1:
                    exp, file_items = llm.generate_multi_file_edit(
                        task, context=ctx_text, errors=last_errors,
                    )
                else:
                    exp, file_items = llm.generate_patched_edit(
                        task, path=target, content=content,
                        context=ctx_text, errors=last_errors,
                    )

                explanation = exp or explanation

                for item in file_items:
                    p = item.get("path") or target
                    original = fs.read_file(p, base=self.base)
                    if original.startswith("ERROR:"):
                        original = ""
                    new_code = item.get("code", "")
                    hunks = item.get("hunks")
                    if hunks:
                        from jarvis.patch_util import apply_hunks_to_content
                        new_code, hunk_errs = apply_hunks_to_content(original, hunks)
                        if hunk_errs and item.get("code"):
                            new_code = item["code"]
                    elif not new_code:
                        continue
                    else:
                        new_code = merge_file_change(p, original, new_code, hunks)

                    err = self._compile_check(p, new_code) if p.endswith(".py") else None
                    if err:
                        last_errors = err
                        self._log("compile", f"{p}: failed", ok=False)
                        all_files[p] = {"path": p, "code": new_code, "error": err}
                        continue

                    all_files[p] = {"path": p, "code": new_code}
                    self._log("propose", p)

            file_list = [{"path": v["path"], "code": v["code"]} for v in all_files.values()]
            if not file_list:
                continue

            verify = self._verify_file_items(file_list, mode=mode)
            verify_failed = not self._verify_passed(verify)
            if verify_failed:
                last_errors = verify
                self._log("verify", "tests/syntax failed", ok=False)
                if step < self.max_steps - 1:
                    continue
                return AgentResult(
                    False,
                    f"Could not pass verification after {self.max_steps} attempts.\n\n{verify}",
                    files=[],
                    steps=self.steps,
                    mode=mode,
                )
            else:
                self._log("verify", "passed")
                break

        if not all_files:
            return AgentResult(False, "Could not generate valid changes.", steps=self.steps)

        file_list = [{"path": v["path"], "code": v["code"]} for v in all_files.values()]
        combined_diff = ""
        for f in file_list:
            orig = fs.read_file(f["path"], base=self.base)
            if orig.startswith("ERROR:"):
                orig = ""
            combined_diff += make_diff(orig, f["code"]) + "\n"

        msg = (
            f"**Agent finished** ({len(self.steps)} steps, {len(file_list)} file(s))\n\n"
            f"{explanation}\n\n"
            "Review the diff and say **apply it** to save changes."
        )
        return AgentResult(
            ok=True,
            message=msg,
            files=file_list,
            explanation=explanation,
            diff=combined_diff.strip(),
            steps=self.steps,
            mode=mode,
        )

    def run_stream(
        self,
        task: str,
        *,
        path: str | None = None,
        mode: str = "agent",
        diagnose_first: bool = False,
    ) -> Iterator[dict]:
        """Yield status events, then final result dict."""
        yield {"type": "status", "message": "Planning coding task…"}
        yield {"type": "status", "message": "Gathering project context…"}

        result = self.run(task, path=path, mode=mode, diagnose_first=diagnose_first)

        for step in result.steps:
            yield {
                "type": "agent_step",
                "step": step.step,
                "action": step.action,
                "detail": step.detail,
                "ok": step.ok,
            }

        if not result.ok:
            yield {"type": "done", "ok": False, "message": result.message, "module": "coding"}
            return

        if result.diagnose_only:
            yield {
                "type": "done",
                "ok": True,
                "message": result.message,
                "module": "coding",
                "result_type": "diagnose",
            }
            return

        yield {"type": "status", "message": f"Proposal ready — {len(result.files)} file(s)"}
        yield {
            "type": "done",
            "ok": True,
            "message": result.message,
            "module": "coding",
            "result_type": "proposal",
            "explanation": result.explanation,
            "diff": result.diff,
            "agent_steps": [
                {"step": s.step, "action": s.action, "detail": s.detail, "ok": s.ok}
                for s in result.steps
            ],
            "_agent_files": result.files,
            "_agent_mode": result.mode,
        }
