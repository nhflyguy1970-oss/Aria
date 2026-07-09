"""Engineering operations extracted from JarvisAssistant (generated)."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from jarvis.response import err as _err, ok as _ok

import logging

from jarvis import fs
from jarvis.coding_agent import CodingAgent
from jarvis.diff_util import make_diff
from jarvis.response import stream_done as _stream_done

logger = logging.getLogger("jarvis.behaviors.engineering")


class EngineeringOperations:
    """Coding, git, LSP, and refactor handlers using engineering context."""


    @classmethod
    @classmethod
    def store_refactor_proposal(
        cls,
        ctx,
        files: list[dict],
        *,
        explanation: str,
        mode: str = "refactor",
    ) -> dict:
        if not files:
            return _err("No changes to propose.")
        proposal_id, payload = ctx._store_agent_proposal(
            files, mode=mode, explanation=explanation,
        )
        combined_diff = ""
        for f in files:
            if f.get("delete"):
                combined_diff += f"--- delete {f['path']}\n"
                continue
            orig = fs.read_file(f["path"], base=ctx.coding._base())
            if orig.startswith("ERROR:"):
                orig = ""
            combined_diff += make_diff(orig, f.get("code", "")) + "\n"
        files_note = "\n".join(
            f"- `{f['path']}`" + (" (delete)" if f.get("delete") else "")
            for f in files
        )
        syntax_note = ""
        if payload.get("_diag_summary"):
            syntax_note = f"\n\n**Syntax check:**\n{payload['_diag_summary']}"
        intro = (
            f"**Refactor proposal** ({len(files)} change(s)):\n{files_note}\n\n"
            f"{explanation}{syntax_note}\n\n"
            "Review the diff and hit **Apply changes** or say `apply it`."
        )
        extra = ctx._proposal_response_extra([f for f in files if not f.get("delete")])
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        return _ok(
            intro,
            module="coding",
            type="proposal",
            proposal_id=proposal_id,
            diff=combined_diff.strip(),
            explanation=explanation,
            diagnostics=payload.get("diagnostics", []),
            syntax_ok=payload.get("syntax_ok", True),
            **extra,
        )

    @classmethod
    def apply_editor_params(cls, eng_ctx, params: dict, message: str, action: str) -> None:
        from jarvis.editor_context import get_context
        editor_ctx = get_context()
        if not editor_ctx:
            return
        if not params.get("path") and editor_ctx.relative_file:
            params["path"] = editor_ctx.relative_file
        lower = message.lower()
        if editor_ctx.has_selection() and (
            params.get("use_selection")
            or re.search(r"\b(selection|selected|this code)\b", lower)
        ):
            params["use_selection"] = True
            params["_editor_prompt"] = editor_ctx.format_for_prompt()
        elif action.startswith("coding_") and editor_ctx.relative_file:
            params.setdefault("_editor_prompt", editor_ctx.format_for_prompt(max_selection=800))

    @classmethod
    def resolve_coding_path(cls, ctx, path: str) -> str:
        return ctx.session.resolve_path(path or None) or ""

    @classmethod
    def coding_read(cls, ctx, params: dict, message: str) -> dict:
        path = EngineeringOperations.resolve_coding_path(ctx, params.get("path", ""))
        if not path:
            return _err("Which file should I read?")
        content = fs.read_file(path, base=ctx.coding._base())
        if content.startswith("ERROR:"):
            return _err(content)
        ctx.session.note_file(path)
        ctx.coding.conversation.add_system(f"Loaded file: {path}\n\n{content}")
        preview = content[:3000] + ("…" if len(content) > 3000 else "")
        return _ok(f"Here's **{path}** ({len(content)} chars):\n\n```\n{preview}\n```", module="coding")

    @classmethod
    def coding_agent_stream(cls, ctx, params: dict, message: str, *, mode: str = "agent"):
        """Shared streaming agent path with TaskManager + max_steps."""
        try:
            yield from EngineeringOperations.coding_agent_stream_inner(ctx, params, message, mode=mode)
        except Exception as e:
            logger.exception("coding agent stream failed")
            yield _stream_done(_err(f"Coding agent failed: {e}", module="coding"))

    @classmethod
    def coding_agent_stream_inner(cls, ctx, params: dict, message: str, *, mode: str = "agent"):
        task_text = params.get("task") or message
        path = params.get("path") or ctx.session.resolve_path(None) or None
        max_steps = int(params.get("max_steps") or 5)
        task_id = params.get("task_id") or ""
        ct = None

        if not task_id:
            ct = ctx.task_manager.create(task_text[:120], path=path or "", mode=mode)
            task_id = ct.id
        else:
            ct = ctx.task_manager.get(task_id)
            if ct:
                ctx.task_manager.resume(task_id)
                path = path or ct.path or None
                task_text = ct.checkpoint.get("task") or task_text
                mode = ct.checkpoint.get("mode") or mode

        initial_errors = ""
        if ct:
            initial_errors = ct.checkpoint.get("last_errors") or ""

        ctx._active_task_id = task_id
        agent = CodingAgent(ctx.coding._base(), max_steps=max_steps)

        yield {"type": "status", "message": "Planning coding task…"}
        yield {"type": "status", "message": "Gathering project context…"}

        result = agent.run(
            task_text,
            path=path,
            mode=mode,
            diagnose_first=bool(params.get("diagnose_first")),
            initial_errors=initial_errors,
        )

        for step in result.steps:
            ctx.task_manager.add_step(task_id, step.action, step.detail, ok=step.ok)
            yield {
                "type": "agent_step",
                "step": step.step,
                "action": step.action,
                "detail": step.detail,
                "ok": step.ok,
            }

        if not result.ok:
            from jarvis.trust_memory import record_failure

            ctx.task_manager.save_state(task_id, last_errors=result.message)
            ctx.task_manager.complete(task_id, ok=False)
            record_failure(
                ctx.memory,
                path=path or "",
                error=result.message[:600],
                task=task_text[:160],
            )
            yield {"type": "done", "ok": False, "message": result.message, "module": "coding", "task_id": task_id}
            return

        if result.diagnose_only:
            ctx.task_manager.complete(task_id, ok=True)
            yield {
                "type": "done", "ok": True, "message": result.message,
                "module": "coding", "result_type": "diagnose", "task_id": task_id,
            }
            return

        proposal_id, payload = ctx._store_agent_proposal(
            result.files, mode=result.mode, explanation=result.explanation, task_id=task_id,
        )
        ctx.task_manager.save_state(
            task_id,
            task_text=task_text,
            path=path or "",
            mode=mode,
            files=[f["path"] for f in result.files],
            proposal_id=proposal_id,
        )
        ctx.task_manager.complete(task_id, ok=True)

        extra = ctx._proposal_response_extra(result.files)
        msg = result.message
        if payload.get("_diag_summary"):
            msg += f"\n\n**Syntax check:**\n{payload['_diag_summary']}"
        if extra.get("test_impact"):
            msg += f"\n\n{extra['test_impact']}"

        yield {"type": "status", "message": f"Proposal ready — {len(result.files)} file(s)"}
        yield _stream_done({
            "ok": True,
            "message": msg,
            "module": "coding",
            "result_type": "proposal",
            "proposal_id": proposal_id,
            "path": result.files[0]["path"] if result.files else "",
            "diff": result.diff,
            "explanation": result.explanation,
            "diagnostics": payload.get("diagnostics", []),
            "syntax_ok": payload.get("syntax_ok", True),
            "agent_steps": [
                {"step": s.step, "action": s.action, "detail": s.detail, "ok": s.ok}
                for s in result.steps
            ],
            "task_id": task_id,
            **extra,
        })

    @classmethod
    def code_unchanged(cls, ctx, original: str, candidate: str) -> bool:
        return original.strip() == (candidate or "").strip()

    @classmethod
    def coding_propose(
        cls,
        ctx,
        path: str,
        mode: str,
        *,
        task: str | None = None,
        editor_prompt: str = "",
    ) -> dict:
        content = fs.read_file(path, base=ctx.coding._base())
        if content.startswith("ERROR:"):
            return _err(content)

        ctx = gather_context(path, ctx.coding._base(), task=task or mode)
        context_text = format_context(ctx)
        from jarvis.code_context import _find_test_files, _is_sandbox_script
        if _is_sandbox_script(path):
            slim = [f"FILE: {path}\n{content}"]
            for rel_test in _find_test_files(path, ctx.coding._base()):
                t = fs.read_file(rel_test, base=ctx.coding._base())
                if not t.startswith("ERROR:"):
                    slim.append(f"--- {rel_test} (test) ---\n{t[:4000]}")
            context_text = "\n".join(slim)

        if editor_prompt:
            context_text = f"{context_text}\n\n--- Editor (Cursor) ---\n{editor_prompt}"

        stderr = ""
        resolved = fs.resolve_path(path, base=ctx.coding._base())
        if mode == "fix":
            try:
                compile_check = subprocess.run(
                    ["python3", "-m", "py_compile", str(resolved)],
                    capture_output=True, text=True, timeout=15,
                )
                if compile_check.returncode == 0:
                    result = run_sandboxed(
                        ["python3", str(resolved)],
                        cwd=str(ctx.coding._base()),
                        timeout=30,
                    )
                    stderr = result.stderr or (result.stdout if result.returncode != 0 else "")
                else:
                    stderr = compile_check.stderr or compile_check.stdout
            except Exception as e:
                return _err(str(e))
            if not stderr:
                from jarvis.coding_verify import collect_test_failures
                stderr = collect_test_failures(resolved, ctx.coding._base())
            if not stderr:
                from jarvis import lsp
                diag = lsp.check_python(resolved)
                if diag:
                    stderr = "\n".join(diag)
            if not stderr and not task:
                return _ok("Syntax, run, and tests look clean — no errors to fix.", module="coding")
            fix_task = task or "Fix all errors with minimal changes."
            if editor_prompt and "Selected text" in editor_prompt:
                fix_task += "\n\nFocus on the selected code in the Editor (Cursor) context."
            llm_errors = stderr or task or ""
            explanation, new_code = ctx._llm_edit_file(
                fix_task,
                path=path,
                content=content,
                context=context_text,
                errors=llm_errors,
                require_test_pass=bool(llm_errors and "pytest" in llm_errors.lower()),
            )
        else:
            improve_task = task or "Improve readability, structure, and robustness with minimal changes."
            explanation, new_code = ctx._llm_edit_file(
                improve_task, path=path, content=content, context=context_text,
            )

        diff = make_diff(content, new_code)
        files = [{"path": path, "code": new_code}]
        diag_dicts, diag_summary = ctx._check_proposal_syntax(files)
        proposal_id = str(uuid.uuid4())[:8]
        syntax_ok = not any(d.get("severity") == "error" for d in diag_dicts)
        ctx.pending_proposals[proposal_id] = {
            "path": path, "code": new_code, "mode": mode,
            "files": files, "diagnostics": diag_dicts,
            "syntax_ok": syntax_ok, "explanation": explanation,
        }
        ctx._persist_proposals()
        ctx.session.note_proposal(proposal_id)
        ctx.session.note_file(path)

        extra = ctx._proposal_response_extra(files)
        verb = "fixes" if mode == "fix" else "improvements"
        syntax_note = f"\n\n**Syntax check:**\n{diag_summary}" if diag_summary else ""
        intro = (
            f"I found {verb} for **{path}** (used {len(ctx.get('related', []))} related files for context).\n\n"
            f"{explanation}{syntax_note}\n\n"
            "Want me to apply these changes? Hit **Apply** or just say \"apply it\"."
        )
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        return _ok(
            intro,
            module="coding",
            type="proposal",
            proposal_id=proposal_id,
            path=path,
            diff=diff,
            explanation=explanation,
            diagnostics=diag_dicts,
            syntax_ok=syntax_ok,
            **extra,
        )

    @classmethod
    def coding_propose_stream(
        cls,
        ctx,
        path: str,
        mode: str,
        *,
        task: str | None = None,
        message: str = "",
        editor_prompt: str = "",
    ) -> Iterator[dict]:
        try:
            if not path:
                yield _stream_done(_err(
                    "Which file? Say e.g. `fix data/scripts/your_file.py`",
                ))
                return
            yield {"type": "status", "message": f"Loading **{path}**…"}
            yield {"type": "agent_step", "step": 1, "action": "read", "detail": path, "ok": True}
            content = fs.read_file(path, base=ctx.coding._base())
            if content.startswith("ERROR:"):
                yield _stream_done(_err(content))
                return
            yield {"type": "status", "message": "Running diagnostics…"}
            if mode == "fix":
                yield {"type": "agent_step", "step": 2, "action": "diagnose", "detail": "errors/tests", "ok": True}
            yield {"type": "status", "message": "Generating changes…"}
            yield {"type": "agent_step", "step": 3, "action": "edit", "detail": path, "ok": True}
            result = EngineeringOperations.coding_propose(ctx, path, mode, task=task, editor_prompt=editor_prompt)
            if result.get("ok"):
                yield {"type": "agent_step", "step": 4, "action": "propose", "detail": path, "ok": True}
            yield _stream_done(result)
        except Exception as e:
            logger.exception("coding propose stream failed for %s", path)
            yield _stream_done(_err(f"Coding failed: {e}", module="coding"))

    @classmethod
    def coding_create_stream(cls, ctx, params: dict, message: str) -> Iterator[dict]:
        try:
            yield {"type": "status", "message": "Planning new script + tests…"}
            yield {"type": "agent_step", "step": 1, "action": "plan", "detail": "create", "ok": True}
            yield {"type": "status", "message": "Generating code…"}
            yield {"type": "agent_step", "step": 2, "action": "generate", "detail": "script + pytest", "ok": True}
            result = EngineeringOperations.coding_create(ctx, params, message)
            if result.get("ok"):
                yield {"type": "agent_step", "step": 3, "action": "propose", "detail": "ready", "ok": True}
            yield _stream_done(result)
        except Exception as e:
            logger.exception("coding create stream failed")
            yield _stream_done(_err(f"Could not create script: {e}", module="coding"))

    @classmethod
    def coding_create(cls, ctx, params: dict, message: str) -> dict:
        description = (params.get("description") or message).strip()
        path = (params.get("path") or "").strip()
        if not path:
            path = py_path_from_message(message)
            if not path and re.search(r"hello\s*world", description, re.I):
                path = "data/scripts/hello_world.py"
            elif not path:
                path = infer_script_path(message)

        Path(path).parent  # ensure path shape valid
        scripts_dir = fs.resolve_path("data/scripts", base=ctx.coding._base())
        scripts_dir.mkdir(parents=True, exist_ok=True)

        explanation, file_items = llm.generate_script_with_test(description, path)
        if not file_items or not file_items[0].get("code", "").strip():
            return _err("I couldn't generate a script from that request. Try being more specific.")

        from jarvis.coding_verify import verify_proposed_files
        ok, verify_detail = verify_proposed_files(file_items, ctx.coding._base())
        verify_note = ""
        if verify_detail:
            verify_note = f"\n\n**Pre-apply verify:** {verify_detail}" + ("" if ok else " (failed — review before apply)")

        main = file_items[0]
        new_code = main["code"]
        path = main.get("path") or path
        proposal_id, payload = ctx._store_agent_proposal(
            file_items, mode="create", explanation=explanation,
        )
        combined_diff = ""
        for f in file_items:
            orig = fs.read_file(f["path"], base=ctx.coding._base())
            if orig.startswith("ERROR:"):
                orig = ""
            combined_diff += make_diff(orig, f["code"]) + "\n"

        files_note = "\n".join(f"- `{f['path']}`" for f in file_items)
        syntax_note = ""
        if payload.get("_diag_summary"):
            syntax_note = f"\n\n**Syntax check:**\n{payload['_diag_summary']}"
        extra = ctx._proposal_response_extra(file_items)
        intro = (
            f"I wrote:\n{files_note}\n\n"
            f"{explanation}{syntax_note}{verify_note}\n\n"
            "```python\n"
            f"{new_code[:2000]}{'…' if len(new_code) > 2000 else ''}\n"
            "```\n\n"
            "Say **apply it** to save — I'll run the script and pytest."
        )
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        return _ok(
            intro,
            module="coding",
            type="proposal",
            proposal_id=proposal_id,
            path=path,
            diff=combined_diff.strip() or make_diff("", new_code),
            explanation=explanation,
            diagnostics=payload.get("diagnostics", []),
            syntax_ok=payload.get("syntax_ok", True),
            verify_ok=ok,
            **extra,
        )

    @classmethod
    def coding_fix_tests_stream(cls, ctx, params: dict, message: str) -> Iterator[dict]:
        """Fast path: pytest → fix → verify (max 2 LLM calls)."""
        path = EngineeringOperations.resolve_coding_path(ctx, params.get("path", ""))
        if not path:
            yield _stream_done(_err(
                "Which file? Open it in Cursor or say e.g. "
                "`debug until tests pass for data/scripts/your_file.py`",
            ))
            return

        ctx.session.note_file(path)
        content = fs.read_file(path, base=ctx.coding._base())
        if content.startswith("ERROR:"):
            yield _stream_done(_err(content))
            return

        from jarvis.code_context import _find_test_files
        from jarvis.coding_verify import collect_test_failures

        resolved = fs.resolve_path(path, base=ctx.coding._base())
        yield {"type": "status", "message": "Running pytest…"}
        errors = collect_test_failures(resolved, ctx.coding._base())
        if not errors:
            yield _stream_done(_ok(
                f"**Tests already pass** for `{path}`. Nothing to fix.",
                module="coding",
            ))
            return

        yield {"type": "agent_step", "step": 1, "action": "pytest", "detail": "failures loaded", "ok": False}

        slim = [f"FILE: {path}\n{content}"]
        for rel_test in _find_test_files(path, ctx.coding._base()):
            t = fs.read_file(rel_test, base=ctx.coding._base())
            if not t.startswith("ERROR:"):
                slim.append(f"--- {rel_test} (test) ---\n{t[:4000]}")
        ctx_text = "\n".join(slim)
        task = f"Fix `{path}` so all tests pass. Minimal changes only."

        explanation = ""
        new_code = content
        verify = ""
        for attempt in range(1, 3):
            yield {"type": "status", "message": f"Generating fix (attempt {attempt}/2)…"}
            yield {"type": "agent_step", "step": attempt + 1, "action": "edit", "detail": path, "ok": True}
            explanation, new_code = ctx._llm_edit_file(
                task, path=path, content=content, context=ctx_text, errors=errors,
                require_test_pass=True,
            )
            if EngineeringOperations.code_unchanged(ctx, content, new_code):
                errors = (errors + "\n\nNo effective code change.").strip()
                continue
            verify = verify_python_files([resolved], ctx.coding._base(), run_scripts=False)
            if ctx._tests_verify_ok(verify):
                yield {"type": "agent_step", "step": attempt + 1, "action": "verify", "detail": "tests passed", "ok": True}
                break
            errors = verify or errors
            yield {"type": "agent_step", "step": attempt + 1, "action": "verify", "detail": "tests still failing", "ok": False}

        if EngineeringOperations.code_unchanged(ctx, content, new_code):
            from jarvis.trust_memory import record_failure

            record_failure(
                ctx.memory,
                path=path,
                error=errors[:500],
                task=message[:160],
            )
            yield _stream_done(_err(
                f"Could not produce a fix for `{path}` after 2 attempts.\n\n"
                "The model returned the same broken code (often failed SEARCH/REPLACE patches).\n"
                "Try: `fix data/scripts/your_file.py` or check **Settings → coder model**.",
                module="coding",
            ))
            return

        diff = make_diff(content, new_code)
        files = [{"path": path, "code": new_code}]
        diag_dicts, diag_summary = ctx._check_proposal_syntax(files)
        syntax_ok = not any(d.get("severity") == "error" for d in diag_dicts)
        tests_ok = ctx._tests_verify_ok(verify)

        proposal_id = str(uuid.uuid4())[:8]
        ctx.pending_proposals[proposal_id] = {
            "path": path, "code": new_code, "mode": "fix",
            "files": files, "diagnostics": diag_dicts,
            "syntax_ok": syntax_ok, "explanation": explanation,
        }
        ctx._persist_proposals()
        ctx.session.note_proposal(proposal_id)

        extra = ctx._proposal_response_extra(files)
        status = "Tests pass in verify." if tests_ok else "Tests still failing — review diff or try again."
        intro = (
            f"**Fix proposal** for `{path}` ({status})\n\n"
            f"{explanation or 'Changes ready to review.'}"
        )
        if diag_summary:
            intro += f"\n\n**Syntax check:**\n{diag_summary}"
        if verify and not tests_ok:
            intro += f"\n\n**Verify:**\n{verify}"
        intro += "\n\nReview the diff and hit **Apply changes** or say `apply`."

        yield {"type": "status", "message": "Proposal ready"}
        yield _stream_done({
            "ok": True,
            "message": intro,
            "module": "coding",
            "result_type": "proposal",
            "proposal_id": proposal_id,
            "path": path,
            "diff": diff,
            "explanation": explanation,
            "diagnostics": diag_dicts,
            "syntax_ok": syntax_ok,
            "agent_steps": [
                {"step": 1, "action": "pytest", "detail": "failures loaded", "ok": False},
            ],
            **extra,
        })

    @classmethod
    def coding_fix_tests(cls, ctx, params: dict, message: str) -> dict:
        for event in EngineeringOperations.coding_fix_tests_stream(ctx, params, message):
            if event.get("type") == "done":
                return event
        return _err("Fix task did not complete.")

    @classmethod
    def coding_fix(cls, ctx, params: dict, message: str) -> dict:
        path = EngineeringOperations.resolve_coding_path(ctx, params.get("path", ""))
        if not path:
            return _err(
                "Which file should I fix? Open a file in Cursor (with the ARIA extension) "
                "or say e.g. `fix data/scripts/duration.py`."
            )
        diagnosis = ctx._diagnosis_for_path(path)
        task = f"Fix based on diagnosis:\n{diagnosis}" if diagnosis else None
        if params.get("use_selection"):
            task = (task or "Fix the selected code.") + "\n\nSee Editor context for the selection."
        return EngineeringOperations.coding_propose(ctx, 
            path, "fix", task=task, editor_prompt=ctx._editor_task_suffix(params),
        )

    @classmethod
    def coding_improve(cls, ctx, params: dict, message: str) -> dict:
        path = EngineeringOperations.resolve_coding_path(ctx, params.get("path", ""))
        if not path:
            return _err("Which file should I improve?")
        return EngineeringOperations.coding_propose(ctx, 
            path, "improve", editor_prompt=ctx._editor_task_suffix(params),
        )

    @classmethod
    def coding_find(cls, ctx, params: dict, message: str) -> dict:
        query = params.get("query") or message
        matches = fs.find_files(query, ctx.coding._base())
        if not matches:
            return _ok(f"I couldn't find any files matching '{query}'.", module="coding")
        for m in matches[:3]:
            ctx.session.note_file(m)
        lines = "\n".join(matches[:30])
        return _ok(f"Found {len(matches)} file(s):\n\n{lines}", module="coding")

    @classmethod
    def coding_search(cls, ctx, params: dict, message: str) -> dict:
        query = params.get("query") or message
        ctx.session.note_search(query)
        results = fs.search_files(query, ctx.coding._base())
        if not results:
            return _ok(f"No matches for '{query}'.", module="coding")
        lines = "\n".join(f"{p}:{n}: {line}" for p, n, line in results[:40])
        return _ok(f"Found {len(results)} match(es):\n\n{lines}", module="coding")

    @classmethod
    def coding_run(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.project_runner import run_script, runner_info
        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I run?")
        try:
            resolved = fs.resolve_path(path, base=ctx.coding._base())
            ctx.session.note_file(str(resolved))
            result = run_script(resolved, ctx.coding._base(), timeout=60)
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n--- stderr ---\n{result.stderr}"
            info = runner_info(ctx.coding._base())
            header = f"_Runner: `{info['python']}`"
            if info.get("firejail"):
                header += " (firejail)"
            return _ok(f"{header}\n\n{output or '(no output)'}", module="coding", type="code_output")
        except Exception as e:
            return _err(str(e))

    @classmethod
    def coding_project(cls, ctx, params: dict, message: str) -> dict:
        path = params.get("path") or str(PROJECT_ROOT)
        ctx.coding.project_root, ctx.coding.project_files = fs.scan_project(path)
        ctx.coding.search_root = ctx.coding.project_root
        return _ok(
            f"I've indexed **{len(ctx.coding.project_files)}** files. "
            "Ask me to review the project whenever you're ready.",
            module="coding",
        )

    @classmethod
    def coding_review(cls, ctx, params: dict, message: str) -> dict:
        if not ctx.coding.project_root:
            EngineeringOperations.coding_project(ctx, {}, message)
        if not ctx.coding.project_root:
            return _err("No project loaded.")
        important = []
        for p in ctx.coding.project_files:
            lower = p.lower()
            if (
                ".history" not in lower and ".log" not in lower
                and (
                    "readme" in lower
                    or lower.endswith(("main.py", "app.py", "server.py", "config.py"))
                )
            ):
                important.append(p)
        if not important:
            important = [
                p for p in ctx.coding.project_files
                if p.lower().endswith((".py", ".sh", ".json", ".yml"))
            ][:25]
        context = ""
        for p in important[:20]:
            full = ctx.coding.project_root / p
            c = fs.read_file(str(full), base=ctx.coding.project_root)
            if c.startswith("ERROR:"):
                continue
            chunk = f"\n\nFILE: {p}\n\n{c[:1000]}"
            if len(context) + len(chunk) > 12000:
                break
            context += chunk
        prompt = f"""You are a senior software architect. Review this project. Do NOT generate code.
Focus on risks, improvements, and architecture.

PROJECT ROOT: {ctx.coding.project_root}
PROJECT: {context}"""
        answer = llm.ask(llm.review_model(), [{"role": "user", "content": prompt}])
        return _ok(answer, module="coding", type="review")

    @classmethod
    def coding_show(cls, ctx, params: dict, message: str) -> dict:
        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I show?")
        content = fs.read_file(path, base=ctx.coding._base())
        if content.startswith("ERROR:"):
            return _err(content)
        ctx.session.note_file(path)
        numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(content.splitlines(), 1))
        return _ok(f"**{path}**\n\n```\n{numbered[:8000]}\n```", module="coding")

    @classmethod
    def coding_job_result(cls, ctx, message: str, job_id: str, action: str) -> dict:
        return _ok(
            message,
            module="coding",
            type="coding_job",
            job_id=job_id,
            pending=True,
            action=action,
        )

    @classmethod
    def rename_symbol(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import rename as rename_util
        symbol = params.get("symbol", "")
        new_name = params.get("new_name", "")
        dry_run = params.get("dry_run", False)
        if not symbol or not new_name:
            m = re.search(r"rename\s+(\w+)\s+(?:to|as)\s+(\w+)", message, re.I)
            if m:
                symbol, new_name = m.group(1), m.group(2)
        if not symbol or not new_name:
            return _err('Usage: rename SYMBOL to NEW_NAME (or "rename foo to bar")')

        from jarvis import refactor_ast
        preview = refactor_ast.preview_rename_python_symbol_project(
            symbol, new_name, ctx.coding._base(),
        )
        files = preview.get("files") or []
        if not files:
            files = rename_util.rename_symbol_preview(symbol, new_name, root=ctx.coding._base())
        if not files:
            return _ok(f"No usages of `{symbol}` found in the project.", module="coding")
        if dry_run:
            paths = ", ".join(f["path"] for f in files[:10])
            return _ok(
                f"Would rename `{symbol}` → `{new_name}` in **{len(files)}** file(s): {paths}",
                module="coding",
            )
        explanation = f"Rename `{symbol}` → `{new_name}` across {len(files)} file(s)."
        return EngineeringOperations.store_refactor_proposal(ctx, files, explanation=explanation, mode="rename")

    @classmethod
    def find_references(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.code_context import find_references
        symbol = params.get("symbol", "")
        if not symbol:
            m = re.search(r"\b(?:find references|who uses|references for)\s+(\w+)", message, re.I)
            if m:
                symbol = m.group(1)
        if not symbol:
            return _err('Usage: find references SYMBOL (or "who uses parse_duration")')
        hits = find_references(symbol, ctx.coding._base())
        if not hits:
            return _ok(f"No references to `{symbol}` found.", module="coding")
        lines = "\n".join(f"- `{h['path']}:{h['line']}` — `{h['text'][:80]}`" for h in hits[:25])
        return _ok(f"**References to `{symbol}`** ({len(hits)}):\n\n{lines}", module="coding")

    @classmethod
    def coding_run_tests(cls, ctx, params: dict, message: str) -> dict:
        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file's tests? e.g. `run tests for data/scripts/duration.py`")
        resolved = fs.resolve_path(path, base=ctx.coding._base())
        from jarvis.coding_verify import collect_test_failures, verify_python_files
        failures = collect_test_failures(resolved, ctx.coding._base())
        if failures:
            return _ok(f"**Tests failed** for `{path}`:\n\n```\n{failures[:3000]}\n```", module="coding")
        report = verify_python_files([resolved], ctx.coding._base(), run_scripts=False)
        if "passed" in report.lower():
            return _ok(f"**Tests passed** for `{path}`.\n\n{report}", module="coding")
        return _ok(f"**Test run** for `{path}`:\n\n{report or 'No paired tests found.'}", module="coding")

    @classmethod
    def coding_run_command(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.project_runner import run_project_command
        cmd = params.get("command", "")
        if not cmd:
            m = re.search(r"\brun command[:\s]+(.+)", message, re.I)
            if m:
                cmd = m.group(1).strip()
        if not cmd:
            return _err("Usage: run command: pytest data/scripts/test_duration.py -q")
        try:
            result = run_project_command(cmd, ctx.coding._base(), timeout=120)
        except ValueError as e:
            return _err(str(e))
        out = ((result.stdout or "") + (result.stderr or "")).strip()[:4000]
        status = "OK" if result.returncode == 0 else f"exit {result.returncode}"
        return _ok(f"**Command** `{cmd}` — {status}\n\n```\n{out or '(no output)'}\n```", module="coding")

    @classmethod
    def git_pr(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import git_util
        title = params.get("title", "")
        body = params.get("body", "")
        if not title:
            m = re.search(r"\bcreate (?:a )?pull request[:\s]+(.+)", message, re.I)
            title = m.group(1).strip() if m else "Jarvis coding changes"
        result = git_util.create_pull_request(title, body, path=ctx.coding._base())
        if result.startswith("ERROR"):
            return _err(result)
        return _ok(f"**Pull request:** {result}", module="coding")

    @classmethod
    def coding_editor_status(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.editor_context import get_context, load_context
        ctx = get_context() or load_context()
        if not ctx.relative_file:
            return _ok(
                "No editor context synced.\n\n"
                "Install the Cursor extension: `./scripts/install-cursor-extension.sh` "
                "then reload Cursor and open a file.",
                module="coding",
            )
        fresh = get_context() is not None
        body = ctx.format_for_prompt(max_selection=1500)
        note = "live from Cursor" if fresh else "stale — click in Cursor or run **ARIA: Push Editor Context Now**"
        return _ok(f"**Editor context** ({note}):\n\n{body}", module="coding")

    @classmethod
    def coding_explain_selection(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.editor_context import get_context
        ctx = get_context()
        if not ctx or not ctx.has_selection():
            return _err(
                "No selection synced from Cursor. Select code, install the extension "
                "(`./scripts/install-cursor-extension.sh`), and try **ARIA: Push Editor Context Now**."
            )
        path = ctx.relative_file
        content = fs.read_file(path, base=ctx.coding._base())
        if content.startswith("ERROR:"):
            return _err(content)
        explanation = llm.diagnose_code(
            message or "Explain what this selected code does and any issues.",
            path=path,
            content=content,
            context=ctx.format_for_prompt(),
            errors="",
        )
        ctx.session.note_file(path)
        return _ok(
            f"**Selection in `{path}`:**\n\n{explanation}",
            module="coding",
            type="diagnose",
            path=path,
        )

    @classmethod
    def coding_lsp(cls, ctx, params: dict, message: str) -> dict:
        return EngineeringOperations.syntax_check(ctx, params, message)

    @classmethod
    def lsp_line_col(cls, ctx, params: dict) -> tuple[int, int]:
        try:
            line = int(params.get("line") or 1)
        except (TypeError, ValueError):
            line = 1
        try:
            column = int(params.get("column") or 1)
        except (TypeError, ValueError):
            column = 1
        return max(1, line), max(1, column)

    @classmethod
    def lsp_definition(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_definition

        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file? Give a path or open one in Cursor.", module="coding")
        line, col = EngineeringOperations.lsp_line_col(ctx, params)
        out = lsp_definition(path, ctx.coding._base(), line, col)
        if not out.get("ok"):
            return _err(out.get("message", "LSP definition failed"), module="coding")
        locs = out.get("locations") or []
        if not locs:
            return _ok(f"No definition found at `{path}`:{line}", module="coding", locations=[])
        lines = [f"- `{loc['path']}`:{loc['line']}:{loc['column']}" for loc in locs[:10]]
        return _ok(
            f"**Definition** ({len(locs)}):\n" + "\n".join(lines),
            module="coding",
            locations=locs,
        )

    @classmethod
    def lsp_references(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_references

        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file?", module="coding")
        line, col = EngineeringOperations.lsp_line_col(ctx, params)
        out = lsp_references(path, ctx.coding._base(), line, col)
        if not out.get("ok"):
            return _err(out.get("message", "LSP references failed"), module="coding")
        refs = out.get("references") or []
        if not refs:
            return _ok(f"No references for `{path}`:{line}", module="coding", references=[])
        lines = [f"- `{r['path']}`:{r['line']}" for r in refs[:20]]
        more = f"\n… and {len(refs) - 20} more" if len(refs) > 20 else ""
        return _ok(
            f"**References** ({len(refs)}):\n" + "\n".join(lines) + more,
            module="coding",
            references=refs,
        )

    @classmethod
    def lsp_hover(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_hover

        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file?", module="coding")
        line, col = EngineeringOperations.lsp_line_col(ctx, params)
        out = lsp_hover(path, ctx.coding._base(), line, col)
        if not out.get("ok"):
            return _err(out.get("message", "LSP hover failed"), module="coding")
        text = (out.get("hover") or "").strip() or "(no hover info)"
        return _ok(f"**Hover** `{path}`:{line}\n\n{text}", module="coding", hover=text)

    @classmethod
    def lsp_format(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_format

        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I format?", module="coding")
        write = bool(params.get("write", True))
        out = lsp_format(path, ctx.coding._base(), write=write)
        if not out.get("ok"):
            return _err(out.get("message", "LSP format failed"), module="coding")
        if write:
            return _ok(f"Formatted **`{path}`** via language server.", module="coding", path=path)
        return _ok(f"Format preview for **`{path}`** (not written).", module="coding", formatted=out.get("formatted", ""))

    @classmethod
    def lsp_symbols(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_symbols

        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file?", module="coding")
        out = lsp_symbols(path, ctx.coding._base())
        if not out.get("ok"):
            return _err(out.get("message", "LSP symbols failed"), module="coding")
        symbols = out.get("symbols") or []
        if not symbols:
            return _ok(f"No symbols in `{path}`", module="coding", symbols=[])
        lines = [f"- {s['name']} (L{s['line']})" for s in symbols[:40]]
        more = f"\n… and {len(symbols) - 40} more" if len(symbols) > 40 else ""
        return _ok(
            f"**Symbols in `{path}`** ({len(symbols)}):\n" + "\n".join(lines) + more,
            module="coding",
            symbols=symbols,
        )

    @classmethod
    def syntax_check(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.lsp import check_any, tools_status as lsp_tools
        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I check?")
        resolved = fs.resolve_path(path, base=ctx.coding._base())
        if not resolved.exists():
            return _err(f"File not found: {path}")
        deep = params.get("deep", True)
        if isinstance(deep, str):
            deep = deep.lower() not in ("0", "false", "no")
        diags = check_any(resolved, deep=deep)
        tools = {**available_tools(), **lsp_tools()}
        tool_line = ", ".join(k for k, v in tools.items() if v)
        if not diags:
            return _ok(
                f"No issues in **{path}**.\n\n_Checkers: {tool_line}_",
                module="coding",
                diagnostics=[],
                syntax_ok=True,
            )
        summary = format_diagnostics(diags)
        ok = not any(d.severity == "error" for d in diags)
        return _ok(
            f"**Syntax/lint for `{path}`:**\n\n{summary}\n\n_Checkers: {tool_line}_",
            module="coding",
            diagnostics=diagnostics_to_dicts(diags),
            syntax_ok=ok,
        )

    @classmethod
    def coding_agent(cls, ctx, params: dict, message: str, on_step=None) -> dict:
        task_text = params.get("task") or message
        path = ctx.session.resolve_path(params.get("path", "")) or None
        mode = params.get("mode", "agent")
        task_id = params.get("task_id") or ""
        ct = None
        initial_errors = ""

        if not task_id:
            ct = ctx.task_manager.create(task_text[:120], path=path or "", mode=mode)
            task_id = ct.id
        else:
            ct = ctx.task_manager.get(task_id)
            if ct:
                ctx.task_manager.resume(task_id)
                path = path or ct.path or None
                task_text = ct.checkpoint.get("task") or task_text
                mode = ct.checkpoint.get("mode") or mode
                initial_errors = ct.checkpoint.get("last_errors") or ""

        agent = CodingAgent(ctx.coding._base(), max_steps=int(params.get("max_steps") or 5))
        result = agent.run(
            task_text,
            path=path,
            mode=mode,
            initial_errors=initial_errors,
        )
        for s in result.steps:
            step_dict = {"step": s.step, "action": s.action, "detail": s.detail, "ok": s.ok}
            if on_step:
                on_step(step_dict)
            ctx.task_manager.add_step(task_id, s.action, s.detail, ok=s.ok)

        if not result.ok:
            ctx.task_manager.save_state(task_id, last_errors=result.message)
            ctx.task_manager.complete(task_id, ok=False)
            return _err(result.message)

        if result.diagnose_only:
            ctx.task_manager.complete(task_id, ok=True)
            return _ok(result.message, module="coding", type="diagnose", task_id=task_id)

        proposal_id, payload = ctx._store_agent_proposal(
            result.files, mode=result.mode, explanation=result.explanation, task_id=task_id,
        )
        ctx.task_manager.save_state(
            task_id,
            task_text=task_text,
            path=path or "",
            mode=mode,
            files=[f["path"] for f in result.files],
            proposal_id=proposal_id,
        )
        ctx.task_manager.complete(task_id, ok=True)

        extra = ctx._proposal_response_extra(result.files)
        steps_note = "\n".join(f"{s.step}. {s.action}: {s.detail}" for s in result.steps[-6:])
        diag_summary = payload.get("_diag_summary", "")
        intro = f"{result.message}\n\n**Steps:**\n{steps_note}"
        if diag_summary:
            intro += f"\n\n**Syntax check:**\n{diag_summary}"
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        return _ok(
            intro,
            module="coding",
            type="proposal",
            proposal_id=proposal_id,
            path=result.files[0]["path"] if result.files else "",
            diff=result.diff,
            explanation=result.explanation,
            agent_steps=[{"step": s.step, "action": s.action, "detail": s.detail} for s in result.steps],
            diagnostics=payload.get("diagnostics", []),
            syntax_ok=payload.get("syntax_ok", True),
            task_id=task_id,
            **extra,
        )

    @classmethod
    def coding_task(cls, ctx, params: dict, message: str) -> dict:
        action = (params.get("action") or "").lower()
        lower = message.lower().strip()

        if re.search(r"\b(list|show)\b.*\b(tasks?)\b", lower) or action == "list":
            tasks = ctx.task_manager.list_tasks()
            if not tasks:
                return _ok("No coding tasks yet.", module="coding")
            lines = "\n".join(
                f"- `{t.id}` **{t.title[:60]}** — {t.status} ({len(t.steps)} steps)"
                for t in tasks[:15]
            )
            return _ok(f"**Coding tasks:**\n\n{lines}", module="coding")

        if re.search(r"\bpause\b.*\b(task|coding)\b", lower) or action == "pause":
            active = ctx.task_manager.active()
            tid = params.get("task_id") or (active.id if active else "")
            if not tid:
                return _err("No active coding task to pause.")
            ctx.task_manager.pause(tid)
            return _ok(f"Paused task `{tid}`. Say **resume task** to continue.", module="coding", task_id=tid)

        if re.search(r"\bresume\b.*\b(task|coding)\b", lower) or action == "resume":
            tid = params.get("task_id") or ""
            task = ctx.task_manager.get(tid) if tid else ctx.task_manager.active()
            if not task:
                return _err("No task to resume.")
            ctx.task_manager.resume(task.id)
            checkpoint = task.checkpoint
            resume_msg = checkpoint.get("task") or task.title
            return ctx._enqueue_coding(
                {
                    "task": resume_msg,
                    "path": task.path,
                    "mode": task.mode,
                    "task_id": task.id,
                    "max_steps": 5,
                },
                resume_msg,
            )

        active = ctx.task_manager.active()
        if active:
            lines = "\n".join(f"{s.step}. {s.action}: {s.detail}" for s in active.steps[-10:])
            return _ok(
                f"**Active task** `{active.id}` — {active.status}\n\n{lines}",
                module="coding",
                task_id=active.id,
            )
        return _ok("No active coding task. Start one with **implement …**", module="coding")

    @classmethod
    def extract_function(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import refactor_ast
        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file?")
        resolved = fs.resolve_path(path, base=ctx.coding._base())
        func_name = params.get("name", "")
        start = int(params.get("start_line") or params.get("start") or 0)
        end = int(params.get("end_line") or params.get("end") or 0)
        if not func_name or not start or not end:
            m = re.search(
                r"extract\s+(?:lines?\s+)?(\d+)\s*[-–]\s*(\d+)\s+(?:as|into|to)\s+(\w+)",
                message, re.I,
            )
            if m:
                start, end, func_name = int(m.group(1)), int(m.group(2)), m.group(3)
        if not func_name or not start or not end:
            return _err('Usage: extract lines 10-25 as my_function from path/to/file.py')
        dry_run = params.get("dry_run", False)
        result = refactor_ast.extract_function(resolved, start, end, func_name, dry_run=True)
        if result.get("error"):
            return _err(result["error"])
        if not result.get("changed") or not result.get("code"):
            return _ok(f"No changes for `{func_name}` in **{path}**.", module="coding")
        if dry_run:
            return _ok(f"Would extract `{func_name}` from lines {start}-{end} in **{path}**.", module="coding")
        files = [{"path": result["path"], "code": result["code"]}]
        return EngineeringOperations.store_refactor_proposal(ctx, 
            files,
            explanation=f"Extract lines {start}-{end} as `{func_name}()` in **{path}**.",
            mode="extract",
        )

    @classmethod
    def move_module(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import refactor_ast
        from_p = params.get("from") or params.get("from_path", "")
        to_p = params.get("to") or params.get("to_path", "")
        if not from_p or not to_p:
            m = re.search(r"move\s+(\S+)\s+to\s+(\S+)", message, re.I)
            if m:
                from_p, to_p = m.group(1), m.group(2)
        if not from_p or not to_p:
            return _err('Usage: move jarvis/old_module.py to jarvis/new_module.py')
        dry_run = params.get("dry_run", False)
        preview = refactor_ast.preview_move_module(
            fs.resolve_path(from_p, base=ctx.coding._base()),
            fs.resolve_path(to_p, base=ctx.coding._base()),
            ctx.coding._base(),
        )
        if preview.get("error"):
            return _err(preview["error"])
        files = preview.get("files") or []
        if not files:
            return _ok(f"Nothing to change for move `{from_p}` → `{to_p}`.", module="coding")
        if dry_run:
            return _ok(
                f"Would move `{preview['from']}` → `{preview['to']}` "
                f"and update **{preview.get('imports_updated', 0)}** import(s).",
                module="coding",
            )
        return EngineeringOperations.store_refactor_proposal(ctx, 
            files,
            explanation=f"Move `{preview['from']}` → `{preview['to']}` and update imports.",
            mode="move",
        )

    @classmethod
    def coding_refactor(cls, ctx, params: dict, message: str) -> dict:
        params = dict(params)
        params["mode"] = "refactor"
        params["task"] = params.get("task") or message
        return EngineeringOperations.coding_agent(ctx, params, message)

    @classmethod
    def coding_diagnose(cls, ctx, params: dict, message: str) -> dict:
        path = ctx.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I diagnose?")
        agent = CodingAgent(ctx.coding._base())
        result = agent.diagnose(path, params.get("task") or message)
        if not result.ok:
            return _err(result.message)
        diag_id = str(uuid.uuid4())[:8]
        ctx.pending_diagnoses[diag_id] = {"path": path, "explanation": result.message}
        ctx.session.note_file(path)
        return _ok(
            f"**Diagnosis for `{path}`:**\n\n{result.message}\n\n"
            "Say **fix it** to apply a fix based on this diagnosis.",
            module="coding",
            type="diagnose",
            diagnose_id=diag_id,
            path=path,
        )

    @classmethod
    def coding_chat(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import code_index
        from jarvis.trust_memory import filter_trusted_content

        query = params.get("query") or message
        parts = []
        code_ctx = code_index.context_for_query(query, limit=5)
        if code_ctx:
            parts.append(code_ctx)
        mem_hits = ctx.memory.search(query, limit=4)
        if mem_hits:
            mem_lines = []
            for m in mem_hits:
                line = filter_trusted_content(m.get("content", ""))
                if line:
                    mem_lines.append(f"- {line}")
            if mem_lines:
                parts.append("Relevant memory:\n" + "\n".join(mem_lines))
        if ctx.session.last_file:
            content = fs.read_file(ctx.session.last_file, base=ctx.coding._base())
            if not content.startswith("ERROR:"):
                parts.append(f"Last file ({ctx.session.last_file}):\n{content[:4000]}")
        doc_ctx, doc_warnings = rag.context_for_query(query)
        if doc_ctx:
            parts.append(doc_ctx)
        if doc_warnings:
            parts.extend(doc_warnings)
        context = "\n\n".join(parts)
        answer = llm.coding_chat_answer(query, context=context)
        return _ok(answer, module="coding", type="coding_chat")

    @classmethod
    def code_index(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import code_index
        root = params.get("path") or str(ctx.coding._base())
        chunks = code_index.build_index(Path(root))
        return _ok(
            f"Indexed **{len(chunks)}** code chunks from `{root}`. "
            "Ask coding questions or say \"search code for …\".",
            module="coding",
        )

    @classmethod
    def code_search(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import code_index
        query = params.get("query") or re.sub(
            r"^(search code for|find in code|where is)\s*",
            "",
            message,
            flags=re.I,
        ).strip()
        if not query:
            return _err("What should I search for in the codebase?")
        hits = code_index.search(query, limit=8)
        if not hits:
            return _ok(f"No semantic matches for '{query}'. Try `index code` first.", module="coding")
        lines = "\n\n".join(
            f"**{h['source']}**\n```\n{h['text'][:600]}\n```" for h in hits
        )
        for h in hits[:3]:
            ctx.session.note_file(h["source"])
        return _ok(f"Found {len(hits)} match(es) for **{query}**:\n\n{lines}", module="coding")

    @classmethod
    def git_commit(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import git_util
        msg = params.get("message") or ""
        if not msg:
            m = re.search(r"commit(?:\s+with\s+message)?[:\s]+(.+)", message, re.I)
            msg = m.group(1).strip() if m else ""
        if not msg:
            return _err('Provide a commit message, e.g. "commit: fix hello world script"')
        files = params.get("files")
        if isinstance(files, str):
            files = [files]
        result = git_util.commit(msg, path=ctx.coding._base(), files=files)
        if result.startswith("ERROR:"):
            return _err(result)
        return _ok(f"```\n{result}\n```", module="coding")

    @classmethod
    def git_branch(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import git_util
        name = params.get("name") or ""
        if not name:
            m = re.search(r"(?:create\s+)?branch\s+[`'\"]?([\w./-]+)", message, re.I)
            name = m.group(1) if m else ""
        if not name:
            return _err('Provide a branch name, e.g. "create branch feature/coding-agent"')
        result = git_util.create_branch(name, path=ctx.coding._base())
        if result.startswith("ERROR:"):
            return _err(result)
        return _ok(result, module="coding")

    @classmethod
    def git_summarize(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import git_util
        f = params.get("file", "")
        diff_text = git_util.summarize_diff(path=ctx.coding._base(), file=f or None)
        if diff_text in ("No changes.", "Not a git repository."):
            return _ok(diff_text, module="coding")
        summary = llm.ask(llm.general_model(), [{
            "role": "user",
            "content": f"Summarize this git diff in plain English (bullet points):\n\n```diff\n{diff_text[:12000]}\n```",
        }])
        return _ok(f"**Changes summary:**\n\n{summary}", module="coding")
