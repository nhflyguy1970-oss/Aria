#!/usr/bin/env bash
# Launch ARIA (uncensored) from desktop shortcut.
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
ARIA_UNC="${ARIA_NAME} (Uncensored)"
jarvis_log "=== ${ARIA_UNC} launch $(date -Iseconds) ==="

if [[ -f "$JARVIS_ROOT/data/uncensored_auth.json" && -z "${JARVIS_UNCENSORED_PASSWORD:-}" ]]; then
  jarvis_notify "$ARIA_NAME" "Add JARVIS_UNCENSORED_PASSWORD to data/jarvis.env for uncensored launch"
fi

if jarvis_server_responsive; then
  jarvis_notify "$ARIA_UNC" "Opening…"
  jarvis_open_gui_detached || jarvis_notify "$ARIA_NAME" "Could not open window — try again"
  exit 0
fi

if jarvis_port_open; then
  jarvis_log "Port ${PORT} open but API not responding — restarting stuck server"
  jarvis_notify "$ARIA_UNC" "Restarting (server was stuck)…"
  jarvis_stop_stale
fi

jarvis_notify "$ARIA_UNC" "Starting…"
jarvis_stop_stale

export JARVIS_UNCENSORED=1
export JARVIS_GUI_MODE="${JARVIS_GUI_MODE:-app}"
export JARVIS_APP_WINDOW="${JARVIS_APP_WINDOW:-1}"
"$(jarvis_python)" "$JARVIS_ROOT/main.py" tray-uncensored >>"$LOG_FILE" 2>&1 &
TRAY_PID=$!
jarvis_log "Tray PID: $TRAY_PID"

if ! jarvis_wait_for_server "$TRAY_PID"; then
  if jarvis_port_open; then
    jarvis_log "Health slow after start — opening window anyway"
    jarvis_run_gui_foreground
  fi
  jarvis_notify "$ARIA_NAME" "Failed to start — check data/logs/jarvis.log"
  exit 1
fi

jarvis_run_gui_foreground
