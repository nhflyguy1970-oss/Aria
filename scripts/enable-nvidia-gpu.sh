#!/usr/bin/env bash
# Route Ollama + ARIA ML workloads to NVIDIA (RTX 3060) on dual-GPU systems.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "$ROOT/data/jarvis.env" 2>/dev/null || true

export JARVIS_GPU_PREFER="${JARVIS_GPU_PREFER:-nvidia}"
export JARVIS_CUDA_DEVICE="${JARVIS_CUDA_DEVICE:-0}"
export CUDA_VISIBLE_DEVICES="${JARVIS_CUDA_DEVICE}"
export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:--1}"
unset HSA_OVERRIDE_GFX_VERSION 2>/dev/null || true

echo "GPU routing: NVIDIA device ${CUDA_VISIBLE_DEVICES} (HIP hidden)"

if command -v nvidia-smi &>/dev/null; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
  echo "WARNING: nvidia-smi not found" >&2
fi

echo "Stopping Ollama to apply GPU env…"
pkill -x ollama 2>/dev/null || true
sleep 2

if command -v ollama &>/dev/null; then
  nohup env CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}" HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES}" \
    ollama serve >>"$ROOT/data/logs/ollama-gpu.log" 2>&1 &
  sleep 3
  if curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
    echo "Ollama ready on CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
  else
    echo "Ollama starting — check data/logs/ollama-gpu.log" >&2
  fi
else
  echo "ollama not in PATH" >&2
  exit 1
fi

echo "Restart ARIA: ./scripts/stop-jarvis.sh && ./scripts/launch-jarvis.sh"

COMFY_PORT="${JARVIS_COMFYUI_PORT:-8188}"
echo "Stopping ComfyUI on port ${COMFY_PORT}…"
fuser -k "${COMFY_PORT}/tcp" 2>/dev/null || true
pkill -f "ComfyUI/main.py" 2>/dev/null || true
pkill -f "main.py --listen.*${COMFY_PORT}" 2>/dev/null || true
sleep 2
echo "ComfyUI stopped — ARIA will start it on NVIDIA on the next image request."
