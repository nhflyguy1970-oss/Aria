"""Editors — how proposed code changes are produced.

Kept separate from the loop so the loop is testable with a deterministic editor
and so the production path reuses ARIA's existing CodingAgent rather than a new
model integration.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from jarvis.dev_agent.workspace import Workspace

log = logging.getLogger("jarvis.dev_agent.editors")

_TEST_NAME = re.compile(r"(^|/)(test_[^/]+|[^/]+_test)\.py$")
_IMPORT = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", re.M)


def static_editor(files: list[dict[str, str]], summary: str = "static edit"):
    """Deterministic editor for tests and scripted changes."""

    def _edit(task: dict[str, Any], ws: Workspace, context: dict[str, Any]) -> dict[str, Any]:
        return {"files": files, "summary": summary}

    return _edit


def is_test_file(rel: str) -> bool:
    return bool(_TEST_NAME.search(rel.replace("\\", "/")))


def _sources(ws: Workspace) -> list[str]:
    out = []
    for p in sorted(ws.root.rglob("*.py")):
        if ".git" in p.parts or "venv" in p.parts or "__pycache__" in p.parts:
            continue
        out.append(str(p.relative_to(ws.root)))
    return out


def pick_target(task: dict[str, Any], ws: Workspace, context: dict[str, Any]) -> str | None:
    """Choose the source file to edit.

    Deliberately biased away from test files: the module a failing test imports
    is the thing to fix, not the test that caught it.
    """
    sources = _sources(ws)
    if not sources:
        return None
    by_stem = {Path(s).stem: s for s in sources if not is_test_file(s)}

    failing = list(context.get("failing_tests") or []) or list(task.get("baseline_failures") or [])
    for entry in failing:
        rel = str(entry).split("::", 1)[0]
        candidate = ws.root / rel
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # The module under test, reached through the failing test's imports.
        for mod in _IMPORT.findall(text):
            hit = by_stem.get(mod.split(".")[0])
            if hit:
                return hit

    changed = [f for f in (task.get("files_changed") or []) if not is_test_file(str(f))]
    if changed:
        return str(changed[0])
    non_test = [s for s in sources if not is_test_file(s)]
    return non_test[0] if non_test else None


def _describe(task: dict[str, Any], context: dict[str, Any]) -> str:
    """Ground the model in the objective plus what is actually failing."""
    parts = [task["objective"]]
    failing = context.get("failing_tests") or []
    if failing:
        parts.append("Failing tests: " + ", ".join(str(f) for f in failing))
    output = (context.get("test_output") or "").strip()
    if output:
        parts.append("Test output:\n" + output[:4000])
    return "\n\n".join(parts)


def model_editor(assistant: Any = None):
    """Production editor backed by ARIA's coder model.

    Uses the same edit primitive CodingAgent does, but not CodingAgent's own
    verification gate: for a single-file edit that gate resolves the path on
    disk and re-checks the *unmodified* file, so it always fails and discards
    the proposal. The dev agent does not need it — it applies changes inside
    the confined workspace and runs the real suite, and refuses completion
    unless the tests are genuinely green.
    """

    def _edit(task: dict[str, Any], ws: Workspace, context: dict[str, Any]) -> dict[str, Any]:
        try:
            from jarvis import llm
            from jarvis.code_context import format_context, gather_context

            target = pick_target(task, ws, context)
            if not target:
                return {
                    "files": [],
                    "summary": "no editable source file found",
                    "error": "no target file",
                }
            current = (ws.root / target).read_text(encoding="utf-8", errors="replace")
            ctx_text = ""
            try:
                ctx_text = format_context(gather_context(target, ws.root, task=task["objective"]))
            except Exception:  # noqa: BLE001 - context is a nicety, not a requirement
                log.debug("context unavailable for %s", target, exc_info=True)

            explanation, items = llm.generate_patched_edit(
                _describe(task, context),
                path=target,
                content=current,
                context=ctx_text,
                errors=(context.get("test_output") or "")[:4000],
            )

            files, refused = [], []
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                path = str(item.get("path") or target)
                code = item.get("code")
                if code is None:
                    code = item.get("content")
                if code is None and item.get("hunks"):
                    from jarvis.patch_util import apply_hunks_to_content

                    original = ""
                    try:
                        original = (ws.root / path).read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        original = ""
                    code, _errs = apply_hunks_to_content(original, item["hunks"])
                if not code:
                    continue
                # Never let a red test be "fixed" by rewriting the test.
                if is_test_file(path) and not target_allows_tests(task):
                    refused.append(path)
                    continue
                files.append({"path": path, "content": str(code)})

            summary = (explanation or "model edit").strip()
            if refused:
                summary += f" (refused to edit test file(s): {', '.join(refused)})"
            proposal: dict[str, Any] = {"files": files, "summary": summary, "target": target}
            if not files:
                proposal["error"] = "model produced no usable changes"
            return proposal
        except Exception as exc:  # noqa: BLE001 - a model failure is data, not a crash
            log.warning("model editor failed: %s", exc, exc_info=True)
            return {
                "files": [],
                "summary": f"model editor failed: {type(exc).__name__}: {exc}",
                "error": f"{type(exc).__name__}: {exc}",
            }

    return _edit


def target_allows_tests(task: dict[str, Any]) -> bool:
    """Only edit tests when the objective actually asks for test changes."""
    return bool(re.search(r"\btests?\b", task.get("objective") or "", re.I))
