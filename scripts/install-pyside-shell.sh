#!/usr/bin/env bash
# Install PySide6 desktop shell dependencies into the Jarvis venv.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/venv/bin/python"
[[ -x "$PY" ]] || PY=python3

"$PY" -m pip install -U PySide6 PySide6-Addons
if [[ "${JARVIS_INSTALL_FLUENT:-1}" != "0" ]]; then
  "$PY" -m pip install -U PySide6-Fluent-Widgets 2>/dev/null || echo "Optional: PySide6-Fluent-Widgets install failed (Fusion theme still works)"
fi

if command -v dpkg >/dev/null; then
  missing=()
  dpkg -s libxcb-cursor0 >/dev/null 2>&1 || missing+=(libxcb-cursor0)
  dpkg -s libayatana-appindicator3-1 >/dev/null 2>&1 || missing+=(libayatana-appindicator3-1)
  if ((${#missing[@]})); then
    echo "Also install system packages: sudo apt install ${missing[*]}"
  fi
fi

echo "Done. Test: JARVIS_GUI_MODE=fluent ./scripts/launch-jarvis.sh"
