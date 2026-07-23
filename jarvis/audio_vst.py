"""AE-5 VST bridge — software EQ chains, optional VST3 (pedalboard), file processing."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from jarvis.config import DATA_DIR

PROCESSED_DIR = DATA_DIR / "audio" / "vst_processed"
CONFIG_FILE = DATA_DIR / "audio_vst.json"

# ffmpeg -af chains (always available when ffmpeg is installed)
SOFTWARE_CHAINS: dict[str, dict] = {
    "flat": {
        "label": "Bypass (no processing)",
        "filters": None,
        "description": "Pass-through — no EQ or dynamics.",
    },
    "voice": {
        "label": "Voice clarity (podcast / TTS)",
        "filters": (
            "highpass=f=80,"
            "acompressor=threshold=-18dB:ratio=3:attack=5:release=50,"
            "equalizer=f=250:width_type=o:width=1:g=-2,"
            "equalizer=f=3000:width_type=o:width=1:g=4,"
            "equalizer=f=8000:width_type=o:width=1:g=2,"
            "loudnorm=I=-16:TP=-1.5:LRA=11"
        ),
        "description": "Speech-focused EQ + light compression for AE-5 playback.",
    },
    "music": {
        "label": "Music (warm)",
        "filters": (
            "equalizer=f=80:width_type=o:width=1:g=2,"
            "equalizer=f=10000:width_type=o:width=1:g=1.5,"
            "acompressor=threshold=-20dB:ratio=2:attack=10:release=100"
        ),
        "description": "Gentle warmth and dynamics for music on the Sound Blaster.",
    },
    "scout": {
        "label": "Scout-style wide (virtual surround approx)",
        "filters": (
            "extrastereo=m=2.2,"
            "highshelf=f=8000:width_type=o:width=1:g=3,"
            "equalizer=f=120:width_type=o:width=1:g=1"
        ),
        "description": "Wider stereo + treble lift — approximates Creative Scout Mode in software.",
    },
    "gaming": {
        "label": "Gaming (footsteps / mids)",
        "filters": (
            "equalizer=f=200:width_type=o:width=1:g=-1,"
            "equalizer=f=2500:width_type=o:width=1:g=3,"
            "equalizer=f=6000:width_type=o:width=1:g=2,"
            "acompressor=threshold=-22dB:ratio=2:attack=3:release=40"
        ),
        "description": "Mid/high emphasis for positional audio cues.",
    },
}


def _load_user_config() -> dict:
    if not CONFIG_FILE.exists():
        return {"plugins": [], "chains": {}}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"plugins": [], "chains": {}}


def _save_user_config(data: dict) -> dict:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def pedalboard_available() -> bool:
    try:
        import pedalboard  # noqa: F401

        return True
    except ImportError:
        return False


def list_chains() -> list[dict]:
    """All chains: built-in software + user-defined."""
    out = []
    for chain_id, meta in SOFTWARE_CHAINS.items():
        out.append(
            {
                "id": chain_id,
                "label": meta["label"],
                "description": meta.get("description", ""),
                "engine": "ffmpeg",
            }
        )
    cfg = _load_user_config()
    for chain_id, meta in (cfg.get("chains") or {}).items():
        if chain_id in SOFTWARE_CHAINS:
            continue
        out.append(
            {
                "id": chain_id,
                "label": meta.get("label", chain_id),
                "description": meta.get("description", ""),
                "engine": meta.get("engine", "vst"),
                "plugin": meta.get("plugin", ""),
            }
        )
    return out


def register_vst_plugin(name: str, path: str) -> dict:
    """Register a VST3 plugin path for custom chains (DATA_DIR plugins only)."""
    plugins_root = (DATA_DIR / "audio" / "vst_plugins").resolve()
    plugins_root.mkdir(parents=True, exist_ok=True)
    plugin_path = Path(path).expanduser().resolve()
    if not plugin_path.is_file():
        raise FileNotFoundError(f"VST plugin not found: {plugin_path}")
    try:
        plugin_path.relative_to(plugins_root)
    except ValueError as exc:
        raise FileNotFoundError(f"VST plugin must be under {plugins_root}") from exc
    if not pedalboard_available():
        raise RuntimeError("pedalboard not installed — run ./scripts/install-ae5-vst-bridge.sh")

    cfg = _load_user_config()
    plugins = cfg.setdefault("plugins", [])
    entry = {"name": name.strip(), "path": str(plugin_path)}
    plugins = [p for p in plugins if p.get("name") != entry["name"]]
    plugins.append(entry)
    cfg["plugins"] = plugins
    _save_user_config(cfg)
    return entry


def status() -> dict:
    from jarvis.audio_settings import saved_vst_playback_chain, saved_vst_live_chain

    ffmpeg = shutil.which("ffmpeg")
    return {
        "ffmpeg": bool(ffmpeg),
        "pedalboard": pedalboard_available(),
        "chains": list_chains(),
        "playback_chain": saved_vst_playback_chain()
        or os.getenv("JARVIS_VST_CHAIN", "").strip()
        or "flat",
        "live_chain": saved_vst_live_chain() or "off",
        "plugin_path": os.getenv("JARVIS_VST_PLUGIN_PATH", "").strip(),
        "user_plugins": _load_user_config().get("plugins", []),
    }


def _ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def _process_ffmpeg(src: Path, filters: str, dest: Path) -> str:
    ffmpeg = _ffmpeg_path()
    if not ffmpeg:
        return "ERROR: ffmpeg not found — sudo apt install ffmpeg"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-af",
        filters,
        str(dest),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return "ERROR: VST/ffmpeg processing timed out"
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "ffmpeg failed").strip()
        return f"ERROR: VST processing failed: {err[:300]}"
    if not dest.is_file() or dest.stat().st_size < 100:
        return "ERROR: VST processing produced an empty file"
    return str(dest)


def _process_pedalboard(src: Path, plugin_path: str, dest: Path) -> str:
    if not pedalboard_available():
        return "ERROR: pedalboard not installed — run ./scripts/install-ae5-vst-bridge.sh"

    import numpy as np
    from pedalboard import Pedalboard
    from pedalboard.io import AudioFile

    plugin_file = Path(plugin_path).expanduser().resolve()
    if not plugin_file.is_file():
        return f"ERROR: VST plugin not found: {plugin_file}"

    try:
        from pedalboard import load_plugin

        plugin = load_plugin(str(plugin_file))
        board = Pedalboard([plugin])
        with AudioFile(str(src)) as f:
            audio = f.read(f.frames)
            sr = f.samplerate
        processed = board(audio, sr)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        with AudioFile(str(dest), "w", sr, processed.shape[0]) as out:
            out.write(processed.astype(np.float32))
    except Exception as e:
        return f"ERROR: VST plugin failed: {e}"
    return str(dest)


def process_file(
    path: str | Path,
    chain_id: str,
    *,
    output_path: str | Path | None = None,
) -> str:
    """Apply an EQ/VST chain to an audio file. Returns output path or ERROR: string."""
    from jarvis.security.path_confine import resolve_audio_library_path

    chain_id = (chain_id or "flat").strip().lower()
    src = resolve_audio_library_path(path)
    if src is None:
        return "ERROR: File not found or path not allowed"

    if chain_id == "flat":
        return str(src)

    cfg = _load_user_config()
    user_chain = (cfg.get("chains") or {}).get(chain_id)
    if user_chain and user_chain.get("plugin"):
        dest = (
            Path(output_path)
            if output_path
            else (PROCESSED_DIR / f"vst_{chain_id}_{src.stem}_{int(time.time())}.wav")
        )
        return _process_pedalboard(src, user_chain["plugin"], dest)

    env_plugin = os.getenv("JARVIS_VST_PLUGIN_PATH", "").strip()
    if chain_id == "custom" and env_plugin:
        dest = (
            Path(output_path)
            if output_path
            else (PROCESSED_DIR / f"vst_custom_{src.stem}_{int(time.time())}.wav")
        )
        return _process_pedalboard(src, env_plugin, dest)

    meta = SOFTWARE_CHAINS.get(chain_id)
    if not meta or not meta.get("filters"):
        return f"ERROR: Unknown VST chain '{chain_id}'"

    dest = (
        Path(output_path)
        if output_path
        else (PROCESSED_DIR / f"vst_{chain_id}_{src.stem}_{int(time.time())}.wav")
    )
    return _process_ffmpeg(src, meta["filters"], dest)
