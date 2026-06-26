#!/usr/bin/env bash
# Set or change the uncensored-mode password (stored hashed in data/uncensored_auth.json).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_ROOT"

if [[ -f "$JARVIS_ROOT/venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$JARVIS_ROOT/venv/bin/activate"
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <password>"
  echo "  Or:   JARVIS_UNCENSORED_PASSWORD=secret $0"
  exit 1
fi

PW="${1:-${JARVIS_UNCENSORED_PASSWORD:-}}"
if [[ -z "$PW" ]]; then
  echo "ERROR: password required"
  exit 1
fi

export JARVIS_SET_PW="$PW"
python <<'PY'
import os
from jarvis.uncensored_auth import set_password
set_password(os.environ["JARVIS_SET_PW"])
print("Uncensored password saved to data/uncensored_auth.json")
PY
unset JARVIS_SET_PW
