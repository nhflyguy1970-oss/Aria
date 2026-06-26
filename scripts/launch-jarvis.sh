#!/usr/bin/env bash
# Launch ARIA from desktop shortcut: background server + tray + PySide/Fluent window.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${JARVIS_PORT:-8765}"
HOST="${JARVIS_HOST:-127.0.0.1}"
CLIENT_HOST="${HOST}"
if [[ "${HOST}" == "0.0.0.0" || "${HOST}" == "::" || "${HOST}" == "::0" ]]; then
  CLIENT_HOST="127.0.0.1"
fi
URL="http://${CLIENT_HOST}:${PORT}"
LOG_DIR="$JARVIS_ROOT/data/logs"
LOG_FILE="$LOG_DIR/jarvis.log"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"

mkdir -p "$LOG_DIR"
jarvis_activate_env
ARIA_NAME="$(jarvis_app_name)"
jarvis_log "=== ${ARIA_NAME} launch $(date -Iseconds) DISPLAY=${DISPLAY:-unset} GUI_MODE=${JARVIS_GUI_MODE:-fluent} ==="

# Prevent double-click races: second click focuses the window instead of restarting everything.
LAUNCH_LOCK_FILE="$JARVIS_ROOT/data/launch.lock"
exec 9>"$LAUNCH_LOCK_FILE"
if ! flock -n 9; then
  jarvis_log "Launch already in progress — focusing GUI"
  jarvis_run_gui_foreground
  exit 0
fi

if jarvis_server_responsive; then
  jarvis_notify "$ARIA_NAME" "Opening…"
  jarvis_run_gui_foreground
  exit 0
fi

if jarvis_port_open; then
  jarvis_log "Port ${PORT} open but API not responding — restarting stuck server"
  jarvis_notify "$ARIA_NAME" "Restarting (server was stuck)…"
  jarvis_stop_stale
fi

jarvis_notify "$ARIA_NAME" "Starting…"
jarvis_stop_stale
unset JARVIS_UNCENSORED

# Tray daemon owns the API server — do not also start `main.py serve` (causes port fights + watchdog loop).
if ! jarvis_start_tray_background; then
  jarvis_log "Tray unavailable — starting headless serve"
  jarvis_start_serve_background
fi

if ! jarvis_wait_for_server "${SERVE_PID:-${TRAY_PID:-}}"; then
  if jarvis_server_responsive; then
    jarvis_log "Health slow after start — opening window anyway"
    jarvis_run_gui_foreground
  fi
  jarvis_notify "$ARIA_NAME" "Failed to start — check data/logs/jarvis.log"
  jarvis_log "${ARIA_NAME} failed to become ready"
  exit 1
fi

jarvis_run_gui_foreground
