#!/usr/bin/env bash
# ARIA tray entrypoint for the systemd --user aria-tray.service (login autostart).
# The tray attaches to jarvis.service; it never starts a second server.
# Secrets stay in data/jarvis.env / Owner Vault — never in the unit file.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export JARVIS_DATA_DIR="${JARVIS_DATA_DIR:-${JARVIS_ROOT}/data}"
export VIRTUAL_ENV="${VIRTUAL_ENV:-${JARVIS_ROOT}/venv}"
export JARVIS_NO_BROWSER=1

cd "$JARVIS_ROOT"
if [[ -f "${JARVIS_ROOT}/venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${JARVIS_ROOT}/venv/bin/activate"
fi
if [[ -f "${JARVIS_DATA_DIR}/jarvis.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${JARVIS_DATA_DIR}/jarvis.env"
  set +a
fi
export JARVIS_NO_BROWSER=1

PY="${JARVIS_ROOT}/venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
exec "$PY" "${JARVIS_ROOT}/main.py" tray
