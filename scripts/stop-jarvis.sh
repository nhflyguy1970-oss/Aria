#!/usr/bin/env bash
# Quit only identified ARIA processes; never kill listeners or unrelated apps.
set -euo pipefail
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_ROOT"
exec "$JARVIS_ROOT/venv/bin/python" -m jarvis.shutdown quit
