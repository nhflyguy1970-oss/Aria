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
  local icon="${JARVIS_ROOT}/assets/jarvis-icon.svg"
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

jarvis_native_available() {
  "$(jarvis_python)" -c \
    "from jarvis.native_window import is_available; import sys; sys.exit(0 if is_available() else 1)" \
    2>/dev/null
}

jarvis_open_gui_detached() {
  export JARVIS_GUI_MODE="${JARVIS_GUI_MODE:-fluent}"
  export JARVIS_APP_WINDOW="${JARVIS_APP_WINDOW:-0}"
  export JARVIS_SHELL_FORCE_NEW="${JARVIS_SHELL_FORCE_NEW:-1}"
  "$(jarvis_python)" -m jarvis.gui_launcher "$URL"
}

jarvis_run_gui_foreground() {
  export JARVIS_NO_BROWSER=1
  export JARVIS_GUI_MODE="${JARVIS_GUI_MODE:-fluent}"
  export JARVIS_APP_WINDOW="${JARVIS_APP_WINDOW:-0}"
  export JARVIS_SHELL_FORCE_NEW="${JARVIS_SHELL_FORCE_NEW:-1}"
  cd "$JARVIS_ROOT"

  if [[ "${JARVIS_GUI_MODE}" == "native" ]] && jarvis_native_available; then
    jarvis_notify "$(jarvis_app_name)" "Ready — opening native window"
    jarvis_log "ARIA ready at $URL — opening native window (legacy)"
    exec "$(jarvis_python)" -m jarvis.native_window "$URL" --no-wait
  fi

  jarvis_notify "$(jarvis_app_name)" "Ready — opening Chrome app"
  jarvis_log "ARIA ready at $URL — Chrome app window"
  jarvis_open_gui_detached || true
  wait "$TRAY_PID"
}

jarvis_wait_for_server() {
  local pid="$1"
  local attempts="${2:-120}"
  local i
  for ((i = 0; i < attempts; i++)); do
    if jarvis_server_responsive; then
      return 0
    fi
    if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
      return 1
    fi
    sleep 0.5
  done
  return 1
}

jarvis_stop_stale() {
  pkill -f "${JARVIS_ROOT}/main.py tray" 2>/dev/null || true
  pkill -f "${JARVIS_ROOT}/main.py serve" 2>/dev/null || true
  if command -v fuser &>/dev/null; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
  fi
  sleep 1
}

jarvis_activate_env() {
  cd "$JARVIS_ROOT"
  export DISPLAY="${DISPLAY:-:0}"
  if [[ -f "$JARVIS_ROOT/venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$JARVIS_ROOT/venv/bin/activate"
  fi
  if [[ -f "$JARVIS_ROOT/data/jarvis.env" ]]; then
    # shellcheck disable=SC1091
    source "$JARVIS_ROOT/data/jarvis.env"
  fi
}
