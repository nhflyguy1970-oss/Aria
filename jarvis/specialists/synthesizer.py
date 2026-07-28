"""Final synthesis — one coherent answer from specialist outputs."""

from __future__ import annotations

from typing import Any

from jarvis.specialists.scratchpad import SharedScratchpad


def synthesize(goal: str, steps: list[dict[str, Any]], pad: SharedScratchpad) -> dict[str, Any]:
    ok_steps = [s for s in steps if s.get("ok")]
    fail_steps = [s for s in steps if not s.get("ok") and not s.get("skipped")]
    lines = [
        f"## Specialist Team synthesis",
        f"",
        f"**Goal:** {goal}",
        f"",
        f"**Outcome:** {len(ok_steps)} succeeded, {len(fail_steps)} failed, {len(steps)} total steps.",
        f"",
        "### Key findings",
    ]
    seen: set[str] = set()
    for s in ok_steps:
        text = (s.get("message") or "").strip()
        if not text:
            continue
        key = text[:120]
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- **{s.get('name') or s.get('agent')}:** {text[:500]}")

    if fail_steps:
        lines.append("")
        lines.append("### Issues")
        for s in fail_steps:
            lines.append(f"- **{s.get('agent')}:** {s.get('error') or s.get('message') or 'failed'}")

    if pad.artifacts:
        lines.append("")
        lines.append("### Artifacts")
        for a in pad.artifacts[-6:]:
            lines.append(f"- {a.get('agent')}: {a.get('kind')}")

    lines.append("")
    lines.append("_This synthesis merges specialist outputs. It does not auto-apply writes or enable automations._")
    text = "\n".join(lines)
    return {"ok": True, "synthesis": text, "message": text, "action": "synthesize"}
