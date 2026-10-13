#!/usr/bin/env bash
# Start the ARIA tray at every graphical login (systemd --user aria-tray.service).
# Crashes restart it; Quit Tray / Quit ARIA Completely exit cleanly and stay quit
# until the next login. Remove with: systemctl --user disable --now aria-tray.service
set -euo pipefail
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_DIR="${HOME}/.config/systemd/user"
UNIT_FILE="${UNIT_DIR}/aria-tray.service"

mkdir -p "$UNIT_DIR"
cat > "$UNIT_FILE" <<EOF
[Unit]
Description=ARIA system tray
# Needs the desktop session (display, D-Bus, AppIndicator host); stops with it.
PartOf=graphical-session.target
After=graphical-session.target jarvis.service
# Wants, not Requires: "Stop ARIA" in the tray stops the server, not the tray.
Wants=jarvis.service

[Service]
Type=simple
WorkingDirectory=${JARVIS_ROOT}
Environment=JARVIS_DATA_DIR=${JARVIS_ROOT}/data
ExecStart=${JARVIS_ROOT}/scripts/aria-tray.sh
Restart=on-failure
RestartSec=10
# Quit stops the scheduler and mission worker gracefully (each joins for up to 30 s).
TimeoutStopSec=120

[Install]
WantedBy=graphical-session.target
EOF

systemctl --user daemon-reload
systemctl --user enable aria-tray.service
echo "Installed ${UNIT_FILE} (starts at login)"
echo "Start now: systemctl --user start aria-tray.service"
echo "Disable:   systemctl --user disable --now aria-tray.service"
