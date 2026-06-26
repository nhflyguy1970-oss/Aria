#!/usr/bin/env bash
# Sound Blaster AE-5 Plus — quick EQ / mic presets via ALSA (amixer).
# Usage: ./scripts/apply-creative-eq.sh [voice|music|flat|status]
set -euo pipefail

CARD="${JARVIS_ALSA_CARD:-Creative}"
PRESET="${1:-status}"

_run() {
  amixer -c "$CARD" "$@" 2>/dev/null || true
}

case "$PRESET" in
  voice)
    echo "AE-5 voice preset (mic boost + playback level)"
    _run sset "Mic Boost" 75%
    _run sset "Capture" 100%
    _run sset "Master" 85%
    _run sset "PCM" 85%
  ;;
  music)
    echo "AE-5 music preset (line-friendly levels)"
    _run sset "Mic Boost" 0%
    _run sset "Master" 90%
    _run sset "PCM" 90%
    _run sset "Front" 90%
  ;;
  flat)
    echo "AE-5 flat / unity"
    _run sset "Mic Boost" 0%
    _run sset "Master" 100%
    _run sset "PCM" 100%
  ;;
  status|*)
    echo "Card: $CARD"
    _run sget "Master" | head -5
    _run sget "PCM" | head -5
    _run sget "Mic Boost" | head -5
    _run sget "Capture" | head -5
    echo ""
    echo "Presets: voice | music | flat"
    echo "Set JARVIS_ALSA_CARD=Creative in data/jarvis.env"
  ;;
esac
