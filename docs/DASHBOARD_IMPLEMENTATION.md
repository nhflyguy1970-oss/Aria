# Dashboard / Home — Implementation Guide

Operator-facing name: **Home**  
Internal product: **Dashboard** (`jarvis/dashboard_product/`)

## Architecture

```
Operator
  → Home (#dashboard)
  → /api/dashboard/home  (aggregate)
  → Widget contracts (honest show | coach | hide)
  → Layout (order / hidden / density / role)
  → Presentation (dashboard_home.js)
  → Deep links → Product Homes
  → Diagnostics → Mission Control summary
```

Dashboard **aggregates and presents**. Products **own data stores**.

## Ownership

### Dashboard owns
- Home surface
- Widget catalog + schema
- Aggregate API
- Layout presentation prefs (mirrored; Settings indexes appearance)
- Attention strip (ranking presentation)
- Daily Brief **presentation** (indexes Morning Briefing)
- Diagnostics, Search registration, Mission Control bridge

### Dashboard does NOT own
Planner, Calendar, Journal, Memory, Search, Mission Control, Home Assistant, Automation, Coding, Gallery, Voice, Vision, Morning Briefing data, secrets, or a monolithic dashboard database.

## Aggregate API

| Route | Purpose |
|---|---|
| `GET /api/dashboard/product` | Product status |
| `GET /api/dashboard/home` | Full Home aggregate |
| `GET /api/dashboard/widgets` | Widget catalog |
| `GET /api/dashboard/attention` | Attention strip |
| `GET /api/dashboard/brief` | Daily Brief card |
| `GET/POST /api/dashboard/layout` | Layout prefs |
| `GET /api/dashboard/diagnostics` | Health + recovery |
| `GET /api/dashboard/mission` | MC bridge |
| `GET /api/dashboard/open` | Deep-link resolve |
| `GET /api/dashboard/experimental/*` | Voice brief script, kiosk, policies |

Compat: `/api/system-info` still exists for PySide/voice; greeting now uses Dashboard `personalized_greeting`.

## Widget schema

Every widget includes: `id`, `title`, `owner`, `category`, `priority`, `health`, `available`, `status`, `payload`, `actions`, `deep_links`, `refreshed_at`, `coach`, `error`, `empty`, `render` ∈ {`show`,`coach`,`hide`}.

**Honesty rule:** never invent Live intelligence, weather, or headlines. Hide or coach.

## Daily Brief

One card. Source: `jarvis.morning_briefing.build_briefing`. Deep-links to Chat / Planner / Calendar / Journal. Does not replace the Chat launch briefing overlay.

## Attention strip

Ranks overdue planner tasks, upcoming events, jobs, provider/HA warnings. Calm empty state: “Nothing urgent.”

## Search

Facet `dashboard` — Home, Daily Brief, widgets, deep links. No second search engine.

## Settings

Indexes Home density / layout / role under Appearance. Dashboard owns presentation; Settings does not store a second DB.

## Mission Control

Overview card **Home** shows widget counts + latency. MC remains ops detail. Never clone MC into Home.

## Entry points

- View tab / sidebar **Home**
- `Ctrl+Home`
- Command Palette “Open Home”
- First-run discoverability
- Mission Control → Open Home
- Search facet results
- Settings deep links

## Developer guide

1. Add widget def in `widgets.py`
2. Build payload in `aggregate.py` via `make_widget`
3. Render in `dashboard_home.js` (show / coach / hide)
4. Register Search aliases if needed
5. Add contract tests in `tests/test_dashboard_product.py`

## Operator guide

1. Open **Home** (`Ctrl+Home`)
2. Read Attention + Daily Brief
3. Jump via Quick launch or deep links
4. Customize cards (order/visibility)
5. Use Mission Control for provider/runtime detail

## Migration notes

- Logic extracted from `planner.js` → `dashboard_home.js` + `dashboard_product/`
- Fake “Live” intelligence removed
- News category filter wired on `/api/curated-news`
- Layout defaults hide standalone News (Daily Brief preferred)
