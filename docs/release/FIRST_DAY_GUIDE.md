# First Day Guide — AI Workstation

This guide is for **daily use only**. No developer setup required.

## Start your workstation

**Easiest:** Double-click **AI Workstation** on the desktop.

**Or from a terminal:**

```bash
cd /media/jeff/AI/jarvis
./workstation start
```

Wait until Aria opens (tray icon and chat window). The morning greeting appears when services are healthy.

## Stop your workstation

**Easiest:** Right-click the Aria tray icon → **Quit**.

**Or:**

```bash
cd /media/jeff/AI/jarvis
./workstation stop
```

Docker services (database, Redis, etc.) keep running unless you stop them separately. That is normal — next start is faster.

## Check health

```bash
cd /media/jeff/AI/jarvis
./workstation acceptance
```

You want **Passed: YES** with daily-required at **100%**.

Quick check in Aria: open the GUI and ask *"Is anything broken?"* or run the daily briefing.

## Repair (when something is wrong)

```bash
cd /media/jeff/AI/jarvis
./workstation repair
```

This restarts Docker services, fixes LiteLLM routing, restarts Aria if it is down, and reruns acceptance.

If repair reports **human action required** (Claude login, Gemini auth), follow the one-line instruction shown.

## Update

```bash
cd /media/jeff/AI/jarvis
./workstation update
```

Pulls latest code, refreshes dependencies, and restarts Aria if it was running.

## Backup

```bash
cd /media/jeff/AI/jarvis
./workstation backup
```

Archive is saved under `backups/workstation_YYYYMMDD_HHMMSS.tar.gz` (includes your `data/` and platform state).

## Restore from backup

```bash
cd /media/jeff/AI/jarvis
./workstation stop
./workstation restore backups/workstation_YYYYMMDD_HHMMSS.tar.gz
./workstation start
```

## Platform memory mode

The workstation runs in **compatibility mode** (legacy data authoritative, platform mirrors writes). Do **not** enable platform-authoritative mode unless you have reviewed cutover status with acceptance passing.

Check cutover status (Aria must be running):

```bash
curl -s http://127.0.0.1:8765/api/platform/cutover | python3 -m json.tool
```

Look for `"ready": true` in the verification section. Cutover is verified but **not enabled** by default.

## When to ask for help

- Repair and acceptance both fail after a reboot
- Data loss or memory entries missing after an update
- Repeated Docker or disk errors in logs

Log location: `data/logs/`
