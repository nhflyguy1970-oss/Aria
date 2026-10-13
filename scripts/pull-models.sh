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
  echo "Mode: UNCENSORED (Jeff's RTX 3060 12GB + 62GB RAM)"
  MODELS=(
    "huihui_ai/gemma-4-abliterated:12b"
    "qwen2.5-coder:14b"
    "deepseek-r1:14b"
    "moondream"
    "nomic-embed-text"
  )
else
  echo "Mode: STANDARD (Jeff's RTX 3060 12GB + 62GB RAM)"
  MODELS=(
    "gemma4:12b"
    "qwen2.5-coder:14b"
    "deepseek-r1:14b"
    "qwen2.5vl:7b"
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
