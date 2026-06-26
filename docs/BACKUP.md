# ARIA GitHub backup

## One-time setup

1. Install [GitHub CLI](https://cli.github.com/) if needed.
2. Authenticate:

```bash
gh auth login
```

3. Point `origin` at the ARIA repo and push (from project root):

```bash
cd /media/jeff/AI/jarvis
git remote add origin https://github.com/nhflyguy1970-oss/Aria.git
# or, if origin already exists:
# git remote set-url origin https://github.com/nhflyguy1970-oss/Aria.git
git push -u origin main
```

If you need to create the repo first (empty GitHub account):

```bash
gh repo create nhflyguy1970-oss/Aria --private --source=. --remote=origin --push
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
