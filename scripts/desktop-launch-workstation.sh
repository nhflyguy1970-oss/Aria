#!/usr/bin/env bash
# Launch AI Workstation from .desktop entries.
# GNOME/Zorin desktop sessions use a minimal PATH (/usr/bin:/bin) that excludes
# ~/.local/bin, so .desktop Exec lines must call this script by absolute path.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$JARVIS_ROOT/data/logs"
LOG_FILE="$LOG_DIR/desktop-launch.log"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"

mkdir -p "$LOG_DIR"

# Desktop sessions omit ~/.local/bin; children (docker, ollama helpers) may need it.
export PATH="${HOME}/.local/bin:${JARVIS_ROOT}:${PATH}"

jarvis_activate_env

cmd="${1:-start}"
shift || true

case "$cmd" in
  start)
    ws_args=(start --desktop)
    if (($#)); then ws_args+=("$@"); fi
    ;;
  stop|repair|doctor|acceptance|report|status|verify|configure|install|update|recover|backup|restore)
    ws_args=("$cmd" "$@")
    ;;
  *)
    jarvis_notify "AI Workstation" "Unknown command: $cmd"
    jarvis_log "desktop-launch: unknown command: $cmd $*"
    exit 1
    ;;
esac

jarvis_log "=== desktop launch $(date -Iseconds) ${ws_args[*]} DISPLAY=${DISPLAY:-unset} ==="

if ! "${JARVIS_ROOT}/workstation" "${ws_args[@]}" >>"$LOG_FILE" 2>&1; then
  rc=$?
  jarvis_notify "AI Workstation" "Failed — see data/logs/desktop-launch.log"
  jarvis_log "workstation exited $rc"
  exit "$rc"
fi
