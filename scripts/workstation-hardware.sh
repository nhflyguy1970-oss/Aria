#!/usr/bin/env bash
# Hardware report wrapper — delegates to Python inventory/hardware module.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/venv/bin/python"
[[ -x "$PY" ]] || PY=python3
exec "$PY" -m jarvis.workstation.cli hardware "$@"
