#!/usr/bin/env bash
# Restore data/ from a jarvis_data_*.tar.gz backup.
set -euo pipefail
ARCHIVE="${1:-}"
if [[ -z "$ARCHIVE" || ! -f "$ARCHIVE" ]]; then
  echo "Usage: $0 /path/to/jarvis_data_YYYYMMDD_HHMMSS.tar.gz"
  exit 1
fi
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP=$(date +%Y%m%d_%H%M%S)
if [[ -d "${JARVIS_ROOT}/data" ]]; then
  mv "${JARVIS_ROOT}/data" "${JARVIS_ROOT}/data.bak.${STAMP}"
  echo "Previous data moved to data.bak.${STAMP}"
fi
tar -xzf "$ARCHIVE" -C "$JARVIS_ROOT"
echo "Restored data/ from $ARCHIVE"
