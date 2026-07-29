# Calendar Implementation

## Executive Summary

Aria Calendar is the **unified scheduling hub** for a local AI OS — not a Google Calendar clone.
It presents commitments from Journal, Planner, ICS, work schedule, and holidays through a
**Schedule Abstraction Layer**, while each system keeps ownership of its data.

| Role | System |
|------|--------|
| Actionable work | Planner |
| Notes / reflections | Journal |
| Scheduled commitments (UI hub) | Calendar |
| Subscribed external events | ICS (read-only) |
| Attention delivery | Notifications |

## Architecture

```
calendar.js  →  /api/calendar/*  →  calendar_api.py
                                      ↓
                              calendar_tab.py
                                      ↓
                              calendar_schedule.py  (abstraction)
                                      ↓
              ┌─────────────┬─────────────┬──────────────┬────────────┐
         planner_store   journal     calendar_ics   calendar_store  holidays
```

| Module | Responsibility |
|--------|----------------|
| `calendar_api.py` | HTTP routes (Calendar-owned; not Planner) |
| `calendar_time.py` | Local today, time validation, week/agenda ranges |
| `calendar_schedule.py` | Unified read model + routed mutations |
| `calendar_ics.py` | Cached ICS fetch, sync status, basic RRULE |
| `calendar_services.py` | NL schedule, conflicts, prep, focus, vision, HA modes |
| `calendar_tab.py` | HTTP-facing wrappers + back-compat day fields |
| `calendar_store.py` | Weekly work schedule + Calendar prefs |
| `calendar_notify.py` | Publish to Notifications (delivery owned elsewhere) |
| `calendar_bridges.py` | Dashboard / Search / Mission Control consumers |
| `calendar_terminology.py` | Ownership boundaries |
| `gui/static/calendar.js` | Month / Week / Agenda / Timeline UI |

## Ownership

**Calendar owns:** events presentation, work calendars, availability, scheduling aids,
time (local day / TZ), ICS subscribe, recurrence (basic RRULE), schedule abstraction, Calendar API/UI.

**Calendar does not own:** tasks, projects, planner workflows, notifications delivery, jobs,
search index, settings DB, shell chrome, Mission Control ops.

## Schedule Abstraction Layer

`schedule_for_day()` merges items with:

- `id` prefixed by source (`journal:…`, `planner:…`, `ics:…`)
- `source` / `source_label` / `color` / `editable`
- `time` / `all_day` / `kind`

Mutations route to the owning store:

- Journal bullets → `daily_add` / `bullet_update` / `bullet_delete`
- Planner events/tasks → `planner_store`

Databases are **not** merged.

## Integrations

| Product | Direction | Mechanism |
|---------|-----------|-----------|
| Planner | Calendar consumes | `events_for_day` / tasks (Planner owns data) |
| Journal | Calendar consumes | Day events / notes |
| Notifications | Calendar publishes | `calendar_notify.publish_calendar_event` |
| Home / Dashboard | Consumes Calendar | `calendar_bridges.dashboard_summary` |
| Search | Consumes Calendar | `calendar_bridges.search_hits` via Search retriever |
| Settings | Indexes deep links | Preference catalog → Calendar view |
| Voice | Uses NL confirm | Chat + `/api/calendar/nl` |
| Mission Control | Status only | `/api/calendar/mission` |
| HA | Optional scenes | Calendar prefs + scene presets |

## Release blockers addressed

1. **Time picker** — explicit time persistence on Journal events
2. **Untimed events** — visible in all views
3. **Planner events** — merged in schedule layer
4. **Inline management** — create / edit / delete / duplicate / complete
5. **Timezone** — local calendar date via `calendar_time.today_iso()`
6. **ICS** — cache, sync status, refresh, stale fallback, basic RRULE
7. **API ownership** — routes live in `calendar_api.py`, not Planner

## Views

Month · Week · Agenda · Timeline (see UI). Keyboard: `←`/`→`, `T`, `N`, `1`–`4`.

## AI Scheduling

| Feature | Endpoint | Confirm? |
|---------|----------|----------|
| Natural language parse | `POST /api/calendar/nl` | Yes (`/nl/confirm`) |
| Conflict detection | `GET /api/calendar/conflicts` | Suggest only |
| Meeting prep | `POST /api/calendar/prep` | Read-only |
| Focus suggestions | `GET /api/calendar/focus-suggestions` | Yes before focus |
| Memory dates | `GET /api/calendar/memory-dates` | Suggest only |
| Vision import | `POST /api/calendar/vision/extract` + `/import` | Yes |
| HA Meeting/Focus/Travel | `POST /api/calendar/ha-mode` | Optional prefs |

## Testing

```bash
.venv/bin/pytest tests/test_calendar.py tests/test_calendar_enhancements.py -q
```

Coverage: local today, time validation, schedule merge, CRUD, ICS RRULE, NL + conflicts,
week/agenda/timeline, work schedule, HA skip, bridges, terminology.

## Env

| Variable | Meaning |
|----------|---------|
| `JARVIS_ICS_URL` | External calendar feed |
| `JARVIS_ICS_CACHE_TTL` | ICS cache seconds (default 300) |

## Developer notes

- Register via `jarvis.calendar_api.register_product_routes` in `extra_routes.py`.
- Do not re-add `/api/calendar/*` under Planner.
- Soft-consume Intelligence / Memory in meeting prep; never own those stores.
