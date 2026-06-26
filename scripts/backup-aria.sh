#!/usr/bin/env bash
# Backup ARIA source to git remote (private GitHub repo).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAMP="$(date -u +"%Y-%m-%d %H:%M UTC")"
MSG="Backup: ${STAMP}"

git add jarvis/ scripts/ tests/ main.py .gitignore docs/ assets/ README.md 2>/dev/null || true

if git diff --cached --quiet; then
  echo "No staged changes to commit."
else
  git commit -m "$MSG"
  echo "Committed: $MSG"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git push origin HEAD
  echo "Pushed to $(git remote get-url origin)"
else
  echo "No git remote 'origin'. Run: gh repo create jarvis --private --source=. --push"
  exit 1
fi
