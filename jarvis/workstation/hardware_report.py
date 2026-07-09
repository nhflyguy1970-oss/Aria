"""Hardware detection, benchmarks, and workload placement recommendations."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from typing import Any


def _cpu_count() -> int:
    return os.cpu_count() or 0


def _ram_gb() -> float:
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / (1024 * 1024)
    except OSError:
        pass
    return 0.0


def _disk_free_gb(path: str = "~") -> float:
    try:
        usage = shutil.disk_usage(os.path.expanduser(path))
        return usage.free / (1024**3)
    except OSError:
        return 0.0


def _nvidia_gpus() -> list[dict[str, Any]]:
    gpus: list[dict[str, Any]] = []
    if shutil.which("nvidia-smi"):
        try:
            proc = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.used",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=8,
            )
            if proc.returncode == 0:
                for line in proc.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        gpus.append(
                            {
                                "vendor": "nvidia",
                                "name": parts[0],
                                "vram_mb": float(parts[1]),
                                "used_mb": float(parts[2]),
                            }
                        )
        except Exception:
            pass
    try:
        import torch

        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                name = torch.cuda.get_device_name(i)
                if not any(g.get("name") == name for g in gpus):
                    props = torch.cuda.get_device_properties(i)
                    gpus.append(
                        {
                            "vendor": "nvidia",
                            "name": name,
                            "vram_mb": props.total_memory / (1024**2),
                            "used_mb": None,
                        }
                    )
    except Exception:
        pass
    return gpus


def _amd_detected() -> bool:
    if shutil.which("rocminfo"):
        try:
            proc = subprocess.run(["rocminfo"], capture_output=True, text=True, timeout=8)
            return proc.returncode == 0 and "Agent" in (proc.stdout or "")
        except Exception:
            return False
    return False


def _benchmark_cpu_ms() -> float | None:
    started = time.perf_counter()
    try:
        total = 0.0
        for i in range(200_000):
            total += (i % 97) * 0.001
        del total
        return (time.perf_counter() - started) * 1000
    except Exception:
        return None


def _benchmark_matmul_ms() -> float | None:
    try:
        import torch

        if not torch.cuda.is_available():
            return None
        device = torch.device("cuda")
        a = torch.randn(512, 512, device=device)
        b = torch.randn(512, 512, device=device)
        torch.cuda.synchronize()
        started = time.perf_counter()
        for _ in range(20):
            _ = a @ b
        torch.cuda.synchronize()
        return (time.perf_counter() - started) * 1000 / 20
    except Exception:
        return None


def collect_hardware(*, benchmark: bool = True) -> dict[str, Any]:
    nvidia = _nvidia_gpus()
    amd = _amd_detected()
    cpu_ms = _benchmark_cpu_ms() if benchmark else None
    gpu_ms = _benchmark_matmul_ms() if benchmark else None

    has_nvidia = bool(nvidia)
    recommendations = {
        "llm_inference": "nvidia" if has_nvidia else ("cpu" if not amd else "rocm"),
        "embeddings": "nvidia" if has_nvidia else "cpu",
        "image_generation": "amd" if amd else ("nvidia" if has_nvidia else "cpu"),
        "ocr_image_processing": "amd" if amd else ("nvidia" if has_nvidia else "cpu"),
        "indexing_ingestion": "cpu",
        "schedulers_automation": "cpu",
    }

    bottlenecks: list[str] = []
    ram = _ram_gb()
    if ram and ram < 16:
        bottlenecks.append(f"Low RAM ({ram:.0f}GB): prefer 7B models, enable VRAM guard")
    if not has_nvidia and not amd:
        bottlenecks.append("No GPU detected: inference and image gen will be CPU-bound")
    if gpu_ms and gpu_ms > 50:
        bottlenecks.append(f"CUDA matmul slow ({gpu_ms:.1f}ms): check drivers or thermals")

    current = {
        "JARVIS_GPU_PREFER": os.getenv("JARVIS_GPU_PREFER", ""),
        "JARVIS_COMFYUI_DEVICE": os.getenv("JARVIS_COMFYUI_DEVICE", ""),
        "OLLAMA_HOST": os.getenv("OLLAMA_HOST", ""),
    }

    return {
        "ok": True,
        "ts": time.time(),
        "cpu_cores": _cpu_count(),
        "ram_gb": round(ram, 1),
        "disk_free_gb": round(_disk_free_gb(), 1),
        "nvidia_gpus": nvidia,
        "amd_rocm": amd,
        "benchmarks": {
            "cpu_loop_ms": cpu_ms,
            "cuda_matmul_ms": gpu_ms,
        },
        "current_placement": current,
        "recommended_placement": recommendations,
        "bottlenecks": bottlenecks,
        "expected_utilization": {
            "nvidia": "high during chat/embed" if has_nvidia else "n/a",
            "amd": "high during ComfyUI/OCR" if amd else "n/a",
            "cpu": "background indexing and automation",
        },
    }


def format_hardware_markdown(report: dict[str, Any] | None = None) -> str:
    data = report or collect_hardware()
    lines = ["## Hardware Report", ""]
    lines.append(f"CPU cores: **{data.get('cpu_cores')}** · RAM: **{data.get('ram_gb')} GB**")
    lines.append(f"Disk free: **{data.get('disk_free_gb')} GB**")
    for gpu in data.get("nvidia_gpus") or []:
        lines.append(f"NVIDIA: **{gpu.get('name')}** ({gpu.get('vram_mb', 0):.0f} MB)")
    if data.get("amd_rocm"):
        lines.append("AMD ROCm: **detected**")
    bench = data.get("benchmarks") or {}
    if bench.get("cuda_matmul_ms") is not None:
        lines.append(f"CUDA matmul benchmark: **{bench['cuda_matmul_ms']:.2f} ms**")
    lines.append("\n### Recommended placement")
    for role, target in (data.get("recommended_placement") or {}).items():
        lines.append(f"- {role}: `{target}`")
    if data.get("bottlenecks"):
        lines.append("\n### Bottlenecks")
        for item in data["bottlenecks"]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def hardware_json() -> str:
    return json.dumps(collect_hardware(), indent=2)
