#!/usr/bin/env bash
# Pull recommended Ollama models for Jarvis
set -euo pipefail

UNCENSORED="${JARVIS_UNCENSORED:-0}"

echo "Jarvis model installer"
echo "======================"

if ! command -v ollama &>/dev/null; then
  echo "ERROR: ollama not found. Install from https://ollama.com"
  exit 1
fi

if [[ "$UNCENSORED" == "1" ]]; then
  echo "Mode: UNCENSORED (Jeff's RX 7600 + 62GB RAM)"
  MODELS=(
    "dolphin3:latest"
    "qwen2.5-coder:14b"
    "llava:13b"
    "moondream"
    "nomic-embed-text"
  )
else
  echo "Mode: STANDARD (Jeff's RX 7600 + 62GB RAM)"
  MODELS=(
    "qwen2.5:14b"
    "qwen2.5-coder:14b"
    "deepseek-r1:14b"
    "llava:13b"
    "moondream"
    "nomic-embed-text"
  )
fi

echo ""
echo "Faster alternative (already installed):"
echo "  qwen2.5:7b for chat"
echo ""

for model in "${MODELS[@]}"; do
  echo "Pulling $model ..."
  ollama pull "$model"
done

echo ""
echo "Done. Set env vars to override defaults:"
echo "  JARVIS_GENERAL_MODEL  JARVIS_CODER_MODEL  JARVIS_VISION_MODEL"
