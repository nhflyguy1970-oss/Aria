#!/usr/bin/env bash
# Install Ollama 0.24.0 (last line with llama3.2-vision / mllama support).
# Ollama 0.30.x intentionally dropped mllama — upgrading to "latest" will NOT fix vision.
#
# For AMD GPU (RX 7600): uses the ROCm build.
# Requires sudo. After install: restart ollama, then restart Jarvis.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="v0.24.0"
ARCH="amd64"
VARIANT="rocm"

if command -v rocm-smi &>/dev/null; then
  VARIANT="rocm"
  echo "ROCm detected — installing ${TAG} ${VARIANT} build for AMD GPU."
else
  VARIANT=""
  echo "No ROCm — installing ${TAG} standard Linux build."
fi

ASSET="ollama-linux-${ARCH}"
[[ -n "$VARIANT" ]] && ASSET="${ASSET}-${VARIANT}"
ASSET="${ASSET}.tar.zst"
URL="https://github.com/ollama/ollama/releases/download/${TAG}/${ASSET}"
TMP="/tmp/${ASSET}"

echo "Downloading ${URL}…"
curl -fsSL "$URL" -o "$TMP"

echo "Stopping Ollama…"
pkill -x ollama 2>/dev/null || true
sleep 2

echo "Installing to /usr/local (sudo required)…"
sudo mkdir -p /usr/local/bin /usr/local/lib/ollama
sudo tar -xaf "$TMP" -C /usr/local
sudo ln -sf /usr/local/bin/ollama /usr/bin/ollama 2>/dev/null || true

echo "Starting Ollama…"
nohup /usr/local/bin/ollama serve >>"$JARVIS_ROOT/data/logs/ollama.log" 2>&1 &
sleep 3

VER="$(/usr/local/bin/ollama --version 2>&1 || true)"
echo "Installed: ${VER}"

echo
echo "Test llama3.2-vision (optional):"
echo "  ollama run llama3.2-vision:11b 'describe a red square'"
echo
echo "Jarvis: restart tray, or run ./scripts/verify-ollama-jarvis.sh"
rm -f "$TMP"
