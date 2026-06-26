# Bullet Journal — Quick Reference

Stored in memory namespace **`cheatsheet`** (key: `journal`). Edit in Memory tab or say **"journal cheatsheet"**.

Data file: **`data/journal/bullet_journal.json`** · Photos: **`data/journal/photos/`**

## Symbols (editable on **Key** tab)

• task · × done · > migrated · < scheduled · ~ cancelled · ○ event · — note · * important · ! inspiration · 👁 explore

## Ryder Carroll workflow

| Stage | Tab | Action |
|-------|-----|--------|
| Capture | Daily / Rapid log | Log tasks, events, notes |
| Organize | Monthly | Month tasks + calendar |
| Schedule | Future | `<` schedule or transfer → month |
| Execute | Daily | Thread ↓ from monthly/future |
| Review | Monthly | End-of-month checklist |
| Track | Habits / Wellness | Habits grid + mood/gratitude |
| Find | Index | Auto-index + page numbers (p.N) |

## Chat

| You say | ARIA does |
|---------|-------------|
| "Log: • finish taxes" | Rapid log to today |
| "Journal today" | Daily log with quote + reflections |
| "What are my open tasks?" | Open tasks (daily/monthly/weekly/future/collections) |
| "Remember journal entry" | Save today to memory |
| "Migrate journal month" | Move open monthly tasks to next month (monthly log or future) |
| "Schedule finish taxes to 2026-08" | Schedule matching open task to future month |
| "Thread report draft to today" | Migrate matching task to today's daily log |
| "Run journal review" | AI summary after month/week checklist |

## Daily page

- **Weather** — local high/low + conditions (Open-Meteo; auto via IP or set `JARVIS_WEATHER_CITY` in `data/jarvis.env`)
- **Quote** — Stoic / Native American / Tai Chi (daily rotation)
- **Timeline** — timed events sorted by hour (set 🕐 on events)
- **Mood 1–5** + **gratitude lines**
- **Morning / evening prompts** with saved answers
- **Photos** per day
- **Migrate open → tomorrow** (BuJo daily migration)
- Events: type `14:30 Meeting` or set 🕐 time

## Bullet actions

| Button | Meaning |
|--------|---------|
| × | Complete |
| › | Migrate to tomorrow |
| < | Schedule to future month |
| ↓ thread / ↓ copy | Migrate or duplicate to daily (monthly/future/weekly) |
| ~ | Cancel |
| ↳ | Nest sub-bullet |
| 🔗 | Link to another bullet ID |
| * / ! | Important / inspiration (auto-index) |
| ★ | Save to memory |

## Tabs

| Tab | Use |
|-----|-----|
| **Daily** | Full day spread |
| **Weekly** | ISO week log + weekly review checklist |
| **Monthly** | Calendar, timed events, review checklist, thread tasks |
| **Habits** | Monthly tracker (mobile scroll) |
| **Wellness** | Mood overview + gratitude stream |
| **Future** | Pick month in toolbar → add here or use rapid log · `<` schedule from other tabs · transfer open → monthly |
| **Index** | Auto + manual · click page links · p.N page numbers |
| **Collections** | Themed lists |
| **Key** | Custom symbol legend |

**Toolbar:** Undo · Redo · Search · Print · PDF · JSON export/import · AI Reflect · Migrate month (monthly or future)

## Rapid log

One line per entry. **Indent 2 spaces** to nest under the previous line.

## Backup & undo

- **Undo / Redo** — last 20 changes (toolbar)
- **Export JSON** — full journal + history metadata
- Copy **`data/journal/`** folder

## Index (auto)

Auto-indexes: daily pages, monthly/weeks/collections, ★/! bullets. **Rebuild auto-index** preserves manual entries.

Page refs: `daily:YYYY-MM-DD` · `monthly:YYYY-MM` · `weekly:YYYY-Www` · `collection:Name` · **p.42**
