#!/usr/bin/env bash
# Download NSFW-friendly ComfyUI checkpoints (~16 GB total).
# RealVisXL V5 (photoreal SDXL), Realistic Vision V6 (photoreal SD 1.5), Pony Diffusion V6 XL.
set -euo pipefail

COMFY_ROOT="${JARVIS_COMFYUI_ROOT:-$HOME/ComfyUI}"
CKPT_DIR="$COMFY_ROOT/models/checkpoints"
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -f "$JARVIS_ROOT/data/jarvis.env" ]]; then
  # shellcheck disable=SC1091
  source "$JARVIS_ROOT/data/jarvis.env"
fi

HF_AUTH=()
if [[ -n "${HF_TOKEN:-}" ]]; then
  HF_AUTH=(-H "Authorization: Bearer ${HF_TOKEN}")
fi

log() { echo "[nsfw-checkpoints] $*"; }

download_one() {
  local file="$1"
  local url="$2"
  local min_bytes="$3"
  local out="$CKPT_DIR/$file"

  if [[ -f "$out" ]]; then
    local size
    size=$(stat -c%s "$out" 2>/dev/null || stat -f%z "$out")
    if (( size >= min_bytes )); then
      log "Already installed: $file"
      return 0
    fi
    log "Incomplete $file — resuming download"
  fi

  log "Downloading $file"
  log "  → $out"
  if command -v curl &>/dev/null; then
    curl -L --retry 3 --continue-at - "${HF_AUTH[@]}" -o "$out" "$url"
  elif command -v wget &>/dev/null; then
    if ((${#HF_AUTH[@]})); then
      wget -c --header="Authorization: Bearer ${HF_TOKEN}" -O "$out" "$url"
    else
      wget -c -O "$out" "$url"
    fi
  else
    log "ERROR: need curl or wget"
    exit 1
  fi
  log "Done: $file"
}

mkdir -p "$CKPT_DIR"

log "Installing NSFW-friendly checkpoints to $CKPT_DIR"
log "Uncensored mode will auto-select RealVisXL when available."

download_one \
  "RealVisXL_V5.0_fp16.safetensors" \
  "https://huggingface.co/SG161222/RealVisXL_V5.0/resolve/main/RealVisXL_V5.0_fp16.safetensors" \
  6500000000

download_one \
  "Realistic_Vision_V6.0_NV_B1_fp16.safetensors" \
  "https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE/resolve/main/Realistic_Vision_V6.0_NV_B1_fp16.safetensors" \
  2000000000

download_one \
  "ponyDiffusionV6XL_v6StartWithThisOne.safetensors" \
  "https://huggingface.co/AiAF/ponyDiffusionV6XL_v6StartWithThisOne.safetensors/resolve/main/ponyDiffusionV6XL_v6StartWithThisOne.safetensors" \
  6500000000

log ""
log "Extended NSFW checkpoint pack (~28 GB additional if not already installed)…"

download_one \
  "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors" \
  "https://huggingface.co/RunDiffusion/Juggernaut-XL-v9/resolve/main/Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors" \
  6500000000

download_one \
  "lustifySDXLNSFWSFW_v10.safetensors" \
  "https://huggingface.co/modelzpalace/lustifySDXLNSFWSFW_v10/resolve/main/lustifySDXLNSFWSFW_v10.safetensors" \
  6500000000

download_one \
  "leosamsHelloworldXL_helloworldXL60.safetensors" \
  "https://huggingface.co/misri/leosamsHelloworldXL_helloworldXL60/resolve/main/leosamsHelloworldXL_helloworldXL60.safetensors" \
  6500000000

download_one \
  "DreamShaperXL_Turbo_v2.safetensors" \
  "https://huggingface.co/Lykon/dreamshaper-xl-v2-turbo/resolve/main/DreamShaperXL_Turbo_v2.safetensors" \
  6500000000

download_one \
  "epicrealism_naturalSinRC1VAE.safetensors" \
  "https://huggingface.co/Kalashnikov/epiCRealism/resolve/main/epicrealism_naturalSinRC1VAE.safetensors" \
  2000000000

log ""
log "All done. In Jarvis:"
log "  1. Enable Uncensored mode (sidebar toggle or launch script)"
log "  2. Gallery → Image Engine — RealVisXL should be selected automatically"
log "  3. Pick Pony XL or Realistic Vision from Installed checkpoint for other styles"
log "Restart ComfyUI if it is already running."
