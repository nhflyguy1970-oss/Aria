#!/usr/bin/env bash
# Desktop-friendly workstation commands (status, doctor, acceptance).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_ROOT"

MODE="${1:-status}"
TITLE="AI Workstation"

_run_text() {
  local cmd=("$@")
  local tmp
  tmp="$(mktemp)"
  if "${cmd[@]}" >"$tmp" 2>&1; then
    :
  else
    echo "(command exited with errors)" >>"$tmp"
  fi
  if command -v zenity >/dev/null 2>&1; then
    zenity --text-info --title="$TITLE" --width=900 --height=650 --scroll <"$tmp" || true
  elif command -v kdialog >/dev/null 2>&1; then
    kdialog --textbox "$tmp" 900 650 || true
  else
    cat "$tmp"
  fi
  rm -f "$tmp"
}

case "$MODE" in
  status)
    _run_text ./workstation status
    ;;
  doctor)
    _run_text ./workstation doctor
    ;;
  acceptance)
    _run_text ./workstation acceptance
    ;;
  *)
    echo "Usage: $0 {status|doctor|acceptance}" >&2
    exit 2
    ;;
esac
