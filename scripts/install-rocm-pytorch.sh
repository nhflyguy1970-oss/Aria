#!/usr/bin/env bash
# Install PyTorch with ROCm support for AMD-only AI (not dual-GPU NVIDIA-for-AI setups).
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
ROCM_VER="${ROCM_VERSION:-6.4}"

if ! command -v rocm-smi >/dev/null 2>&1; then
  echo "ROCm not found. Install ROCm first, then re-run this script."
  exit 1
fi

ENV_FILE="${JARVIS_ROOT}/data/jarvis.env"
gpu_pref="${JARVIS_GPU_PREFER:-}"
if [[ -z "$gpu_pref" && -f "$ENV_FILE" ]]; then
  gpu_pref="$(grep -E '^export JARVIS_GPU_PREFER=' "$ENV_FILE" 2>/dev/null | tail -1 | sed 's/^export JARVIS_GPU_PREFER=//; s/^"//; s/"$//')"
fi
if command -v nvidia-smi >/dev/null 2>&1 && [[ "${gpu_pref:-nvidia}" == "nvidia" && "${ROCM_FORCE:-0}" != "1" ]]; then
  cat <<EOF
NVIDIA GPU detected and JARVIS_GPU_PREFER=nvidia.

This machine uses AMD for display/desktop and NVIDIA for Jarvis AI.
Install CUDA PyTorch instead:

  bash ${JARVIS_ROOT}/scripts/install-cuda-pytorch.sh

ROCm PyTorch is for AMD-only AI (JARVIS_GPU_PREFER=amd).
To force ROCm anyway: ROCM_FORCE=1 $0
EOF
  exit 1
fi

if [[ ! -x "${VENV}/bin/pip" ]]; then
  echo "venv not found at ${VENV} — run ./scripts/install-dependencies.sh first"
  exit 1
fi

echo "Installing ROCm PyTorch (ROCm ${ROCM_VER}) into ${VENV}…"
"${VENV}/bin/pip" install --upgrade pip
"${VENV}/bin/pip" uninstall -y torch torchvision torchaudio pytorch-triton-rocm 2>/dev/null || true
"${VENV}/bin/pip" uninstall -y torchao 2>/dev/null || true
"${VENV}/bin/pip" install --force-reinstall torch torchvision torchaudio \
  --index-url "https://download.pytorch.org/whl/rocm${ROCM_VER}"

if ! grep -q 'JARVIS_TORCH_DEVICE' "$ENV_FILE" 2>/dev/null; then
  {
    echo ""
    echo "# PyTorch ROCm — use cuda device name with ROCm builds"
    echo 'export JARVIS_TORCH_DEVICE="cuda"'
  } >> "$ENV_FILE"
  echo "Added JARVIS_TORCH_DEVICE=cuda to data/jarvis.env"
fi

echo ""
export PYTHONPATH="${JARVIS_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
"${VENV}/bin/python" -c "
import torch
print('torch', torch.__version__)
print('cuda available', torch.cuda.is_available())
print('hip', getattr(torch.version, 'hip', None))
if '+cu' in torch.__version__:
    raise SystemExit('Still on CUDA build — uninstall failed or wrong index')
from jarvis.torch_device import device_info
import json
print(json.dumps(device_info(), indent=2))
"
echo "Done. Restart Jarvis and check GET /api/audio/torch-device"
