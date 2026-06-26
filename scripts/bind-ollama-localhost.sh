#!/usr/bin/env bash
# Restrict Ollama to localhost (recommended for home LAN security).
set -euo pipefail

DROPIN_DIR="/etc/systemd/system/ollama.service.d"
DROPIN_FILE="${DROPIN_DIR}/localhost.conf"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo $0" >&2
  exit 1
fi

mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_FILE" <<'EOF'
[Service]
Environment=OLLAMA_HOST=127.0.0.1:11434
EOF
echo "Wrote $DROPIN_FILE"
systemctl daemon-reload
systemctl restart ollama
sleep 1
if ss -tln | grep -qE '127\.0\.0\.1:11434'; then
  echo "OK: Ollama listening on 127.0.0.1:11434 only"
else
  echo "WARN: Check Ollama bind with: ss -tln | grep 11434"
fi
