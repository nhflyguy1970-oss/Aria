#!/usr/bin/env bash
# Commit and push ARIA source to git (real backup — not chat/data export).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $ROOT" >&2
  exit 1
fi

MSG="${1:-Backup ARIA $(date -Iseconds)}"
git add -A
git reset HEAD data/ venv/ .env .env.* 2>/dev/null || true

if git diff --quiet HEAD && git diff --cached --quiet; then
  echo "Nothing to commit."
else
  git commit -m "$MSG"
  echo "Committed: $(git log -1 --oneline)"
fi

if git remote get-url origin >/dev/null 2>&1; then
  if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    git push origin "$(git branch --show-current)"
    echo "Pushed to origin."
  else
    echo "Remote exists but gh not authenticated — run: gh auth login && git push"
  fi
else
  echo "No origin remote. After gh auth login:"
  echo "  gh repo create jarvis --private --source=. --push"
fi
