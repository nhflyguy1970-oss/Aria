"""Auto-download optional voice assets on first run (#33)."""

from __future__ import annotations

import logging
import shutil
import subprocess
import urllib.request
from pathlib import Path

from jarvis.config import DATA_DIR, PROJECT_ROOT, piper_model_path, piper_ready

log = logging.getLogger("jarvis.first_run_dl")

PIPER_VOICE_BASE = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
)
PIPER_RELEASE = (
    "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
)


def _download(url: str, dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 0
    except Exception as exc:
        log.warning("download %s failed: %s", url, exc)
        return False


def ensure_piper_voice() -> tuple[bool, str]:
    """Download Piper ONNX voice if missing."""
    model = piper_model_path() or (DATA_DIR / "models" / "piper" / "en_US-lessac-medium.onnx")
    json_path = model.with_suffix(".onnx.json")
    if model.is_file() and json_path.is_file():
        return True, f"voice ready: {model.name}"
    ok1 = _download(f"{PIPER_VOICE_BASE}/en_US-lessac-medium.onnx", model)
    ok2 = _download(f"{PIPER_VOICE_BASE}/en_US-lessac-medium.onnx.json", json_path)
    if ok1 and ok2:
        return True, f"downloaded Piper voice to {model.parent}"
    return False, "Piper voice download failed — run scripts/install-dependencies.sh"


def ensure_piper_binary() -> tuple[bool, str]:
    """Download bundled Piper binary when tools/piper is empty."""
    if shutil.which("piper"):
        return True, "piper on PATH"
    bundled = PROJECT_ROOT / "tools" / "piper" / "piper"
    if bundled.is_file():
        return True, "bundled piper"
    if not shutil.which("curl") or not shutil.which("tar"):
        return False, "curl/tar required for Piper binary install"
    dest_dir = PROJECT_ROOT / "tools" / "piper"
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive = DATA_DIR / "cache" / "piper_linux_x86_64.tar.gz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.is_file():
        if not _download(PIPER_RELEASE, archive):
            return False, "Piper binary download failed"
    try:
        subprocess.run(
            ["tar", "-xzf", str(archive), "-C", str(dest_dir.parent)],
            check=True,
            timeout=120,
            capture_output=True,
        )
        inner = dest_dir.parent / "piper"
        if inner.is_dir() and inner != dest_dir:
            for item in inner.iterdir():
                target = dest_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, target)
            shutil.rmtree(inner, ignore_errors=True)
        if bundled.is_file():
            bundled.chmod(0o755)
            return True, "installed bundled piper"
    except Exception as exc:
        log.warning("piper extract failed: %s", exc)
    return False, "Piper binary extract failed"


def warm_whisper_weights() -> tuple[bool, str]:
    """Trigger faster-whisper model download if backend is available."""
    try:
        from jarvis.audio_whisper import whisper_backend

        if whisper_backend() == "none":
            return False, "Whisper backend not installed"
    except Exception:
        return False, "Whisper check skipped"

    model_name = __import__("os").getenv("JARVIS_WHISPER_MODEL", "small").strip() or "small"
    try:
        from faster_whisper import WhisperModel

        WhisperModel(model_name, device="cpu", compute_type="int8")
        return True, f"faster-whisper weights cached ({model_name})"
    except ImportError:
        return False, "pip install faster-whisper"
    except Exception as exc:
        log.warning("whisper warm failed: %s", exc)
        return False, str(exc)


def ensure_voice_assets() -> dict:
    """Run all first-run voice asset steps."""
    notes: list[str] = []
    pulled: list[str] = []

    ok_v, msg_v = ensure_piper_voice()
    notes.append(msg_v)
    if ok_v:
        pulled.append("piper_voice")

    if not piper_ready():
        ok_b, msg_b = ensure_piper_binary()
        notes.append(msg_b)
        if ok_b:
            pulled.append("piper_binary")

    ok_w, msg_w = warm_whisper_weights()
    notes.append(msg_w)
    if ok_w:
        pulled.append("whisper")

    return {"ok": True, "pulled": pulled, "voice": notes}
