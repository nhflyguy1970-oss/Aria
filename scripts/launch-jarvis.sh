#!/usr/bin/env bash
# Launch ARIA from desktop shortcut: tray + Chrome app window.
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
jarvis_log "=== ${ARIA_NAME} launch $(date -Iseconds) ==="

if jarvis_server_responsive; then
  jarvis_notify "$ARIA_NAME" "Opening…"
  jarvis_open_gui_detached || jarvis_notify "$ARIA_NAME" "Could not open window — try again"
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
export JARVIS_GUI_MODE="${JARVIS_GUI_MODE:-app}"
export JARVIS_APP_WINDOW="${JARVIS_APP_WINDOW:-1}"
"$(jarvis_python)" "$JARVIS_ROOT/main.py" tray >>"$LOG_FILE" 2>&1 &
TRAY_PID=$!
jarvis_log "Tray PID: $TRAY_PID"

if ! jarvis_wait_for_server "$TRAY_PID"; then
  if jarvis_port_open; then
    jarvis_log "Health slow after start — opening window anyway"
    jarvis_run_gui_foreground
  fi
  jarvis_notify "$ARIA_NAME" "Failed to start — check data/logs/jarvis.log"
  jarvis_log "${ARIA_NAME} failed to become ready"
  exit 1
fi

jarvis_run_gui_foreground
