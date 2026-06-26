#!/usr/bin/env bash
# Download Stable Diffusion XL 1.0 base checkpoint for ComfyUI (~6.5 GB).
set -euo pipefail

COMFY_ROOT="${JARVIS_COMFYUI_ROOT:-$HOME/ComfyUI}"
CKPT_DIR="$COMFY_ROOT/models/checkpoints"
FILE="sd_xl_base_1.0.safetensors"
URL="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/$FILE"
OUT="$CKPT_DIR/$FILE"

log() { echo "[sdxl-base] $*"; }

mkdir -p "$CKPT_DIR"

if [[ -f "$OUT" ]]; then
  size=$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT")
  if (( size > 6000000000 )); then
    log "Already installed: $OUT"
    exit 0
  fi
  log "Incomplete file found — resuming download"
fi

log "Downloading SDXL 1.0 base to $OUT"
log "This is ~6.5 GB and may take several minutes…"

if command -v curl &>/dev/null; then
  curl -L --retry 3 --continue-at - -o "$OUT" "$URL"
elif command -v wget &>/dev/null; then
  wget -c -O "$OUT" "$URL"
else
  log "ERROR: need curl or wget"
  exit 1
fi

log "Done: $OUT"
log "Jarvis will use SDXL 1.0 by default (Quality mode in sidebar). Restart ComfyUI if it is running."
