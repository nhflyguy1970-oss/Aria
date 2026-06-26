#!/usr/bin/env bash
# Generate and install a strong JARVIS_API_KEY in data/jarvis.env.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

KEY="$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)"
./venv/bin/python -c "
from jarvis.env_loader import upsert_env_vars, load_jarvis_env
upsert_env_vars({'JARVIS_API_KEY': '$KEY'})
load_jarvis_env(force=True)
print('JARVIS_API_KEY updated in data/jarvis.env')
print('Save this key in your password manager — it will not be shown again.')
"

chmod 600 "$ROOT/data/jarvis.env" 2>/dev/null || true
echo "Restart ARIA after updating browser/API clients."
