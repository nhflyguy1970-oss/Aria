#!/usr/bin/env bash
# Verify Ollama + Jarvis models after an Ollama upgrade.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${JARVIS_ROOT}/venv/bin/python"
HOST="${JARVIS_HOST:-127.0.0.1}"
PORT="${JARVIS_PORT:-8765}"
OLLAMA="${OLLAMA_HOST:-http://127.0.0.1:11434}"

pass() { echo "  [OK] $*"; }
fail() { echo "  [FAIL] $*"; exit 1; }

echo "=== Ollama + Jarvis verification ==="
echo

command -v ollama >/dev/null && pass "ollama CLI: $(ollama --version)" || fail "ollama CLI not found"

VER="$(curl -sf "${OLLAMA}/api/version" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin).get('version','?'))" 2>/dev/null || echo '?')"
pass "Ollama API version: ${VER}"

"$PYTHON" - <<'PY'
from jarvis.ollama_health import check_ollama, ollama_version, supports_mllama
from jarvis.model_store import get_models, get_missing_models

o = check_ollama()
assert o["running"], f"Ollama not reachable: {o.get('error')}"
print(f"  [OK] Ollama reachable ({len(o['models'])} models)")

v = ollama_version()
print(f"  [OK] Parsed version: {v}")

m = get_models()
print(f"  [OK] Jarvis chat model: {m.get('general')}")
print(f"  [OK] Jarvis vision model: {m.get('vision')}")

missing = get_missing_models()
if missing:
    print(f"  [WARN] Missing models: {', '.join(missing)}")
else:
    print("  [OK] All configured models installed")

mllama = supports_mllama()
print(f"  [OK] llama3.2-vision (mllama): {'supported' if mllama else 'not on 0.30.x — use moondream/llava or install Ollama 0.24.x'}")
PY

chat_model="$("$PYTHON" -c "from jarvis.model_store import get_models; print(get_models()['general'])")"
vision_model="$("$PYTHON" -c "from jarvis.model_store import get_models; print(get_models()['vision'])")"

echo
echo "Model smoke tests (may take a minute on first load)…"

CHAT_ERR="$(curl -sf -X POST "${OLLAMA}/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${chat_model}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"stream\":false,\"options\":{\"num_predict\":3}}" \
  | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',''))" 2>/dev/null || echo 'request failed')"
[[ -z "$CHAT_ERR" ]] && pass "Chat model ${chat_model}" || fail "Chat model ${chat_model}: ${CHAT_ERR}"

VISION_ERR="$(curl -sf -X POST "${OLLAMA}/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${vision_model}\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"stream\":false,\"options\":{\"num_predict\":3}}" \
  | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',''))" 2>/dev/null || echo 'request failed')"
[[ -z "$VISION_ERR" ]] && pass "Vision model ${vision_model}" || fail "Vision model ${vision_model}: ${VISION_ERR}"

if curl -sf "http://${HOST}:${PORT}/api/health" >/dev/null 2>&1; then
  pass "Jarvis GUI http://${HOST}:${PORT}"
else
  echo "  [WARN] Jarvis GUI not running — start with: ${JARVIS_ROOT}/scripts/launch-jarvis.sh"
fi

echo
echo "All checks passed."
