#!/usr/bin/env bash
# Install Jarvis system tools, Python packages, Piper TTS, and optional downloads.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$JARVIS_ROOT/venv"
PIPER_DIR="$JARVIS_ROOT/tools/piper"
PIPER_VOICES="$JARVIS_ROOT/data/models/piper"
WHISPER_MODEL="${JARVIS_WHISPER_MODEL:-base}"
SKIP_APT=0
SKIP_PIP=0
SKIP_PIPER=0
SKIP_WHISPER=0
SKIP_OLLAMA=0
SKIP_DESKTOP=0

usage() {
  cat <<'EOF'
Usage: ./scripts/install-dependencies.sh [options]

Installs everything Jarvis can use locally.

Options:
  --skip-apt       Skip apt system packages (espeak-ng, ffmpeg, etc.)
  --skip-pip       Skip Python venv + pip packages
  --skip-piper     Skip Piper TTS binary + voice model download
  --skip-whisper   Skip Whisper model pre-download
  --skip-ollama    Skip Ollama model pulls (large downloads)
  --skip-desktop   Skip desktop shortcut install
  --whisper MODEL  Whisper model size: tiny|base|small|medium (default: base)
  -h, --help       Show this help

After install, optional env vars (add to ~/.bashrc or jarvis.env):
  export JARVIS_PIPER_MODEL="$JARVIS_ROOT/data/models/piper/en_US-lessac-medium.onnx"
  export JARVIS_TTS_VOICE="en-us"
  export JARVIS_WHISPER_MODEL="base"
  export OLLAMA_KEEP_ALIVE="30m"
EOF
}

for arg in "$@"; do
  case "$arg" in
    --skip-apt) SKIP_APT=1 ;;
    --skip-pip) SKIP_PIP=1 ;;
    --skip-piper) SKIP_PIPER=1 ;;
    --skip-whisper) SKIP_WHISPER=1 ;;
    --skip-ollama) SKIP_OLLAMA=1 ;;
    --skip-desktop) SKIP_DESKTOP=1 ;;
    --whisper) shift; WHISPER_MODEL="${1:-base}" ;;
    -h|--help) usage; exit 0 ;;
    --whisper=*) WHISPER_MODEL="${arg#*=}" ;;
  esac
done

log() { echo "[jarvis install] $*"; }

install_apt() {
  if [[ "$SKIP_APT" == "1" ]]; then
    log "Skipping apt packages"
    return
  fi
  log "Installing system packages (sudo required)..."
  sudo apt-get update -qq
  # Ubuntu 24.04+ / Zorin 18 renamed libasound2 → libasound2t64
  local alsa_pkg="libasound2"
  local alsa_candidate
  alsa_candidate="$(apt-cache policy "$alsa_pkg" 2>/dev/null | awk '/Candidate:/ {print $2; exit}')"
  if [[ -z "$alsa_candidate" || "$alsa_candidate" == "(none)" ]]; then
    alsa_pkg="libasound2t64"
  fi
  sudo apt-get install -y \
    espeak-ng \
    ffmpeg \
    curl \
    wget \
    unzip \
    git \
    lsof \
    psmisc \
    "$alsa_pkg" \
    libportaudio2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    shared-mime-info \
    python3-venv \
    python3-dev \
    build-essential
}

setup_venv() {
  if [[ "$SKIP_PIP" == "1" ]]; then
    log "Skipping pip packages"
    return
  fi
  log "Setting up Python venv..."
  if [[ ! -d "$VENV" ]]; then
    python3 -m venv "$VENV"
  fi
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  pip install -U pip wheel setuptools
  pip install -r "$JARVIS_ROOT/requirements.txt"
  pip install -r "$JARVIS_ROOT/requirements-optional.txt"
}

install_piper() {
  if [[ "$SKIP_PIPER" == "1" ]]; then
    log "Skipping Piper TTS"
    return
  fi

  mkdir -p "$PIPER_DIR" "$PIPER_VOICES"
  PIPER_BIN="$PIPER_DIR/piper"
  VOICE_ONNX="$PIPER_VOICES/en_US-lessac-medium.onnx"
  VOICE_JSON="$PIPER_VOICES/en_US-lessac-medium.onnx.json"

  if [[ ! -x "$PIPER_BIN" ]] || [[ ! -f "$PIPER_DIR/libpiper_phonemize.so.1" ]]; then
    log "Downloading Piper TTS bundle..."
    TMP=$(mktemp -d)
    curl -fsSL -o "$TMP/piper.tar.gz" \
      "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
    tar -xzf "$TMP/piper.tar.gz" -C "$TMP"
    mkdir -p "$PIPER_DIR"
    rm -rf "${PIPER_DIR:?}/"*
    cp -a "$TMP/piper/." "$PIPER_DIR/"
    chmod +x "$PIPER_BIN" "$PIPER_DIR/piper_phonemize" 2>/dev/null || chmod +x "$PIPER_BIN"
    rm -rf "$TMP"
  else
    log "Piper bundle already present"
  fi

  if [[ ! -f "$VOICE_ONNX" ]]; then
    log "Downloading Piper voice (en_US-lessac-medium)..."
    curl -fsSL -o "$VOICE_ONNX" \
      "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    curl -fsSL -o "$VOICE_JSON" \
      "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
  else
    log "Piper voice already present"
  fi

  mkdir -p "$JARVIS_ROOT/data"
  ENV_FILE="$JARVIS_ROOT/data/jarvis.env"
  if [[ ! -f "$ENV_FILE" ]]; then
    cat > "$ENV_FILE" <<EOF
# Jarvis optional environment — source before launch:
#   source $ENV_FILE
export JARVIS_PIPER_MODEL="$VOICE_ONNX"
export PATH="$PIPER_DIR:\$PATH"
export JARVIS_TTS_VOICE="en-us"
export JARVIS_WHISPER_MODEL="$WHISPER_MODEL"
export OLLAMA_KEEP_ALIVE="30m"
export JARVIS_AUDIO_SINK="alsa_output.pci-0000_04_00.0.analog-stereo"
export JARVIS_AUDIO_SOURCE="alsa_input.pci-0000_04_00.0.analog-stereo"
export JARVIS_ALSA_CARD="Creative"
export JARVIS_ALSA_DEVICE="0"
export JARVIS_ALSA_PLAYBACK="plughw:CARD=Creative,DEV=0"
export JARVIS_ALSA_CAPTURE="plughw:CARD=Creative,DEV=0"
export JARVIS_AUTO_PLAY="1"
export JARVIS_SET_DEFAULT_SINK="1"
EOF
    log "Wrote $ENV_FILE"
  fi

  ln -sf "$PIPER_BIN" "$HOME/.local/bin/piper" 2>/dev/null || true
}

predownload_whisper() {
  if [[ "$SKIP_WHISPER" == "1" ]]; then
    log "Skipping Whisper model pre-download"
    return
  fi
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  log "Pre-downloading Whisper model: $WHISPER_MODEL"
  python - <<PY
import whisper
print("Downloading whisper model:", "${WHISPER_MODEL}")
whisper.load_model("${WHISPER_MODEL}")
print("Whisper model ready.")
PY
}

pull_ollama_models() {
  if [[ "$SKIP_OLLAMA" == "1" ]]; then
    log "Skipping Ollama model pulls"
    return
  fi
  if ! command -v ollama &>/dev/null; then
    log "WARNING: ollama not in PATH — skip model pulls"
    return
  fi
  log "Pulling standard Ollama models (this may take a while)..."
  "$JARVIS_ROOT/scripts/pull-models.sh"
  log "Pulling fast-preset extras..."
  ollama pull qwen2.5:7b || true
  ollama pull dolphin-mistral:latest || true
}

install_desktop() {
  if [[ "$SKIP_DESKTOP" == "1" ]]; then
    return
  fi
  "$JARVIS_ROOT/scripts/install-desktop-shortcuts.sh"
}

chmod +x "$JARVIS_ROOT/scripts/"*.sh 2>/dev/null || true

log "Jarvis dependency installer"
log "Root: $JARVIS_ROOT"
install_apt
setup_venv
install_piper
predownload_whisper
pull_ollama_models
install_desktop

log ""
log "Done. Summary:"
log "  Core pip:     requirements.txt"
log "  Optional pip: requirements-optional.txt"
log "  Env file:     data/jarvis.env (source before launch for Piper)"
log "  Full list:    DEPENDENCIES.md"
log ""
log "Launch: ./scripts/launch-jarvis.sh"
log "  (auto-starts Ollama, GUI, and optional ComfyUI — no manual steps)"
