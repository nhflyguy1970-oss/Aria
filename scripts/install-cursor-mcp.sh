#!/usr/bin/env bash
# Register Jarvis MCP server in Cursor (global + project).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GLOBAL_MCP="${HOME}/.cursor/mcp.json"
PROJECT_MCP="${JARVIS_ROOT}/.cursor/mcp.json"
PYTHON="${JARVIS_ROOT}/venv/bin/python"
SERVER="${JARVIS_ROOT}/scripts/jarvis-mcp-server.py"

JARVIS_MCP_JSON=$(cat <<EOF
{
  "type": "stdio",
  "command": "$PYTHON",
  "args": ["-u", "$SERVER"],
  "env": {
    "PYTHONUNBUFFERED": "1",
    "PYTHONDONTWRITEBYTECODE": "1"
  }
}
EOF
)

write_mcp() {
  local dest="$1"
  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" ]] && command -v jq &>/dev/null; then
    local tmp
    tmp="$(mktemp)"
    jq --argjson cfg "$JARVIS_MCP_JSON" '.mcpServers.jarvis = $cfg' "$dest" >"$tmp" \
      && mv "$tmp" "$dest"
  else
    cat >"$dest" <<EOF
{
  "mcpServers": {
    "jarvis": {
      "type": "stdio",
      "command": "$PYTHON",
      "args": ["-u", "$SERVER"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1"
      }
    }
  }
}
EOF
  fi
  chmod 644 "$dest" 2>/dev/null || true
  echo "  $dest"
}

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing venv: $PYTHON — run ./scripts/install-dependencies.sh first" >&2
  exit 1
fi
if [[ ! -f "$SERVER" ]]; then
  echo "Missing MCP server: $SERVER" >&2
  exit 1
fi

chmod +x "$SERVER"
chmod +x "${JARVIS_ROOT}/scripts/fix-cursor-mcp-permissions.sh"
echo "Jarvis MCP registered:"
write_mcp "$GLOBAL_MCP"
write_mcp "$PROJECT_MCP"

if [[ -f "$GLOBAL_MCP" ]] && [[ ! -r "$GLOBAL_MCP" ]]; then
  echo ""
  echo "WARNING: $GLOBAL_MCP is not readable by $USER."
  echo "Run: ./scripts/fix-cursor-mcp-permissions.sh"
fi

echo ""
echo "In Cursor: Ctrl+Shift+P → Open MCP Settings → enable jarvis"
echo "Editor bridge: ./scripts/install-cursor-extension.sh (syncs active file + selection)"
echo "Then: Ctrl+Shift+P → Developer: Reload Window"
