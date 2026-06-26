#!/usr/bin/env bash
set -euo pipefail
JARVIS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${JARVIS_ROOT}/backups"
STAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE="${BACKUP_DIR}/jarvis_data_${STAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"
tar -czf "$ARCHIVE" -C "$JARVIS_ROOT" data/
echo "Backup saved: $ARCHIVE"
