# Mission Control — Root Cause & Fix (Release Blocker)

**Date:** 2026-07-09

## Measured Startup Sequence (Before Fix)

```
AI Platform desktop icon
  → scripts/desktop-launch-platform.sh
  → workstation start                    (AI Platform bootstrap)
  → launch_application("aria")         (auto-started Aria server)
  → jarvis.gui_launcher
  → http://127.0.0.1:8765/?app=1#workstation   (ARIA GUI, not platform)
```

### What We Measured

| Check | Result |
|-------|--------|
| Port 8765 responding | Yes — Aria `main.py serve` (started Jul 8) |
| `/api/mission-control` on 8765 | **404 Not Found** — running server predates routes |
| Mission Control HTML in Aria index | Present in disk, but tab buried inside Aria chrome |
| Port 8780 (platform) | **Not listening** — no platform-owned server existed |
| Mission Control independent GUI | **Did not exist** |

## Root Cause

1. **Wrong ownership** — Mission Control was implemented as a tab inside Aria's GUI (`jarvis/gui/static/mission_control.js`), not as an AI Platform console.
2. **Wrong launcher target** — `desktop-launch-platform.sh` opened Aria at `#workstation` on port 8765.
3. **Stale Aria process** — Long-running server never restarted after Mission Control API was added, so even the embedded tab's API returned 404.

Mission Control was **embedded in Aria**, **not started by AI Platform**, and **not reachable** on double-click.

## Fix (After)

```
AI Platform desktop icon
  → scripts/desktop-launch-platform.sh
  → workstation start --console --no-app
      → bootstrap infrastructure
      → discover & attach applications (ApplicationHost)
      → ensure_running Mission Control server (port 8780)
  → curl /api/health (wait)
  → jarvis.gui_launcher http://127.0.0.1:8780/
```

### Verified (Measured)

```bash
curl http://127.0.0.1:8780/api/health
# {"ok": true, "service": "mission-control"}

curl http://127.0.0.1:8780/api/mission-control
# title: AI Platform Mission Control
# owner: aiplatform
# apps: aria, aria-uncensored, flytying, housefly
# status: healthy
```

## Architecture

| Component | Owner | Port |
|-----------|-------|------|
| Mission Control UI + API | **AI Platform** (`aiplatform/mission_control/`) | 8780 |
| Aria chat GUI | Aria (`jarvis`) | 8765 |
| Aria status commands | Delegate to platform Mission Control API/data |

Aria `jarvis/mission_control.py` now **delegates** to `aiplatform.mission_control.aggregator`.

Launch Aria from Mission Control → `POST /api/applications/aria/launch` → `scripts/launch-jarvis.sh`

## Files

**AI Platform (source of truth):**
- `aiplatform/mission_control/aggregator.py`
- `aiplatform/mission_control/server.py`
- `aiplatform/mission_control/static/`

**Launcher:**
- `jarvis/scripts/desktop-launch-platform.sh`

**Workstation CLI:**
- `workstation start --console --no-app`
