#!/usr/bin/env bash
# Install ARIA Editor Bridge into Cursor (VSIX — most reliable method).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${ROOT}/extensions/jarvis-cursor-bridge"
VSIX="${SRC}/jarvis-editor-bridge-0.1.0.vsix"

if [[ ! -f "${SRC}/package.json" ]]; then
  echo "Missing extension source: ${SRC}" >&2
  exit 1
fi

if ! command -v cursor &>/dev/null; then
  echo "cursor CLI not found. Install Cursor, or add /usr/bin/cursor to PATH." >&2
  exit 1
fi

echo "Packaging extension…"
(
  cd "${SRC}"
  npx --yes @vscode/vsce package --no-dependencies --allow-missing-repository -o "${VSIX}" >/dev/null
)

echo "Installing via Cursor CLI…"
cursor --install-extension "${VSIX}"

# Remove legacy manual copy folders if present.
rm -rf "${HOME}/.cursor/extensions/jarvis-editor-bridge-0.1.0"
rm -rf "${HOME}/.cursor/extensions/jarvis.jarvis-editor-bridge-0.1.0"

echo ""
echo "Installed ARIA Editor Bridge."
echo ""
echo "In Cursor:"
echo "  1. Ctrl+Shift+P → Developer: Reload Window"
echo "  2. Ctrl+Shift+P → type: Push Editor"
echo "     → ARIA: Push Editor Context Now"
echo "  3. In ARIA chat: fix selection / explain selection"
echo ""
echo "Start ARIA first: desktop shortcut or ./scripts/launch-jarvis.sh"
