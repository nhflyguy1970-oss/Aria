"""Automation bridge — candidate/preview only (HA owns device automations; Aria owns orchestration)."""

from __future__ import annotations

from typing import Any


def automation_candidates(
    *,
    kind: str = "webhook_scene",
    title: str = "",
    notes: str = "",
    scene: str = "",
    entity_id: str = "",
) -> dict[str, Any]:
    """
    Return preview candidates for Automation / webhook mapping.
    Never authors HA automations silently — confirm-gated drafts only.
    """
    kind = (kind or "webhook_scene").strip().lower()
    candidates: list[dict[str, Any]] = []

    webhook_url = ""
    try:
        from jarvis.home_assistant import status_payload

        webhook_url = str((status_payload() or {}).get("automation_webhook_url") or "")
    except Exception:
        webhook_url = ""

    if kind in ("webhook_scene", "ha_scene_inbound"):
        scene_name = scene or "leaving"
        candidates.append(
            {
                "title": title or f"HA → Aria webhook: activate `{scene_name}`",
                "notes": notes
                or (
                    "Map Home Assistant automation webhook to Aria ha_scene. "
                    "HA owns the trigger; Aria owns orchestration receipt."
                ),
                "kind": kind,
                "scene": scene_name,
                "webhook_url": webhook_url,
                "source": "smarthome_webhook",
                "selected": True,
            }
        )

    elif kind in ("draft_ha_yaml", "automation_authoring"):
        eid = entity_id or "light.example"
        scene_name = scene or "movie mode"
        yaml_draft = (
            f"# DRAFT ONLY — never auto-applied\n"
            f"alias: Aria {scene_name}\n"
            f"trigger:\n"
            f"  - platform: state\n"
            f"    entity_id: {eid}\n"
            f"action:\n"
            f"  - service: scene.turn_on\n"
            f"    target:\n"
            f"      entity_id: scene.{scene_name.replace(' ', '_').lower()}\n"
        )
        candidates.append(
            {
                "title": title or f"Draft HA automation: {scene_name}",
                "notes": notes or "Operator must paste into Home Assistant — Aria does not write HA automations.",
                "kind": kind,
                "yaml_draft": yaml_draft,
                "entity_id": eid,
                "scene": scene_name,
                "source": "smarthome_draft",
                "selected": True,
            }
        )

    elif kind in ("sunlight_schedule", "daylight"):
        candidates.append(
            {
                "title": title or "Sunlight / daylight schedule",
                "notes": notes
                or "Preview sunlight_scene scheduling via Aria Automation — confirm before enabling",
                "kind": kind,
                "source": "smarthome_sunlight",
                "selected": True,
            }
        )
    else:
        candidates.append(
            {
                "title": title or "Smart Home automation candidate",
                "notes": notes,
                "kind": kind,
                "scene": scene,
                "entity_id": entity_id,
                "source": "smarthome",
                "selected": True,
            }
        )

    return {
        "ok": True,
        "product": "Smart Home",
        "target": "Automation",
        "requires_confirmation": True,
        "kind": kind,
        "candidates": candidates,
        "message": (
            "Preview only — Home Assistant owns device automations; "
            "Aria owns orchestration. Confirm before applying."
        ),
        "pipeline": "smarthome_automation_bridge",
    }
