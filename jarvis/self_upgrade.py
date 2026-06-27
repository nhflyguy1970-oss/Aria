"""Semi-automatic self-upgrading code — git branch, change, test, report, merge on approval."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from jarvis.config import PROJECT_ROOT
from jarvis.upgrade_wizard import (
    get_session,
    normalize_rel_path,
    save_session,
    verify_proposal,
)

log = logging.getLogger("jarvis.self_upgrade")

_SELF_UPGRADE = re.compile(
    r"^(?:please\s+)?(?:"
    r"self[- ]?upgrad(?:e|ing)(?:\s+code)?[:\s]+.+|"
    r"run\s+self[- ]?upgrade[:\s]+.+"
    r")",
    re.I | re.S,
)


def pipeline_enabled() -> bool:
    return os.getenv("JARVIS_SELF_UPGRADE_PIPELINE", "1").lower() not in ("0", "false", "off", "no")


def is_self_upgrade_task(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False
    if _SELF_UPGRADE.match(text):
        return True
    lower = text.lower()
    return bool(
        re.search(
            r"\b(self[- ]?upgrad(?:e|ing)(?:\s+code)?|run\s+self[- ]?upgrade\s+pipeline)\b",
            lower,
        )
    )


def parse_self_upgrade_task(message: str) -> str:
    text = (message or "").strip()
    for pat in (
        r"^self[- ]?upgrad(?:e|ing)(?:\s+code)?[:\s]+(.+)$",
        r"^run\s+self[- ]?upgrade(?:\s+pipeline)?[:\s]+(.+)$",
    ):
        m = re.match(pat, text, re.I | re.S)
        if m:
            return m.group(1).strip()
    return re.sub(
        r"^(please\s+)?(self[- ]?upgrad(?:e|ing)(?:\s+code)?|run\s+self[- ]?upgrade)[:\s]*",
        "",
        text,
        flags=re.I,
    ).strip() or text


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (text or "").lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s[:36] or "upgrade")


def branch_name_for_task(task: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    return f"aria/upgrade-{_slugify(task)}-{stamp}"


def _abort_branch(base_branch: str, upgrade_branch: str) -> list[str]:
    from jarvis.git_util import checkout_branch, delete_branch

    notes: list[str] = []
    ok, out = checkout_branch(base_branch)
    notes.append(out if ok else f"checkout failed: {out}")
    ok, out = delete_branch(upgrade_branch, force=True)
    notes.append(out if ok else f"delete branch: {out}")
    return notes


def run_pipeline(assistant, task: str, *, max_steps: int = 4) -> dict[str, Any]:
    """Create branch → propose → apply → commit → test → report (no merge)."""
    from jarvis.git_util import (
        commit,
        create_branch,
        current_branch,
        has_local_changes,
        is_repo,
    )

    task = (task or "").strip()
    if not task:
        return {"ok": False, "message": "Describe the self-upgrade — e.g. `self upgrade: add /api/ping`."}

    if not pipeline_enabled():
        return {"ok": False, "message": "Self-upgrade pipeline disabled (`JARVIS_SELF_UPGRADE_PIPELINE=0`)."}

    if not is_repo():
        return {
            "ok": False,
            "message": "Self-upgrade pipeline needs a git repository. Initialize git or use manual **upgrade jarvis:** flow.",
        }

    if has_local_changes():
        return {
            "ok": False,
            "message": "Working tree has uncommitted changes. Commit or stash before running self-upgrade.",
        }

    base_branch = current_branch() or "main"
    upgrade_branch = branch_name_for_task(task)

    branch_msg = create_branch(upgrade_branch)
    if branch_msg.startswith("ERROR:"):
        return {"ok": False, "message": branch_msg}

    try:
        propose = assistant._upgrade_wizard(
            {"task": task, "max_steps": max_steps},
            f"self upgrade: {task}",
        )
        if not propose.get("ok"):
            _abort_branch(base_branch, upgrade_branch)
            return propose

        pid = propose.get("proposal_id") or assistant.session.last_proposal_id
        verify = assistant._upgrade_verify({"proposal_id": pid}, "verify upgrade")
        verified = bool(verify.get("ok"))

        if not verified:
            _abort_branch(base_branch, upgrade_branch)
            session = get_session() or {}
            session.update({
                "pipeline": True,
                "branch": upgrade_branch,
                "base_branch": base_branch,
                "step": "verify_failed",
                "verified": False,
            })
            save_session(session)
            return {
                "ok": False,
                "message": (
                    f"**Self-upgrade stopped** — tests failed on proposal (branch `{upgrade_branch}` removed).\n\n"
                    f"{verify.get('message', '')}\n\n"
                    "Fix the task description and try again, or use **upgrade jarvis:** for manual steps."
                ),
                "type": "self_upgrade_failed",
                "upgrade_wizard": True,
                "pipeline": True,
                "verified": False,
                "proposal_id": pid,
            }

        apply = assistant._upgrade_apply({"proposal_id": pid, "_confirmed": True}, "apply upgrade")
        if not apply.get("ok"):
            _abort_branch(base_branch, upgrade_branch)
            return apply

        proposal = assistant._upgrade_proposal(pid) or {}
        paths = [normalize_rel_path(f.get("path") or "") for f in proposal.get("files") or [] if f.get("path")]
        commit_msg = f"ARIA self-upgrade: {task[:120]}"
        commit_out = commit(commit_msg, files=paths or None)
        if commit_out.startswith("ERROR:"):
            _abort_branch(base_branch, upgrade_branch)
            return {"ok": False, "message": commit_out, "type": "self_upgrade_failed", "pipeline": True}

        post_ok, post_detail = verify_proposal(proposal, base=PROJECT_ROOT)
        session = get_session() or {}
        session.update({
            "pipeline": True,
            "branch": upgrade_branch,
            "base_branch": base_branch,
            "proposal_id": pid,
            "verified": post_ok,
            "verify_log": post_detail[:4000],
            "snapshot_id": apply.get("snapshot_id") or session.get("snapshot_id", ""),
            "task": task,
            "step": "awaiting_merge" if post_ok else "verify_failed_on_branch",
            "commit": commit_out[:200],
        })
        save_session(session)

        files_note = "\n".join(f"- `{p}`" for p in paths)
        if post_ok:
            body = (
                f"**Self-upgrade pipeline complete** — ready for your approval.\n\n"
                f"**Branch:** `{upgrade_branch}` (from `{base_branch}`)\n"
                f"**Commit:** {commit_out[:160]}\n\n"
                f"**Files:**\n{files_note}\n\n"
                f"**Tests:** passed\n\n{post_detail[:2000]}\n\n"
                "Say **merge upgrade** to merge into your base branch, or **abort upgrade** to discard the branch."
            )
            return {
                "ok": True,
                "message": body,
                "type": "self_upgrade_ready",
                "upgrade_wizard": True,
                "pipeline": True,
                "verified": True,
                "proposal_id": pid,
                "branch": upgrade_branch,
                "base_branch": base_branch,
                "awaiting_merge": True,
            }

        body = (
            f"**Self-upgrade applied on branch** `{upgrade_branch}` but **post-commit tests failed**.\n\n"
            f"{post_detail[:2000]}\n\n"
            "Say **abort upgrade** to discard the branch, or fix manually on the branch."
        )
        return {
            "ok": False,
            "message": body,
            "type": "self_upgrade_verify_failed",
            "upgrade_wizard": True,
            "pipeline": True,
            "verified": False,
            "branch": upgrade_branch,
            "base_branch": base_branch,
            "proposal_id": pid,
        }
    except Exception as exc:
        log.exception("Self-upgrade pipeline failed")
        _abort_branch(base_branch, upgrade_branch)
        return {"ok": False, "message": f"Self-upgrade pipeline error: {exc}", "pipeline": True}


def merge_pipeline(assistant, *, force: bool = False) -> dict[str, Any]:
    from jarvis.git_util import checkout_branch, current_branch, delete_branch, merge_branch

    session = get_session() or {}
    if not session.get("pipeline"):
        return {
            "ok": False,
            "message": "No self-upgrade pipeline session. Run **self upgrade: …** first.",
        }

    branch = (session.get("branch") or "").strip()
    base = (session.get("base_branch") or current_branch() or "main").strip()
    if not branch:
        return {"ok": False, "message": "Pipeline session missing upgrade branch."}

    if session.get("step") != "awaiting_merge" and not force:
        return {
            "ok": False,
            "message": (
                f"Upgrade is not ready to merge (step: `{session.get('step')}`). "
                "Tests must pass first, or say **merge upgrade anyway** to force."
            ),
        }

    if not session.get("verified") and not force:
        return {
            "ok": False,
            "message": "Tests did not pass. Say **merge upgrade anyway** to force merge.",
        }

    ok, msg = merge_branch(branch, base=base)
    if not ok:
        return {"ok": False, "message": f"Merge failed: {msg}"}

    delete_branch(branch, force=True)
    session["step"] = "merged"
    session["merged"] = True
    save_session(session)

    restart = ""
    from jarvis.upgrade_wizard import requires_jarvis_restart

    proposal = assistant._upgrade_proposal(session.get("proposal_id")) or {}
    if requires_jarvis_restart(proposal.get("files") or []):
        from jarvis.branding import assistant_name

        restart = f"\n\n**Restart {assistant_name()}** to load server/GUI changes."

    return {
        "ok": True,
        "message": (
            f"**Merged** `{branch}` → `{base}`.\n\n{msg}"
            f"{restart}\n\nSnapshot `{session.get('snapshot_id', '')}` kept for rollback if needed."
        ),
        "type": "self_upgrade_merged",
        "upgrade_wizard": True,
        "pipeline": True,
        "branch": branch,
        "base_branch": base,
    }


def abort_pipeline(assistant) -> dict[str, Any]:
    from jarvis.upgrade_wizard import rollback_snapshot

    session = get_session() or {}
    if not session.get("pipeline"):
        return {"ok": False, "message": "No active self-upgrade pipeline to abort."}

    branch = (session.get("branch") or "").strip()
    base = (session.get("base_branch") or "main").strip()
    notes: list[str] = []

    if session.get("snapshot_id"):
        ok, msg, _restored = rollback_snapshot(session.get("snapshot_id"))
        if ok:
            notes.append(msg)

    if branch:
        notes.extend(_abort_branch(base, branch))

    session["step"] = "aborted"
    session["aborted"] = True
    save_session(session)

    return {
        "ok": True,
        "message": "**Self-upgrade aborted.**\n\n" + "\n".join(notes),
        "type": "self_upgrade_aborted",
        "pipeline": True,
    }


def is_merge_command(message: str) -> bool:
    lower = (message or "").lower()
    return bool(re.search(r"\b(merge upgrade|approve upgrade|approve merge)\b", lower))


def is_abort_command(message: str) -> bool:
    lower = (message or "").lower()
    return bool(re.search(r"\b(abort upgrade|cancel upgrade|discard upgrade branch)\b", lower))


def merge_force(message: str) -> bool:
    return bool(re.search(r"\b(anyway|force)\b", (message or "").lower()))
