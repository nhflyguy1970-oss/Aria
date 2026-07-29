# Layouts — Implementation Guide

Operator-facing name: **Layouts** (or Shell Layouts)  
Internal product: **Layouts** (`jarvis/layouts_product/`)  
Legacy chrome alias: `workspace_layouts` / `AriaWorkspaces` (compat only)

## Architecture

```
Operator
  → Layouts (modal / palette / hotkey / Search / Settings / MC / Projects offer)
  → Snapshot (versioned chrome profile)
  → Validation
  → Preview
  → Apply (client mutates chrome; server persists active + history)
  → Product Views (presentation only)
  → Diagnostics
  → Mission Control (health summary)
```

**One pipeline.** All entry points call the same preview → apply → history → undo path. Never bypass it with ad-hoc chrome mutations for layout switching.

## Ownership

### Layouts owns
- Layout catalog (starter / custom / role / experimental)
- Versioned snapshot schema
- Snapshot engine + validation + migration
- Application contract (preview / apply / undo)
- History + restore engine
- Diagnostics + Layout API
- Palette / hotkey / Search registration
- Settings bridge (restore prefs indexed in Settings; Layouts applies)
- Mission Control bridge (health only)
- Export / import
- Documentation + tests

### Layouts does NOT own
Projects, Chat sessions, Planner / Calendar / Journal data, Mission Control ops, Search engine, Dashboard data stores, Favorites authoritative store, product databases, secrets, Settings database, virtual desktops, automatic AI layouts.

### Mental model
| Term | Meaning | Owner |
|---|---|---|
| **Layouts** | How Aria looks (shell presentation) | Layouts |
| **Projects / Workspace Identity** | What you are working on | Projects |
| **Surfaces** | Sidebar nav group of product views | Chrome / products |
| **Settings** | Preference catalog (restore options live here) | Settings |
| **Home** | Dashboard aggregate | Dashboard |

## Honest presets

Starter layouts are **full frozen chrome snapshots**, not partial overlays. Applying Coding replaces favorites, view, role, and related chrome fields from the frozen snapshot. They are labeled **Starter layouts** in the UI — never marketed as “complete workspaces” that own product data.

## Snapshot schema

`SCHEMA_VERSION = 1`

Captured fields (chrome only):

`view`, `favorites`, `sidebarCollapsed`, `sidebarWidth`, `dockHidden`, `statusBarHidden`, `miniChatHidden`, `dashboardLayout`, `theme`, `accent`, `panelCollapsed`, `split`, `module`, `model`, `density`, `role`

Never capture: passwords, tokens, secrets, API keys, auth cookies, chat bodies, product records.

Validate before apply. Migrate older snapshots forward. Reject `schema_too_new` and sensitive keys.

## Restore

Opt-in only (`restore_on_boot` default **false**).

| Mode | Behavior |
|---|---|
| Boot restore | If enabled + active layout valid → apply frozen snapshot |
| Manual restore | Preview/apply active or named layout |
| Undo | Instant restore of previous client snapshot |
| Corruption | Skip restore; coach operator to pick a starter |

## Apply pipeline

1. Resolve layout (builtin / custom / alias)
2. Migrate + validate snapshot
3. Diff vs current (preview)
4. Optional confirm when many changes
5. Client `applySnapshot` mutates chrome
6. Server `commit_apply` persists `active_layout`, undo buffer, history
7. Update active indicator (header / status bar / chips)

## Entry points

- Layouts modal (`Ctrl+Shift+L`; `Ctrl+Shift+P` alias)
- Command palette: Apply Coding / Writing / Research / Planning / Media / Maker / Home + Undo
- `Ctrl+Alt+1`–`8` starter shortcuts
- Home Quick launch → Layouts
- Settings Appearance → Layouts / restore preference
- Projects optional offer (“recommends Coding”) — never forced
- Search facet `layouts`
- Mission Control overview card → Open Layouts
- Voice experimental script (never auto-spoken)

## API

| Route | Purpose |
|---|---|
| `GET /api/layouts/product` | Product status |
| `GET /api/layouts/home` | Layouts Home payload |
| `GET /api/layouts/catalog` | Builtins + customs |
| `GET /api/layouts/open` | Deep-link resolve |
| `POST /api/layouts/preview` | Validate + diff |
| `POST /api/layouts/apply` | Persist apply + history |
| `POST /api/layouts/undo` | Undo buffer |
| `POST /api/layouts/save` | Save custom |
| `DELETE /api/layouts/custom/{id}` | Delete (confirm) |
| `GET/POST /api/layouts/settings` | Restore + behavior prefs |
| `GET /api/layouts/restore` | Boot restore plan |
| `GET /api/layouts/history` | Apply history |
| `GET/POST /api/layouts/export\|import` | JSON pack |
| `GET /api/layouts/diagnostics` | Health + recovery |
| `GET /api/layouts/mission` | MC bridge |
| `GET /api/layouts/suggest/project` | Optional project offer |
| `GET /api/layouts/suggest/intent` | Experimental coach |
| `GET /api/layouts/experimental/voice` | Voice script |

Compat: `GET /api/workspace-layouts/product` (deprecated).

Data root: `data/layouts_product/` (`custom.json`, `settings.json`, `history.json`, `undo.json`).

## Search

Facet `layouts` — starters, customs, Open Layouts, apply actions. Search indexes; Layouts applies. No second search engine.

## Settings

Indexes restore-on-boot and Layouts entry under Appearance. Settings owns preference catalog; Layouts owns application and snapshot store.

## Mission Control

Shows Layouts health: starter/custom counts, schema version, active layout, restore flag, recent failures. Does **not** edit layouts.

## AI / experimental

Intent coach and voice switch scripts may **recommend**. Never silently apply, rearrange, invent preferences, or require an LLM.

## Accessibility

- Modal listbox + `aria-pressed` on chips
- Enter-to-save on name field
- Typeahead filter
- Keyboard: `Ctrl+Shift+L`, `Ctrl+Alt+1`–`8`
- Status bar segment + header button announce active layout

## Developer guide

1. Add starter in `catalog.py` via `make_snapshot(...)` (full frozen fields)
2. Expose apply via palette / Search aliases if needed
3. Keep chrome mutation in `workspace_layouts.js` `applySnapshot`
4. Persist only through `apply.commit_apply` / `store`
5. Add tests in `tests/test_layouts_product.py`

## Operator guide

1. Open **Layouts** (`Ctrl+Shift+L`)
2. Pick a **Starter** (full frozen) or save your own
3. Optional: enable **Restore last layout on boot**
4. Undo last apply from modal or palette
5. Export/import JSON to move customs between machines
6. Projects may *suggest* Coding — you choose

## Migration notes

- Renamed operator copy from Workspace layouts → **Layouts**
- Sidebar nav group labeled **Surfaces** (not Workspaces)
- Projects keep **Workspace Identity**
- Client prefs keys `workspaceLayouts` / `activeWorkspace` retained for compat; prefer `activeLayout`
- Starters are full snapshots (honest), not partial overlays
