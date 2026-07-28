"""Single critic revision loop — at most one pass."""

from __future__ import annotations

from typing import Any

from jarvis.specialists.scratchpad import SharedScratchpad


def one_revision(
    assistant: Any,
    goal: str,
    pad: SharedScratchpad,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """Critique existing steps and produce one revision note. No infinite loops."""
    from jarvis.specialists.execute import run_specialist

    critique = run_specialist(assistant, "critic", goal, pad, approve_writes=True)
    revision = (
        f"## Single revision pass\n\n"
        f"{critique.get('message') or ''}\n\n"
        f"### Suggested adjustments\n"
        f"- Re-check failed specialists\n"
        f"- Prefer cited sources for claims\n"
        f"- Do not auto-apply writes\n"
    )
    return {
        "ok": True,
        "agent": "critic_loop",
        "name": "Critic loop",
        "role": "qa",
        "message": revision[:3000],
        "action": "critic_one_revision",
        "recovered": False,
        "data": {"critique": critique},
    }
