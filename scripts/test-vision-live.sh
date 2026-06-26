#!/usr/bin/env bash
# Live vision smoke test against running Jarvis (http://127.0.0.1:8765).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${JARVIS_HOST:-127.0.0.1}"
PORT="${JARVIS_PORT:-8765}"
BASE="http://${HOST}:${PORT}"
PYTHON="${JARVIS_ROOT}/venv/bin/python"
CURL=(curl -sS --max-time 180)
IMG="${JARVIS_ROOT}/data/uploads/vision-live-test.png"

if ! "${CURL[@]}" "${BASE}/api/live" | grep -q '"ok"'; then
  echo "Jarvis is not running. Start it first:"
  echo "  ${JARVIS_ROOT}/scripts/launch-jarvis.sh"
  exit 1
fi

echo "=== Jarvis live vision test (${BASE}) ==="
echo

pass() { echo "  [PASS] $*"; }
fail() { echo "  [FAIL] $*"; exit 1; }

mkdir -p "$(dirname "$IMG")"
"$PYTHON" -c "
from pathlib import Path
from PIL import Image
p = Path('${IMG}')
Image.new('RGB', (64, 64), 'orange').save(p)
"

r="$("${CURL[@]}" "${BASE}/api/vision/settings")"
echo "$r" | grep -q '"quality_mode"' && pass "vision settings GET" || fail "vision settings GET"

r="$("${CURL[@]}" -X POST "${BASE}/api/chat" \
  -F "message=Describe this image briefly." \
  -F "file=@${IMG}")"
echo "$r" | grep -q '"ok":true' && pass "describe image" || fail "describe image"
echo "$r" | grep -q '"module":"vision"' && pass "describe routed to vision" || fail "vision module"

r="$("${CURL[@]}" -X POST "${BASE}/api/chat" \
  -F "message=Read all text in this image" \
  -F "file=@${IMG}")"
echo "$r" | grep -q '"ok":true' && pass "ocr prompt" || fail "ocr prompt"

r="$("${CURL[@]}" -X POST "${BASE}/api/chat" -F "message=What color is dominant?")"
echo "$r" | grep -q '"ok":true' && pass "vision follow-up" || fail "vision follow-up"

r="$("${CURL[@]}" -X POST "${BASE}/api/chat" -F "message=what can you do?")"
if echo "$r" | grep -qi "can help\|abilities\|services\|what I can"; then
  pass "capabilities after vision"
else
  fail "capabilities hijacked after vision"
fi

echo
echo "All live vision checks passed."
echo "GUI: paste (Ctrl+V), drag-drop, Compare, Crop on attachment preview."
echo "Open: ${BASE}"
