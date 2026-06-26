#!/usr/bin/env bash
# Install PyTorch with ROCm support for MusicGen / Whisper GPU on AMD RX cards.
set -euo pipefail
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${JARVIS_ROOT}/venv"
# Prefer ROCM_VERSION env; else pick index with newest cp312 wheels (6.4 → 2.9.x).
ROCM_VER="${ROCM_VERSION:-6.4}"

if ! command -v rocm-smi >/dev/null 2>&1; then
  echo "ROCm not found. Install ROCm first, then re-run this script."
  exit 1
fi

echo "Installing ROCm PyTorch (ROCm ${ROCM_VER}) into ${VENV}…"
"${VENV}/bin/pip" install --upgrade pip
"${VENV}/bin/pip" install torch torchvision torchaudio \
  --index-url "https://download.pytorch.org/whl/rocm${ROCM_VER}"

ENV_FILE="${JARVIS_ROOT}/data/jarvis.env"
if ! grep -q 'JARVIS_TORCH_DEVICE' "$ENV_FILE" 2>/dev/null; then
  {
    echo ""
    echo "# PyTorch ROCm — use cuda device name with ROCm builds"
    echo 'export JARVIS_TORCH_DEVICE="cuda"'
  } >> "$ENV_FILE"
  echo "Added JARVIS_TORCH_DEVICE=cuda to data/jarvis.env"
fi

"${VENV}/bin/python" -c "
from jarvis.torch_device import device_info
import json
print(json.dumps(device_info(), indent=2))
"
echo "Done. Restart Jarvis and check GET /api/audio/torch-device"
