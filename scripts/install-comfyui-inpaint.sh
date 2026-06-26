#!/usr/bin/env bash
# ComfyUI inpaint for Jarvis — built-in workflow (no export required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMFY="${JARVIS_COMFYUI_ROOT:-$HOME/ComfyUI}"
WF="$ROOT/data/comfyui_workflows/inpaint_sdxl.json"

mkdir -p "$ROOT/data/comfyui_workflows"

echo "ComfyUI inpaint (Jarvis)"
echo "========================"
echo ""
echo "Jarvis ships a built-in SD/SDXL inpaint workflow (VAEEncodeForInpaint + KSampler)."
echo "Use Gallery → ✎ on any image, or chat: \"inpaint the center: blue sky\""
echo ""
echo "Optional tuning in data/jarvis.env:"
echo "  export JARVIS_COMFYUI_INPAINT_DENOISE=0.85"
echo "  export JARVIS_COMFYUI_INPAINT_MAX_DIM=1024"
echo "  export JARVIS_COMFYUI_INPAINT_GROW_MASK=6"
echo ""
echo "Custom workflow override (API format from ComfyUI UI):"
echo "  export JARVIS_COMFYUI_INPAINT_WORKFLOW=\"/path/to/your/inpaint.json\""
echo "  Label LoadImage nodes: Source Image / Mask Image"
echo "  Label CLIPTextEncode: Positive / Negative"
echo ""
echo "ComfyUI root: $COMFY"
echo "Placeholder doc: $WF"
echo ""
if [[ -d "$COMFY" ]]; then
  echo "ComfyUI found. Built-in nodes VAEEncodeForInpaint and ImageToMask are standard."
else
  echo "Note: ComfyUI not found at $COMFY — set JARVIS_COMFYUI_ROOT if elsewhere."
fi
