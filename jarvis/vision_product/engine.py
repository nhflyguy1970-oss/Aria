"""One Vision engine — shared analyze / OCR / compare / import for all entry points."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from jarvis.vision_product.history import add_entry
from jarvis.vision_product.honesty import honesty_report
from jarvis.vision_product.ocr import run_ocr
from jarvis.vision_product.settings import load_settings
from jarvis.vision_product.status_bus import set_vision_state
from jarvis.vision_product.terminology import BOUNDARIES, TERMINOLOGY


ACTIONS = (
    "describe",
    "ocr",
    "ocr_structured",
    "identify",
    "compare",
    "image_to_code",
    "region",
    "summarize",
    "translate",
    "remember",
    "import",
)


def analyze(
    *,
    path: str | Path | None = None,
    path2: str | Path | None = None,
    action: str = "describe",
    question: str = "",
    crop: dict | None = None,
    source: str = "api",
    assistant=None,
    import_target: str = "",
    speak: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """
    Shared Vision pipeline entry for Chat, Gallery, Browser, Coding, imports, automation, API.
    """
    from jarvis import llm
    from jarvis.config import is_uncensored
    from jarvis.vision_media import build_vision_prompt, parse_region, vision_task_for_question

    action = (action or "describe").strip().lower()
    if action == "tables":
        action = "ocr_structured"
    started = time.time()
    honesty = honesty_report(task=_task_for_action(action, question))
    if honesty.get("warnings") and honesty.get("warn_before_heavy") and honesty.get("heavy") and not force:
        # Still proceed but surface warnings prominently (operator honesty, not a hard block)
        pass

    if assistant is None:
        try:
            from jarvis.assistant_instance import get_assistant

            assistant = get_assistant()
        except Exception:
            assistant = None

    set_vision_state(
        "analyzing" if action != "ocr" else "ocr",
        detail=source,
        model=honesty.get("model") or "",
        task=action,
        progress=0.1,
    )

    try:
        if action == "compare":
            return _compare(path, path2, question=question, source=source, assistant=assistant, started=started, honesty=honesty)

        if not path:
            set_vision_state("error", detail="no_path", error="path required")
            return {"ok": False, "error": "path required", "honesty": honesty}

        p = str(path)
        analyze_path = p
        if crop or action == "region":
            from jarvis.config import DATA_DIR
            from jarvis.vision_media import apply_crop_bytes

            region = parse_region(question, crop)
            if region:
                cropped = apply_crop_bytes(Path(p).read_bytes(), region)
                region_file = DATA_DIR / "uploads" / f"region_{Path(p).stem}.jpg"
                region_file.parent.mkdir(parents=True, exist_ok=True)
                region_file.write_bytes(cropped)
                analyze_path = str(region_file)

        result_text = ""
        ocr_text = ""
        confidence = None
        task = _task_for_action(action, question)

        if action in ("ocr", "ocr_structured"):
            ocr = run_ocr(analyze_path, structured=(action == "ocr_structured"), assistant=assistant)
            if not ocr.get("ok"):
                set_vision_state("error", detail=str(ocr.get("error") or ""), error=str(ocr.get("error") or ""))
                return {"ok": False, "error": ocr.get("error"), "honesty": honesty, "pipeline": "vision_engine"}
            result_text = str(ocr.get("text") or "")
            ocr_text = result_text
            confidence = ocr.get("confidence")
        elif action == "import":
            from jarvis.vision_product.import_pipeline import vision_import

            out = vision_import(
                path=analyze_path,
                target=import_target or "preview",
                assistant=assistant,
                source=source,
            )
            latency = int((time.time() - started) * 1000)
            if out.get("ok"):
                add_entry(
                    {
                        "path": p,
                        "prompt": f"import:{import_target or 'preview'}",
                        "analysis": (out.get("raw_text") or "")[:2000],
                        "ocr": (out.get("raw_text") or "")[:2000],
                        "task": "import",
                        "model": honesty.get("model"),
                        "latency_ms": latency,
                        "confidence": out.get("confidence"),
                        "import_target": import_target or "preview",
                        "source": source,
                        "uncensored_origin": bool(is_uncensored()),
                    }
                )
            return {**out, "honesty": honesty, "pipeline": "vision_engine", "latency_ms": latency}
        elif action == "remember":
            ocr = run_ocr(analyze_path, assistant=assistant)
            blob = str(ocr.get("text") or "") if ocr.get("ok") else ""
            if not blob and assistant:
                blob = str(assistant.vision.analyze("Summarize this image for memory.", analyze_path) or "")
            result_text = blob
            ocr_text = blob if ocr.get("ok") else ""
            try:
                from jarvis.action_log import log_event

                log_event("vision_remember_staged", path=p, chars=len(blob))
            except Exception:
                pass
        else:
            if not assistant:
                set_vision_state("error", detail="assistant_unavailable", error="assistant unavailable")
                return {"ok": False, "error": "assistant unavailable", "honesty": honesty}
            q = (question or "").strip()
            if action == "describe" and not q:
                q = "Describe this image in detail."
            elif action == "summarize" and not q:
                q = "Summarize the key content of this image in a few sentences."
            elif action == "translate" and not q:
                q = "Transcribe and translate all visible text to English."
            elif action == "region" and not q:
                q = "What is in this region?"

            if action == "image_to_code":
                result_text = assistant.vision.image_to_code(analyze_path)
            elif action == "identify" or vision_task_for_question(q) == "identify":
                task = "identify"
                prompt = build_vision_prompt(q or "What is this?", "identify")
                result_text = assistant.vision.analyze(prompt, analyze_path, task="identify")
            else:
                result_text = assistant.vision.analyze(q, analyze_path, task=task)

        if str(result_text).startswith("ERROR:"):
            set_vision_state("error", detail=str(result_text), error=str(result_text))
            return {"ok": False, "error": result_text, "honesty": honesty, "pipeline": "vision_engine"}

        latency = int((time.time() - started) * 1000)
        style = load_settings().get("output_style") or "balanced"
        if style == "brief" and result_text and len(result_text) > 600:
            result_text = result_text[:597].rstrip() + "…"

        entry = add_entry(
            {
                "path": p,
                "prompt": question or action,
                "analysis": result_text,
                "ocr": ocr_text,
                "task": action,
                "model": honesty.get("model") or llm.vision_model_for_task(task),
                "latency_ms": latency,
                "confidence": confidence,
                "import_target": import_target,
                "source": source,
                "uncensored_origin": bool(is_uncensored()),
            }
        )

        if speak or load_settings().get("speak_results"):
            _maybe_speak(result_text)

        set_vision_state("idle", detail=source, model=honesty.get("model") or "", progress=1)
        try:
            from jarvis.action_log import log_event

            log_event("vision_analyze", action=action, source=source, latency_ms=latency)
        except Exception:
            pass

        return {
            "ok": True,
            "message": result_text,
            "analysis": result_text,
            "ocr": ocr_text,
            "action": action,
            "path": p,
            "image_path": analyze_path,
            "module": "vision",
            "honesty": honesty,
            "warnings": honesty.get("warnings") or [],
            "latency_ms": latency,
            "confidence": confidence,
            "history_id": entry.get("id"),
            "pipeline": "vision_engine",
            "source": source,
        }
    except Exception as exc:
        set_vision_state("error", detail=str(exc), error=str(exc))
        return {"ok": False, "error": str(exc), "honesty": honesty, "pipeline": "vision_engine"}


def _task_for_action(action: str, question: str) -> str:
    from jarvis.vision_media import vision_task_for_question

    mapping = {
        "describe": "describe",
        "summarize": "describe",
        "ocr": "ocr",
        "ocr_structured": "ocr_structured",
        "tables": "ocr_structured",
        "identify": "identify",
        "compare": "compare",
        "image_to_code": "image_to_code",
        "region": "region",
        "translate": "ocr",
        "remember": "ocr",
        "import": "ocr",
    }
    if action == "describe" and question:
        return vision_task_for_question(question)
    return mapping.get(action, "describe")


def _compare(path, path2, *, question, source, assistant, started, honesty) -> dict[str, Any]:
    from jarvis.config import DATA_DIR, is_uncensored

    if not path or not path2:
        set_vision_state("error", detail="compare needs two images", error="two paths required")
        return {"ok": False, "error": "compare requires path and path2", "honesty": honesty}
    if not assistant:
        return {"ok": False, "error": "assistant unavailable", "honesty": honesty}
    set_vision_state("comparing", detail=source, model=honesty.get("model") or "", task="compare")
    payload = None
    for kind, data in assistant.vision.compare_events(
        str(path), str(path2), question or None, uploads_dir=DATA_DIR / "uploads"
    ):
        if kind == "status":
            set_vision_state("comparing", detail=str(data), model=honesty.get("model") or "", task="compare")
        elif kind == "error":
            set_vision_state("error", detail=str(data), error=str(data))
            return {"ok": False, "error": data, "honesty": honesty, "pipeline": "vision_engine"}
        elif kind == "result":
            payload = data
    if not payload:
        return {"ok": False, "error": "compare failed", "honesty": honesty}
    latency = int((time.time() - started) * 1000)
    answer = payload.get("answer") or ""
    entry = add_entry(
        {
            "path": str(path),
            "prompt": question or "compare",
            "analysis": answer,
            "task": "compare",
            "model": honesty.get("model"),
            "latency_ms": latency,
            "source": source,
            "uncensored_origin": bool(is_uncensored()),
            "compare_paths": [str(path), str(path2)],
            "diff_path": payload.get("diff_path") or "",
        }
    )
    set_vision_state("idle", detail=source, progress=1)
    return {
        "ok": True,
        "message": answer,
        "analysis": answer,
        "action": "compare",
        "path": str(path),
        "path2": str(path2),
        "compare_paths": [payload.get("path1"), payload.get("path2")],
        "diff_path": payload.get("diff_path"),
        "module": "vision",
        "honesty": honesty,
        "warnings": honesty.get("warnings") or [],
        "latency_ms": latency,
        "history_id": entry.get("id"),
        "pipeline": "vision_engine",
        "source": source,
    }


def _maybe_speak(text: str) -> None:
    try:
        from jarvis.voice_product.engine import speak_text

        speak_text(text[:800], force=True, source="vision")
    except Exception:
        pass


def product_status() -> dict[str, Any]:
    from jarvis.vision_product.history import list_history
    from jarvis.vision_product.profiles import active_profile_id, list_profiles
    from jarvis.vision_product.settings import load_settings
    from jarvis.vision_product.status_bus import get_vision_state

    honesty = honesty_report(task="describe")
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "boundaries": BOUNDARIES,
        "state": get_vision_state(),
        "settings": load_settings(),
        "honesty": honesty,
        "profiles": {"active": active_profile_id(), "count": len(list_profiles())},
        "history_recent": list_history(limit=5),
        "actions": list(ACTIONS),
        "pipeline": [
            "media_input",
            "vision_engine",
            "intent",
            "analysis",
            "optional_import",
            "activity",
            "mission_control",
            "completion",
        ],
    }


def action_rail() -> list[dict[str, str]]:
    return [
        {"id": "describe", "label": "Describe"},
        {"id": "ocr", "label": "OCR"},
        {"id": "ocr_structured", "label": "Structured OCR"},
        {"id": "tables", "label": "Tables"},
        {"id": "identify", "label": "Identify"},
        {"id": "compare", "label": "Compare"},
        {"id": "image_to_code", "label": "UI→Code"},
        {"id": "remember", "label": "Remember"},
        {"id": "import", "label": "Import"},
        {"id": "translate", "label": "Translate"},
        {"id": "summarize", "label": "Summarize"},
    ]
