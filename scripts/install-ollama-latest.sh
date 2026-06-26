#!/usr/bin/env bash
# Install latest Ollama (currently 0.30.x). Best for chat/coding models.
# Note: llama3.2-vision (mllama) is NOT supported on 0.30.x — use moondream/llava for vision.
set -euo pipefail

echo "Installing latest Ollama from ollama.com…"
echo "Requires sudo."
curl -fsSL https://ollama.com/install.sh | sh

echo
ollama --version
echo
echo "Vision on 0.30.x: use moondream:latest or llava:13b (not llama3.2-vision)."
echo "For llama3.2-vision only: ./scripts/install-ollama-0.24.sh instead."
