#!/usr/bin/env bash
# System packages for the 14-phase system audit (SMART, sensors, GPU tools, etc.).
set -euo pipefail

JARVIS_ROOT="${JARVIS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

echo "Installing system audit dependencies…"
echo "Jarvis: $JARVIS_ROOT"
echo ""

sudo apt-get update -qq
sudo apt-get install -y \
  smartmontools \
  lm-sensors \
  mesa-utils \
  vulkan-tools \
  clinfo \
  deborphan \
  sysstat \
  mokutil \
  apparmor-utils

echo ""
echo "Optional: detect motherboard/GPU sensors (run once):"
echo "  sudo sensors-detect --auto"
echo ""
echo "Enable passwordless SMART for ARIA System tab:"
echo "  sudo ${JARVIS_ROOT}/scripts/install-audit-sudoers.sh"
echo ""
echo "Done."
