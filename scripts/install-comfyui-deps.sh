#!/usr/bin/env bash
# Install ComfyUI Python deps into ComfyUI's own venv — NOT Jarvis's venv.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMFY_ROOT="${JARVIS_COMFYUI_ROOT:-$HOME/ComfyUI}"
COMFY_VENV="$COMFY_ROOT/venv"

usage() {
  cat <<EOF
Usage: ./scripts/install-comfyui-deps.sh [options]

Installs ComfyUI requirements into ~/ComfyUI/venv (separate from Jarvis).

Do NOT run: pip install sqlalchemy
That installs into the wrong environment. Use this script instead.

Options:
  --comfy-root PATH   ComfyUI directory (default: ~/ComfyUI)
  --recreate-venv     Delete and recreate ComfyUI venv first
  -h, --help          Show this help
EOF
}

RECREATE=0
for arg in "$@"; do
  case "$arg" in
    --comfy-root) shift; COMFY_ROOT="${1:?}"; COMFY_VENV="$COMFY_ROOT/venv" ;;
    --recreate-venv) RECREATE=1 ;;
    -h|--help) usage; exit 0 ;;
  esac
done

log() { echo "[comfyui install] $*"; }

if [[ ! -f "$COMFY_ROOT/main.py" ]]; then
  log "ERROR: ComfyUI not found at $COMFY_ROOT"
  log "Clone it first:"
  log "  git clone https://github.com/comfyanonymous/ComfyUI.git ~/ComfyUI"
  exit 1
fi

if [[ "$RECREATE" == "1" && -d "$COMFY_VENV" ]]; then
  log "Removing old venv: $COMFY_VENV"
  rm -rf "$COMFY_VENV"
fi

if [[ ! -d "$COMFY_VENV" ]]; then
  log "Creating ComfyUI venv at $COMFY_VENV"
  python3 -m venv "$COMFY_VENV"
fi

# shellcheck disable=SC1091
source "$COMFY_VENV/bin/activate"

log "Using Python: $(which python)"
log "Installing from $COMFY_ROOT/requirements.txt …"
pip install -U pip wheel setuptools
pip install -r "$COMFY_ROOT/requirements.txt"

log "Verifying SQLAlchemy…"
python -c "import sqlalchemy; print('SQLAlchemy', sqlalchemy.__version__, 'OK')"

ENV_FILE="$JARVIS_ROOT/data/jarvis.env"
if [[ -f "$ENV_FILE" ]]; then
  if ! grep -q 'JARVIS_AUTOSTART_COMFYUI' "$ENV_FILE"; then
    echo 'export JARVIS_AUTOSTART_COMFYUI="1"' >> "$ENV_FILE"
  else
    sed -i 's/^export JARVIS_AUTOSTART_COMFYUI=.*/export JARVIS_AUTOSTART_COMFYUI="1"/' "$ENV_FILE" 2>/dev/null || true
  fi
fi

log ""
log "Done. ComfyUI deps are in: $COMFY_VENV"
log "Jarvis will use: $COMFY_VENV/bin/python"
log "Restart Jarvis to auto-start ComfyUI for image generation."
