#!/usr/bin/env bash
# Aria workstation control plane — registry, lifecycle, diagnostics.
set -euo pipefail
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"
exec "$(jarvis_python)" -m jarvis.workstation.cli "$@"
