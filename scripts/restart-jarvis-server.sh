#!/usr/bin/env bash
# Restart the canonical systemd-owned Aria HTTP server.
# Tray stays up and re-attaches. Does not spawn a second serve.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${JARVIS_PORT:-8765}"
HOST="${JARVIS_HOST:-127.0.0.1}"
CLIENT_HOST="${HOST}"
if [[ "${HOST}" == "0.0.0.0" || "${HOST}" == "::" || "${HOST}" == "::0" ]]; then
  CLIENT_HOST="127.0.0.1"
fi
URL="http://${CLIENT_HOST}:${PORT}"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"

echo "$(date -Iseconds) cli jarvis-ctl/restart-jarvis-server" >> "${JARVIS_ROOT}/data/logs/restart_audit.jsonl" 2>/dev/null || true

if jarvis_systemd_unit; then
  echo "Restarting systemd --user jarvis.service…"
  systemctl --user restart jarvis.service
  for _ in $(seq 1 45); do
    if jarvis_server_responsive; then
      echo "Jarvis server is back on port ${PORT}."
      exit 0
    fi
    sleep 1
  done
  echo "Timed out waiting for systemd-owned server."
  exit 1
fi

TRAY_PID="$(pgrep -f "${JARVIS_ROOT}/main.py tray" | head -1 || true)"
if [[ -n "${TRAY_PID}" ]]; then
  echo "No systemd unit — signaling tray (PID ${TRAY_PID}) to restart server…"
  kill -USR1 "${TRAY_PID}" 2>/dev/null || true
  for _ in $(seq 1 45); do
    if jarvis_server_responsive; then
      echo "Jarvis server is back on port ${PORT}."
      exit 0
    fi
    sleep 1
  done
  echo "Timed out waiting for server — try: ${JARVIS_ROOT}/scripts/stop-jarvis.sh && ${JARVIS_ROOT}/scripts/launch-jarvis.sh"
  exit 1
fi

echo "Neither systemd unit nor tray is running — start with: systemctl --user start jarvis.service"
exit 1
