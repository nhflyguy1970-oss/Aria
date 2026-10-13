"""The coding-agent result contract.

Every run reports six separate things, because they are different kinds of
fact:

  requested   what the owner approved (the plan)
  attempted   what the agent reports doing (commands, edits) — its word
  changed     what git shows changed in the workspace — ARIA's observation
  tests_run   tests ARIA ran itself, sandboxed, with exit codes
  verified    statements ARIA checked
  unverified  the agent's claims ARIA did not (or could not) check

``success`` is True only for verified completion. An agent exiting 0 is
necessary, never sufficient.
"""

from __future__ import annotations

from typing import Any

from jarvis.coding_agents.discovery import READ_ONLY

# Terminal run states.
COMPLETED = "completed"  # read-only task finished within bounds; findings are the agent's
VERIFIED = "verified"  # changes made and ARIA's tests passed
UNVERIFIED = "changes_unverified"  # changes made; no test command to verify them
TESTS_FAILED = "tests_failed"
NO_CHANGES = "no_changes"
FAILED = "failed"
TIMEOUT = "timeout"
CANCELLED = "cancelled"
INTERRUPTED = "interrupted"  # ARIA stopped mid-run (restart); never re-run automatically
VIOLATION = "boundary_violation"
REFUSED = "refused"
TERMINAL = (COMPLETED, VERIFIED, UNVERIFIED, TESTS_FAILED, NO_CHANGES, FAILED, TIMEOUT, CANCELLED,
            INTERRUPTED, VIOLATION, REFUSED)


def verdict(
    *,
    mode: str,
    exit_code: int | None,
    timed_out: bool,
    cancelled: bool,
    changes: dict[str, Any] | None,
    tests: dict[str, Any] | None,
    protected_before: dict[str, Any] | None,
    protected_after: dict[str, Any] | None,
    protected_report: dict[str, Any] | None = None,
    config_before: dict[str, Any] | None,
    config_after: dict[str, Any] | None,
    agent_claims: list[str],
    report_errors: list[str],
    final_message: str,
) -> dict[str, Any]:
    changes = changes or {}
    files = changes.get("files") or []
    verified: list[str] = []
    problems: list[str] = []

    if protected_report is not None:
        if protected_report["violations"]:
            shown = ", ".join(protected_report["violations"][:5])
            more = len(protected_report["violations"]) - 5
            problems.append(f"a protected path changed during the run: {shown}" + (f" (+{more} more)" if more > 0 else ""))
        else:
            aria = len(protected_report["runtime_writes"]) + len(protected_report["controller_writes"])
            verified.append(f"protected paths unchanged ({protected_report['checked_files']} files checked"
                            + (f"; {aria} ARIA runtime writes attributed)" if aria else ")"))
    elif protected_before is not None and protected_after is not None:
        if protected_before != protected_after:
            problems.append("a protected path changed during the run")
        else:
            verified.append(f"protected paths unchanged ({len(protected_before)} checked)")
    if config_before is not None and config_after is not None and config_before != config_after:
        problems.append("the agent's own permission/config files changed during the run")
    push_url = changes.get("push_url")
    if push_url is not None and push_url and "no-push://" not in push_url:
        problems.append("workspace push URL was changed")

    if cancelled:
        status, reason = CANCELLED, "cancelled by the owner"
    elif timed_out:
        status, reason = TIMEOUT, "time limit reached; the agent was stopped"
    elif problems:
        status, reason = VIOLATION, "; ".join(problems)
    elif exit_code != 0:
        status, reason = FAILED, f"agent exited with code {exit_code}"
    elif mode == READ_ONLY:
        if files:
            status, reason = VIOLATION, f"read-only task changed {len(files)} file(s)"
        elif not (final_message or "").strip():
            status, reason = FAILED, "agent exited 0 but produced no report"
        else:
            status, reason = COMPLETED, "read-only task finished within bounds; findings are unverified"
            verified.append("no files changed (git)")
    elif not files:
        status, reason = NO_CHANGES, "agent exited 0 but git shows no changes"
    elif tests and tests.get("ran"):
        if tests.get("passed"):
            status, reason = VERIFIED, f"{len(files)} file(s) changed and ARIA's test run passed"
            verified.append(f"tests passed when ARIA ran `{tests.get('command')}`")
        else:
            status, reason = TESTS_FAILED, f"ARIA's test run failed (exit {tests.get('exit_code')})"
    else:
        status, reason = UNVERIFIED, "files changed; no test command configured, so not verified"

    if files:
        verified.append(f"{len(files)} file(s) changed per git diff")
    if exit_code is not None and not cancelled and not timed_out:
        verified.append(f"agent process exited {exit_code}")

    contradicted = []
    if tests and tests.get("ran") and not tests.get("passed"):
        contradicted = [c for c in agent_claims if "test" in c.lower() or "pass" in c.lower()]

    return {
        "status": status,
        "success": status in (VERIFIED, COMPLETED) and not problems,
        "verified_completion": status == VERIFIED,
        "reason": reason,
        "verified": verified,
        "unverified": [c for c in agent_claims if c not in contradicted],
        "contradicted_claims": contradicted,
        "problems": problems,
        "errors": report_errors[:5],
    }
