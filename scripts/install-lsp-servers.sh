#!/usr/bin/env bash
# Install language servers for Jarvis IDE-grade LSP bridge.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${ROOT}/venv/bin/python"

echo "Jarvis LSP language servers"
echo "========================="
echo ""

if [[ ! -x "$VENV" ]]; then
  echo "ERROR: venv not found at $ROOT/venv"
  exit 1
fi

echo "Installing Python LSP (pylsp + common plugins)…"
"$VENV" -m pip install -q \
  'python-lsp-server[all]' \
  python-lsp-ruff \
  pylsp-mypy || echo "  (some pylsp plugins optional)"

if command -v npm >/dev/null 2>&1; then
  echo "Installing TypeScript/JavaScript language server…"
  npm install -g typescript typescript-language-server 2>/dev/null || echo "  (npm global install failed — try: sudo npm i -g typescript-language-server)"
else
  echo "Skip TS/JS — install node/npm for typescript-language-server"
fi

if command -v npm >/dev/null 2>&1; then
  echo "Installing bash-language-server…"
  npm install -g bash-language-server 2>/dev/null || echo "  (optional)"
fi

echo ""
echo "Verify:"
for bin in pylsp python-lsp-server typescript-language-server bash-language-server; do
  if command -v "$bin" >/dev/null 2>&1; then
    echo "  ✓ $bin"
  else
    echo "  · $bin (not on PATH)"
  fi
done

echo ""
echo "Jarvis picks up servers automatically when JARVIS_LSP=1 (default)."
echo "Use Coding sidebar → LSP panel or chat: 'go to definition', 'find references', 'format file'."
