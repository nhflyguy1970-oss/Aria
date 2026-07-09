#!/usr/bin/env bash
# Update Aria + optional AI-Platform from git and refresh Python deps.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLATFORM_ROOT="${AI_PLATFORM_ROOT:-$(dirname "$ROOT")/AI-Platform}"

log() { echo "[workstation update] $*"; }

if [[ -d "$ROOT/.git" ]]; then
  log "Pulling Aria..."
  git -C "$ROOT" pull --ff-only || log "WARN: git pull failed (local changes?)"
fi

if [[ ! -x "$ROOT/venv/bin/python" ]]; then
  log "venv missing — run ./scripts/install.sh first"
  exit 1
fi

# shellcheck disable=SC1091
source "$ROOT/venv/bin/activate"
pip install -U pip wheel
pip install -r "$ROOT/requirements.txt"
[[ -f "$ROOT/requirements-optional.txt" ]] && pip install -r "$ROOT/requirements-optional.txt" || true

if [[ -d "$PLATFORM_ROOT/.git" ]]; then
  log "Pulling AI-Platform..."
  git -C "$PLATFORM_ROOT" pull --ff-only || log "WARN: platform git pull failed"
fi

if [[ -d "$PLATFORM_ROOT" && -f "$PLATFORM_ROOT/pyproject.toml" ]]; then
  if command -v uv >/dev/null 2>&1; then
    (cd "$PLATFORM_ROOT" && uv sync --group dev) || log "WARN: uv sync failed"
  else
    pip install -e "$PLATFORM_ROOT" || log "WARN: platform pip install failed"
  fi
fi

log "Update complete."
if pgrep -f "main.py tray" >/dev/null 2>&1 || pgrep -f "main.py serve" >/dev/null 2>&1; then
  log "Restarting Aria server..."
  "$ROOT/scripts/restart-jarvis-server.sh" || "$ROOT/scripts/jarvis-ctl.sh stop && $ROOT/scripts/launch-jarvis.sh" || true
else
  log "Aria not running — start with: ./scripts/jarvis-ctl.sh start"
fi
