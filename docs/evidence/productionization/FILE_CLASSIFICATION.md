# Productionization file classification

Recorded before commit. Nothing was reset, cleaned, or discarded.

## A. Intended Aria production repairs (COMMIT)

- All currently modified tracked files under `jarvis/`, `aria_acm/`, `aria_core/`, `tests/`, `scripts/`, `requirements.txt`
- New production modules: `jarvis/security/owner/`, `jarvis/health_product/`, `jarvis/integrity_product/`, `jarvis/repair_product/`, `jarvis/certification_product/`, `jarvis/gui/static/workspace/`, owner/session daily-use, launch ownership
- Launch path: `scripts/aria-serve.sh`, `scripts/install-systemd-user.sh`, `scripts/launch-jarvis.sh`, `scripts/_jarvis-launch-lib.sh`, `scripts/restart-jarvis-server.sh`, `jarvis/daemon.py`, `jarvis/server_restart.py`, `jarvis/launch_ownership.py`

## B. Certification evidence (COMMIT)

- `docs/ARIA_*.md` including 34-room and live-instance verification
- `docs/evidence/`, `docs/architecture/`, operational certification docs
- `.cursor/rules/` engineering law

## C. Temporary test artifacts (DO NOT COMMIT)

- `00000.log`
- `result.json`
- `jarvis/__init__.py.bak.*`

## D. Generated caches/bytecode (gitignored / DO NOT COMMIT)

- `__pycache__/`, `*.pyc`, `venv/`, `.pytest_cache/`

## E. Personal/local files (DO NOT COMMIT)

- `cooling_tower_chimney.scad`, `cooling_tower_chimney_freecad.py`
- `design/chat_room_v1/` mockups (not the certified house)

## F. Secrets / credentials (DO NOT COMMIT)

- `data/` (already gitignored) including `jarvis.env` and Owner Vault
- No live credential values found in intended commit paths (scan: only test placeholders and env *names*)
