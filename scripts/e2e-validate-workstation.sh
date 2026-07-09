#!/usr/bin/env bash
# End-to-end workstation validation — power-on through shutdown.
# Run from Jeff's machine: ./scripts/e2e-validate-workstation.sh
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_ROOT"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"

LOG_DIR="$JARVIS_ROOT/data/logs"
mkdir -p "$LOG_DIR"
REPORT="$LOG_DIR/e2e-validation-$(date +%Y%m%d-%H%M%S).log"
PORT="${JARVIS_PORT:-8765}"
HOST="${JARVIS_HOST:-127.0.0.1}"
CLIENT_HOST="${HOST}"
[[ "${HOST}" == "0.0.0.0" || "${HOST}" == "::" ]] && CLIENT_HOST="127.0.0.1"
URL="http://${CLIENT_HOST}:${PORT}"

PASS=0
FAIL=0
FRICTION=()

log() { echo "$@" | tee -a "$REPORT"; }
pass() { PASS=$((PASS + 1)); log "PASS: $*"; }
fail() { FAIL=$((FAIL + 1)); FRICTION+=("$*"); log "FAIL: $*"; }

check_cmd() {
  local label="$1"
  shift
  if "$@" >>"$REPORT" 2>&1; then
    pass "$label"
  else
    fail "$label"
  fi
}

log "=== E2E Workstation Validation $(date -Iseconds) ==="
log "Report: $REPORT"

log ""
log "--- Phase 0: clean shutdown ---"
./workstation stop >>"$REPORT" 2>&1 || true
if pgrep -f "${JARVIS_ROOT}/main.py tray" >/dev/null || pgrep -f "${JARVIS_ROOT}/main.py serve" >/dev/null; then
  fail "Aria still running after workstation stop"
else
  pass "Aria stopped (clean baseline)"
fi

log ""
log "--- Phase 1: power-on (workstation start) ---"
if ./workstation start >>"$REPORT" 2>&1; then
  pass "workstation start exited 0"
else
  fail "workstation start failed"
fi

log ""
log "--- Phase 2: infrastructure ---"
check_cmd "PostgreSQL port open" bash -c 'ss -ltn | grep -q ":5432"'
check_cmd "Redis port open" bash -c 'ss -ltn | grep -q ":6379"'
check_cmd "Ollama API" curl -sf --max-time 5 http://127.0.0.1:11434/api/tags

log ""
log "--- Phase 3: Aria API ---"
for i in $(seq 1 60); do
  if jarvis_server_responsive; then
    break
  fi
  sleep 1
done
if jarvis_server_responsive; then
  pass "Aria API responsive"
else
  fail "Aria API not responsive after 60s"
fi

if pgrep -f "${JARVIS_ROOT}/main.py tray" >/dev/null || pgrep -f "${JARVIS_ROOT}/main.py serve" >/dev/null; then
  pass "Aria process running (tray or serve)"
else
  fail "No Aria tray/serve process"
fi

log ""
log "--- Phase 4: real work probes ---"
check_cmd "health endpoint" curl -sf --max-time 5 "${URL}/api/health"
check_cmd "models list" curl -sf --max-time 10 "${URL}/api/models"
check_cmd "briefing endpoint" curl -sf --max-time 15 "${URL}/api/briefing" -H "X-Jarvis-Key: ${JARVIS_API_KEY:-local}"
if curl -sf --max-time 120 -X POST "${URL}/api/chat" \
  -F "message=Reply with exactly: WORKSTATION_OK" \
  -F "stream=false" \
  -H "X-Jarvis-Key: ${JARVIS_API_KEY:-local}" | tee -a "$REPORT" | grep -q WORKSTATION_OK; then
  pass "chat inference (real LLM response)"
else
  fail "chat inference did not return WORKSTATION_OK"
fi

log ""
log "--- Phase 5: acceptance snapshot ---"
if ./workstation acceptance >>"$REPORT" 2>&1; then
  pass "acceptance passed"
else
  fail "acceptance failed (see report)"
fi

log ""
log "--- Phase 6: clean shutdown ---"
if ./workstation stop >>"$REPORT" 2>&1; then
  pass "workstation stop exited 0"
else
  fail "workstation stop failed"
fi
sleep 2
if pgrep -f "${JARVIS_ROOT}/main.py tray" >/dev/null || pgrep -f "${JARVIS_ROOT}/main.py serve" >/dev/null; then
  fail "Aria still running after workstation stop"
else
  pass "Aria fully stopped"
fi
if jarvis_port_open; then
  fail "Port ${PORT} still open after stop"
else
  pass "Port ${PORT} closed"
fi

log ""
log "=== Summary: ${PASS} passed, ${FAIL} failed ==="
if ((${#FRICTION[@]} > 0)); then
  log "Friction points:"
  for item in "${FRICTION[@]}"; do
    log "  - ${item}"
  done
fi

if ((FAIL > 0)); then
  exit 1
fi
exit 0
