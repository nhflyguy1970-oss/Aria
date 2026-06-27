"""ARIA coder utilities — filesystem tools, tests, and self-fix/self-upgrade bridges."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

from jarvis import fs
from jarvis.config import PROJECT_ROOT

SMOKE_TEST_TARGETS = tuple(
    os.getenv(
        "JARVIS_DIAGNOSE_TESTS",
        "tests/test_coding.py tests/test_aria_coder.py tests/test_cursor_bridge.py "
        "tests/test_coding_jobs.py tests/test_coding_jobs_cancel.py",
    ).split()
)

_SELF_FIX_TRIGGER = re.compile(
    r"^(?:please\s+)?(?:(?:self[- ]?)?fix|heal|repair|diagnose and fix)\s+aria"
    r"(?:\s+(?:and\s+)?apply)?[.!]?\s*",
    re.I,
)


def list_dir(path: str, base: Path, *, limit: int = 200) -> list[dict[str, str]]:
    return fs.list_dir(path, base=base, limit=limit)


def write_file_bridge(path: str, content: str, base: Path, *, backup: bool = True) -> dict[str, Any]:
    try:
        resolved = fs.resolve_path(path, base=base)
        backup_path = ""
        if backup and resolved.is_file():
            backup_path = fs.backup_file(path, base=base)
        fs.write_file(path, content, base=base)
        return {
            "ok": True,
            "path": str(resolved),
            "bytes": len(content.encode("utf-8")),
            "backup": backup_path,
        }
    except fs.PathError as e:
        return {"ok": False, "error": str(e)}
    except OSError as e:
        return {"ok": False, "error": str(e)}


def run_tests_bridge(
    target: str,
    base: Path,
    *,
    timeout: int = 180,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    from jarvis.project_runner import run_pytest

    args = list(extra_args or [])
    for flag in ("-q", "--tb=short"):
        if flag not in args:
            args.append(flag)
    result = run_pytest(target or "tests/", base, timeout=timeout, extra_args=args)
    stdout = ((result.stdout or "") + (result.stderr or "")).strip()
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "output": stdout[-8000:],
        "target": target or "tests/",
    }


def normalize_self_fix_task(task: str) -> str:
    """Strip chat trigger phrases so 'fix aria' does not become the LLM task."""
    text = (task or "").strip()
    text = _SELF_FIX_TRIGGER.sub("", text).strip()
    text = re.sub(r"^[:—\-]\s*", "", text).strip()
    if text.lower() in ("", "fix aria", "heal aria", "repair aria"):
        return ""
    return text


def _run_pytest_targets(
    targets: list[str],
    base: Path,
    *,
    timeout: int = 180,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess:
    from jarvis.project_runner import project_python

    py = project_python(base)
    args = list(extra_args or ["-q", "--tb=line", "--maxfail=3"])
    cmd = [py, "-m", "pytest", *targets, *args]
    return subprocess.run(
        cmd,
        cwd=str(base),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def aria_self_diagnose(base: Path | None = None, *, full: bool = False) -> dict[str, Any]:
    """Quick import + pytest smoke for ARIA health (full suite optional)."""
    from jarvis.project_runner import project_python, run_pytest

    root = (base or PROJECT_ROOT).resolve()
    py = project_python(root)
    import_check = subprocess.run(
        [py, "-c", "import jarvis.gui.server; import jarvis.assistant; import jarvis.aria_coder"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=90,
    )
    if full:
        pytest = run_pytest(
            "tests/",
            root,
            timeout=600,
            extra_args=["-q", "--tb=line", "--maxfail=5"],
            sandbox=False,
        )
        scope = "full"
    else:
        targets = [t for t in SMOKE_TEST_TARGETS if (root / t).exists()]
        if not targets:
            targets = ["tests/test_coding.py"]
        pytest = _run_pytest_targets(targets, root, timeout=120)
        scope = "smoke"
    combined = ((pytest.stdout or "") + (pytest.stderr or "")).strip()
    return {
        "ok": import_check.returncode == 0 and pytest.returncode == 0,
        "import_ok": import_check.returncode == 0,
        "import_error": (import_check.stderr or import_check.stdout or "")[-1500:],
        "pytest_ok": pytest.returncode == 0,
        "pytest_output": combined[-6000:],
        "pytest_code": pytest.returncode,
        "scope": scope,
        "targets": list(SMOKE_TEST_TARGETS) if not full else ["tests/"],
    }


def _infer_path_from_pytest(output: str) -> str:
    for line in output.splitlines():
        m = re.search(r"FAILED\s+(\S+?)::", line)
        if m:
            test_path = m.group(1).replace("::", "/")
            if test_path.endswith(".py"):
                return test_path
        m = re.search(r"(\S+?\.py):\d+:", line)
        if m:
            return m.group(1)
    return ""


def _record_self_fix_experience(assistant, *, ok: bool, task: str, detail: str) -> None:
    try:
        from jarvis.experience_memory import record_experience

        record_experience(
            assistant.memory,
            outcome="success" if ok else "failure",
            task=task[:160] or "ARIA self-fix",
            detail=detail[:500],
            module="coding",
            context="aria_self_fix",
        )
    except Exception:
        pass


def self_fix_aria(
    assistant,
    task: str = "",
    *,
    apply: bool = False,
    max_steps: int = 5,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Diagnose ARIA, run coding agent on failures, optionally apply proposal."""
    base = assistant.coding._base()
    fix_task = normalize_self_fix_task(task)
    diag = aria_self_diagnose(base, full=False)
    path = ""

    if not fix_task:
        if diag["pytest_ok"] and diag["import_ok"]:
            return {
                "ok": True,
                "message": "ARIA diagnostics pass — no fixes needed.",
                "diagnostics": diag,
            }
        path = _infer_path_from_pytest(diag.get("pytest_output", ""))
        if not path and not diag["import_ok"]:
            path = "jarvis/gui/server.py"
        fix_task = (
            "Fix the failing tests or import errors shown in diagnostics. "
            "Prefer minimal correct changes in jarvis/ and tests/."
        )
        if diag.get("pytest_output"):
            fix_task += f"\n\nPytest output (tail):\n{diag['pytest_output'][-3000:]}"

    if cancel_check and cancel_check():
        return {"ok": False, "message": "Cancelled.", "diagnostics": diag}

    agent_result = assistant._coding_agent(
        {
            "task": fix_task,
            "path": path or None,
            "max_steps": max_steps,
            "mode": "fix",
            "_cancel_check": cancel_check,
        },
        fix_task,
    )
    out: dict[str, Any] = {
        "ok": agent_result.get("ok", False),
        "message": agent_result.get("message", ""),
        "diagnostics": diag,
        "proposal_id": agent_result.get("proposal_id"),
        "agent_steps": agent_result.get("agent_steps"),
    }
    if apply and agent_result.get("proposal_id"):
        applied = assistant.apply_proposal(agent_result["proposal_id"])
        out["apply"] = applied
        out["ok"] = applied.get("ok", False)
        if applied.get("ok"):
            verify = aria_self_diagnose(base, full=False)
            out["verify"] = verify
            out["message"] = (
                f"{applied.get('message', 'Applied.')}\n\n"
                f"Re-check: imports={'ok' if verify['import_ok'] else 'fail'}, "
                f"pytest={'ok' if verify['pytest_ok'] else 'fail'} ({verify.get('scope', 'smoke')})"
            )
            _record_self_fix_experience(assistant, ok=verify["ok"], task=fix_task, detail=out["message"])
        else:
            _record_self_fix_experience(assistant, ok=False, task=fix_task, detail=applied.get("message", ""))
    elif not out["ok"]:
        _record_self_fix_experience(assistant, ok=False, task=fix_task, detail=out.get("message", ""))
    return out


def propose_agent_bridge(
    task: str,
    path: str,
    base: Path,
    *,
    max_steps: int = 5,
    mode: str = "agent",
) -> dict[str, Any]:
    from jarvis.cursor_bridge import _assistant

    _ = base
    return _assistant()._coding_agent(
        {"task": task, "path": path, "max_steps": max_steps, "mode": mode},
        task,
    )


def self_upgrade_bridge(task: str, *, max_steps: int = 4) -> dict[str, Any]:
    from jarvis.cursor_bridge import _assistant
    from jarvis.self_upgrade import run_pipeline

    return run_pipeline(_assistant(), task, max_steps=max_steps)
