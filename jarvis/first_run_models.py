"""First-run model checks and optional Ollama pulls."""

from __future__ import annotations

import logging
import os
import subprocess

from jarvis.config import DATA_DIR
from jarvis.p1_flags import first_run_models_enabled

log = logging.getLogger("jarvis.first_run")

MARKER = DATA_DIR / ".first_run_models_done"


def _pull(model: str) -> bool:
    try:
        subprocess.run(
            ["ollama", "pull", model],
            check=False,
            timeout=600,
            capture_output=True,
        )
        return True
    except Exception as exc:
        log.warning("pull %s failed: %s", model, exc)
        return False


def ensure_optional_models(*, force: bool = False) -> dict:
    if not first_run_models_enabled():
        return {"skipped": True, "reason": "disabled"}
    marker_path = MARKER
    if marker_path.exists() and not force:
        return {"skipped": True, "reason": "already ran"}

    from jarvis.ollama_health import check_ollama, model_available
    from jarvis.local_router import router_model
    from jarvis.brain_routing import fast_chat_model, reasoning_model
    from jarvis.p1_flags import brain_routing_enabled

    pulled: list[str] = []
    if not check_ollama().get("running"):
        return {"ok": False, "error": "ollama not running"}

    targets: list[str] = [
        router_model(),
        fast_chat_model(),
    ]
    if brain_routing_enabled():
        targets.append(reasoning_model())

    whisper_model = os.getenv("JARVIS_WHISPER_MODEL", "small").strip() or "small"
    if whisper_model not in targets:
        targets.append(whisper_model)

    seen: set[str] = set()
    voice_notes: list[str] = []
    for m in targets:
        m = (m or "").strip()
        if not m or m in seen:
            continue
        seen.add(m)
        if not model_available(m):
            if _pull(m):
                pulled.append(m)

    try:
        from jarvis.first_run_downloads import ensure_voice_assets

        dl = ensure_voice_assets()
        for note in dl.get("voice") or []:
            if note not in voice_notes:
                voice_notes.append(note)
        for item in dl.get("pulled") or []:
            if item not in pulled:
                pulled.append(item)
    except Exception as exc:
        voice_notes.append(f"Voice asset download: {exc}")

    try:
        from jarvis.config import piper_ready, piper_voice_label

        if not piper_ready():
            voice_notes.append("Piper TTS not ready after auto-download — run scripts/install-dependencies.sh")
        else:
            voice_notes.append(f"Piper OK ({piper_voice_label()})")
    except Exception:
        voice_notes.append("Piper check skipped")

    try:
        from jarvis.audio_whisper import whisper_backend

        wb = whisper_backend()
        if wb == "none":
            voice_notes.append("Whisper not available — pip install faster-whisper")
        else:
            voice_notes.append(f"Whisper backend: {wb}")
    except Exception:
        pass

    backend = (os.getenv("JARVIS_ROUTER_BACKEND") or "auto").strip().lower()
    if backend in ("auto", "functiongemma"):
        try:
            from jarvis.functiongemma_router import functiongemma_ready, warm_model

            if functiongemma_ready():
                voice_notes.append("FunctionGemma weights cached")
            elif backend == "functiongemma":
                warm = warm_model()
                if warm.get("ok"):
                    voice_notes.append("FunctionGemma loaded")
                else:
                    voice_notes.append(
                        "FunctionGemma missing — pip install transformers torch; "
                        "accept license at huggingface.co/google/functiongemma-270m-it"
                    )
        except Exception:
            pass

    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("ok\n", encoding="utf-8")
    except OSError:
        pass
    return {"ok": True, "pulled": pulled, "voice": voice_notes}
