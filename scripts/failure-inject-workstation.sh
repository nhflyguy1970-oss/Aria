#!/usr/bin/env bash
# Failure injection — verify self-healing, repair, recovery, and acceptance.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_ROOT"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"

LOG_DIR="$JARVIS_ROOT/data/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/failure-injection-$(date +%Y%m%d-%H%M%S).log"
PORT="${JARVIS_PORT:-8765}"
URL="http://127.0.0.1:${PORT}"

PASS=0
FAIL=0
RESULTS=()

log() { echo "$@" | tee -a "$LOG"; }
pass() { PASS=$((PASS + 1)); RESULTS+=("PASS: $*"); log "PASS: $*"; }
fail() { FAIL=$((FAIL + 1)); RESULTS+=("FAIL: $*"); log "FAIL: $*"; }

timed() {
  local label="$1"
  shift
  local start end elapsed
  start=$(date +%s)
  if "$@" >>"$LOG" 2>&1; then
    end=$(date +%s)
    elapsed=$((end - start))
    pass "${label} (${elapsed}s)"
    return 0
  fi
  end=$(date +%s)
  elapsed=$((end - start))
  fail "${label} (${elapsed}s)"
  return 1
}

verify_aria() {
  jarvis_server_responsive
}

verify_acceptance() {
  ./workstation acceptance >>"$LOG" 2>&1
}

inject_and_recover() {
  local name="$1"
  shift
  log ""
  log "=== Inject: ${name} ==="
  local t0
  t0=$(date +%s)
  "$@" >>"$LOG" 2>&1 || true
  sleep 3
  if ./workstation repair >>"$LOG" 2>&1; then
    pass "repair after ${name}"
  else
    fail "repair after ${name}"
  fi
  if verify_aria; then
    pass "Aria API after repair (${name})"
  else
    fail "Aria API down after repair (${name})"
  fi
  if verify_acceptance; then
    pass "acceptance after ${name}"
  else
    fail "acceptance after ${name}"
  fi
  log "elapsed=$(( $(date +%s) - t0 ))s"
}

log "=== Failure injection $(date -Iseconds) ==="
log "Report: $LOG"

# --- Docker infrastructure ---
inject_and_recover "stop redis" docker stop ai-redis
inject_and_recover "stop postgres" docker stop ai-postgres
inject_and_recover "stop litellm" docker stop ai-litellm
inject_and_recover "stop qdrant" docker stop ai-qdrant

# --- Ollama ---
if docker ps -a --format '{{.Names}}' | grep -qx 'ai-ollama'; then
  inject_and_recover "stop ollama container" docker stop ai-ollama
elif systemctl is-active ollama >/dev/null 2>&1; then
  log ""
  log "=== Inject: stop ollama (systemd) ==="
  sudo systemctl stop ollama >>"$LOG" 2>&1 || true
  sleep 2
  if ./workstation repair >>"$LOG" 2>&1; then pass "repair after stop ollama"; else fail "repair after stop ollama"; fi
  if verify_aria; then pass "Aria after ollama repair"; else fail "Aria after ollama repair"; fi
  if verify_acceptance; then pass "acceptance after ollama"; else fail "acceptance after ollama"; fi
else
  log "SKIP ollama stop (no container or systemd unit)"
fi

# --- Aria process ---
inject_and_recover "stop aria" ./workstation stop

# --- Corrupt temp cache (safe) ---
log ""
log "=== Inject: corrupt temp cache ==="
TMP_CACHE="$JARVIS_ROOT/data/cache"
mkdir -p "$TMP_CACHE"
echo "corrupt" >"$TMP_CACHE/.probe_corrupt"
find "$TMP_CACHE" -maxdepth 1 -name '*.tmp' -delete 2>/dev/null || true
if ./workstation repair >>"$LOG" 2>&1; then
  pass "repair after corrupt cache"
else
  fail "repair after corrupt cache"
fi

# --- Network block (localhost only, brief) ---
log ""
log "=== Inject: block outbound (5s) ==="
if command -v iptables >/dev/null 2>&1 && [[ "${FAILURE_INJECT_NETWORK:-}" == "1" ]]; then
  sudo iptables -A OUTPUT -p tcp --dport 443 -j REJECT >>"$LOG" 2>&1 || true
  sleep 2
  if curl -sf --max-time 3 http://127.0.0.1:11434/api/tags >>"$LOG" 2>&1; then
    pass "localhost still reachable during outbound block"
  else
    fail "localhost broken during outbound block"
  fi
  sudo iptables -D OUTPUT -p tcp --dport 443 -j REJECT >>"$LOG" 2>&1 || true
else
  log "SKIP network block (set FAILURE_INJECT_NETWORK=1 to enable)"
fi

# --- Full recovery ---
log ""
log "=== Recovery: full workstation start ==="
if timed "workstation start" ./workstation start; then
  :
else
  fail "workstation start after all injections"
fi

for i in $(seq 1 90); do
  if verify_aria; then
    break
  fi
  sleep 1
done
if verify_aria; then
  pass "Aria responsive after full recovery"
else
  fail "Aria not responsive after full recovery"
fi

if curl -sf --max-time 120 -X POST "${URL}/api/chat" \
  -F "message=Reply with exactly: RECOVERY_OK" \
  -F "stream=false" \
  -H "X-Jarvis-Key: ${JARVIS_API_KEY:-local}" >>"$LOG" 2>&1 | grep -q RECOVERY_OK; then
  pass "real chat after recovery"
else
  fail "real chat after recovery"
fi

if verify_acceptance; then
  pass "final acceptance"
else
  fail "final acceptance"
fi

# --- Rollback sanity (compatibility mode) ---
log ""
log "=== Platform rollback sanity ==="
if curl -sf -X POST "${URL}/api/platform/cutover/rollback" >>"$LOG" 2>&1; then
  if curl -sf -X POST "${URL}/api/platform/cutover/verify" | grep -q '"ready":true'; then
    pass "platform rollback + verify"
  else
    fail "platform verify after rollback"
  fi
else
  fail "platform rollback API"
fi

log ""
log "=== Summary: ${PASS} passed, ${FAIL} failed ==="
for row in "${RESULTS[@]}"; do
  log "  $row"
done
log "Full report: $LOG"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
