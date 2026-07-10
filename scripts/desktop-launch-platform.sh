#!/usr/bin/env bash
# Launch AI Platform — bootstrap workstation and open native Mission Control desktop.
# GNOME/Zorin sessions use minimal PATH; .desktop Exec must be an absolute path.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MC_PORT="${MISSION_CONTROL_PORT:-8780}"
MC_HOST="${MISSION_CONTROL_HOST:-127.0.0.1}"
CLIENT_HOST="${MC_HOST}"
if [[ "${MC_HOST}" == "0.0.0.0" || "${MC_HOST}" == "::" || "${MC_HOST}" == "::0" ]]; then
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

if ! "${JARVIS_ROOT}/workstation" start --console --no-app >>"$LOG_FILE" 2>&1; then
  jarvis_notify "AI Platform" "Start failed — see data/logs/desktop-launch.log"
  exit 1
fi

MC_API="http://${CLIENT_HOST}:${MC_PORT}/api/health"
jarvis_log "Ensuring Mission Control API at ${MC_API}"

deadline=$((SECONDS + 20))
while (( SECONDS < deadline )); do
  if curl -sf --max-time 2 "${MC_API}" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -sf --max-time 2 "${MC_API}" >/dev/null 2>&1; then
  jarvis_notify "AI Platform" "Platform API not ready — check logs"
  jarvis_log "Mission Control API failed health check at ${MC_API}"
  exit 1
fi

jarvis_notify "AI Platform" "Opening Mission Control…"
jarvis_log "Launching native Mission Control desktop (PySide6)"
"$(jarvis_python)" -m aiplatform.mission_control.desktop &
DESKTOP_PID=$!

deadline=$((SECONDS + 30))
visible=0
while (( SECONDS < deadline )); do
  if "$(jarvis_python)" -c "from aiplatform.mission_control.desktop.health import desktop_window_visible; import sys; sys.exit(0 if desktop_window_visible() else 1)"; then
    visible=1
    break
  fi
  sleep 0.5
done

if (( visible != 1 )); then
  jarvis_notify "AI Platform" "Mission Control window did not appear — check logs"
  jarvis_log "Desktop window visibility check failed (pid=${DESKTOP_PID})"
  exit 1
fi

jarvis_notify "AI Platform" "Mission Control ready"
jarvis_log "Mission Control desktop visible (pid=${DESKTOP_PID})"
wait "${DESKTOP_PID}"
