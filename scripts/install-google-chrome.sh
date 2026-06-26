#!/usr/bin/env bash
# Install Google Chrome (.deb) for Jarvis GUI — avoids xdg-open opening Brave.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEB="/tmp/google-chrome-stable_current_amd64.deb"
URL="https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"

if command -v google-chrome-stable &>/dev/null || [[ -x /opt/google/chrome/google-chrome ]]; then
  echo "Google Chrome already installed (.deb)."
  exit 0
fi
if [[ -x /var/lib/flatpak/exports/bin/com.google.Chrome ]] || flatpak info com.google.Chrome &>/dev/null; then
  echo "Google Chrome already installed (Flatpak)."
  ENV_FILE="$JARVIS_ROOT/data/jarvis.env"
  if [[ -x /var/lib/flatpak/exports/bin/com.google.Chrome ]]; then
    if grep -q '^export JARVIS_BROWSER_PATH=' "$ENV_FILE" 2>/dev/null; then
      sed -i 's|^export JARVIS_BROWSER_PATH=.*|export JARVIS_BROWSER_PATH="/var/lib/flatpak/exports/bin/com.google.Chrome"|' "$ENV_FILE"
    else
      printf '\nexport JARVIS_BROWSER_PATH="/var/lib/flatpak/exports/bin/com.google.Chrome"\n' >> "$ENV_FILE"
    fi
  fi
  exit 0
fi

echo "Downloading Google Chrome…"
curl -fsSL "$URL" -o "$DEB"

echo "Installing (sudo required)…"
if ! sudo apt-get install -y "$DEB"; then
  sudo dpkg -i "$DEB" || { echo "Install failed — run manually: sudo apt install $DEB"; exit 1; }
  sudo apt-get install -f -y
fi

ENV_FILE="$JARVIS_ROOT/data/jarvis.env"
if [[ -x /opt/google/chrome/google-chrome ]]; then
  if grep -q '^export JARVIS_BROWSER_PATH=' "$ENV_FILE" 2>/dev/null; then
    sed -i 's|^export JARVIS_BROWSER_PATH=.*|export JARVIS_BROWSER_PATH="/opt/google/chrome/google-chrome"|' "$ENV_FILE"
  else
    printf '\nexport JARVIS_BROWSER_PATH="/opt/google/chrome/google-chrome"\n' >> "$ENV_FILE"
  fi
  echo "Added JARVIS_BROWSER_PATH to data/jarvis.env"
fi

echo "Done. Restart Jarvis — it will open in Chrome, not Brave."
rm -f "$DEB"
