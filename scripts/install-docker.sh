#!/usr/bin/env bash
# Install Docker Engine + compose plugin (for MongoDB stacks, etc.).
set -euo pipefail

JARVIS_ROOT="${JARVIS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo "Docker already running: $(docker --version)"
  exit 0
fi

echo "Installing Docker…"
sudo apt-get update -qq
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
fi
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${VERSION_CODENAME:-$UBUNTU_CODENAME}") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER" 2>/dev/null || true
echo ""
echo "Docker installed. Log out/in (or: newgrp docker) then: docker info"
echo "Jarvis: $JARVIS_ROOT"
