#!/usr/bin/env bash
# Rust toolchain (rustup) — no sudo; installs to ~/.cargo/bin
set -euo pipefail

export PATH="${HOME}/.cargo/bin:${PATH}"

if command -v cargo >/dev/null 2>&1 && command -v rustc >/dev/null 2>&1; then
  echo "Rust already installed:"
  cargo --version
  rustc --version
  exit 0
fi

echo "Installing Rust via rustup → ${HOME}/.cargo/bin …"
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable

# shellcheck disable=SC1091
[[ -f "${HOME}/.cargo/env" ]] && source "${HOME}/.cargo/env"
export PATH="${HOME}/.cargo/bin:${PATH}"

echo ""
cargo --version
rustc --version
echo "Done. Open a new terminal or: source ~/.cargo/env"
