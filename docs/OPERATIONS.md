# Operations Guide

Day-to-day operations for the Aria AI Workstation.

## Daily use

```bash
./workstation start          # morning
./scripts/jarvis-ctl.sh open # focus window
./workstation stop           # evening (optional — tray can stay running)
```

## Monitoring

```bash
./scripts/jarvis-ctl.sh status --full
./workstation diagnose
./workstation list
```

Morning briefing and "anything broken?" are available in the GUI and daily workflow actions.

Prometheus/Grafana are optional registry components — start via `./workstation up` when docker profiles are configured.

## Self-healing

Automatic recovery runs every 5 minutes when `JARVIS_AUTO_RECOVER=1` (default):

- Restarts Ollama, ComfyUI, docker services in `SAFE_RESTART`
- Restarts Aria HTTP server when offline (`server_restart`)
- Nightly maintenance: knowledge sync, diagnose, recover

Optional: `JARVIS_AUTO_RECOVER_OPTIONAL=1` includes postgres, redis, litellm, etc.

Manual recovery:

```bash
./workstation recover
```

## Backup and restore

```bash
./workstation backup
# → backups/workstation_YYYYMMDD_HHMMSS.tar.gz

./workstation stop
./workstation restore backups/workstation_YYYYMMDD_HHMMSS.tar.gz
./workstation start
```

Includes `data/` and platform `Data/`, `compose/`, `applications/` when `AI_ROOT` is set.

Source code backup: `./scripts/backup-aria.sh` (git push).

## Updates

```bash
./workstation update
```

Pulls git, refreshes pip/uv deps, restarts server if running.

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Server down | `./workstation recover` or `./workstation start` |
| Ollama missing models | `./scripts/pull-models.sh` |
| Low VRAM | Ask Aria to unload models, or set `JARVIS_VRAM_GUARD=1` |
| Platform attachment warnings | `./workstation doctor` |
| Cutover blocked | See [PLATFORM_CUTOVER.md](PLATFORM_CUTOVER.md) |
| CI-style local check | `./scripts/ci_check.py all` |

## Logs

- Server: `data/logs/serve.log` (when tray-managed)
- Automation: `data/automation/last_maintenance.json`
- Platform cutover: `data/platform/cutover.json`

## Recovery drill

1. `./workstation backup`
2. `./workstation stop`
3. Simulate failure (stop ollama, rename data dir)
4. `./workstation restore <archive>`
5. `./workstation verify && ./workstation start`
