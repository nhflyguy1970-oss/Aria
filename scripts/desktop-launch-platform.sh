#!/usr/bin/env bash
# Launch AI Platform — bootstrap workstation and open the runtime dashboard.
# GNOME/Zorin sessions use minimal PATH; .desktop Exec must be an absolute path.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${JARVIS_PORT:-8765}"
HOST="${JARVIS_HOST:-127.0.0.1}"
CLIENT_HOST="${HOST}"
if [[ "${HOST}" == "0.0.0.0" || "${HOST}" == "::" || "${HOST}" == "::0" ]]; then
  CLIENT_HOST="127.0.0.1"
fi
LOG_DIR="$JARVIS_ROOT/data/logs"
LOG_FILE="$LOG_DIR/desktop-launch.log"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"

mkdir -p "$LOG_DIR"
export PATH="${HOME}/.local/bin:${JARVIS_ROOT}:${PATH}"
jarvis_activate_env

jarvis_notify "AI Platform" "Starting…"
jarvis_log "=== AI Platform launch $(date -Iseconds) DISPLAY=${DISPLAY:-unset} ==="

if ! "${JARVIS_ROOT}/workstation" start >>"$LOG_FILE" 2>&1; then
  jarvis_notify "AI Platform" "Start failed — see data/logs/desktop-launch.log"
  exit 1
fi

if ! jarvis_server_responsive; then
  if ! jarvis_start_tray_background; then
    jarvis_start_serve_background
  fi
  if ! jarvis_wait_for_server "${SERVE_PID:-${TRAY_PID:-}}"; then
    if ! jarvis_server_responsive; then
      jarvis_notify "AI Platform" "API not ready — check logs"
      exit 1
    fi
  fi
fi

URL="http://${CLIENT_HOST}:${PORT}/?app=1#workstation"
jarvis_notify "AI Platform" "Opening dashboard…"
jarvis_log "Opening platform dashboard at $URL"
exec "$(jarvis_python)" -m jarvis.gui_launcher "$URL"
