"""Optional operator-controlled image metadata (never auto-index everything)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

META_FILE = DATA_DIR / "gallery_product" / "metadata.json"


def _load() -> dict[str, dict[str, Any]]:
    if not META_FILE.exists():
        return {}
    try:
        data = json.loads(META_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(store: dict[str, dict[str, Any]]) -> None:
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    META_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def key_for(name: str) -> str:
    return Path(name or "").name


def get_meta(name: str) -> dict[str, Any]:
    return dict(_load().get(key_for(name)) or {})


def set_meta(name: str, patch: dict[str, Any], *, merge: bool = True) -> dict[str, Any]:
    store = _load()
    k = key_for(name)
    cur = dict(store.get(k) or {}) if merge else {}
    for field, val in (patch or {}).items():
        if val is None:
            cur.pop(field, None)
        else:
            cur[field] = val
    cur["updated_at"] = time.time()
    cur["name"] = k
    store[k] = cur
    _save(store)
    return {"ok": True, "meta": cur}


def delete_meta(name: str) -> dict[str, Any]:
    store = _load()
    k = key_for(name)
    existed = k in store
    store.pop(k, None)
    _save(store)
    return {"ok": True, "deleted": existed}


def mark_generation(
    name: str,
    *,
    prompt: str = "",
    enhanced: str = "",
    negative: str = "",
    checkpoint: str = "",
    uncensored: bool = False,
    project: str = "",
    seed: str = "",
    engine: str = "comfyui",
) -> dict[str, Any]:
    """Record generation provenance (called on create — not full Vision indexing)."""
    return set_meta(
        name,
        {
            "prompt": (prompt or "")[:2000],
            "enhanced_prompt": (enhanced or "")[:4000],
            "negative_prompt": (negative or "")[:2000],
            "checkpoint": checkpoint or "",
            "uncensored": bool(uncensored),
            "project": project or "",
            "seed": seed or "",
            "engine": engine,
            "created_at": time.time(),
            "source": "generation",
        },
    )


def generate_vision_meta(name: str, path: str, *, assistant=None) -> dict[str, Any]:
    """Opt-in Vision caption/OCR for one image. Never batch-auto."""
    try:
        from jarvis.config import is_uncensored
        from jarvis.gallery_product.visibility import is_restricted_for_viewer

        if is_restricted_for_viewer(name):
            return {
                "ok": False,
                "message": "Restricted image — switch to uncensored profile or reveal first",
                "restricted": True,
            }
    except Exception:
        pass

    caption = ""
    ocr = ""
    try:
        # Prefer vision module if available
        if assistant and getattr(assistant, "vision", None):
            caption = str(
                assistant.vision.analyze(
                    "Describe this image in one short paragraph for search.",
                    path,
                )
                or ""
            )[:2000]
        else:
            from jarvis import llm
            from jarvis.model_store import model_for

            # Text-only fallback note — still requires vision-capable stack
            model = model_for("vision") or model_for("browser_vision")
            if not model:
                return {"ok": False, "message": "No vision model configured in Models"}
            caption = str(
                llm.ask_with_system(
                    model,
                    "You describe images briefly for a local gallery search index.",
                    f"Image path: {path}. If you cannot see it, say so.",
                    options={"temperature": 0.2, "num_predict": 120},
                )
                or ""
            )[:2000]
    except Exception as exc:
        return {"ok": False, "message": f"Vision metadata failed: {exc}"}

    return set_meta(
        name,
        {
            "vision_description": caption,
            "caption": caption[:500],
            "ocr_text": ocr,
            "vision_at": time.time(),
            "vision_opt_in": True,
        },
    )


def export_all() -> dict[str, Any]:
    return {"ok": True, "metadata": _load()}
