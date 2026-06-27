#!/usr/bin/env bash
# 14-phase system audit — CLI wrapper (engine in jarvis/system_audit_engine.py).
set -uo pipefail

ROOT="${JARVIS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PY="${JARVIS_VENV:-$ROOT/venv}/bin/python"
[[ -x "$PY" ]] || PY="$ROOT/venv/bin/python"
[[ -x "$PY" ]] || PY=python3
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
BRIEF=0
JSON_MODE=0
for arg in "$@"; do
  case "$arg" in
    --brief) BRIEF=1 ;;
    --json)  JSON_MODE=1; BRIEF=1 ;;
  esac
done

run_audit() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    "$PY" -m jarvis.system_audit_engine
    return $?
  fi
  if sudo -n true 2>/dev/null; then
    sudo -n env PYTHONPATH="$PYTHONPATH" "$PY" -m jarvis.system_audit_engine
    return $?
  fi
  if [[ -n "${DISPLAY:-}" ]] && [[ -x "${ROOT}/scripts/sudo-askpass-zenity.sh" ]]; then
    SUDO_ASKPASS="${ROOT}/scripts/sudo-askpass-zenity.sh" sudo -A env PYTHONPATH="$PYTHONPATH" "$PY" -m jarvis.system_audit_engine
    return $?
  fi
  "$PY" -m jarvis.system_audit_engine
}

if (( JSON_MODE )); then
  run_audit
  exit $?
fi

echo "Running 14-phase system audit…"
echo "Jarvis root: $ROOT"
run_audit | "$PY" -c "
import json, sys
data = json.load(sys.stdin)
phases = data.get('phases') or []
print()
for ph in phases:
    p, w, f = ph.get('pass', []), ph.get('warn', []), ph.get('fail', [])
    print(f\"=== {ph.get('title', ph.get('id', 'Phase'))} ===\")
    for item in p:
        print(f\"  PASS  {item.get('message', '')}\")
    for item in w:
        print(f\"  WARN  {item.get('message', '')}\")
        if item.get('fix'):
            print(f\"        Fix: {item['fix']}\")
    for item in f:
        print(f\"  FAIL  {item.get('message', '')}\")
        if item.get('fix'):
            print(f\"        Fix: {item['fix']}\")
    print()
s = data.get('summary', {})
print(f\"Summary: {s.get('pass',0)} pass, {s.get('warn',0)} warn, {s.get('fail',0)} fail ({s.get('total',0)} checks, {s.get('phases', len(phases))} phases)\")
print(f\"System: {data.get('result', 'unknown').upper()} · Jarvis: {data.get('jarvis_result', 'unknown').upper()}\")
"
exit "${PIPESTATUS[0]}"
