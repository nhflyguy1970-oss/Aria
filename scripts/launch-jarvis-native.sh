#!/usr/bin/env bash
# Legacy pywebview window (less stable for coding). Prefer the main ARIA shortcut.
export JARVIS_GUI_MODE=native
export JARVIS_APP_WINDOW=0
exec "$(cd "$(dirname "$0")" && pwd)/launch-jarvis.sh" "$@"
