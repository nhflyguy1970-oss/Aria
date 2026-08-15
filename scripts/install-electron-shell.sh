#!/usr/bin/env bash
# Install Electron shell spike into scripts/electron-shell (Phase 1).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/scripts/electron-shell"
mkdir -p "$DIR"
cd "$DIR"
if [[ ! -f package.json ]]; then
  echo "electron-shell package.json missing — create spike scaffold first"
  exit 1
fi
npm install
echo "Done. Binary candidates under node_modules/electron"
