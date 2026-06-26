#!/usr/bin/env bash
# Live chat smoke test against running Jarvis (http://127.0.0.1:8765).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${JARVIS_HOST:-127.0.0.1}"
PORT="${JARVIS_PORT:-8765}"
BASE="http://${HOST}:${PORT}"
PYTHON="${JARVIS_ROOT}/venv/bin/python"
CURL=(curl -sS --max-time 120)

if ! "${CURL[@]}" "${BASE}/api/live" | grep -q '"ok"'; then
  echo "Jarvis is not running. Start it first:"
  echo "  ${JARVIS_ROOT}/scripts/launch-jarvis.sh"
  exit 1
fi

echo "=== Jarvis live chat test (${BASE}) ==="
echo

chat() {
  local msg="$1"
  local stream="${2:-false}"
  "${CURL[@]}" -X POST "${BASE}/api/chat" \
    -F "message=${msg}" \
    -F "stream=${stream}"
}

pass() { echo "  [PASS] $*"; }
fail() { echo "  [FAIL] $*"; exit 1; }

# Instant
r="$(chat "what can you do?")"
echo "$r" | grep -q '"ok":true' && pass "capabilities" || fail "capabilities"

# Memory
r="$(chat "Remember that live test codename is Falcon")"
echo "$r" | grep -q '"module":"memory"' && pass "remember" || fail "remember"

r="$(chat "recall")"
echo "$r" | grep -qi falcon && pass "recall" || fail "recall (Falcon not found)"

# LLM chat (~10s)
r="$(chat "Reply with exactly one word: ok")"
echo "$r" | grep -qi ok && pass "plain chat — $(echo "$r" | "$PYTHON" -c 'import sys,json; print(json.load(sys.stdin).get("message","")[:60])')" || fail "plain chat"

# Stream
echo -n "  [....] stream chat (waiting) "
stream_out="$(chat "Say hi in five words or fewer." true)"
echo "$stream_out" | grep -q '"type": "done"' && echo && pass "stream chat" || fail "stream chat"

# Clear + branches
r="$(chat "clear")"
echo "$r" | grep -q '"ok":true' && pass "clear" || fail "clear"

r="$(chat "list branches")"
echo "$r" | grep -qi main && pass "branches" || fail "branches"

echo
echo "All live chat checks passed."
echo "Open the GUI: ${BASE}"
