#!/usr/bin/env bash
# Restore workstation from backup-workstation.sh archive.
set -euo pipefail

ARCHIVE="${1:-}"
if [[ -z "$ARCHIVE" || ! -f "$ARCHIVE" ]]; then
  echo "Usage: $0 /path/to/workstation_YYYYMMDD_HHMMSS.tar.gz"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AI_ROOT="${AI_ROOT:-$(dirname "$(dirname "$ROOT")")}"
STAMP="$(date +%Y%m%d_%H%M%S)"
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT

tar -xzf "$ARCHIVE" -C "$STAGING"

if [[ -d "$STAGING/jarvis/data" ]]; then
  if [[ -d "$ROOT/data" ]]; then
    mv "$ROOT/data" "$ROOT/data.bak.${STAMP}"
    echo "Previous jarvis data → data.bak.${STAMP}"
  fi
  cp -a "$STAGING/jarvis/data" "$ROOT/data"
  echo "Restored jarvis data/"
fi

if [[ -d "$STAGING/platform/Data" ]]; then
  mkdir -p "$AI_ROOT"
  if [[ -d "${AI_ROOT}/Data" ]]; then
    mv "${AI_ROOT}/Data" "${AI_ROOT}/Data.bak.${STAMP}"
    echo "Previous platform Data → Data.bak.${STAMP}"
  fi
  cp -a "$STAGING/platform/Data" "${AI_ROOT}/Data"
  echo "Restored platform Data/"
fi

if [[ -d "$STAGING/platform/compose" ]]; then
  mkdir -p "$AI_ROOT"
  cp -a "$STAGING/platform/compose" "${AI_ROOT}/compose"
  echo "Restored platform compose/"
fi

if [[ -d "$STAGING/platform/applications" ]]; then
  mkdir -p "$AI_ROOT"
  cp -a "$STAGING/platform/applications" "${AI_ROOT}/applications"
  echo "Restored platform applications/"
fi

echo "Restore complete from $ARCHIVE"
