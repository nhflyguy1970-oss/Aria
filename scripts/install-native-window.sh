#!/usr/bin/env bash
# Native window deps for Jarvis (pywebview). Prefers pip/Qt (no sudo); falls back to apt/GTK.
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_ROOT"

if [[ -f "$JARVIS_ROOT/venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$JARVIS_ROOT/venv/bin/activate"
fi

echo "Installing Python packages (pywebview + Qt WebEngine)…"
pip install -q 'pywebview>=5.3' 'PyQt6>=6.6' PyQt6-WebEngine qtpy

if python - <<'PY'
from jarvis.native_window import is_available
import sys
sys.exit(0 if is_available() else 1)
PY
then
  echo "OK — native window backend ready (Qt)."
  exit 0
fi

echo ""
echo "Qt backend unavailable — trying GTK system packages (sudo may be required)…"

if command -v apt-get &>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y \
    python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
    libwebkit2gtk-4.1-0 libgtk-3-0 \
    libgirepository-2.0-dev libcairo2-dev pkg-config
elif command -v dnf &>/dev/null; then
  sudo dnf install -y python3-gobject gtk3 webkit2gtk4.1 gobject-introspection-devel
elif command -v pacman &>/dev/null; then
  sudo pacman -S --needed webkit2gtk-4.1 python-gobject gtk3
else
  echo "Install GTK3 + WebKit2GTK 4.1 for your distro, then re-run."
  exit 1
fi

echo "Optional: PyGObject in venv for GTK backend…"
pip install -q PyGObject || echo "(PyGObject pip install skipped — use system packages)"

python - <<'PY'
from jarvis.native_window import is_available, missing_dependency_hint
if is_available():
    print("OK — native window backend ready.")
else:
    print(missing_dependency_hint())
    raise SystemExit(1)
PY

echo ""
echo "Launch with:"
echo "  ./scripts/launch-jarvis-native.sh"
echo "Or install desktop shortcut:"
echo "  ./scripts/install-desktop-shortcuts.sh"
