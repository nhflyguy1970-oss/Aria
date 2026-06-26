"""Load data/jarvis.env into os.environ (once per process)."""

import hashlib
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / "data" / "jarvis.env"
_LOADED = False
_ENV_DIGEST = ""
_PREVIOUS_JARVIS_KEYS: set[str] = set()


def load_jarvis_env(force: bool = False) -> None:
    global _LOADED, _ENV_DIGEST, _PREVIOUS_JARVIS_KEYS
    try:
        raw = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    except OSError:
        raw = ""
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw else ""
    if _LOADED and not force and digest == _ENV_DIGEST:
        return
    keys_in_file: set[str] = set()
    _ENV_DIGEST = digest
    if not raw:
        for key in _PREVIOUS_JARVIS_KEYS - keys_in_file:
            os.environ.pop(key, None)
        _PREVIOUS_JARVIS_KEYS = keys_in_file
        _apply_gpu_routing()
        _apply_rocm_override()
        _LOADED = True
        return
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key:
            continue
        if "$PATH" in val:
            val = val.replace("$PATH", os.environ.get("PATH", ""))
        if key == "PATH":
            os.environ["PATH"] = val
        if key.startswith("JARVIS_"):
            os.environ[key] = val
            keys_in_file.add(key)
        elif key not in os.environ:
            os.environ[key] = val
    for key in _PREVIOUS_JARVIS_KEYS - keys_in_file:
        os.environ.pop(key, None)
    _PREVIOUS_JARVIS_KEYS = keys_in_file
    _apply_gpu_routing()
    _apply_rocm_override()
    _LOADED = True


def upsert_env_vars(updates: dict[str, str]) -> list[str]:
    """Set or append export KEY=\"value\" lines in data/jarvis.env."""
    import re

    changed: list[str] = []
    text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.is_file() else ""
    for key, value in updates.items():
        pattern = re.compile(rf"^export\s+{re.escape(key)}=.*$", re.MULTILINE)
        line = f'export {key}="{value}"'
        if pattern.search(text):
            new_text = pattern.sub(line, text)
            if new_text != text:
                changed.append(key)
            text = new_text
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            text += f"\n# {key}\n{line}\n"
            changed.append(key)
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(text, encoding="utf-8")
    for key, value in updates.items():
        os.environ[key] = value
    return changed


def _apply_gpu_routing() -> None:
    """Apply CUDA_VISIBLE_DEVICES / HIP_VISIBLE_DEVICES from JARVIS_GPU_PREFER."""
    try:
        from jarvis.gpu_routing import gpu_env_for_subprocess, gpu_preference

        if gpu_preference() == "nvidia":
            os.environ.pop("HSA_OVERRIDE_GFX_VERSION", None)
        for key, value in gpu_env_for_subprocess().items():
            os.environ[key] = value
    except Exception:
        pass


def _apply_rocm_override() -> None:
    """RX 7600 (gfx1102) needs HSA_OVERRIDE_GFX_VERSION so ROCm uses gfx1100 kernels."""
    pref = (os.getenv("JARVIS_GPU_PREFER") or "auto").strip().lower()
    if pref == "nvidia":
        return
    gfx = os.getenv("JARVIS_ROCM_GFX", "11.0.0").strip()
    if gfx:
        os.environ.setdefault("HSA_OVERRIDE_GFX_VERSION", gfx)
