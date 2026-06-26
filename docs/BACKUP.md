# ARIA backup

ARIA does **not** auto-backup source code. Chat exports and the sidebar **Backup** button save conversation/data — not your Python tree.

## What to back up

| What | How |
|------|-----|
| Source code | `git commit` + push to GitHub |
| Chat / memory / journal | `data/` (excluded from git by design) |
| Upgrade snapshots | Created only during the upgrade wizard |

## One-command backup (source)

```bash
chmod +x scripts/backup-aria.sh
./scripts/backup-aria.sh
```

## First-time GitHub setup

```bash
gh auth login
gh repo create jarvis --private --source=. --remote=origin --push
```

## Habit

Run `./scripts/backup-aria.sh` after meaningful changes, or at least daily.

## Recovery notes

- **Jun 2026:** Source was recovered from `.pyc` via pycdc and Cursor checkpoint `aa000cf`.
- Decompiled files may be incomplete; prefer git history once pushed.
- Life UI lives in `jarvis/gui/static/` (not in bytecode).
