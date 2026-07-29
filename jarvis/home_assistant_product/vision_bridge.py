"""Vision bridge — HA camera snapshots analyzed by Vision product (never duplicate Vision)."""

from __future__ import annotations

from typing import Any


def analyze_camera(
    entity_id: str = "",
    *,
    path: str = "",
    assistant=None,
    question: str = "",
    force: bool = True,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Analyze a camera still. Prefer an existing local path; otherwise stage a confirm-gated
    snapshot request (HA camera_proxy) without auto-capturing.
    """
    from jarvis.config import is_uncensored
    from jarvis.home_assistant_product.history import add_entry
    from jarvis.home_assistant_product.status_bus import set_smarthome_state

    eid = (entity_id or "").strip()
    media_path = (path or "").strip()

    if not media_path:
        return {
            "ok": False,
            "requires_confirmation": True,
            "staged": {"entity_id": eid, "action": "camera_snapshot"},
            "message": (
                "Provide a snapshot path, or confirm camera snapshot from Home Assistant "
                f"({eid or 'camera.*'}). Vision never auto-captures."
            ),
            "bridge": "vision_product",
            "confirmed_needed": not confirmed,
        }

    if not confirmed and force is False:
        return {
            "ok": False,
            "requires_confirmation": True,
            "path": media_path,
            "entity_id": eid,
            "message": "Confirm Vision analysis of this camera snapshot.",
            "bridge": "vision_product",
        }

    set_smarthome_state("scanning", detail="vision_camera", task="vision", entity_id=eid)
    try:
        from jarvis.vision_product.engine import analyze

        prompt = (question or "").strip() or (
            "Describe this home security / camera snapshot for an operator. "
            "Note people, vehicles, open doors, packages, and anything unusual. "
            "Be concise and factual."
        )
        result = analyze(
            path=media_path,
            action="describe",
            question=prompt,
            source="smarthome_vision",
            assistant=assistant,
            force=True,
        )
        analysis = str(result.get("analysis") or result.get("message") or result.get("answer") or "")
        entry = add_entry(
            {
                "kind": "vision_camera",
                "entity_id": eid,
                "path": media_path,
                "summary": "Camera analysis",
                "detail": analysis[:4000],
                "confidence": result.get("confidence"),
                "source": "vision_bridge",
                "uncensored_origin": bool(is_uncensored()),
                "meta": {"history_id": result.get("history_id")},
            }
        )
        return {
            "ok": bool(result.get("ok", True)),
            "vision": result,
            "analysis": analysis,
            "entity_id": eid,
            "path": media_path,
            "history_id": entry.get("id"),
            "bridge": "vision_product",
            "pipeline": "smarthome_engine",
        }
    finally:
        set_smarthome_state("idle", detail="vision_done")
