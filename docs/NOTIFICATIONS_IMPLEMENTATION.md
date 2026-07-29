# Notifications — Implementation Guide

Operator-facing name: **Notifications**  
Durable inbox UI: **Activity Center**  
Internal product: `jarvis/notifications_product/`

## Architecture

```
Producer (any product)
  → Publish API (normalize + validate)
  → Preferences / Quiet hours / DND / Critical-only
  → History (append-only jsonl)
  → Activity Store (durable inbox)
  → Toast / Desktop channels (gated)
  → Operator → Deep link / Resolve
```

**One pipeline.** Never bypass with ad-hoc second inboxes.

## Ownership

### Notifications owns
Pipeline, schema, publish API, Activity Center inbox contract, routing, history, preferences enforcement, desktop/toast bridges, grouping, correlation, digest, diagnostics, Settings/Search/MC/Dashboard bridges, outbox drain.

### Notifications does NOT own
Jobs, Mission Control, Planner/Calendar/Gallery/Browser/Models/Automation/Projects data stores, Dashboard data, a second notification database, Slack clones, auto-dismiss of unread, AI-invented alerts.

### Mental model
| Surface | Role |
|---|---|
| **Notifications** | Unified delivery product |
| **Activity Center** | Durable inbox UI |
| **Toasts** | Transient feedback |
| **Desktop** | OS delivery |
| **Job Center** | Live work |
| **Mission Control** | Infrastructure health (may promote critical) |

## Schema

`SCHEMA_VERSION = 1` (server). Activity Center client remains schema v2.

Fields: severity, priority, timestamp, source, category, type, title, summary, detail, actions, deepLink, mute/snooze/group/correlation, digest/voice/desktop/toast flags, read/pinned/dismissed/resolved, metadata.

Legacy aliases accepted: `message`→summary, `tone`→severity, `fix`→deepLink, `kind`→category.

## Publish API

```python
from jarvis.notifications_product import publish
publish({"title": "...", "severity": "error", "source": "models", "deepLink": "models"})
```

HTTP: `POST /api/notifications/publish`  
Compat: `POST /api/notifications/add`, client `AriaActivity.add` / `.push` / `.publish`, `AriaNotifications.publish`.

## Preferences (enforced)

`enabled`, `toast_enabled`, `desktop_enabled`, `activity_enabled`, `soft_tips`, `critical_only`, `quiet_hours_*`, `dnd`, `digest_enabled`, `voice_summaries`, `muted_sources`, `muted_categories`, retention.

Settings indexes these; Notifications applies them. Critical severity overrides quiet hours for inbox + desktop.

## Outbox drain

`POST /api/notifications/drain` clears product outboxes (gallery, browser, models, automation, coding, vision, voice, planner) into the pipeline. Client polls drain periodically.

## Digests & grouping

`GET /api/notifications/digest?kind=today|needs_attention|critical|failures|morning|eod`  
`GET /api/notifications/groups?by=source|day|category|incident`

## Entry points

- Header **Notifications** / Ctrl+Shift+A
- Search facet `notifications`
- Settings → Notifications prefs
- Home widget `notifications_summary`
- Mission Control Notifications card (health/proxy — not a second inbox)
- Desktop notification click → inbox
- Voice experimental failure script (never auto-spoken)

## API surface

| Route | Purpose |
|---|---|
| `/api/notifications/product` | Status |
| `/api/notifications/home` | Home payload |
| `/api/notifications/publish` | Publish |
| `/api/notifications/preferences` | Get/set prefs |
| `/api/notifications/history` | History |
| `/api/notifications/drain` | Outbox drain |
| `/api/notifications/digest` | Digests |
| `/api/notifications/correlate` | Correlation |
| `/api/notifications/dashboard` | Home summary |
| `/api/notifications/mission` | MC bridge |
| `/api/notifications/diagnostics` | Health |

Compat: `/api/activity-center/product`.

Data: `data/notifications_product/` (`preferences.json`, `history.jsonl`).

## Developer guide

1. Emit via `publish()` or product outbox jsonl — never invent a parallel store
2. Use deepLinks that `AriaActivityActions` understands
3. Map `message`/`fix` correctly when migrating legacy emitters
4. Add tests in `tests/test_notifications_product.py`

## Operator guide

1. Open **Notifications** (`Ctrl+Shift+A`)
2. Triage unread / errors; pin or snooze as needed
3. Configure quiet hours / desktop in Settings → Notifications
4. Use **What’s wrong?** for an unread failure summary
5. Job Center for live work; Mission Control for infra

## Migration notes

- Operator rename: Activity button → Notifications; inbox remains Activity Center
- Fixed `AriaActivity.add` alias; desktop `notify.js` no longer clobbers wrappers
- Settings `notifications_enabled` now mirrors into Notifications prefs and gates delivery
- Product outboxes drain into one pipeline
