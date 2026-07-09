# Operations Checklist

Use before declaring the workstation ready for daily use, and monthly thereafter.

## Daily (automated)

- [ ] `JARVIS_AUTO_RECOVER=1` (default) — self-healing every 5 minutes
- [ ] Aria tray running after login (optional: add AI Workstation to startup applications)

## Weekly

- [ ] `./workstation acceptance` → **Passed: YES**, daily-required **≥ 95%**
- [ ] `./workstation backup` — confirm archive under `backups/`
- [ ] `git pull` in `jarvis` and `AI-Platform` if using `./workstation update`

## After updates or power loss

- [ ] `./workstation start` or double-click **AI Workstation**
- [ ] `./workstation repair` if anything looks off
- [ ] `./workstation acceptance`

## Cutover (platform memory) — do not enable until checklist complete

- [ ] `curl -X POST http://127.0.0.1:8765/api/platform/cutover/verify` → `"ready": true`
- [ ] Memory backfill: 447/447 verified
- [ ] Semantic vectors: 1691 mirrored to application index
- [ ] Rollback tested: `POST /api/platform/cutover/rollback` → still `"ready": true`
- [ ] **Only then** consider `POST /api/platform/cutover/enable` (irreversible without rollback)

## Failure recovery drill (quarterly)

- [ ] `./scripts/failure-inject-workstation.sh` — all critical injections pass
- [ ] `./scripts/e2e-validate-workstation.sh` — 14/14 pass
- [ ] Restore test: backup → stop → restore → start → acceptance

## CI / release

- [ ] `./scripts/ci-local.sh` in `jarvis` and `AI-Platform`
- [ ] GitHub Actions green on `main`
