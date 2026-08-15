#!/usr/bin/env bash
# Canonical production HTTP server entrypoint for systemd --user.
# Secrets stay in data/jarvis.env / Owner Vault — never in the unit file.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export JARVIS_DATA_DIR="${JARVIS_DATA_DIR:-${JARVIS_ROOT}/data}"
export VIRTUAL_ENV="${VIRTUAL_ENV:-${JARVIS_ROOT}/venv}"
export JARVIS_LAUNCH_OWNER=systemd
export JARVIS_NO_BROWSER=1
unset JARVIS_SERVICES_MANAGED

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

# Re-assert ownership after env file (must not inherit tray-managed mode).
export JARVIS_DATA_DIR="${JARVIS_DATA_DIR:-${JARVIS_ROOT}/data}"
export VIRTUAL_ENV="${VIRTUAL_ENV:-${JARVIS_ROOT}/venv}"
export JARVIS_LAUNCH_OWNER=systemd
export JARVIS_NO_BROWSER=1
unset JARVIS_SERVICES_MANAGED

PY="${JARVIS_ROOT}/venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
exec "$PY" "${JARVIS_ROOT}/main.py" serve
