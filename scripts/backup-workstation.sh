#!/usr/bin/env bash
# Backup Jarvis data and optional AI-Platform state into a single archive.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${JARVIS_BACKUP_DIR:-$ROOT/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE="${BACKUP_DIR}/workstation_${STAMP}.tar.gz"
AI_ROOT="${AI_ROOT:-$(dirname "$(dirname "$ROOT")")}"

mkdir -p "$BACKUP_DIR"
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT

mkdir -p "$STAGING/jarvis"
if [[ -d "$ROOT/data" ]]; then
  cp -a "$ROOT/data" "$STAGING/jarvis/"
fi
printf 'jarvis_root=%s\nai_root=%s\nstamp=%s\n' "$ROOT" "$AI_ROOT" "$STAMP" >"$STAGING/MANIFEST.txt"

if [[ -d "${AI_ROOT}/Data" || -d "${AI_ROOT}/compose" || -d "${AI_ROOT}/applications" ]]; then
  mkdir -p "$STAGING/platform"
  [[ -d "${AI_ROOT}/Data" ]] && cp -a "${AI_ROOT}/Data" "$STAGING/platform/"
  [[ -d "${AI_ROOT}/compose" ]] && cp -a "${AI_ROOT}/compose" "$STAGING/platform/"
  [[ -d "${AI_ROOT}/applications" ]] && cp -a "${AI_ROOT}/applications" "$STAGING/platform/"
fi

tar -czf "$ARCHIVE" -C "$STAGING" .
echo "Backup saved: $ARCHIVE"
