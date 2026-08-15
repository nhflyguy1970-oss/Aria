#!/usr/bin/env bash
# Launch Aria Living Workspace on Runtime R1 (Electron-class).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export JARVIS_GUI_MODE=electron
export JARVIS_NO_BROWSER=1
if [[ ! -x "$ROOT/scripts/electron-shell/node_modules/electron/dist/electron" ]]; then
  echo "Installing Electron R1 host…"
  "$ROOT/scripts/install-electron-shell.sh"
fi
exec "$ROOT/scripts/launch-jarvis.sh"
