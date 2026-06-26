# ARIA GitHub backup

## One-time setup

1. Install [GitHub CLI](https://cli.github.com/) if needed.
2. Authenticate:

```bash
gh auth login
```

3. Create a private repo and push (from project root):

```bash
cd /media/jeff/AI/jarvis
gh repo create jarvis --private --source=. --push
```

If the repo name is taken, pick another name and set `origin` manually:

```bash
gh repo create my-jarvis-backup --private --source=. --remote=origin --push
```

## Regular backups

```bash
./scripts/backup-aria.sh
```

This stages `jarvis/`, `scripts/`, `tests/`, `main.py`, `.gitignore`, `docs/`, `assets/`, and `README.md`, commits if there are changes, and pushes to `origin`.

**Not committed:** `data/`, `.env`, `venv/`, logs, secrets.

## Verify auth

```bash
gh auth status
```
