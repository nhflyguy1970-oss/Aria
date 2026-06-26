#!/usr/bin/env bash
# Install a systemd user unit to start Jarvis tray on login.
set -euo pipefail
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_DIR="${HOME}/.config/systemd/user"
UNIT_FILE="${UNIT_DIR}/jarvis.service"

mkdir -p "$UNIT_DIR"
cat > "$UNIT_FILE" <<EOF
[Unit]
Description=ARIA AI assistant (tray)
After=network.target

[Service]
Type=simple
WorkingDirectory=${JARVIS_ROOT}
ExecStart=${JARVIS_ROOT}/scripts/launch-jarvis.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable jarvis.service
echo "Installed ${UNIT_FILE}"
echo "Start now: systemctl --user start jarvis"
echo "Disable:   systemctl --user disable jarvis"
