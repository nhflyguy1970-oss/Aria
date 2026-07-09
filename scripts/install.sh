#!/usr/bin/env bash
# Fresh-machine install orchestrator for the Aria AI Workstation.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLATFORM_ROOT="${AI_PLATFORM_ROOT:-$(dirname "$ROOT")/AI-Platform}"
SKIP_DEPS=0
SKIP_PLATFORM=0

usage() {
  cat <<'EOF'
Usage: ./scripts/install.sh [options] [-- install-dependencies.sh flags]

Orchestrates a fresh Linux install:
  1. Python venv + pip requirements
  2. System tools via install-dependencies.sh
  3. data/jarvis.env from example (if missing)
  4. AI-Platform init (when sibling repo exists)

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
    --skip-deps) SKIP_DEPS=1 ;;
    --skip-platform) SKIP_PLATFORM=1 ;;
    -h|--help) usage; exit 0 ;;
    *) args+=("$arg") ;;
  esac
done

log() { echo "[workstation install] $*"; }
warn() { echo "[workstation install] WARN: $*" >&2; }

log "Aria workstation install — $ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install with: sudo apt install python3 python3-venv python3-pip" >&2
  exit 1
fi

if [[ ! -d "$ROOT/venv" ]]; then
  log "Creating Python venv..."
  python3 -m venv "$ROOT/venv"
fi

# shellcheck disable=SC1091
source "$ROOT/venv/bin/activate"
python -m pip install -U pip wheel setuptools

log "Installing Python requirements..."
pip install -r "$ROOT/requirements.txt"
if [[ -f "$ROOT/requirements-optional.txt" ]]; then
  pip install -r "$ROOT/requirements-optional.txt" || warn "optional requirements partially failed"
fi

if [[ "$SKIP_DEPS" == "0" ]]; then
  log "Running install-dependencies.sh..."
  bash "$ROOT/scripts/install-dependencies.sh" "${args[@]}"
else
  log "Skipping install-dependencies.sh"
fi

mkdir -p "$ROOT/data"
if [[ ! -f "$ROOT/data/jarvis.env" ]]; then
  if [[ -f "$ROOT/jarvis.env.example" ]]; then
    cp "$ROOT/jarvis.env.example" "$ROOT/data/jarvis.env"
    log "Created data/jarvis.env from jarvis.env.example"
  else
    warn "jarvis.env.example missing — create data/jarvis.env manually"
  fi
fi

if [[ "$SKIP_PLATFORM" == "0" && -d "$PLATFORM_ROOT" && -f "$PLATFORM_ROOT/pyproject.toml" ]]; then
  log "AI-Platform found at $PLATFORM_ROOT"
  export AI_ROOT="${AI_ROOT:-$(dirname "$PLATFORM_ROOT")}"
  if command -v uv >/dev/null 2>&1; then
    (cd "$PLATFORM_ROOT" && uv sync --group dev) || warn "uv sync failed"
  else
    pip install -e "$PLATFORM_ROOT" || warn "editable AI-Platform install failed (install uv for best results)"
  fi
  COMPOSE_FILE="${AI_ROOT}/compose/compose.yaml"
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    log "Initializing AI-Platform infrastructure (compose, env)..."
    python -m aiplatform.cli init || warn "aiplatform init failed — run manually after setting AI_ROOT"
  else
    log "Platform compose already present at $COMPOSE_FILE"
  fi
else
  log "AI-Platform not found at $PLATFORM_ROOT (optional — skip with --skip-platform)"
fi

log ""
log "Install complete."
log "  Verify:  ./scripts/jarvis-ctl.sh verify"
log "  Start:   ./scripts/jarvis-ctl.sh start"
log "  Status:  ./scripts/jarvis-ctl.sh status --full"
