#!/usr/bin/env bash
# Chrome app window — same as the main ARIA desktop shortcut.
export JARVIS_GUI_MODE=app
export JARVIS_APP_WINDOW=1
exec "$(cd "$(dirname "$0")" && pwd)/launch-jarvis.sh" "$@"
