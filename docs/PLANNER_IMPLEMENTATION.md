# Planner Implementation

## Overview

Aria Planner remains a **lightweight AI-powered day operations center** — not a Todoist/Motion clone.
This release closes release blockers (trustworthy notifications, live countdown, timer/alarm management),
repairs Morning Briefing integration, clarifies Planner vs Journal vs Calendar, completes Today event CRUD,
and ships Daily Focus plus optional intelligence surfaces (morning triage, vision capture, HA Focus mode,
schedule suggestions).

## Architecture

| Layer | Role |
|-------|------|
| `jarvis/planner_store.py` | SQLite local-first store: tasks, events, timers, alarms, prefs, undo |
| `jarvis/planner_services.py` | Daily Focus, morning triage, vision import, HA focus, schedule suggest/apply |
| `jarvis/extensions/planner/api.py` | HTTP API used by the GUI |
| `jarvis/gui/static/planner.js` | Main Planner UI: lists, CRUD actions, Enter-to-submit, shortcuts |
| `jarvis/gui/static/planner_live.js` | Tick polling, live countdown, Daily Focus rendering, focus actions |
| `jarvis/morning_briefing.py` | Includes Planner block (tasks / timers / alarms / events) |
| `jarvis/workflows/daily.py` | Morning workflow surfaces Planner data without silent failure |

Schema migrations are additive (`due_date`, `priority`, `deleted`, timer `paused` / `remaining_sec` / `kind`, undo + prefs tables).

## New capabilities

### Release blockers

- **Reliable notifications** — `POST /api/planner/tick` polled every ~4s; delivers toast, desktop notify (`jarvisNotify`), Activity Center, and optional beep (respects `notify_sound` pref). Continues while tab is hidden; retries on next interval.
- **Live countdown** — DOM updates via `[data-timer-ends]` every 1s; pause-aware; low CPU.
- **Timer / alarm management** — pause, resume, cancel, duplicate, edit duration/label; alarm edit/cancel; undo soft deletes.

### Today panel

Create / edit / delete Planner day events; natural language time via existing parsers; “Calendar” deep link for commitments.

### Product clarity

- **Planner** = today’s actionable work  
- **Journal** = notes, thoughts, reflections  
- **Calendar** = scheduled commitments  

Header copy, empty states, command palette entries, and Journal↔Planner promotion prompt reinforce this.

## Daily Focus

Primary Planner experience (`#plannerDailyFocus`):

- Top 3 priorities, events, running timers, upcoming alarms  
- Estimated available focus minutes, tasks at risk, suggested next action  
- Recently completed, health badge, optional morning briefing snippet  

Actions: Plan My Day · Start Focus Session · Review Morning Plan · Reprioritize · Ask Aria · Calendar · Journal · Documents · Vision capture · Suggest schedule · Undo  

Keyboard (Planner visible, not typing in an input): `N` `P` `F` `T` `U` · `?` opens shortcuts.

## Morning Triage

`POST /api/planner/triage` blends:

- Planner snapshot / Daily Focus heuristics  
- Memory search (when assistant present)  
- Hybrid RAG / knowledge graph / reasoning (best-effort; graceful if offline)  

Produces: top priorities, suggested schedule, risks, recommendations, confidence score. **Never auto-applies.**

## Vision task capture

1. `POST /api/planner/vision/extract` — OCR / vision → candidate tasks  
2. User review / confirm in UI  
3. `POST /api/planner/vision/import` — selected candidates become Planner tasks (`source=vision`)

## Home Assistant Focus mode

Preference `ha_focus_enabled` (checkbox in Planner header).

- `POST /api/planner/focus/start` starts a focus timer and optionally activates a Focus scene preset  
- `POST /api/planner/focus/end` cancels the focus timer and may restore a relax/default scene  

Always preference-gated; failures are non-fatal and returned in the response.

## Intelligent calendar suggestions

- `POST /api/planner/schedule/suggest` — proposes slots around today’s events  
- `POST /api/planner/schedule/apply` — creates a Planner event **only after user confirmation**

## Planner workflow

1. Open Planner → Daily Focus loads  
2. Plan My Day / Morning Briefing for context  
3. Capture tasks (manual, Chat, Journal promote, vision)  
4. Start Focus 25m (optional HA)  
5. Manage timers/alarms with live countdown + notifications  
6. Light Today events; escalate commitments to Calendar  
7. Undo accidental deletes  

## UX / accessibility

- Premium empty states with next actions  
- Row hover/focus-within action reveal  
- Enter-to-submit on all add inputs  
- Validation toasts; aria-live status  
- Context menus on tasks  
- Command palette Planner actions  
- Shortcuts listed in Shortcuts modal  

## Testing

| Suite | Coverage |
|-------|----------|
| `tests/test_p0_planner.py` | Baseline task/timer + related P0 checks |
| `tests/test_planner_enhancements.py` | Soft-delete/undo, pause/resume/tick, alarms, events, Daily Focus, triage, vision, schedule, focus session, morning workflow |

Run:

```bash
venv/bin/pytest tests/test_p0_planner.py tests/test_planner_enhancements.py -q
```

## Performance

- Tick every 4s (network + SQLite), countdown every 1s (DOM text only)  
- Soft deletes keep undo cheap  
- Intelligence calls are best-effort and skipped/logged when unavailable  

## Future roadmap

- Recurring Planner events UI if/when recurrence APIs expand  
- Richer vision review modal (multi-select)  
- HA Focus scene picker in Settings  
- Optional native-app wake lock for ultra-reliable background alarms  
- Deeper Calendar write-back (ICS) behind explicit confirm  

## Feature flags / env

| Variable | Default | Meaning |
|----------|---------|---------|
| `JARVIS_PLANNER` | on | Enable Planner store |
| `JARVIS_BRIEFING_PLANNER` | `1` | Include Planner in morning briefing |
