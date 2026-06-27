#!/usr/bin/env bash
# Passwordless sudo for SMART + apt-get check in system audit — run once with your password.
set -euo pipefail

JARVIS_ROOT="${JARVIS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
USER_NAME="$(whoami)"
SCRIPT="$(readlink -f "${JARVIS_ROOT}/scripts/audit-system.sh")"
SMARTCTL="$(command -v smartctl || true)"
APT_GET="$(command -v apt-get || true)"
SUDOERS="/etc/sudoers.d/jarvis-audit"

if [[ ! -x "$SCRIPT" ]]; then
  echo "Missing audit script: $SCRIPT" >&2
  exit 1
fi
if [[ -z "$SMARTCTL" ]]; then
  echo "smartctl not found — run install-system-audit-deps.sh first." >&2
  exit 1
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

{
  echo "# Jarvis system audit — passwordless SMART for ARIA System tab"
  echo "${USER_NAME} ALL=(root) NOPASSWD: ${SCRIPT}"
  echo "${USER_NAME} ALL=(root) NOPASSWD: ${SMARTCTL}"
  if [[ -n "$APT_GET" ]]; then
    echo "${USER_NAME} ALL=(root) NOPASSWD: ${APT_GET} check"
  fi
} > "$TMP"

sudo install -m 0440 "$TMP" "$SUDOERS"
sudo visudo -cf "$SUDOERS" >/dev/null
echo "Installed ${SUDOERS}"
echo "ARIA System tab audits will use sudo for SMART (no password prompt)."
