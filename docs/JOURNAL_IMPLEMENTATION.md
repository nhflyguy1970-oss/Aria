# Journal Implementation

## Executive Summary

Aria Journal is a **local-first digital Bullet Journal** — rapid logging, reflection,
collections, habits, and wellness. It is **not** a task manager, Notion clone, or
project management system.

| Role | System |
|------|--------|
| Thoughts, notes, rapid log, reflection | **Journal** |
| Actionable work | **Planner** |
| Scheduled commitments | **Calendar** |
| Lasting knowledge | **Memory / Knowledge Graph** |

This implementation closes release blockers (rapid-log routing, habit streaks,
one-click Promote to Planner, chat task disambiguation), adds Writing Mode,
AI assistants (confirm-only), voice/vision import previews, and strengthens
reliability (undo sidecar, optional at-rest encryption, backups, tests).

## Architecture

```
journal.js  →  /api/journal/*  →  extra_routes.py
                                      ↓
                         modules/journal.py  (+ journal_bujo.py)
                                      ↓
                         bullet_journal.json  (+ .history sidecar, optional .enc)
                                      ↓
                         journal_services.py  (AI / voice / vision / wizards)
                                      ↓
              ┌────────────┬─────────────┬──────────────┐
         planner_store   memory      knowledge_graph
```

| Module | Responsibility |
|--------|----------------|
| `modules/journal.py` | BuJo store: daily/weekly/monthly/future, habits, search, promote |
| `modules/journal_bujo.py` | Undo/redo, reviews, wellness mixins |
| `journal_services.py` | Reflection, promotion, migration, memory surface, voice, vision |
| `journal_crypto.py` | Password export/import + optional at-rest |
| `gui/static/journal.js` | UI, Writing Mode, shortcuts, promote actions |

## Release blockers addressed

1. **Rapid Log routing** — `POST /api/journal/rapid` accepts `section=daily|weekly|monthly|future` (+ `day` / `week` / `month`). UI button labels match destinations.
2. **Promote to Planner** — `POST /api/journal/bullet/{id}/promote` creates a Planner task, sets `planner_task_id`, badge + open/unlink in the bullet menu. Never silent.
3. **Chat task disambiguation** — “open tasks / my todos / to-do list” asks Planner vs Journal when ambiguous; explicit journal/planner language routes correctly (`journal_services.disambiguate_tasks_intent`).
4. **Habit streaks** — `habit_tracker()` returns `streak`, `longest_streak`, `completion_pct`, week stats; UI shows Done / % / Streak / Best.
5. **Tests** — `tests/test_journal.py` and `tests/test_journal_crypto.py` replace stubs.

## Writing Mode

Toggle with **Writing mode** or `W` (Esc to exit):

- Hides header, tabs, toolbar, stats
- Larger rapid-log canvas and softer typography
- Word count + elapsed time chrome
- Optional typewriter scroll
- Advanced controls remain in **More** when not in Writing Mode

## Planner / Calendar / Memory relationship

- **Promote ↑** moves actionable bullets into Planner with a bidirectional link.
- **Calendar** button opens the day as scheduled commitments (Journal events stay journal-owned until scheduled).
- **Memory ★ remember** and Assist → Memory surface related notes/entities for review only.
- Role hint in the UI: Journal = thoughts · Planner = work · Calendar = commitments.

## AI assistants (user-initiated, confirm-only)

| Assistant | Endpoint | Mutates? |
|-----------|----------|----------|
| Reflection | `POST /api/journal/assist/reflect` | No |
| Promotion | `GET /api/journal/assist/promote` | No (confirm promote) |
| Migration | `GET /api/journal/assist/migrate` | No |
| Memory surface | `GET /api/journal/assist/memory` | No |
| Writing | `POST /api/journal/assist/writing` | No |
| Voice draft | `POST /api/journal/assist/voice` | No until Rapid Log save |
| Vision OCR preview | `POST /api/journal/assist/vision` | No until approve |
| Month-end wizard | `GET /api/journal/wizard/month-end` | No |

Personal thoughts are never rewritten automatically.

## Voice + Vision

- **Voice log** — paste/dictate transcript → structured rapid-log draft → user confirms.
- **Vision import** — paste OCR from notebook/whiteboard/stickies → preview → user confirms into active section.

## Reliability

- Undo/redo snapshots live in `bullet_journal.json.history` (not inside the live journal file).
- Exports strip history/redo.
- `POST /api/journal/backup` writes a timestamped JSON backup.
- Optional at-rest: set `JARVIS_JOURNAL_AT_REST_PASSWORD` to also write `.enc` ciphertext on save.

## Accessibility & keyboard

| Shortcut | Action |
|----------|--------|
| `W` | Writing Mode |
| `/` | Focus search |
| `?` | Shortcut overlay |
| `Esc` | Exit writing / close overlay |
| `1`–`9` | Jump BuJo tabs (when not typing) |
| `Enter` | Commit rapid log |

Menus use progressive disclosure (⋯ / More). Empty states are calm, not alarming.

## Performance

- Rapid log is line-oriented O(n) writes with nested parent stack.
- Habit stats are computed per request for the visible month (acceptable for personal journals).
- History sidecar avoids unbounded growth of the primary JSON file.

## Testing

```bash
./venv/bin/pytest tests/test_journal.py tests/test_journal_crypto.py -q
```

Coverage includes: rapid-log sections, nesting, symbols, habits, promote/unlink,
crypto roundtrip, disambiguation, voice/vision drafts, migration/promotion assistants,
search, collections, backup, import validation.

## Future roadmap

- Native mic capture wired to voice assist (still confirm-before-save)
- Camera capture → OCR pipeline for vision import
- Deeper KG entity linking UI beside Writing Mode (non-interruptive sidebar)
- Per-collection encryption keys
- Sync of Planner completion status back into linked Journal bullets

## Product philosophy (unchanged)

Journal remains Aria’s digital Bullet Journal for thoughts, notes, rapid logging,
reflection, collections, habits, wellness, and memory. Planner remains actionable
work. Calendar remains scheduled commitments.
