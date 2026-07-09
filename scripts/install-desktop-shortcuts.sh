#!/usr/bin/env bash
# Install ARIA .desktop entries (app menu + optional Desktop icon).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"
PY="$(jarvis_python)"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"

# Desktop: platform mode installs AI Workstation; standalone Aria installs Aria only.
if "$PY" -c "import aiplatform.workstation" 2>/dev/null; then
  DESKTOP_SHORTCUTS="${JARVIS_DESKTOP_SHORTCUTS:-ai-workstation}"
else
  DESKTOP_SHORTCUTS="${JARVIS_DESKTOP_SHORTCUTS:-aria}"
fi

chmod +x "$JARVIS_ROOT/scripts/desktop-launch-workstation.sh"
chmod +x "$JARVIS_ROOT/scripts/launch-jarvis.sh"
chmod +x "$JARVIS_ROOT/scripts/launch-jarvis-pyside.sh"
chmod +x "$JARVIS_ROOT/scripts/launch-jarvis-uncensored.sh"
chmod +x "$JARVIS_ROOT/scripts/launch-jarvis-app.sh"
chmod +x "$JARVIS_ROOT/scripts/launch-jarvis-native.sh"
chmod +x "$JARVIS_ROOT/scripts/workstation-gui.sh"
chmod +x "$JARVIS_ROOT/workstation"

mkdir -p "$APPS_DIR"

# App menu entries
APP_MENU_VARIANTS=(
  ai-workstation
  ai-workstation-start
  ai-workstation-stop
  ai-workstation-status
  ai-workstation-doctor
  ai-workstation-repair
  ai-workstation-acceptance
  aria
  aria-pyside
  aria-uncensored
)
LEGACY_VARIANTS=(jarvis jarvis-uncensored jarvis-app jarvis-native aria-app aria-native)

for variant in "${APP_MENU_VARIANTS[@]}"; do
  src="$JARVIS_ROOT/desktop/$variant.desktop"
  [[ -f "$src" ]] || continue
  sed "s|@JARVIS_ROOT@|$JARVIS_ROOT|g; s|@HOME@|$HOME|g" "$src" > "$APPS_DIR/$variant.desktop"
  chmod +x "$APPS_DIR/$variant.desktop"
done

# Remove legacy Jarvis shortcuts from app menu and desktop
for variant in "${LEGACY_VARIANTS[@]}"; do
  rm -f "$APPS_DIR/${variant}.desktop"
done

if [[ -d "$DESKTOP_DIR" ]]; then
  for variant in "${LEGACY_VARIANTS[@]}"; do
    rm -f "$DESKTOP_DIR/${variant}.desktop"
  done
fi

# Desktop icons
if [[ -d "$DESKTOP_DIR" ]]; then
  if [[ "$DESKTOP_SHORTCUTS" == "all" ]]; then
    DESKTOP_LIST=(ai-workstation aria aria-uncensored)
  else
    IFS=',' read -ra DESKTOP_LIST <<< "$DESKTOP_SHORTCUTS"
  fi
  for variant in "${DESKTOP_LIST[@]}"; do
    variant="${variant// /}"
    [[ -n "$variant" ]] || continue
    src="$JARVIS_ROOT/desktop/$variant.desktop"
    [[ -f "$src" ]] || { echo "Skip unknown desktop shortcut: $variant" >&2; continue; }
    sed "s|@JARVIS_ROOT@|$JARVIS_ROOT|g; s|@HOME@|$HOME|g" "$src" > "$DESKTOP_DIR/$variant.desktop"
    chmod +x "$DESKTOP_DIR/$variant.desktop"
    gio set "$DESKTOP_DIR/$variant.desktop" metadata::trusted true 2>/dev/null || true
  done
fi

echo "Installed app menu:"
for variant in "${APP_MENU_VARIANTS[@]}"; do
  echo "  $APPS_DIR/$variant.desktop"
done
if [[ -d "$DESKTOP_DIR" ]]; then
  echo "Desktop icons:"
  ls "$DESKTOP_DIR"/ai-workstation*.desktop "$DESKTOP_DIR"/aria*.desktop 2>/dev/null | sed 's|^|  |' || echo "  (none)"
fi
