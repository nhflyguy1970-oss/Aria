#!/usr/bin/env bash
# Start Home Assistant in Docker (local Jarvis integration).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${JARVIS_HA_CONTAINER:-homeassistant}"
IMAGE="${JARVIS_HA_IMAGE:-ghcr.io/home-assistant/home-assistant:stable}"
CONFIG_DIR="${JARVIS_HA_CONFIG:-$HOME/homeassistant}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker, then re-run this script."
  exit 1
fi

mkdir -p "$CONFIG_DIR"

if docker ps --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "Home Assistant container '$NAME' is already running."
  echo "Open: http://127.0.0.1:8123"
  exit 0
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "Starting existing container '$NAME'…"
  docker start "$NAME" >/dev/null
else
  echo "Creating Home Assistant container '$NAME'…"
  docker run -d \
    --name "$NAME" \
    --restart=unless-stopped \
    --network=host \
    -v "$CONFIG_DIR:/config" \
    "$IMAGE" >/dev/null
fi

echo ""
echo "Home Assistant starting (first boot can take a few minutes)."
echo "Open: http://127.0.0.1:8123"
echo ""
echo "Then in Jarvis sidebar → Smart home:"
echo "  1. Paste long-lived token from HA → Profile → Security"
echo "  2. Test connection → Save"
echo ""
echo "Or run: ./scripts/enable-home-assistant.sh"
