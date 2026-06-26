#!/usr/bin/env bash
# Install ComfyUI AnimateDiff-Evolved + VideoHelperSuite + SD1.5 motion module (~2 GB).
set -euo pipefail

COMFY_ROOT="${JARVIS_COMFYUI_ROOT:-$HOME/ComfyUI}"
CUSTOM_NODES="$COMFY_ROOT/custom_nodes"
MOTION_DIR="$COMFY_ROOT/models/animatediff_models"
MOTION_FILE="mm_sd_v15_v2.ckpt"
MOTION_URL="https://huggingface.co/guoyww/animatediff/resolve/main/mm_sd_v15_v2.ckpt"

log() { echo "[animatediff] $*"; }

if [[ ! -f "$COMFY_ROOT/main.py" ]]; then
  log "ERROR: ComfyUI not found at $COMFY_ROOT"
  log "Clone first: git clone https://github.com/comfyanonymous/ComfyUI.git ~/ComfyUI"
  exit 1
fi

mkdir -p "$CUSTOM_NODES" "$MOTION_DIR"

install_node() {
  local repo="$1"
  local dir="$2"
  if [[ -d "$dir/.git" ]]; then
    log "Updating $(basename "$dir")…"
    git -C "$dir" pull --ff-only || true
  else
    log "Cloning $repo → $dir"
    git clone --depth 1 "$repo" "$dir"
  fi
}

install_node "https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git" \
  "$CUSTOM_NODES/ComfyUI-AnimateDiff-Evolved"
install_node "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" \
  "$CUSTOM_NODES/ComfyUI-VideoHelperSuite"

OUT="$MOTION_DIR/$MOTION_FILE"
if [[ -f "$OUT" ]]; then
  size=$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT")
  if (( size > 1500000000 )); then
    log "Motion module already installed: $OUT"
  else
    log "Incomplete motion module — re-downloading"
    rm -f "$OUT"
  fi
fi

if [[ ! -f "$OUT" ]]; then
  log "Downloading motion module (~1.8 GB) to $OUT"
  if command -v curl &>/dev/null; then
    curl -L --retry 3 --continue-at - -o "$OUT" "$MOTION_URL"
  elif command -v wget &>/dev/null; then
    wget -c -O "$OUT" "$MOTION_URL"
  else
    log "ERROR: need curl or wget"
    exit 1
  fi
fi

COMFY_VENV="$COMFY_ROOT/venv"
if [[ -x "$COMFY_VENV/bin/pip" ]]; then
  log "Installing VideoHelperSuite Python deps into ComfyUI venv…"
  "$COMFY_VENV/bin/pip" install -q opencv-python-headless imageio-ffmpeg || true
fi

# SD 1.5 checkpoint hint — Realistic Vision works if already installed
CKPT_DIR="$COMFY_ROOT/models/checkpoints"
SD15=""
for f in Realistic_Vision_V6.0_NV_B1_fp16.safetensors epicrealism_naturalSinRC1VAE.safetensors v1-5-pruned-emaonly.safetensors; do
  if [[ -f "$CKPT_DIR/$f" ]]; then
    SD15="$f"
    break
  fi
done

log ""
log "Done."
log "  Motion module: $OUT"
log "  Custom nodes:  ComfyUI-AnimateDiff-Evolved, ComfyUI-VideoHelperSuite"
if [[ -n "$SD15" ]]; then
  log "  SD 1.5 checkpoint found: $SD15"
else
  log "  NOTE: No SD 1.5 checkpoint found in $CKPT_DIR"
  log "  AnimateDiff needs SD 1.5 (not SDXL). Realistic Vision V6 or similar."
fi
log ""
log "Restart ComfyUI, then set Video Studio engine to Auto or AnimateDiff."
log "Jarvis will fall back to Ken Burns if AnimateDiff OOMs on 8GB VRAM."
