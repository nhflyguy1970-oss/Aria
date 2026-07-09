#!/usr/bin/env bash
# Compatibility wrapper — prefer AI Platform workstation when installed.
set -euo pipefail
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"
PY="$(jarvis_python)"
if "$PY" -c "import aiplatform.workstation" 2>/dev/null; then
  exec "$PY" -m aiplatform.workstation.cli "$@"
fi
exec "$PY" -m jarvis.application.cli "$@"
