#!/usr/bin/env bash
# Detect workstation hardware and print workload assignment recommendations.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/venv/bin/python"
[[ -x "$PY" ]] || PY=python3

echo "=== Aria Hardware Report ==="
echo ""

"$PY" <<'PY'
from __future__ import annotations

import json
import os
import shutil


def section(title: str) -> None:
    print(f"## {title}")


def main() -> None:
    section("CPU")
    try:
        cores = os.cpu_count() or 0
        print(f"  Logical CPUs: {cores}")
        print("  Recommended: ingestion, indexing, schedulers, automation")
    except Exception as exc:
        print(f"  unavailable: {exc}")

    section("Memory")
    mem_gb = 0.0
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_gb = int(line.split()[1]) / (1024 * 1024)
                    break
        print(f"  RAM: {mem_gb:.1f} GB")
        swap = shutil.disk_usage("/swapfile").total if os.path.exists("/swapfile") else 0
        if swap:
            print(f"  Swap file: {swap / (1024**3):.1f} GB")
    except Exception:
        print("  RAM: unknown")

    section("Storage")
    try:
        usage = shutil.disk_usage(os.path.expanduser("~"))
        print(f"  Home free: {usage.free / (1024**3):.1f} GB")
    except Exception:
        pass

    section("GPU")
    nvidia = False
    amd = False
    try:
        import torch

        if torch.cuda.is_available():
            nvidia = True
            for i in range(torch.cuda.device_count()):
                name = torch.cuda.get_device_name(i)
                vram = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                print(f"  CUDA {i}: {name} ({vram:.1f} GB VRAM)")
            print("  Recommended: LLM inference, embeddings, fine-tuning")
    except Exception:
        pass

    try:
        out = os.popen("rocminfo 2>/dev/null | head -5").read().strip()
        if out:
            amd = True
            print("  AMD ROCm: detected")
            print("  Recommended: desktop, ComfyUI/Forge, OCR, image/video processing")
    except Exception:
        pass

    if not nvidia and not amd:
        print("  No GPU detected via torch/rocminfo — CPU-only mode")

    section("Workload assignments")
    assignments = {
        "llm_inference": "nvidia" if nvidia else "cpu",
        "embeddings": "nvidia" if nvidia else "cpu",
        "image_generation": "amd" if amd else ("nvidia" if nvidia else "cpu"),
        "ingestion_indexing": "cpu",
        "schedulers_automation": "cpu",
    }
    print(json.dumps(assignments, indent=2))

    section("Bottlenecks (heuristic)")
    if mem_gb and mem_gb < 16:
        print("  - Low RAM: prefer 7B models, enable VRAM guard")
    if not nvidia:
        print("  - No NVIDIA CUDA: Ollama on CPU/ROCm only — expect slower inference")
    if not amd and not nvidia:
        print("  - No GPU: image generation will be very slow or unavailable")

    section("Expected utilization")
    print("  Run ./workstation verify after changing hardware or drivers.")
    print("  Measure latency before optimizing — see docs/DEPLOYMENT.md")


if __name__ == "__main__":
    main()
PY
