#!/usr/bin/env bash
# Install PyTorch with NVIDIA CUDA for RTX / GeForce (dual-GPU: AI on NVIDIA, AMD for display).
set -euo pipefail
JARVIS_ROOT="${JARVIS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
if [[ -n "${JARVIS_VENV:-}" ]]; then
  if [[ -d "$JARVIS_VENV" ]]; then
    VENV="$JARVIS_VENV"
  else
    VENV="$(dirname "$(dirname "$JARVIS_VENV")")"
  fi
else
  VENV="${JARVIS_ROOT}/venv"
fi
CUDA_INDEX="${CUDA_INDEX:-cu124}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi not found — install NVIDIA drivers first."
  exit 1
fi

echo "NVIDIA GPU:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo ""
echo "Installing CUDA PyTorch (${CUDA_INDEX}) into ${VENV}…"
"${VENV}/bin/pip" install --upgrade pip
"${VENV}/bin/pip" uninstall -y torch torchvision torchaudio pytorch-triton-rocm 2>/dev/null || true
"${VENV}/bin/pip" uninstall -y torchao 2>/dev/null || true
"${VENV}/bin/pip" install --force-reinstall torch torchvision torchaudio \
  --index-url "https://download.pytorch.org/whl/${CUDA_INDEX}"

echo ""
export PYTHONPATH="${JARVIS_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
"${VENV}/bin/python" -c "
import torch
print('torch', torch.__version__)
print('cuda available', torch.cuda.is_available())
if torch.cuda.is_available():
    print('device', torch.cuda.get_device_name(0))
from jarvis.gpu_routing import routing_status
import json
print(json.dumps(routing_status(), indent=2))
"
echo "Done. Run ./scripts/enable-nvidia-gpu.sh then restart ARIA."
