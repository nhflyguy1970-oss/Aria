#!/usr/bin/env bash
# Fresh-machine install orchestrator for the Aria AI Workstation.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLATFORM_ROOT="${AI_PLATFORM_ROOT:-$(dirname "$ROOT")/AI-Platform}"
PROFILE="developer"
SKIP_DEPS=0
SKIP_PLATFORM=0
HEADLESS=0

usage() {
  cat <<'EOF'
Usage: ./scripts/install.sh [profile] [options]

Profiles (install exactly what each profile needs):
  --minimal      Aria core only (no large downloads, no platform)
  --developer    Dev tools + platform init (default)
  --full         Docker, dev tools, models, platform
  --gpu          Developer + CUDA/ROCm PyTorch scripts
  --headless     API server stack (no desktop shortcuts)

Options:
  --skip-deps       Skip install-dependencies.sh (pip/venv only)
  --skip-platform   Skip AI-Platform uv sync / init
  -h, --help        Show this help

Environment:
  AI_PLATFORM_ROOT  Path to AI-Platform (default: ../AI-Platform)
  AI_ROOT           Platform data root (default: parent of AI-Platform)
EOF
}

args=()
for arg in "$@"; do
  case "$arg" in
    --minimal) PROFILE="minimal" ;;
    --developer) PROFILE="developer" ;;
    --full) PROFILE="full" ;;
    --gpu) PROFILE="gpu" ;;
    --headless) PROFILE="headless"; HEADLESS=1 ;;
    --skip-deps) SKIP_DEPS=1 ;;
    --skip-platform) SKIP_PLATFORM=1 ;;
    -h|--help) usage; exit 0 ;;
    *) args+=("$arg") ;;
  esac
done

log() { echo "[workstation install] $*"; }
warn() { echo "[workstation install] WARN: $*" >&2; }
die() { echo "[workstation install] ERROR: $*" >&2; exit 1; }

log "Aria workstation install — profile: $PROFILE"

if ! command -v python3 >/dev/null 2>&1; then
  die "python3 is required. Fix: sudo apt install python3 python3-venv python3-pip"
fi

if ! command -v git >/dev/null 2>&1; then
  die "git is required. Fix: sudo apt install git"
fi

if [[ ! -d "$ROOT/venv" ]]; then
  log "Creating Python venv..."
  python3 -m venv "$ROOT/venv" || die "venv creation failed"
fi

# shellcheck disable=SC1091
source "$ROOT/venv/bin/activate"
python -m pip install -U pip wheel setuptools

log "Installing Python requirements..."
pip install -r "$ROOT/requirements.txt" || die "pip install requirements.txt failed"
if [[ -f "$ROOT/requirements-optional.txt" ]]; then
  pip install -r "$ROOT/requirements-optional.txt" || warn "optional requirements partially failed"
fi

# Profile-specific dependency flags
deps_args=()
case "$PROFILE" in
  minimal) deps_args=(--skip-ollama --skip-whisper --skip-desktop) ;;
  developer) deps_args=(--skip-ollama) ;;
  headless) deps_args=(--skip-desktop) ;;
  full|gpu) deps_args=() ;;
esac

if [[ "$SKIP_DEPS" == "0" ]]; then
  log "Running install-dependencies.sh ${deps_args[*]}..."
  bash "$ROOT/scripts/install-dependencies.sh" "${deps_args[@]}" "${args[@]}" \
    || die "install-dependencies.sh failed — see output above"
else
  log "Skipping install-dependencies.sh"
fi

run_script() {
  local script="$1"
  if [[ -f "$ROOT/scripts/$script" ]]; then
    log "Running $script..."
    bash "$ROOT/scripts/$script" || warn "$script failed (continuing)"
  else
    warn "Script missing: $script"
  fi
}

case "$PROFILE" in
  developer)
    run_script install-dev-tools.sh
    run_script install-lsp-servers.sh
    ;;
  full)
    run_script install-docker.sh
    run_script install-dev-tools.sh
    run_script install-lsp-servers.sh
    ;;
  gpu)
    run_script install-dev-tools.sh
    if command -v nvidia-smi >/dev/null 2>&1; then
      run_script install-cuda-pytorch.sh
    elif command -v rocminfo >/dev/null 2>&1; then
      run_script install-rocm-pytorch.sh
    else
      warn "No GPU detected — skipping CUDA/ROCm PyTorch (install drivers first, re-run --gpu)"
    fi
    ;;
esac

mkdir -p "$ROOT/data"
if [[ ! -f "$ROOT/data/jarvis.env" ]]; then
  if [[ -f "$ROOT/jarvis.env.example" ]]; then
    cp "$ROOT/jarvis.env.example" "$ROOT/data/jarvis.env"
    log "Created data/jarvis.env from jarvis.env.example"
  else
    warn "jarvis.env.example missing — run: ./workstation configure"
  fi
fi

init_platform=1
[[ "$PROFILE" == "minimal" ]] && init_platform=0
[[ "$SKIP_PLATFORM" == "1" ]] && init_platform=0

if [[ "$init_platform" == "1" && -d "$PLATFORM_ROOT" && -f "$PLATFORM_ROOT/pyproject.toml" ]]; then
  log "AI-Platform found at $PLATFORM_ROOT"
  export AI_ROOT="${AI_ROOT:-$(dirname "$PLATFORM_ROOT")}"
  if command -v uv >/dev/null 2>&1; then
    (cd "$PLATFORM_ROOT" && uv sync --group dev) || warn "uv sync failed — install uv: https://docs.astral.sh/uv/"
  else
    pip install -e "$PLATFORM_ROOT" || warn "editable AI-Platform install failed — install uv for best results"
  fi
  COMPOSE_FILE="${AI_ROOT}/compose/compose.yaml"
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    log "Initializing AI-Platform infrastructure..."
    python -m aiplatform.cli init || warn "aiplatform init failed — run: ./workstation configure"
  fi
else
  log "AI-Platform init skipped (profile=$PROFILE or repo missing)"
fi

if [[ "$HEADLESS" == "1" || "$PROFILE" == "headless" ]]; then
  log "Headless profile — skip desktop shortcuts"
else
  [[ -f "$ROOT/scripts/install-global-commands.sh" ]] && run_script install-global-commands.sh
  [[ -f "$ROOT/scripts/install-desktop-shortcuts.sh" ]] && run_script install-desktop-shortcuts.sh
fi

log ""
log "Install complete (profile: $PROFILE)."
log "  Global commands: workstation, aria, aiplatform (in ~/.local/bin)"
log "  Configure: workstation configure"
log "  Verify:    workstation verify"
log "  Inventory: workstation inventory"
log "  Start:     workstation start"
