#!/usr/bin/env bash
# Backup ARIA source to GitHub (nhflyguy1970-oss/Aria).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

die() { echo "backup-aria: $*" >&2; exit 1; }

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not a git repository: $ROOT"

if ! git remote get-url origin >/dev/null 2>&1; then
  die "no origin remote — run: git remote add origin https://github.com/nhflyguy1970-oss/Aria.git"
fi

if ! command -v gh >/dev/null; then
  die "GitHub CLI (gh) not installed"
fi
if ! gh auth status >/dev/null 2>&1; then
  die "not logged in — run: gh auth login && gh auth setup-git"
fi

BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || die "detached HEAD — checkout main first"

STAMP="$(date -u +"%Y-%m-%d %H:%M UTC")"
MSG="${1:-Backup: ${STAMP}}"

# Stage source only — never data/, secrets, venv, or editor caches.
git add -A
git reset HEAD -- data/ venv/ .venv/ .env .env.local jarvis.log .aider.chat.history.md .aider.input.history .aider.tags.cache.v4/ 2>/dev/null || true

if ! git diff --cached --quiet; then
  git commit -m "$MSG"
  echo "Committed: $(git log -1 --oneline)"
else
  echo "No changes to commit."
fi

git push -u origin "$BRANCH"
echo "Pushed $(git rev-parse --short HEAD) to $(git remote get-url origin) ($BRANCH)"
