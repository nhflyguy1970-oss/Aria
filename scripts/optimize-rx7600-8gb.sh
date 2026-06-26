#!/usr/bin/env bash
# RX 7600 8GB — apply Jarvis tuning: models, Whisper, VRAM guard, ROCm PyTorch, LSP.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${ROOT}/venv/bin/python"

echo "Jarvis RX 7600 / 8GB optimization"
echo "=================================="
echo ""

if [[ ! -x "$VENV" ]]; then
  echo "ERROR: venv missing at ${ROOT}/venv — run install-dependencies.sh first"
  exit 1
fi

echo "→ ROCm PyTorch (idempotent)…"
"${ROOT}/scripts/install-rocm-pytorch.sh" || echo "  (ROCm PyTorch step skipped — fix manually if needed)"

echo ""
echo "→ LSP language servers…"
"${ROOT}/scripts/install-lsp-servers.sh" || true

echo ""
echo "→ Env, Whisper small, fast model preset…"
"$VENV" - <<'PY'
from jarvis.hardware_tune import run_optimizations
import json
print(json.dumps(run_optimizations(pull_models=False), indent=2))
PY

echo ""
echo "→ Pull 8GB-friendly Ollama models (may take a while)…"
for m in qwen2.5:7b qwen2.5-coder:7b moondream:latest nomic-embed-text:latest; do
  if ollama list 2>/dev/null | grep -qF "$m"; then
    echo "  ✓ $m already installed"
  else
    echo "  pulling $m…"
    ollama pull "$m" || echo "  (pull failed for $m)"
  fi
done

echo ""
echo "→ Prefetch Whisper small weights…"
"$VENV" -c "from jarvis.hardware_tune import prefetch_whisper; print(prefetch_whisper('small'))"

echo ""
echo "Done. Restart Jarvis, then:"
echo "  • Sidebar → Gaming profile before games (ComfyUI CPU, short keep-alive)"
echo "  • Sidebar → Work profile for daily use"
echo "  • Free VRAM button before image gen if chat was using GPU"
echo "  • GET /api/gpu for tips"
