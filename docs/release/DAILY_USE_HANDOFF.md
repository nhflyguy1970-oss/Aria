# Daily Use Handoff

**Date:** 2026-07-09  
**Status:** Ready for primary daily use (compatibility mode)

## Current readiness

| Check | Status |
|-------|--------|
| Daily acceptance | 100% |
| Integration | 100% |
| Production readiness | ~99% |
| Platform cutover verified | Yes (`dual_write`, not enabled) |
| CI / GitHub Actions | Green |
| Global commands | `workstation`, `aria`, `aiplatform` in `~/.local/bin` |

## How to start using the workstation

### From anywhere (recommended)

```bash
workstation start          # morning — boots infra + Aria
workstation report         # health homepage
workstation acceptance     # full scorecard
workstation repair         # fix common issues
workstation stop           # evening
```

Or double-click **AI Workstation** on the desktop.

### Aria shortcuts

```bash
aria              # open chat (default)
aria --tray       # tray + background server
aria --status     # JSON status
```

### Platform CLI

```bash
aiplatform doctor
aiplatform applications list
```

## Known limitations

- First chat after cold boot may take ~30s while models load
- Optional components (LM Studio, n8n, Home Assistant) may show "needs configuration" — not required for daily AI work
- `workstation start` may print "NEEDS ATTENTION" while services are still warming — check `workstation report` or wait for phase `READY`
- Acceptance scores are **deferred during startup** (`STARTING`, `INITIALIZING`, `RECOVERING`) so you won't see misleading low scores mid-boot

## Recommended first-week usage

1. **Day 1:** `workstation start` → use Aria for real work → `workstation stop`
2. **Day 2:** Run `workstation backup` before any updates
3. **Day 3:** Run `workstation repair` once to verify self-healing
4. **Week 1:** Run `workstation acceptance` at end of week
5. **Optional:** `scripts/failure-inject-workstation.sh` after a backup (validates recovery)

## Recommended first backup

```bash
workstation backup
# → backups/workstation_YYYYMMDD_HHMMSS.tar.gz
```

Keep at least one backup before `workstation update` or any manual Docker changes.

## Platform-authoritative mode

**Remain in compatibility mode (`dual_write`).**

Cutover is verified and rollback works, but daily use should stay on legacy-authoritative data until you've used the workstation confidently for 1–2 weeks.

Check status:

```bash
curl -s http://127.0.0.1:8765/api/platform/cutover/verify | python3 -m json.tool
```

Enable only when you explicitly choose to (after backup):

```bash
curl -X POST http://127.0.0.1:8765/api/platform/cutover/enable
```

## Top ten improvements from polishing

1. **Global commands** — `workstation`, `aria`, `aiplatform` work from any directory (`~/.local/bin`)
2. **Workstation phases** — `STARTING` / `READY` / `RECOVERING` etc.; acceptance defers scores during transitions
3. **`workstation report`** — single health homepage (hardware, acceptance, git, memory, backups)
4. **Desktop entries use global commands** — survive without `cd` into repo; repair reinstalls shortcuts
5. **Repair auto-starts Aria** when stopped
6. **Backup/restore/update/recover/report** exposed through platform CLI (delegates to Aria)
7. **Acceptance no longer misleads during startup** — shows last known scores or "deferred"
8. **Status includes phase** — `workstation status` JSON has `phase` field
9. **Install runs global commands + desktop shortcuts** together
10. **Failure-injection script** expanded for operational hardening

## When something breaks

```bash
workstation repair
workstation doctor
workstation report
```

If repair doesn't fix it, check `docs/release/KNOWN_ISSUES.md` and `data/logs/`.

## Autonomous development stops here

Future improvements should come from Jeff's real-world usage friction, not planned engineering.
