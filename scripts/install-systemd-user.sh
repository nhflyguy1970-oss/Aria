#!/usr/bin/env bash
# Install the canonical systemd --user unit that owns the Aria HTTP server.
# Tray and desktop launchers attach to this server. They must not spawn another.
set -euo pipefail
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_DIR="${HOME}/.config/systemd/user"
UNIT_FILE="${UNIT_DIR}/jarvis.service"

mkdir -p "$UNIT_DIR"
cat > "$UNIT_FILE" <<EOF
[Unit]
Description=ARIA production HTTP server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${JARVIS_ROOT}
Environment=JARVIS_DATA_DIR=${JARVIS_ROOT}/data
Environment=VIRTUAL_ENV=${JARVIS_ROOT}/venv
Environment=JARVIS_LAUNCH_OWNER=systemd
Environment=JARVIS_NO_BROWSER=1
# Milestone 3 promotion: the background mission worker ships disabled in code
# (JARVIS_MISSION_WORKER defaults to 0) and is switched on explicitly here.
Environment=JARVIS_MISSION_WORKER=1
# Secrets stay in data/jarvis.env and the Owner Vault — never Environment= keys.
ExecStart=${JARVIS_ROOT}/scripts/aria-serve.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable jarvis.service
if command -v loginctl >/dev/null 2>&1; then
  loginctl enable-linger "${USER}" >/dev/null 2>&1 || true
fi
echo "Installed ${UNIT_FILE}"
echo "Canonical server: systemctl --user start jarvis.service"
echo "Disable:          systemctl --user disable --now jarvis.service"
