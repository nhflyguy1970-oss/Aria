#!/usr/bin/env bash
# Fix MCP config permissions so Cursor (your user) can read them.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USER_NAME="${SUDO_USER:-$USER}"

fix_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  if [[ "$(stat -c '%U' "$f")" != "$USER_NAME" ]]; then
    sudo chown "$USER_NAME:$USER_NAME" "$f"
  fi
  chmod 644 "$f"
  echo "  fixed $f ($(stat -c '%U:%a' "$f"))"
}

echo "Fixing MCP config permissions for $USER_NAME..."
fix_file "${HOME}/.cursor/mcp.json"
fix_file "${JARVIS_ROOT}/.cursor/mcp.json"
chmod +x "${JARVIS_ROOT}/scripts/jarvis-mcp-server.py"

echo ""
echo "Done. In Cursor:"
echo "  Ctrl+Shift+P → Developer: Reload Window"
echo "  Ctrl+Shift+P → Open MCP Settings → enable jarvis"
