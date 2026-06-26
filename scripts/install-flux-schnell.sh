#!/usr/bin/env bash
# Download Flux.1 Schnell fp8 checkpoint for ComfyUI (~12 GB).
# Best prompt adherence on 8GB GPUs (RX 7600). Uses ComfyUI's single-checkpoint fp8 build.
set -euo pipefail

COMFY_ROOT="${JARVIS_COMFYUI_ROOT:-$HOME/ComfyUI}"
CKPT_DIR="$COMFY_ROOT/models/checkpoints"
FILE="flux1-schnell-fp8.safetensors"
URL="https://huggingface.co/Comfy-Org/flux1-schnell/resolve/main/${FILE}"
OUT="$CKPT_DIR/$FILE"

log() { echo "[flux-schnell] $*"; }

mkdir -p "$CKPT_DIR"

if [[ -f "$OUT" ]]; then
  size=$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT")
  if (( size > 10000000000 )); then
    log "Already installed: $OUT"
    exit 0
  fi
  log "Incomplete file found — resuming download"
fi

log "Downloading Flux Schnell fp8 to $OUT"
log "This is ~12 GB. Accept the Flux license on Hugging Face if the download fails."
log "After install: sidebar → Image model → Flux Schnell (best prompts)"

if command -v curl &>/dev/null; then
  curl -L --retry 3 --continue-at - -o "$OUT" "$URL"
elif command -v wget &>/dev/null; then
  wget -c -O "$OUT" "$URL"
else
  log "ERROR: need curl or wget"
  exit 1
fi

log "Done: $OUT"
log "Select Flux Schnell in the Jarvis sidebar and restart ComfyUI if it is running."
