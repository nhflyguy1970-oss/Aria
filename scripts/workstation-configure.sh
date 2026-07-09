#!/usr/bin/env bash
# Interactive-first configuration for a fresh install.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/data/jarvis.env"
EXAMPLE="$ROOT/jarvis.env.example"
PLATFORM_ROOT="${AI_PLATFORM_ROOT:-$(dirname "$ROOT")/AI-Platform}"

log() { echo "[workstation configure] $*"; }

mkdir -p "$ROOT/data"

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$EXAMPLE" ]]; then
    cp "$EXAMPLE" "$ENV_FILE"
    log "Created $ENV_FILE from example"
  else
    touch "$ENV_FILE"
    log "Created empty $ENV_FILE"
  fi
else
  log "Using existing $ENV_FILE"
fi

upsert() {
  local name="$1"
  local value="$2"
  if grep -qE "^export ${name}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^export ${name}=.*|export ${name}=\"${value}\"|" "$ENV_FILE"
  elif grep -qE "^# export ${name}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^# export ${name}=.*|export ${name}=\"${value}\"|" "$ENV_FILE"
  else
    printf '\nexport %s="%s"\n' "$name" "$value" >>"$ENV_FILE"
  fi
}

# Detect AI_ROOT default
if [[ -d "$PLATFORM_ROOT" ]]; then
  default_ai_root="$(dirname "$PLATFORM_ROOT")"
  if ! grep -qE '^export AI_ROOT=' "$ENV_FILE" 2>/dev/null; then
    upsert AI_ROOT "$default_ai_root"
    log "Set AI_ROOT=$default_ai_root"
  fi
fi

if [[ -d "$PLATFORM_ROOT" && -f "$PLATFORM_ROOT/pyproject.toml" ]]; then
  export AI_ROOT="${AI_ROOT:-$(dirname "$PLATFORM_ROOT")}"
  COMPOSE="${AI_ROOT}/compose/compose.yaml"
  if [[ ! -f "$COMPOSE" && -x "$ROOT/venv/bin/python" ]]; then
    log "Initializing AI-Platform (compose, env)..."
    "$ROOT/venv/bin/python" -m aiplatform.cli init || log "WARN: aiplatform init failed"
  fi
fi

log ""
log "Configuration complete."
log "  Edit:    $ENV_FILE"
log "  Verify:  ./scripts/jarvis-ctl.sh verify"
log "  Docs:    docs/CONFIG.md"
