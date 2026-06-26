#!/usr/bin/env bash
# Install AE-5 VST bridge dependencies + PipeWire live EQ filter configs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${ROOT}/venv/bin/python"

echo "Jarvis AE-5 VST bridge"
echo "======================"
echo ""

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Installing ffmpeg (required for software EQ chains)…"
  sudo apt install -y ffmpeg
fi

echo "Optional: VST3 plugin support via Spotify pedalboard"
if [[ -x "$VENV" ]]; then
  "$VENV" -m pip install -q 'pedalboard>=0.9.0' || echo "  (pedalboard install failed — software EQ still works)"
else
  echo "  Run from project venv: pip install pedalboard"
fi

echo ""
echo "Installing PipeWire live EQ filter configs…"
"$VENV" - <<'PY'
from jarvis.audio_vst_live import install_filter_configs
ok, msg = install_filter_configs()
print(msg)
if not ok:
    raise SystemExit(1)
PY

echo ""
echo "Done."
echo ""
echo "Usage:"
echo "  • Audio tab → VST bridge: pick playback chain + live EQ"
echo "  • Chat: 'apply voice eq to the audio' or 'enable live scout eq'"
echo "  • Optional VST3: export JARVIS_VST_PLUGIN_PATH=/path/to/Plugin.vst3"
echo ""
echo "After first install, restart PipeWire once:"
echo "  systemctl --user restart pipewire pipewire-pulse wireplumber"
