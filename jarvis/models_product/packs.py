"""Project / workspace model packs."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

_PACKS = DATA_DIR / "models_product" / "packs.json"


def list_packs() -> dict[str, Any]:
    data = _load()
    return {"ok": True, "packs": data.get("packs") or []}


def save_pack(pack: dict[str, Any]) -> dict[str, Any]:
    data = _load()
    packs = list(data.get("packs") or [])
    pid = str(pack.get("id") or pack.get("name") or "").strip()
    if not pid:
        return {"ok": False, "error": "id required"}
    pack = {**pack, "id": pid, "roles": dict(pack.get("roles") or {})}
    packs = [p for p in packs if p.get("id") != pid] + [pack]
    data["packs"] = packs
    _save(data)
    return {"ok": True, "pack": pack}


def apply_pack(pack_id: str, *, mode: str = "") -> dict[str, Any]:
    data = _load()
    pack = next((p for p in (data.get("packs") or []) if p.get("id") == pack_id), None)
    if not pack:
        return {"ok": False, "error": "not_found"}
    from jarvis.models_product.switch import apply_model_change, ModelChangeRequest

    return apply_model_change(
        ModelChangeRequest(scope="role_default", roles=dict(pack.get("roles") or {}), mode=mode, reason=f"pack:{pack_id}")
    )


def _load() -> dict[str, Any]:
    try:
        if _PACKS.is_file():
            return json.loads(_PACKS.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"packs": []}


def _save(data: dict[str, Any]) -> None:
    _PACKS.parent.mkdir(parents=True, exist_ok=True)
    _PACKS.write_text(json.dumps(data, indent=2), encoding="utf-8")
