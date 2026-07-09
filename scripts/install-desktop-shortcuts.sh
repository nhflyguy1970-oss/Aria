#!/usr/bin/env bash
# Install exactly three desktop launchers: AI Platform, Aria, Aria (Uncensored).
set -euo pipefail

JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=_jarvis-launch-lib.sh
source "$JARVIS_ROOT/scripts/_jarvis-launch-lib.sh"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"

# Stable launcher IDs (filename without .desktop).
CANONICAL_IDS=(ai-platform aria aria-uncensored)

# Obsolete launchers removed on every install/repair (prevents duplicates).
STALE_IDS=(
  ai-workstation
  ai-workstation-start
  ai-workstation-stop
  ai-workstation-status
  ai-workstation-doctor
  ai-workstation-repair
  ai-workstation-acceptance
  aria-pyside
  aria-app
  aria-native
  jarvis
  jarvis-uncensored
  jarvis-app
  jarvis-native
)

chmod +x "$JARVIS_ROOT/scripts/desktop-launch-platform.sh"
chmod +x "$JARVIS_ROOT/scripts/desktop-launch-workstation.sh"
chmod +x "$JARVIS_ROOT/scripts/launch-jarvis.sh"
chmod +x "$JARVIS_ROOT/scripts/launch-jarvis-uncensored.sh"
chmod +x "$JARVIS_ROOT/workstation"

mkdir -p "$APPS_DIR"

_remove_stale_from_dir() {
  local dir="$1"
  [[ -d "$dir" ]] || return 0
  local id
  for id in "${STALE_IDS[@]}"; do
    rm -f "$dir/${id}.desktop"
  done
  rm -f "$dir"/ai-workstation*.desktop 2>/dev/null || true
}

_install_canonical_to_dir() {
  local dir="$1"
  local mark_trusted="${2:-0}"
  [[ -d "$dir" ]] || return 0
  local id src dest
  for id in "${CANONICAL_IDS[@]}"; do
    src="$JARVIS_ROOT/desktop/${id}.desktop"
    [[ -f "$src" ]] || { echo "Missing desktop template: $src" >&2; exit 1; }
    dest="$dir/${id}.desktop"
    sed "s|@JARVIS_ROOT@|$JARVIS_ROOT|g; s|@HOME@|$HOME|g" "$src" >"$dest"
    chmod +x "$dest"
    if [[ "$mark_trusted" == "1" ]]; then
      gio set "$dest" metadata::trusted true 2>/dev/null || true
    fi
  done
}

_refresh_launcher_cache() {
  if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
  fi
}

# Repair path: clean stale entries before reinstalling (never accumulate duplicates).
_remove_stale_from_dir "$APPS_DIR"
_remove_stale_from_dir "$DESKTOP_DIR"

_install_canonical_to_dir "$APPS_DIR" 0
_install_canonical_to_dir "$DESKTOP_DIR" 1

_refresh_launcher_cache

echo "Installed launchers (app menu + desktop):"
for id in "${CANONICAL_IDS[@]}"; do
  echo "  ${id}.desktop"
done
if [[ -d "$DESKTOP_DIR" ]]; then
  echo "Desktop:"
  ls "$DESKTOP_DIR"/ai-platform.desktop "$DESKTOP_DIR"/aria.desktop "$DESKTOP_DIR"/aria-uncensored.desktop 2>/dev/null | sed 's|^|  |'
fi
