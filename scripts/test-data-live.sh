#!/usr/bin/env bash
# Live data smoke test against running Jarvis (http://127.0.0.1:8765).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${JARVIS_HOST:-127.0.0.1}"
PORT="${JARVIS_PORT:-8765}"
BASE="http://${HOST}:${PORT}"
PYTHON="${JARVIS_ROOT}/venv/bin/python"
CURL=(curl -sS --max-time 120)
CSV="${JARVIS_ROOT}/data/uploads/data-live-test.csv"

if ! "${CURL[@]}" "${BASE}/api/live" | grep -q '"ok"'; then
  echo "Jarvis is not running. Start: ${JARVIS_ROOT}/scripts/launch-jarvis.sh"
  exit 1
fi

mkdir -p "$(dirname "$CSV")"
"$PYTHON" -c "
import csv
from pathlib import Path
p = Path('${CSV}')
rows = [{'item':'apple','qty':10,'price':1.5},{'item':'pear','qty':5,'price':2.0},{'item':'apple','qty':10,'price':1.5}]
with open(p,'w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
"

pass() { echo "  [PASS] $*"; }
fail() { echo "  [FAIL] $*"; exit 1; }

echo "=== Jarvis live data test (${BASE}) ==="

r="$("${CURL[@]}" -X POST "${BASE}/api/chat" -F "message=Load and summarize" -F "file=@${CSV}")"
echo "$r" | grep -q '"ok":true' && pass "load csv" || fail "load csv"
echo "$r" | grep -q '"module":"data"' && pass "data module" || fail "data module"

r="$("${CURL[@]}" -X POST "${BASE}/api/chat" -F "message=How many rows are there?")"
echo "$r" | grep -qi '3' && pass "row count" || fail "row count"

r="$("${CURL[@]}" -X POST "${BASE}/api/chat" -F "message=clean drop duplicates")"
echo "$r" | grep -q '"ok":true' && pass "clean" || fail "clean"

r="$("${CURL[@]}" -X POST "${BASE}/api/chat" -F "message=export to csv")"
echo "$r" | grep -q '"ok":true' && pass "export" || fail "export"

echo
echo "All live data checks passed."
