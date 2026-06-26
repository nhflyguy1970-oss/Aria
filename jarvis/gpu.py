import json
import os
import re
import subprocess
import time
import urllib.request

_GPU_CACHE: dict = {"at": 0.0, "data": None}
_GPU_CACHE_SEC = 30.0


def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except Exception:
        return ""


def _parse_rocm_smi(out: str) -> dict:
    """Extract GPU name, VRAM, and driver from rocm-smi output."""
    result = {"name": "", "vram_mb": 0, "driver": ""}
    for line in out.splitlines():
        if "Card series:" in line:
            result["name"] = line.split("Card series:", 1)[-1].strip()
        elif "VRAM Total Memory (B):" in line:
            m = re.search(r"VRAM Total Memory \(B\):\s*(\d+)", line)
            if m:
                result["vram_mb"] = round(int(m.group(1)) / (1024 * 1024))
        elif "Driver version:" in line:
            result["driver"] = line.split(":", 1)[-1].strip()
    return result


def _parse_vram_used_mb(out: str) -> int:
    for line in out.splitlines():
        if "VRAM Used Memory (B):" in line or "Used VRAM" in line:
            m = re.search(r"(\d+)\s*$", line.strip())
            if m:
                return round(int(m.group(1)) / (1024 * 1024))
    return 0


def free_vram_mb(*, force: bool = False) -> int:
    info = detect_gpu(force=force)
    free = info.get("free_vram_mb")
    if free is not None:
        return int(free)
    total = info.get("vram_mb") or 0
    used = info.get("vram_used_mb") or 0
    if total and used:
        return max(0, total - used)
    return 0


def _gpu_from_lspci(lspci: str) -> tuple[str, str]:
    """Return (vendor, name) from lspci, preferring actual display adapters."""
    vendor = "unknown"
    name = "Unknown"
    if "AMD" in lspci or "ATI" in lspci:
        vendor = "amd"
    elif "NVIDIA" in lspci:
        vendor = "nvidia"

    for line in lspci.splitlines():
        low = line.lower()
        if "vga compatible controller" in low or "display controller" in low:
            name = line.split(": ", 1)[-1].strip()
            break
        if vendor != "unknown" and ("radeon" in low or "geforce" in low) and "audio" not in low:
            name = line.split(": ", 1)[-1].strip()
            break
    return vendor, name


def _detect_gpu_uncached() -> dict:
    info = {
        "name": "Unknown",
        "vendor": "unknown",
        "vram_mb": 0,
        "rocm_available": False,
        "rocm_version": None,
        "ollama_using_gpu": False,
        "ollama_processor": None,
        "recommendation": "",
    }

    lspci = _run(["lspci"])
    vendor, name = _gpu_from_lspci(lspci)
    info["vendor"] = vendor
    info["name"] = name

    try:
        from jarvis.gpu_routing import gpu_preference, parse_nvidia_smi

        nvidia = parse_nvidia_smi()
        if nvidia:
            info["nvidia"] = nvidia
            info["nvidia_available"] = True
            info["compute_gpu"] = nvidia.get("name", "")
            info["compute_vram_mb"] = nvidia.get("vram_mb", 0)
            info["compute_vendor"] = "nvidia"
            info["display_gpu"] = info.get("name", "")
            info["display_vendor"] = info.get("vendor", "unknown")
            if gpu_preference() in ("nvidia", "both", "auto"):
                info["name"] = nvidia.get("name", info["name"])
                info["vendor"] = "nvidia"
                if nvidia.get("vram_mb"):
                    info["vram_mb"] = nvidia["vram_mb"]
                if nvidia.get("free_vram_mb") is not None:
                    info["free_vram_mb"] = nvidia["free_vram_mb"]
                if nvidia.get("vram_used_mb") is not None:
                    info["vram_used_mb"] = nvidia["vram_used_mb"]
    except Exception:
        pass

    rocm_out = _run(["rocm-smi", "--showproductname"])
    rocm_mem = _run(["rocm-smi", "--showmeminfo", "vram"])
    rocm_drv = _run(["rocm-smi", "--showdriverversion"])
    rocm_all = "\n".join((rocm_out, rocm_mem, rocm_drv))
    if rocm_out and "error" not in rocm_out.lower() and "Card series" in rocm_out:
        info["rocm_available"] = True
        parsed = _parse_rocm_smi(rocm_all)
        if parsed["name"] and not info.get("display_gpu"):
            info["display_gpu"] = parsed["name"]
        if parsed["driver"]:
            info["rocm_version"] = parsed["driver"]
        if info.get("vendor") != "nvidia":
            if parsed["name"]:
                info["name"] = parsed["name"]
            if parsed["vram_mb"]:
                info["vram_mb"] = parsed["vram_mb"]
            used = _parse_vram_used_mb(rocm_all)
            if used:
                info["vram_used_mb"] = used
                if info["vram_mb"]:
                    info["free_vram_mb"] = max(0, info["vram_mb"] - used)

    if not info["rocm_available"]:
        ver = _run(["rocminfo"], timeout=5)
        if "ROCm" in ver or "gfx" in ver.lower():
            info["rocm_available"] = True
            m = re.search(r"ROCm.*?(\d+\.\d+)", ver)
            if m:
                info["rocm_version"] = m.group(1)

    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{host}/api/ps", timeout=2) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("models", [])
            if models:
                m = models[0]
                proc = m.get("processor", "") or ""
                info["ollama_processor"] = proc
                info["ollama_using_gpu"] = "gpu" in proc.lower() or "100%" in proc
    except Exception:
        pass

    vram_note = f" ({info['vram_mb']}MB VRAM)" if info["vram_mb"] else ""

    if info.get("compute_vendor") == "nvidia":
        nv = info.get("nvidia") or {}
        info["recommendation"] = (
            f"NVIDIA compute: {nv.get('name', 'GPU')} "
            f"({nv.get('free_vram_mb', nv.get('vram_mb', 0))}MB free). "
            "Display GPU may be AMD — image gen and Ollama use NVIDIA when ComfyUI is restarted via ARIA."
        )
    elif info["ollama_using_gpu"]:
        info["recommendation"] = f"GPU acceleration active{vram_note}."
    elif info["rocm_available"]:
        info["recommendation"] = (
            f"ROCm is installed and ready{vram_note}. "
            "Send a chat message to load a model — GPU usage appears after the first inference."
        )
    elif info["vendor"] == "amd":
        info["recommendation"] = (
            "Install ROCm so Ollama uses your AMD GPU: "
            "https://ollama.com/blog/amd-preview"
        )
    else:
        info["recommendation"] = "Load a model and send a message to verify GPU usage."

    return info


def invalidate_gpu_cache() -> None:
    global _GPU_CACHE
    _GPU_CACHE = {"at": 0.0, "data": None}


def detect_gpu(*, force: bool = False) -> dict:
    now = time.time()
    if (
        not force
        and _GPU_CACHE["data"] is not None
        and now - _GPU_CACHE["at"] < _GPU_CACHE_SEC
    ):
        return dict(_GPU_CACHE["data"])
    info = _detect_gpu_uncached()
    _GPU_CACHE["at"] = now
    _GPU_CACHE["data"] = info
    return dict(info)


def is_low_vram(threshold_mb: int = 10240) -> bool:
    """True when compute GPU VRAM is at or below threshold (default 10GB)."""
    try:
        from jarvis.gpu_routing import is_compute_low_vram

        return is_compute_low_vram(threshold_mb)
    except Exception:
        info = detect_gpu()
        vram = int(info.get("vram_mb") or 0)
        return 0 < vram <= threshold_mb
