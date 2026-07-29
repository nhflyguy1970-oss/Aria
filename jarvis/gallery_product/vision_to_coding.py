"""Gallery still → Coding proposal (never bypass Coding apply)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def vision_to_coding(assistant, *, image_path: str = "", hint: str = "") -> dict[str, Any]:
    path = (image_path or "").strip()
    if not path or not Path(path).is_file():
        return {"ok": False, "error": "Image path required"}
    try:
        from jarvis.gallery_product.visibility import is_restricted_for_viewer

        if is_restricted_for_viewer(Path(path).name):
            return {"ok": False, "error": "Restricted image — reveal in uncensored mode first"}
    except Exception:
        pass

    description = hint or "UI issue visible in this screenshot"
    try:
        from jarvis.vision_product.engine import analyze

        out = analyze(
            path=path,
            action="describe",
            question="Describe likely UI/software issues visible. Be specific.",
            source="gallery",
            assistant=assistant,
            force=True,
        )
        if out.get("ok"):
            description = str(out.get("message") or out.get("analysis") or description)
    except Exception:
        pass

    # Route through Coding propose path only
    try:
        from jarvis.handlers.registry import call_action, has_action

        prompt = (
            f"From Gallery screenshot analysis:\n{description}\n\n"
            "Identify probable source files and propose a fix. Do not apply — proposal only."
        )
        if has_action("coding_propose") or has_action("propose_fix"):
            action = "coding_propose" if has_action("coding_propose") else "propose_fix"
            result = call_action(assistant, action, {"prompt": prompt, "message": prompt}, prompt)
            if isinstance(result, dict):
                return {
                    "ok": bool(result.get("ok", True)),
                    "message": result.get("message") or "Coding proposal ready — review in Coding",
                    "proposal_id": result.get("proposal_id"),
                    "open_view": "coding",
                }
            return {"ok": True, "message": str(result), "open_view": "coding"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "message": f"Analysis ready for Coding review:\n\n{description[:1500]}",
        "open_view": "coding",
        "analysis": description,
    }
