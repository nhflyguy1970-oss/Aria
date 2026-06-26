#!/usr/bin/env bash
# Stop Jarvis tray + server (when tray Quit hangs or you need a clean restart).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${JARVIS_PORT:-8765}"
HOST="${JARVIS_HOST:-127.0.0.1}"
CLIENT_HOST="${HOST}"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"

echo "Stopping Jarvis…"
jarvis_stop_stale

if jarvis_port_open; then
  echo "Port ${PORT} still open — forcing…"
  if command -v fuser &>/dev/null; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
  fi
  sleep 1
fi

if pgrep -f "${JARVIS_ROOT}/main.py tray" >/dev/null 2>&1; then
  pkill -9 -f "${JARVIS_ROOT}/main.py tray" 2>/dev/null || true
fi
if pgrep -f "${JARVIS_ROOT}/main.py serve" >/dev/null 2>&1; then
  pkill -9 -f "${JARVIS_ROOT}/main.py serve" 2>/dev/null || true
fi

if jarvis_port_open; then
  echo "Warning: something is still listening on port ${PORT}."
  ss -ltnp "sport = :${PORT}" 2>/dev/null || true
  exit 1
fi

echo "Jarvis stopped."
