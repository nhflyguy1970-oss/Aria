#!/bin/bash
# Save Hugging Face token for pyannote diarization.
# Usage: bash scripts/set-hf-token.sh hf_your_token_here
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JARVIS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PY="$JARVIS_ROOT/venv/bin/python"

if [[ ! -f "$SCRIPT_DIR/set_hf_token.py" ]]; then
  echo "ERROR: missing $SCRIPT_DIR/set_hf_token.py" >&2
  exit 1
fi

if [[ -x "$PY" ]]; then
  exec "$PY" "$SCRIPT_DIR/set_hf_token.py" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/set_hf_token.py" "$@"
fi

echo "ERROR: no python found. Run: $PY $SCRIPT_DIR/set_hf_token.py hf_..." >&2
exit 1
