#!/usr/bin/env bash
# Shared helpers for ARIA desktop launchers.

jarvis_app_name() {
  echo "${JARVIS_ASSISTANT_NAME:-ARIA}"
}

jarvis_notify() {
  local title="$1"
  local body="${2:-}"
  local app
  app="$(jarvis_app_name)"
  local icon="${JARVIS_ROOT}/assets/jarvis-tray.png"
  [[ -f "$icon" ]] || icon="${JARVIS_ROOT}/assets/jarvis-icon.svg"
  if command -v notify-send &>/dev/null; then
    notify-send -a "$app" -i "$icon" "$title" "$body" 2>/dev/null || \
      notify-send -a "$app" "$title" "$body" 2>/dev/null || true
  fi
}

jarvis_log() {
  echo "$@" >>"$LOG_FILE"
}

jarvis_python() {
  if [[ -x "${JARVIS_ROOT}/venv/bin/python" ]]; then
    echo "${JARVIS_ROOT}/venv/bin/python"
  else
    echo python3
  fi
}

jarvis_resolve_display() {
  if [[ -n "${DISPLAY:-}" ]]; then
  if command -v xdpyinfo &>/dev/null && xdpyinfo -display "$DISPLAY" &>/dev/null; then
      return 0
    fi
  fi
  local sid dval
  if command -v loginctl &>/dev/null; then
    while read -r sid _; do
      [[ -n "$sid" ]] || continue
      dval="$(loginctl show-session "$sid" -p Display --value 2>/dev/null || true)"
      if [[ -n "$dval" ]]; then
        if command -v xdpyinfo &>/dev/null; then
          xdpyinfo -display "$dval" &>/dev/null && export DISPLAY="$dval" && return 0
        else
          export DISPLAY="$dval"
          return 0
        fi
      fi
    done < <(loginctl list-sessions --no-legend 2>/dev/null || true)
  fi
  local sock dval
  for sock in /tmp/.X11-unix/X*; do
    [[ -S "$sock" ]] || continue
    dval=":${sock##*/X}"
    if command -v xdpyinfo &>/dev/null; then
      xdpyinfo -display "$dval" &>/dev/null && export DISPLAY="$dval" && return 0
    else
      export DISPLAY="$dval"
      return 0
    fi
  done
  export DISPLAY="${DISPLAY:-:0}"
}

jarvis_curl_ok() {
  local path="$1"
  curl -sf --max-time 2 --connect-timeout 1 "${URL}${path}" >/dev/null 2>&1
}

jarvis_server_responsive() {
  jarvis_curl_ok "/api/live" || jarvis_curl_ok "/api/health"
}

jarvis_port_open() {
  local check_host="${CLIENT_HOST:-${HOST:-127.0.0.1}}"
  if [[ "${check_host}" == "0.0.0.0" || "${check_host}" == "::" ]]; then
    check_host="127.0.0.1"
  fi
  if command -v ss &>/dev/null; then
    ss -ltn "sport = :${PORT}" 2>/dev/null | grep -q ":${PORT}"
    return
  fi
  (echo >/dev/tcp/"${check_host}"/"${PORT}") >/dev/null 2>&1
}

jarvis_tray_available() {
  DISPLAY="${DISPLAY:-:0}" "$(jarvis_python)" -c "
import os
os.environ.setdefault('DISPLAY', '${DISPLAY:-:0}')
try:
    from Xlib import display
    display.Display().close()
    from pystray import Icon  # noqa: F401
    raise SystemExit(0)
except Exception:
    raise SystemExit(1)
" 2>/dev/null
}

jarvis_start_tray_background() {
  if [[ "${JARVIS_TRAY:-1}" == "0" ]]; then
    jarvis_log "Tray disabled (JARVIS_TRAY=0)"
    return 1
  fi
  if ! jarvis_tray_available; then
    jarvis_log "Tray unavailable (DISPLAY/pystray) — continuing without tray icon"
    return 1
  fi
  export JARVIS_NO_BROWSER=1
  "$(jarvis_python)" "$JARVIS_ROOT/main.py" tray >>"$LOG_FILE" 2>&1 &
  TRAY_PID=$!
  jarvis_log "Tray PID: $TRAY_PID"
  return 0
}

jarvis_start_serve_background() {
  export JARVIS_NO_BROWSER=1
  export JARVIS_SERVICES_MANAGED=1
  "$(jarvis_python)" "$JARVIS_ROOT/main.py" serve >>"$LOG_FILE" 2>&1 &
  SERVE_PID=$!
  jarvis_log "Serve PID: $SERVE_PID"
}

jarvis_open_gui_detached() {
  export JARVIS_GUI_MODE="${JARVIS_GUI_MODE:-fluent}"
  export JARVIS_APP_WINDOW="${JARVIS_APP_WINDOW:-0}"
  export JARVIS_SHELL_FORCE_NEW="${JARVIS_SHELL_FORCE_NEW:-0}"
  "$(jarvis_python)" -m jarvis.gui_launcher "$URL"
}

jarvis_run_gui_foreground() {
  export JARVIS_NO_BROWSER=1
  export JARVIS_GUI_MODE="${JARVIS_GUI_MODE:-fluent}"
  export JARVIS_APP_WINDOW="${JARVIS_APP_WINDOW:-0}"
  export JARVIS_SHELL_FORCE_NEW="${JARVIS_SHELL_FORCE_NEW:-0}"
  # FluentWindow crashes on some Linux/GPU stacks — stable Fusion QMainWindow by default.
  export JARVIS_FLUENT_WINDOW="${JARVIS_FLUENT_WINDOW:-0}"
  cd "$JARVIS_ROOT"

  if [[ "${JARVIS_GUI_MODE}" == "electron" ]]; then
    jarvis_notify "$(jarvis_app_name)" "Ready — opening Electron shell"
    jarvis_log "ARIA ready at $URL — Electron shell"
    exec "$(jarvis_python)" -c "from jarvis.electron_shell import launch_electron_shell; import sys; sys.exit(0 if launch_electron_shell('${URL}') else 1)"
  fi

  if [[ "${JARVIS_GUI_MODE}" == "pyside" || "${JARVIS_GUI_MODE}" == "fluent" ]]; then
    jarvis_notify "$(jarvis_app_name)" "Ready — opening ARIA window"
    jarvis_log "ARIA ready at $URL — PySide shell (${JARVIS_GUI_MODE}) DISPLAY=${DISPLAY:-unset}"
    export JARVIS_PYSIDE_FOREGROUND=1
    exec "$(jarvis_python)" -m jarvis.pyside_shell "$URL"
  fi

  if [[ "${JARVIS_GUI_MODE}" == "native" ]] && jarvis_native_available; then
    jarvis_notify "$(jarvis_app_name)" "Ready — opening native window"
    jarvis_log "ARIA ready at $URL — native window"
    exec "$(jarvis_python)" -m jarvis.native_window "$URL" --no-wait
  fi

  jarvis_notify "$(jarvis_app_name)" "Ready — opening Chrome app"
  jarvis_log "ARIA ready at $URL — Chrome app window"
  jarvis_open_gui_detached || true
  if [[ -n "${TRAY_PID:-}" ]]; then
    wait "$TRAY_PID"
  elif [[ -n "${SERVE_PID:-}" ]]; then
    wait "$SERVE_PID"
  fi
}

jarvis_wait_for_server() {
  local pid="${1:-}"
  local attempts="${2:-120}"
  local i
  for ((i = 0; i < attempts; i++)); do
    if jarvis_server_responsive; then
      return 0
    fi
    if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
      if jarvis_server_responsive; then
        return 0
      fi
      return 1
    fi
    sleep 0.5
  done
  return 1
}

jarvis_stop_stale() {
  pkill -f "${JARVIS_ROOT}/main.py tray" 2>/dev/null || true
  pkill -f "${JARVIS_ROOT}/main.py serve" 2>/dev/null || true
  pkill -f "${JARVIS_ROOT}/jarvis/pyside_shell" 2>/dev/null || true
  pkill -f "python -m jarvis.pyside_shell" 2>/dev/null || true
  if command -v fuser &>/dev/null; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
  fi
  sleep 1
}

jarvis_activate_env() {
  cd "$JARVIS_ROOT"
  jarvis_resolve_display
  if [[ -f "$JARVIS_ROOT/venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$JARVIS_ROOT/venv/bin/activate"
  fi
  if [[ -f "$JARVIS_ROOT/data/jarvis.env" ]]; then
    # shellcheck disable=SC1091
    source "$JARVIS_ROOT/data/jarvis.env"
  fi
  jarvis_resolve_display
}
