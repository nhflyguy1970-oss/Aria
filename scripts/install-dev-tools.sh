#!/usr/bin/env bash
# Dev tools for Phase 9 audit (build-essential, cmake, git, Java, Node, Rust).
set -euo pipefail

JARVIS_ROOT="${JARVIS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
export PATH="${HOME}/.cargo/bin:${PATH}"

echo "Installing development tools…"
echo "Jarvis: $JARVIS_ROOT"
echo ""

sudo apt-get update -qq
sudo apt-get install -y \
  build-essential \
  cmake \
  git \
  default-jdk-headless

if ! command -v node >/dev/null 2>&1; then
  echo "Installing Node.js LTS (NodeSource)…"
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

bash "${JARVIS_ROOT}/scripts/install-rust.sh"

echo ""
echo "Verify:"
command -v gcc && gcc --version | head -1
command -v cmake && cmake --version | head -1
command -v git && git --version
command -v node && node --version || echo "node: still missing"
command -v npm && npm --version || echo "npm: still missing"
command -v cargo && cargo --version || echo "cargo: still missing"
command -v rustc && rustc --version || echo "rustc: still missing"
command -v java && java -version 2>&1 | head -1 || echo "java: still missing"
echo ""
echo "Done. Re-run System audit in ARIA."
