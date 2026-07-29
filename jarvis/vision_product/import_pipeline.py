"""Shared Vision import — one preview pipeline for Journal / Planner / Calendar / Memory / Documents."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def vision_import(
    *,
    path: str | Path | None = None,
    ocr_text: str = "",
    target: str = "preview",
    section: str = "daily",
    source: str = "vision",
    assistant=None,
    structured: bool = False,
) -> dict[str, Any]:
    """
    Shared import entry point.

    target: preview | journal | planner | calendar | memory | documents | gallery
    Always returns a preview requiring confirmation for write targets (except preview itself).
    """
    from jarvis.vision_product.ocr import run_ocr
    from jarvis.vision_product.status_bus import set_vision_state

    target = (target or "preview").lower().strip()
    text = (ocr_text or "").strip()
    resolved_path = str(path) if path else ""

    set_vision_state("importing", detail=target, task="import")
    try:
        if not text and resolved_path:
            ocr = run_ocr(resolved_path, structured=structured, assistant=assistant)
            if not ocr.get("ok"):
                set_vision_state("error", detail=str(ocr.get("error") or "OCR failed"), error=str(ocr.get("error") or ""))
                return {
                    "ok": False,
                    "error": ocr.get("error") or "OCR failed",
                    "target": target,
                    "requires_confirmation": True,
                    "candidates": [],
                    "preview_lines": [],
                }
            text = str(ocr.get("text") or "")
            engine = ocr.get("engine")
            confidence = ocr.get("confidence")
        else:
            engine = "pasted"
            confidence = 0.9 if text else 0.0

        if not text.strip():
            set_vision_state("idle", detail="import-empty")
            return {
                "ok": False,
                "error": "No OCR text available",
                "target": target,
                "requires_confirmation": True,
                "candidates": [],
                "preview_lines": [],
            }

        lines = _normalize_lines(text)
        candidates = [{"text": ln, "selected": True} for ln in lines if 3 <= len(ln) <= 200][:40]
        preview = {
            "ok": True,
            "target": target,
            "path": resolved_path,
            "source": source,
            "section": section,
            "raw_text": text[:8000],
            "preview_lines": lines[:60],
            "candidates": candidates,
            "engine": engine,
            "confidence": confidence,
            "requires_confirmation": True,
            "pipeline": "vision_import",
            "message": f"Vision import preview for {target} — confirm to apply.",
        }

        if target == "preview":
            set_vision_state("idle", detail="import-preview")
            return preview

        if target == "journal":
            from jarvis.journal_services import vision_import_preview

            out = vision_import_preview(ocr_text=text, source=source, section=section)
            out["pipeline"] = "vision_import"
            out["path"] = resolved_path
            out["engine"] = engine
            set_vision_state("idle", detail="import-journal")
            return out

        if target == "planner":
            # Return candidates only — write via import_vision_tasks after confirm
            preview["message"] = f"Found {len(candidates)} candidate task(s) — review before import"
            set_vision_state("idle", detail="import-planner")
            return preview

        if target == "calendar":
            preview["message"] = f"Found {len(candidates)} candidate event line(s) — review before import"
            set_vision_state("idle", detail="import-calendar")
            return preview

        if target == "memory":
            preview["message"] = "Vision → Memory preview — confirm to remember"
            preview["memory_text"] = text[:2000]
            set_vision_state("idle", detail="import-memory")
            return preview

        if target == "documents":
            preview["message"] = "Vision → Documents preview — confirm to save extract"
            set_vision_state("idle", detail="import-documents")
            return preview

        if target == "gallery":
            preview["message"] = "Vision → Gallery metadata preview — confirm to save"
            set_vision_state("idle", detail="import-gallery")
            return preview

        set_vision_state("idle", detail="import")
        return preview
    except Exception as exc:
        set_vision_state("error", detail=str(exc), error=str(exc))
        return {"ok": False, "error": str(exc), "target": target, "requires_confirmation": True}


def _normalize_lines(text: str) -> list[str]:
    lines: list[str] = []
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        ln = ln.replace("·", "•").replace("–", "—").replace("−", "—")
        if re.match(r"^[\d\.\)\]]+\s+", ln):
            ln = re.sub(r"^[\d\.\)\]]+\s+", "• ", ln)
        lines.append(ln)
    return lines


def apply_import(preview: dict[str, Any], *, confirmed: bool = False) -> dict[str, Any]:
    """Apply a confirmed vision_import preview to the target product."""
    if not confirmed:
        return {"ok": False, "error": "confirmation_required", "requires_confirmation": True}
    target = (preview.get("target") or "").lower()
    if target == "planner":
        from jarvis.planner_services import import_vision_tasks

        return import_vision_tasks(preview.get("candidates") or [])
    if target == "calendar":
        from jarvis.assistant_instance import get_assistant
        from jarvis.calendar_services import import_vision_events

        assistant = get_assistant()
        journal = getattr(assistant, "journal", None)
        return import_vision_events(journal, preview.get("candidates") or [])
    if target == "journal":
        # Journal write goes through existing journal APIs after preview lines approved
        return {
            "ok": True,
            "message": "Use journal assist approve with preview_lines",
            "preview_lines": preview.get("preview_lines") or [],
            "section": preview.get("section") or "daily",
        }
    if target == "memory":
        text = (preview.get("memory_text") or preview.get("raw_text") or "").strip()
        if not text:
            return {"ok": False, "error": "empty"}
        try:
            from jarvis.assistant_instance import get_assistant

            assistant = get_assistant()
            if hasattr(assistant, "memory") and hasattr(assistant.memory, "add"):
                assistant.memory.add(text[:2000], tags=["vision"])
            return {"ok": True, "message": "Remembered vision extract", "text": text[:200]}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
    return {"ok": False, "error": f"unsupported_target:{target}"}
