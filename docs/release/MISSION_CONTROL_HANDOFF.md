# Mission Control Handoff

**Date:** 2026-07-09  
**Phase:** Daily Use / Release Candidate  
**Status:** Mission Control operational console shipped in Aria GUI

---

## What Was Improved

### Operational console (not chatbot)

The **Workstation** tab is now **Mission Control** — a 12-section operational dashboard modeled after Docker Desktop / Portainer / Home Assistant:

| Tab | Purpose |
|-----|---------|
| Overview | Platform status, phase, acceptance, providers, hardware, attention items |
| Applications | Aria + Aria (Uncensored) + future attached apps |
| Inference | Provider, model, loaded/active models, gateway state |
| Memory | Namespaces, entry counts, recent memories, cutover status |
| Knowledge | Retrieval provider, document counts, sources |
| Databases | Redis, MongoDB, PostgreSQL, Qdrant + all services |
| Hardware | CPU load, RAM, swap, GPU/VRAM, disk |
| Jobs | Media/coding queues, recent job activity |
| Activity | Filterable execution timeline with CSV export |
| Performance | Historical metric samples (acceptance, RAM, VRAM, jobs) |
| Settings | Runtime configuration snapshot |
| Recovery | Repair, acceptance, health, backups, known issues |

### Source of truth

- **`jarvis/mission_control.py`** aggregates all operational data.
- **`GET /api/mission-control`** — full snapshot.
- **`GET /api/mission-control/{tab}`** — single section.
- **`GET /api/mission-control/activity/export`** — CSV export.
- **`/api/workstation/dashboard`** delegates to Mission Control (backward compatible).

### Aria integration

- Chat commands (`status`, `health`, `services`, `models`, etc.) and runtime introspection now read from Mission Control — no duplicated logic.
- `format_status_summary()` and operations `_status_summary()` use `format_overview_markdown()`.

### Notifications

- **`jarvis/platform_notifications.py`** — ring buffer + JSONL persistence.
- Startup emits: *"AI Platform started — Mission Control is online"*.
- Designed for concise operational alerts (not chat spam).

### Performance sampling

- **`jarvis/platform_metrics.py`** — throttled samples (30s interval, max 120) stored at `data/automation/platform_metrics.json`.

### Activity timeline

- Reuses **`jarvis/workstation_activity.py`** with startup, user request, and router events.
- Activity tab: search, component filter, CSV export.

### Desktop launcher

- **AI Platform** desktop entry opens `/?app=1#workstation` (Mission Control tab).

### Tests & CI

- **`tests/test_mission_control.py`** — shape, tabs, applications, CSV export, notifications.
- Updated **`tests/test_workstation_polish.py`** for new payload shape.
- CI paths updated in **`scripts/ci_check.py`**.

---

## What Remains (Known Gaps)

These are intentional deferrals for real-world usage feedback — not blockers for daily use.

| Area | Gap |
|------|-----|
| Activity instrumentation | Partial — startup, user_request, router_decision. Missing: inference start/complete, memory lookup, knowledge lookup, tool selection, repair/backup/git sync events |
| Performance graphs | Table-only samples; no chart library / time-series UI yet |
| Application lifecycle | Launch buttons wired; Stop/Restart/Logs per-app not fully implemented |
| Inference actions | Load/Unload/Warm/Benchmark/Switch preferred model — display only |
| Memory actions | Browse/Search/Delete/Merge/Export/Reindex — display only |
| Database actions | Repair/Restart buttons not wired from Mission Control |
| Temperature / power | Hardware tab shows CPU/RAM/GPU/disk; sensors not integrated |
| `#mission-control` hash | Uses existing `#workstation` hash (launcher already correct) |

---

## Suggested Future Enhancements (Usage-Driven Only)

1. **Instrument more activity events** as Jeff notices blind spots (e.g. "what happened overnight?").
2. **Add lightweight charts** to Performance tab once sample history accumulates (7+ days).
3. **Wire inference load/unload** when model switching becomes a daily friction point.
4. **Per-application log viewer** when managing multiple attached applications.
5. **Push notifications** (desktop/tray) for health degraded/restored — only if email/chat alerts prove insufficient.
6. **Overnight summary** on Overview — aggregate Activity events from last 8h on first open.

---

## Key Files

```
jarvis/mission_control.py           # Aggregator — source of truth
jarvis/platform_notifications.py    # Notification ring buffer
jarvis/platform_metrics.py          # Performance samples
jarvis/gui/static/mission_control.js
jarvis/gui/static/index.html        # Mission Control tab UI
jarvis/gui/server.py                # API routes
jarvis/runtime_introspection.py     # Delegates to Mission Control
```

---

## Daily Workflow

1. Open **AI Platform** from app menu → Mission Control loads immediately.
2. Overview answers: healthy? running? model? project? attention needed?
3. Launch **Aria** separately for conversational work.
4. Ask Aria `status` / `health` / `services` — same data as Mission Control.

---

## Verification

```bash
cd /media/jeff/AI/jarvis
uv run --with ruff --with pytest python scripts/ci_check.py all
```

Open: `http://127.0.0.1:8765/?app=1#workstation`
