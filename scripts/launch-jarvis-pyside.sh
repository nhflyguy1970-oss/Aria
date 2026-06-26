#!/usr/bin/env bash
# Launch PySide/Fluent ARIA window (server + optional tray, then foreground shell).
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
export JARVIS_GUI_MODE="${JARVIS_GUI_MODE:-fluent}"
export JARVIS_APP_WINDOW="${JARVIS_APP_WINDOW:-0}"

if ! jarvis_server_responsive; then
  if ! jarvis_start_tray_background; then
    jarvis_start_serve_background
  fi
  jarvis_wait_for_server "${SERVE_PID:-${TRAY_PID:-}}" || {
    echo "ARIA server did not start — see $LOG_FILE" >&2
    exit 1
  }
fi

exec "$(jarvis_python)" -m jarvis.pyside_shell "$URL"
