#!/usr/bin/env bash
# Failure injection — verify self-healing and recovery.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_ROOT"
LOG="$JARVIS_ROOT/data/logs/failure-injection-$(date +%Y%m%d-%H%M%S).log"

log() { echo "$@" | tee -a "$LOG"; }
pass() { log "PASS: $*"; }
fail() { log "FAIL: $*"; }

log "=== Failure injection $(date -Iseconds) ==="

inject() {
  local name="$1"
  shift
  log ""
  log "--- Inject: $name ---"
  "$@" >>"$LOG" 2>&1 || true
  sleep 3
  if ./workstation repair >>"$LOG" 2>&1; then
    pass "repair after $name"
  else
    fail "repair after $name"
  fi
  if ./workstation acceptance >>"$LOG" 2>&1; then
    pass "acceptance after $name"
  else
    fail "acceptance after $name (may be expected for some faults)"
  fi
}

inject "stop redis" docker stop ai-redis
inject "stop postgres" docker stop ai-postgres
inject "stop litellm" docker stop ai-litellm
inject "stop aria" ./workstation stop

log ""
log "=== Recovery: full start ==="
./workstation start >>"$LOG" 2>&1 && pass "workstation start after injections" || fail "workstation start"

log "Report: $LOG"
