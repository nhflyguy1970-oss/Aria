# Activity Center Implementation

## Executive Summary

Activity Center is Aria’s **durable operating-system event inbox**.

It is **not** Job Center (live work), **not** Mission Control (health), and **not** a toast history.

| Surface | Owns |
|---------|------|
| **Activity Center** | Durable events — what happened, what needs attention, until the user resolves them |
| **Job Center** | Live background work — progress, cancel, resume |
| **Mission Control** | Operator health — providers, recovery, diagnostics |
| **Toasts** | Temporary feedback only |

Unread survives opening, filtering, searching, and restart. Unread changes only on Mark Read / Mark All Read / dismiss / configured completion (e.g. snooze marks read) / explicit user action.

## Architecture

```
Subsystem producers / toast bridge / job sync / MC poll
        ↓
activity_store.js     (schema v2, persist, unread, search, correlate)
        ↓
activity_actions.js   (deep-links via AriaActions, Ask Aria, retry)
        ↓
activity_center.js    (UI, keyboard, badge, a11y — never mark-read on render)
        ↓
activity_producers.js (domain emit helpers + showError / health hooks)
```

| Module | Role |
|--------|------|
| `activity_store.js` | Versioned events, localStorage `aria_activity_log_v2`, prefs, dedupe, mute, pin, snooze, undo, NL-ish search, correlate, summarize |
| `activity_actions.js` | Open / Ask Aria / Fix / Retry / What’s wrong — **AriaActions only** |
| `activity_center.js` | Modal inbox UI, filters, grouping, badge, toast+desktop bridges, job sync |
| `activity_producers.js` | Typed producers for chat, memory, documents, … system |

## Event schema (v2)

Every event includes:

`id`, `version`, `timestamp`, `severity`, `priority`, `category`, `source`, `type`,
`title`, `summary`, `detail`, `context`, `deepLink`, `actions`,
`read`, `pinned`, `muted`, `dismissed`, `snoozedUntil`, `groupId`, `metadata`

Legacy v1 (`aria_activity_log_v1`) migrates on first load.

## Producer model

Publish via:

```js
window.AriaActivity.publish({ category, type, severity, title, detail, deepLink, … })
// or
window.AriaActivityProducers.chat.failure("…")
window.emitAriaActivity("documents", "failure", "error", "…", "…", "documents")
```

Instrumentation paths:

- **Toast bridge** — `err`/`warn` toasts → Activity (categorized heuristically)
- **`showError` wrap** — chat/provider failures (suppresses duplicate toast publish)
- **Planner live** — alarms/timers
- **Job sync** — `/api/jobs` failures/completions (completions start read)
- **Mission / status poll** — provider offline ↔ recovered
- **Calendar day poll** — missed events
- **Documents / Connections / chat_done** — domain successes & failures
- **Desktop notify click** — focuses Activity item
- **Startup** — session seed (read)

## Unread semantics

| Action | Unread changes? |
|--------|-----------------|
| Open Activity Center | No |
| Filter / search / render | No |
| Restart Aria | No (persisted) |
| Mark Read / Unread / Mark all read | Yes |
| Dismiss | Yes (read + dismissed) |
| Snooze | Yes (read + hidden until due) |
| Clear read / Clear all | Removes items (confirm + undo) |

Badge (`#activityCenterBadge`) and status segment stay in sync via `aria-activity-change`.

## Deep-link architecture

`deepLink` values resolve through `AriaActivityActions.openDeepLink` → `AriaActions`:

`jobs`, `job:id`, `view:*`, `mc:*`, `chat`, `memory`, `documents`, `connections`,
`planner`, `calendar`, `journal`, `projects`, `gallery`, `providers`, `recovery`, …

Row actions: **Open · Read/Unread · Pin · Ask Aria · Fix · Retry · Snooze · Mute · Dismiss · Copy**

## AI integration

- **Unread summary** line in the modal (`summarizeUnread`)
- **What’s wrong?** → Ask Aria with unread summary (Command Palette + button)
- **Ask Aria** on a row → explain + next steps
- **Fix / Retry** → heuristic Mission Control / Job Center / Documents rebuild
- Voice path: “Aria, what’s wrong?” uses the same summary (via Ask Aria) — does **not** narrate ordinary notifications

## Correlation

Local heuristic over the last 30 minutes groups related failures into incidents
(inference / jobs / home / category). Shown as chips above the list.

## Accessibility

- `role="listbox"` / `option` + `aria-activedescendant`
- Live region `#activityCenterLive` for open / unread / clear announcements
- Unread summary `aria-live="polite"`
- Keyboard: ↑↓ Enter Esc Delete M U P / ? Ctrl+Z Tab
- Focus: search on open; list focus on ↓ from search
- `prefers-reduced-motion` disables item animation

## Search & filtering

Toolbar filters: All · Unread · Pinned · Jobs · Errors · Warnings · Done  
Query searches title, detail, source, category, severity, date string.  
NL-ish tokens: `unread`, `pinned`, `muted`, `dismissed`, `recent`, `today`/`yesterday`,
severity words (`error`, `warning`, …), category words (`chat`, `planner`, …).

Prefs (`aria_activity_prefs_v1`) remember filter + query + muted sources.

## Testing

`tests/test_activity_center.py`:

- HTML wiring order (after `aria_actions.js`)
- Unread-not-on-render / open contract
- Schema + producer domains
- Node VM behavioral tests: persist unread, mark, pin, mute, dedupe, NL parse, correlate, summarize, export, undo, snooze
- Command Palette Activity commands
- Docs presence

## Future roadmap

- Append-only local event history (file-backed) without breaking v2 localStorage
- Voice inbox read of unread summary only for failures
- Stronger Mission Control SSE correlation
- Per-event action catalogs from producers
- Natural-language search via local classifier (optional)

## Design checklist

Every change should improve trust, reduce fatigue, stay local-first, clarify
Activity vs Jobs vs Mission Control, and make failures easier to understand —
without duplicating Job Center or Mission Control.
