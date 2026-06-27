"""Built-in 3D printer profiles for slicing and print routing."""

from __future__ import annotations

from typing import Any

PRINTER_MODELS: dict[str, dict[str, Any]] = {
    "bambu_a1": {
        "label": "Bambu Lab A1",
        "brand": "bambu",
        "backend": "bambu_handoff",
        "orca_names": ["Bambu Lab A1 0.4 nozzle", "Bambu Lab A1"],
        "handoff_hint": "Open Bambu Studio → Send print (cloud/Wi‑Fi) or copy G-code to SD card. LAN mode not required.",
        "slicer_profile": "bambu_a1",
    },
    "bambu_a1_mini": {
        "label": "Bambu Lab A1 Mini",
        "brand": "bambu",
        "backend": "bambu_handoff",
        "orca_names": ["Bambu Lab A1 mini 0.4 nozzle", "Bambu Lab A1 mini"],
        "handoff_hint": "Open Bambu Studio → bind printer → Send, or export to SD/USB. No developer LAN mode needed.",
        "slicer_profile": "bambu_a1_mini",
    },
    "creality_ender3_v3_ke": {
        "label": "Creality Ender-3 V3 KE",
        "brand": "creality",
        "backend": "moonraker",
        "default_port": 7125,
        "orca_names": ["Creality Ender-3 V3 KE 0.4 nozzle", "Creality Ender-3 V3 KE"],
        "handoff_hint": "Install Moonraker (Creality Helper Script) then set host to http://PRINTER_IP:7125",
        "slicer_profile": "creality_ender3_v3_ke",
        "mdns_services": ["_moonraker._tcp.local.", "_http._tcp.local."],
    },
}


def list_models() -> list[dict[str, Any]]:
    return [
        {"id": mid, **{k: v for k, v in meta.items() if k != "orca_names"}}
        for mid, meta in PRINTER_MODELS.items()
    ]


def get_model(model_id: str) -> dict[str, Any] | None:
    mid = (model_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "a1": "bambu_a1",
        "a1_mini": "bambu_a1_mini",
        "a1mini": "bambu_a1_mini",
        "ender3_v3_ke": "creality_ender3_v3_ke",
        "ender_3_v3_ke": "creality_ender3_v3_ke",
        "k3_ke": "creality_ender3_v3_ke",
    }
    mid = aliases.get(mid, mid)
    meta = PRINTER_MODELS.get(mid)
    if not meta:
        return None
    return {"id": mid, **meta}


def default_row_for_model(model_id: str, *, name: str = "", host: str = "") -> dict[str, Any]:
    """Build a printer_store row for a known model."""
    m = get_model(model_id)
    if not m:
        raise ValueError(f"Unknown printer model: {model_id}")
    pid = name.lower().replace(" ", "-")[:40] if name else m["id"]
    row: dict[str, Any] = {
        "id": pid,
        "name": name or m["label"],
        "model": m["id"],
        "backend": m["backend"],
    }
    if m["backend"] == "moonraker":
        h = (host or "").strip()
        if h and not h.startswith("http"):
            port = m.get("default_port", 7125)
            h = f"http://{h}:{port}"
        row["host"] = h
        row["api_key"] = ""
    else:
        row["host"] = ""
        row["handoff_dir"] = ""
    return row
