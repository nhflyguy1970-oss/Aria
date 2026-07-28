"""Vision-assisted bug fixing — screenshot → likely files → explanation → proposal.

Never applies automatically. Operator must Approve Apply.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def vision_bugfix(
    assistant: Any,
    *,
    image_path: str,
    hint: str = "",
    propose: bool = True,
) -> dict[str, Any]:
    """Analyze a screenshot and optionally create a coding proposal."""
    path = Path(image_path).expanduser()
    if not path.is_file():
        return {"ok": False, "error": f"Screenshot not found: {image_path}"}

    description = ""
    try:
        vision = assistant.vision if hasattr(assistant, "vision") else None
        if vision is None and hasattr(assistant, "_vision_engines"):
            # Prefer describe via action path
            pass
        from jarvis.handlers.registry import call_action, has_action

        if has_action("describe_image"):
            out = call_action(assistant, "describe_image", {"path": str(path)}, hint or "describe UI bug")
            description = (out.get("message") or out.get("description") or str(out))[:3000]
        else:
            description = f"(no describe_image action) hint={hint}"
    except Exception as exc:
        description = f"Vision describe failed: {exc}. hint={hint}"

    # Heuristic file candidates from description + hint
    blob = f"{description}\n{hint}".lower()
    likely: list[str] = []
    try:
        from jarvis import code_index

        hits = code_index.search(hint or description[:200] or "ui bug", limit=8) or []
        for h in hits:
            p = h.get("path") or h.get("file")
            if p and p not in likely:
                likely.append(str(p))
    except Exception:
        pass

    # Common GUI paths if UI mentioned
    if any(w in blob for w in ("button", "sidebar", "modal", "css", "panel", "chat", "view")):
        for candidate in (
            "jarvis/gui/static/style.css",
            "jarvis/gui/static/index.html",
            "jarvis/gui/static/view_router.js",
        ):
            if candidate not in likely:
                likely.append(candidate)

    explanation = (
        "## Vision bug analysis\n\n"
        f"**Screenshot:** `{path}`\n\n"
        f"**Description:**\n{description or '(empty)'}\n\n"
        f"**Likely files:**\n"
        + ("\n".join(f"- `{f}`" for f in likely[:8]) if likely else "- (none ranked)")
        + "\n\n**Next:** Review the proposal (if created). Apply is never automatic."
    )

    result: dict[str, Any] = {
        "ok": True,
        "image_path": str(path),
        "likely_files": likely[:12],
        "explanation": explanation,
        "description": description,
        "auto_applied": False,
        "requires_apply_approval": True,
    }

    if not propose:
        return result

    task = (
        f"Fix the UI/bug shown in the screenshot analysis.\n"
        f"Hint: {hint or 'see description'}\n"
        f"Vision notes:\n{description[:1500]}\n"
        f"Focus files: {', '.join(likely[:5]) or 'discover relevant files'}"
    )
    try:
        from jarvis.coding_agent import CodingAgent

        agent = CodingAgent(assistant.coding._base(), max_steps=4)
        focus = likely[0] if likely else None
        agent_result = agent.run(task, path=focus, mode="fix")
        if not agent_result.ok or not agent_result.files:
            result["proposal"] = None
            result["message"] = agent_result.message or explanation
            result["agent_ok"] = False
            return result
        proposal_id, payload = assistant._store_agent_proposal(
            agent_result.files,
            mode="vision_fix",
            explanation=agent_result.explanation or task[:200],
        )
        result["proposal_id"] = proposal_id
        result["proposal"] = {"id": proposal_id, "syntax_ok": payload.get("syntax_ok")}
        result["message"] = explanation + f"\n\nProposal `{proposal_id}` ready — review and Apply when ready."
        result["diff"] = agent_result.diff or ""
        result["agent_ok"] = True
        return result
    except Exception as exc:
        result["ok"] = False
        result["error"] = str(exc)
        result["message"] = explanation
        return result
