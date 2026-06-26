#!/usr/bin/env bash
# Quick health check for RX 7600 / 8GB Jarvis setup (read-only; exits 1 if any check fails).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/venv/bin/python"
FAIL=0

ok()   { echo "  OK   $*"; }
miss() { echo "  MISS $*"; FAIL=1; }
warn() { echo "  WARN $*"; }

echo "=== Jarvis setup verification ==="
echo ""

echo "Python / PyTorch"
if [[ -x "$PY" ]]; then
  ok "venv"
  if "$PY" -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    ver=$("$PY" -c "import torch; print(torch.__version__)")
    ok "ROCm PyTorch ($ver, cuda API available)"
  else
    miss "PyTorch ROCm (torch.cuda.is_available() false)"
  fi
else
  miss "venv ($PY)"
fi
echo ""

echo "Ollama 7B models"
OLLAMA_LIST=""
if command -v ollama &>/dev/null; then
  OLLAMA_LIST=$(ollama list 2>/dev/null || true)
fi
for m in qwen2.5:7b qwen2.5-coder:7b moondream:latest; do
  if [[ -n "$OLLAMA_LIST" ]] && grep -qF "$m" <<<"$OLLAMA_LIST"; then
    ok "$m"
  else
    miss "$m (ollama pull $m)"
  fi
done
echo ""

echo "ComfyUI checkpoints"
COMFY="${COMFYUI_ROOT:-$HOME/ComfyUI}"
for f in \
  "models/checkpoints/flux1-schnell-fp8.safetensors" \
  "models/checkpoints/sd_xl_base_1.0.safetensors"; do
  if [[ -f "$COMFY/$f" ]]; then ok "$(basename "$f")"; else miss "$COMFY/$f"; fi
done
echo ""

echo "Audio (Piper / espeak)"
if command -v espeak-ng &>/dev/null; then ok "espeak-ng"; else miss "espeak-ng (sudo apt install espeak-ng)"; fi
if [[ -x "${HOME}/.local/bin/piper" ]] || command -v piper &>/dev/null; then ok "piper"; else warn "piper not in PATH"; fi
echo ""

echo "VRAM guard / env"
if [[ -f "$ROOT/data/jarvis.env" ]]; then
  grep -qE 'JARVIS_VRAM_GUARD=.?1' "$ROOT/data/jarvis.env" && ok "JARVIS_VRAM_GUARD=1" || warn "JARVIS_VRAM_GUARD not set in jarvis.env"
  grep -qE 'JARVIS_WHISPER_MODEL=.?small' "$ROOT/data/jarvis.env" && ok "Whisper small" || warn "JARVIS_WHISPER_MODEL not small"
else
  warn "data/jarvis.env missing (copy from jarvis.env.example)"
fi
echo ""

echo "Model settings (8GB-safe roles)"
if [[ -x "$PY" && -f "$ROOT/data/model_settings.json" ]]; then
  "$PY" <<'PY' || { miss "model_settings has 14B/13B roles"; FAIL=1; }
import json, sys
from pathlib import Path
p = Path("data/model_settings.json")
data = json.loads(p.read_text())
bad = []
for mode, roles in data.items():
    if not isinstance(roles, dict):
        continue
    for role, model in roles.items():
        if isinstance(model, str) and (":14b" in model.lower() or ":13b" in model.lower()):
            bad.append(f"{mode}.{role}={model}")
if bad:
    print("  MISS heavy models still configured:", ", ".join(bad))
    sys.exit(1)
print("  OK   no 13B/14B roles in model_settings.json")
PY
else
  warn "model_settings.json not found"
fi
echo ""

echo "Web search"
if [[ -x "$PY" ]]; then
  "$PY" -c "from jarvis import web_search; r=web_search.search('Python programming language', limit=2); assert r, 'no results'; print('  OK  ', web_search.backend_name(), '-', len(r), 'hits')" \
    || { miss "web search returned no results (pip install ddgs)"; FAIL=1; }
else
  warn "venv missing for web search check"
fi
echo ""

echo "LSP servers"
if [[ -x "$PY" ]]; then
  if "$PY" -c "from jarvis.lsp_servers import list_servers; assert any(s.get('id')=='python' for s in list_servers())" 2>/dev/null; then
    ok "pylsp registered"
  else
    miss "pylsp (./scripts/install-lsp-servers.sh)"
  fi
fi
echo ""

echo "AE-5 PipeWire live EQ"
PW_DIR="${HOME}/.config/pipewire/filter-chain.conf.d"
if ls "$PW_DIR"/jarvis-*.conf &>/dev/null; then
  ok "$(ls "$PW_DIR"/jarvis-*.conf 2>/dev/null | wc -l) filter configs"
else
  warn "no jarvis-*.conf in $PW_DIR (run install-ae5-vst-bridge.sh)"
fi
echo ""

echo "Systemd autostart"
if systemctl --user is-enabled jarvis.service &>/dev/null; then
  ok "jarvis.service enabled"
else
  miss "jarvis.service not enabled (./scripts/install-systemd-user.sh)"
fi
echo ""

echo "Cursor extension"
if [[ -d "${HOME}/.cursor/extensions/jarvis-editor-bridge-0.1.0" ]]; then
  ok "jarvis-editor-bridge"
else
  warn "Cursor bridge not installed (./scripts/install-cursor-extension.sh)"
fi
echo ""

echo "Security (bind / exposure)"
if ss -tln 2>/dev/null | grep -qE '127\.0\.0\.1:8765'; then
  ok "Jarvis on localhost only"
elif ss -tln 2>/dev/null | grep -qE '0\.0\.0\.0:8765|\*:8765'; then
  if grep -qE '^export JARVIS_API_KEY=' "$ROOT/data/jarvis.env" 2>/dev/null; then
    warn "Jarvis on all interfaces — API key set (also run ./scripts/harden-security.sh)"
  else
    miss "Jarvis on all interfaces without JARVIS_API_KEY"
  fi
else
  warn "Jarvis not listening on :8765"
fi
if ss -tln 2>/dev/null | grep -qE '0\.0\.0\.0:11434|\*:11434'; then
  warn "Ollama exposed on all interfaces — bind to 127.0.0.1 (see harden-security.sh)"
else
  ok "Ollama not on public bind (or not running)"
fi
echo ""

if [[ "$FAIL" -eq 0 ]]; then
  echo "All required checks passed."
else
  echo "Some checks failed — see MISS lines above."
  exit 1
fi
