#!/usr/bin/env bash
# Control ARIA without the tray menu (Linux tray icons often ignore right-click).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${JARVIS_PORT:-8765}"
HOST="${JARVIS_HOST:-127.0.0.1}"
CLIENT_HOST="${HOST}"
if [[ "${HOST}" == "0.0.0.0" || "${HOST}" == "::" || "${HOST}" == "::0" ]]; then
  CLIENT_HOST="127.0.0.1"
fi
URL="http://${CLIENT_HOST}:${PORT}"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

Lifecycle:
  install     Fresh-machine install (--minimal|--developer|--full|--gpu|--headless)
  configure   Create jarvis.env and initialize platform paths
  start       Start Aria desktop (tray + server + window)
  stop        Stop tray + server
  restart-tray Restart only the tray process (picks up new code)
  restart     Restart Aria server (or: workstation restart <component>)
  update      git pull + pip sync + restart if running
  backup      Backup jarvis data and platform state
  restore     Restore from backup archive (pass path as arg)
  verify      Validate install from inventory
  inventory   Show installed/running/healthy components
  hardware    Hardware detection and workload recommendations
  optimize    Apply measured tuning to jarvis.env
  doctor      Workstation diagnose + AI-Platform doctor
  status      Server status (--full for workstation summary)

Desktop:
  open        Open or focus the Jarvis window
  reload      Reload the Jarvis window (UI only)
  audit       Run 14-phase system audit
  workstation Registry/lifecycle (status/up/down/diagnose/recover)

Examples:
  ./scripts/jarvis-ctl.sh install
  ./scripts/jarvis-ctl.sh verify && ./scripts/jarvis-ctl.sh start
  ./scripts/jarvis-ctl.sh status --full
EOF
}

cmd="${1:-}"
shift || true

case "$cmd" in
  install|configure|start|stop|update|backup|verify|doctor|inventory|optimize|hardware)
    exec "$JARVIS_ROOT/scripts/workstation.sh" "$cmd" "$@"
    ;;
  restore)
    exec "$JARVIS_ROOT/scripts/workstation.sh" restore "$@"
    ;;
  open)
    jarvis_notify "$(jarvis_app_name)" "Opening…"
    jarvis_open_gui_detached || {
      echo "Could not open window — is ARIA running? Try: $0 status" >&2
      exit 1
    }
    ;;
  reload)
    jarvis_notify "$(jarvis_app_name)" "Reloading UI…"
    if jarvis_server_responsive; then
      busy="$(curl -sf --max-time 2 "${URL}/api/media/status" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('1' if d.get('busy') or d.get('queue_depth',0)>1 else '0')" 2>/dev/null || echo 0)"
      if [[ "${busy}" == "1" ]]; then
        jarvis_notify "$(jarvis_app_name)" "Image job running — reload skipped (use sidebar Reload UI after job finishes)"
        exit 0
      fi
      title="$("$(jarvis_python)" -c 'from jarvis.native_window import _window_title; print(_window_title())' 2>/dev/null || echo ARIA)"
      if command -v xdotool >/dev/null 2>&1; then
        wid="$(xdotool search --name "${title}" 2>/dev/null | head -1 || true)"
        if [[ -n "${wid}" ]]; then
          xdotool windowactivate --sync "${wid}" key ctrl+shift+r 2>/dev/null || true
          exit 0
        fi
      fi
    fi
    jarvis_notify "$(jarvis_app_name)" "Use Reload UI in the sidebar (Ctrl+Shift+R) — window was not killed"
    exit 0
    ;;
  restart)
    exec "$JARVIS_ROOT/scripts/restart-jarvis-server.sh"
    ;;
  restart-tray)
    # Tray only (scheduler, mission worker, wake word). The systemd server and window stay up.
    jarvis_activate_env
    tray_pattern="${JARVIS_ROOT}/main.py tray"
    if pgrep -f "$tray_pattern" >/dev/null 2>&1; then
      pkill -TERM -f "$tray_pattern" || true
      for _ in $(seq 1 60); do
        pgrep -f "$tray_pattern" >/dev/null 2>&1 || break
        sleep 1
      done
      if pgrep -f "$tray_pattern" >/dev/null 2>&1; then
        echo "Tray did not stop within 60 s; not starting a second tray." >&2
        exit 1
      fi
    fi
    if ! jarvis_tray_available; then
      echo "Tray could not start (no display or pystray)." >&2
      exit 1
    fi
    export JARVIS_NO_BROWSER=1
    # Own user scope, so closing the terminal that ran this command cannot take the tray with it.
    systemd-run --user --scope --quiet --collect --unit="aria-tray-$(date +%s)" \
      setsid "$(jarvis_python)" "$JARVIS_ROOT/main.py" tray >>"$(jarvis_stdio_log tray)" 2>&1 < /dev/null &
    sleep 2
    echo "Tray restarted (PID $(pgrep -f "$tray_pattern" | head -1)); stdout/stderr -> data/logs/tray-stdio.log"
    ;;
  stop)
    exec "$JARVIS_ROOT/scripts/stop-jarvis.sh"
    ;;
  status)
    if [[ "${1:-}" == "--full" ]]; then
      echo "=== Aria server ==="
      if jarvis_server_responsive; then
        echo "  up ($URL)"
      else
        echo "  down"
      fi
      echo ""
      echo "=== Workstation ==="
      "$(jarvis_python)" -m jarvis.workstation.cli diagnose || true
      exit 0
    fi
    if jarvis_server_responsive; then
      echo "$(jarvis_app_name) server: up (${URL})"
      exit 0
    fi
    if jarvis_port_open; then
      echo "$(jarvis_app_name) server: port open but not responding (${URL})"
      exit 1
    fi
    echo "$(jarvis_app_name) server: down"
    exit 1
    ;;
  audit)
    exec "${JARVIS_ROOT}/scripts/audit-system.sh" "$@"
    ;;
  workstation)
    exec "${JARVIS_ROOT}/scripts/workstation.sh" "$@"
    ;;
  -h|--help|help|"")
    usage
    [[ -n "$cmd" ]] || exit 0
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage >&2
    exit 2
    ;;
esac
