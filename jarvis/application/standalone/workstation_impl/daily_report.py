"""Daily-use workstation health report — homepage for system status."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from jarvis.env_loader import PROJECT_ROOT


def _latest_backup() -> str:
    backup_dir = PROJECT_ROOT / "backups"
    if not backup_dir.is_dir():
        return "none"
    archives = sorted(backup_dir.glob("workstation_*.tar.gz"), reverse=True)
    if not archives:
        return "none"
    name = archives[0].name
    try:
        mtime = datetime.fromtimestamp(archives[0].stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"{name} ({mtime})"
    except OSError:
        return name


def _git_summary(path: Path) -> str:
    if not (path / ".git").is_dir():
        return "not a git repo"
    try:
        branch = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        dirty = subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        b = (branch.stdout or "").strip() or "?"
        changes = len([ln for ln in (dirty.stdout or "").splitlines() if ln.strip()])
        suffix = f", {changes} uncommitted" if changes else ", clean"
        return f"{b}{suffix}"
    except Exception:
        return "unavailable"


def _memory_summary() -> str:
    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        if hasattr(mem, "list_entries"):
            count = len(mem.list_entries())
            return f"{count} entries"
    except Exception:
        pass
    return "unavailable"


def _cutover_summary() -> str:
    try:
        from jarvis.platform_cutover import current_mode, verify_readiness

        ver = verify_readiness(persist=False)
        ready = "ready" if ver.get("ready") else "not ready"
        return f"mode={current_mode()}, cutover {ready}"
    except Exception:
        return "unavailable"


def format_daily_report(*, force: bool = False) -> str:
    from jarvis.application.standalone.workstation_impl.acceptance import (
        format_acceptance_markdown,
        last_acceptance,
        run_acceptance,
    )
    from jarvis.application.standalone.workstation_impl.hardware_report import (
        format_hardware_markdown,
    )
    from jarvis.application.standalone.workstation_impl.operations import format_report
    from jarvis.application.standalone.workstation_impl.phase import (
        current_phase,
        phase_snapshot,
    )

    phase = current_phase()
    snap = phase_snapshot()
    lines = [
        "# AI Workstation Report",
        "",
        f"**Phase:** `{phase.value}`",
    ]
    if snap.get("detail"):
        lines.append(f"**Detail:** {snap['detail']}")
    lines.append("")

    lines.append(format_report(force=force))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(format_hardware_markdown())
    lines.append("")
    lines.append("---")
    lines.append("")

    acc = last_acceptance() if phase.value in ("STARTING", "INITIALIZING", "RECOVERING") else None
    if acc is None:
        acc = run_acceptance(persist=False, live=phase.value == "READY")
    lines.append(format_acceptance_markdown(acc))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Repositories")
    platform_root = Path(PROJECT_ROOT).parent / "AI-Platform"
    lines.append(f"- **Aria:** `{PROJECT_ROOT}` — {_git_summary(PROJECT_ROOT)}")
    if platform_root.is_dir():
        lines.append(f"- **AI-Platform:** `{platform_root}` — {_git_summary(platform_root)}")
    lines.append("")
    lines.append("## Data")
    lines.append(f"- **Memory:** {_memory_summary()}")
    lines.append(f"- **Platform cutover:** {_cutover_summary()}")
    lines.append(f"- **Latest backup:** {_latest_backup()}")
    lines.append("")
    lines.append("## Recommended actions")
    scores = (acc or {}).get("score") or {}
    if phase.value != "READY":
        lines.append(f"- Wait for startup to finish (current phase: {phase.value})")
    elif not acc.get("acceptance_passed"):
        lines.append("- Run: `workstation repair`")
    elif scores.get("daily_required", 0) < 100:
        lines.append("- Run: `workstation repair`")
    else:
        lines.append("- Workstation is healthy — no action required")
    if _latest_backup() == "none":
        lines.append("- Run: `workstation backup`")
    lines.append("")
    known = (acc or {}).get("known_issues") or []
    if known:
        lines.append("## Known issues (from acceptance)")
        for item in known[:6]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def report_json(*, force: bool = False) -> dict[str, Any]:
    from jarvis.application.standalone.workstation_impl.operations import diagnose
    from jarvis.application.standalone.workstation_impl.phase import phase_snapshot

    text = format_daily_report(force=force)
    return {
        "ok": True,
        "phase": phase_snapshot(),
        "diagnose": diagnose(force=force),
        "markdown": text,
    }
