# Global UX Implementation

Aria Shell — professional desktop operating environment.

This document is the developer and operator guide for the Global UX + Design System phase.
The shell makes every Product feel like one application. It does **not** own product logic.

## Shell architecture

Package: `jarvis/shell/`

| Module | Role |
|--------|------|
| `terminology.py` | Ownership boundaries + mental model |
| `hotkeys.py` | **Single source of truth** for keyboard chords |
| `design_tokens.py` | Colors, type, spacing, elevation, motion policy |
| `product_home.py` | Product Home compliance checklist |
| `engine.py` | Aggregated shell health / status |
| `api.py` | `/api/shell/*` routes + JS bundle |

### Ownership

**Shell owns:** navigation, chrome, breadcrumbs, hotkey registry, discoverability, sidebar, status bar, Quick Dock, design system, modal chrome, theme tokens, density bridge, accessibility shell, motion policy, docs, tests.

**Shell never owns:** Jobs, Mission Control logic, Planner/Calendar data, Notifications delivery, Search retrieval, Settings stores, Layouts snapshot content, Dashboard data, product business logic, a second command palette, movie HUD effects.

### Client modules (bundled)

`GET /api/shell/bundle.js` concatenates:

- `ui_prefs.js`
- `hotkey_registry.js`
- `breadcrumbs.js`
- `discoverability.js`
- `quick_dock.js`
- `status_bar.js`
- `collapsible_panels.js`
- `global_history.js`
- `split_view.js`

Design CSS: `jarvis/gui/static/shell_design.css` (loaded after `style.css`).

## Navigation mental model

| Surface | Job |
|---------|-----|
| Sidebar | Browse |
| Ctrl+K | Act |
| Search | Find |
| Favorites | Shortcuts |
| Quick Dock | Current tools |
| Layouts | Arrange the workspace |
| Notifications | Attention |
| Mission Control | Operations |
| Jobs | Running work |
| Home | Calm workspace landing |

Do not duplicate responsibilities across these surfaces.

## Design language

Target: professional desktop software (Linear / Raycast / Cursor / VS Code / JetBrains / Docker Desktop / Arc / Obsidian / GitHub Desktop).

**Not:** movie HUD, sci-fi dashboard, gaming launcher, cyberpunk, neon AI, holograms.

### Themes

- Default: **Professional Dark** (`theme: dark`)
- Optional: **Professional Light** (`theme: light`)
- No RGB / gamer / glowing themes

### Accent

One controlled accent, reserved for selection, primary buttons, focus, links, progress, current state.

Allowed: steel blue (default), slate blue, muted teal, deep emerald.

### Tokens

See `jarvis/shell/design_tokens.py` and `GET /api/shell/design`.

Key CSS variables (set by `shell_design.css`):

- `--bg-deep`, `--bg-panel`, `--bg-elevated`, `--border`
- `--text`, `--text-muted`, `--accent`
- `--space-1` … `--space-6`
- `--text-xs` … `--text-xl`
- `--radius-sm|md|lg`, `--elev-1|2`
- `--transition-fast|med`

### Motion

Motion only for state, completion, hierarchy, focus, loading.
Decorative pulse / glow chrome is disabled.
Respect `prefers-reduced-motion`.

### Density

`comfortable` | `standard` | `compact` | `operator`

Exposed in Settings → Appearance and applied via Layouts snapshots through the same `AriaUiPrefs.density` key (`html[data-density]`). No duplicate preference systems.

## Hotkey registry

Python: `jarvis/shell/hotkeys.py`  
Client: `hotkey_registry.js` (loads `/api/shell/hotkeys`, falls back to mirrored list)

Consumers:

- Shortcuts modal (`#shortcutsList`)
- Discoverability / What's New tips
- Tooltips (`data-hotkey-id`)
- Command palette hints (should match registry)

Critical chords:

| Id | Chord | Action |
|----|-------|--------|
| `palette` | Ctrl+K | Command palette |
| `notifications` | Ctrl+Shift+A | Notifications |
| `layouts` | Ctrl+Shift+L (+P alias) | Layouts |
| `mission` | Ctrl+Shift+M | Mission Control |
| `mini_chat` | Ctrl+Shift+K | Floating mini chat |
| `split` | Ctrl+\ | Split view |

Bindings live in `keyboard_nav.js`; docs must never invent alternate chords.

## Discoverability

`discoverability.js` reads chords from `AriaHotkeys.chord()`. Tip ids are unique. Teaching copy uses current product names (**Notifications**, **Layouts**, **Mission Control**).

## Breadcrumbs

`breadcrumbs.js` maps every Product Home (Search, Settings, Models, Coding, Automation, Gallery, Browser, Voice, Vision, Fly Tying, Planner, Calendar, Journal, Projects, Memory, Documents, Notifications, Mission Control, Jobs, Layouts, Dashboard, …).

## Product Home checklist

Required on every Product Home:

header · breadcrumbs · health · actions · search/filter · deep links · status · loading · errors · empty state · help · Esc · accessibility · consistent spacing · consistent toolbar

Source: `jarvis/shell/product_home.py` / `GET /api/shell/product-home`.

## Progressive disclosure

First-run collapses advanced sidebar sections (System, Mission Control, Integrations, Developer, Media) via `aria_shell_disclosure_v1` + `sidebarCollapsed` prefs. Functionality remains available; visual overload is reduced.

## Accessibility

- Clear `:focus-visible` rings (accent, not neon glow)
- Contrast via charcoal / slate / steel palette
- Reduced motion media query
- Modal focus traps (`modal_chrome.js`)
- Hit targets via density + `--touch-min`

## Performance

- Shell scripts bundled (`/api/shell/bundle.js`) — fewer cold-start round-trips
- Design CSS supersedes HUD without rewriting all of `style.css`
- Products continue to lazy-own their Homes

## Developer guide

1. Do not add shell chrome inside a Product package.
2. New global hotkey → add to `hotkeys.py` **and** `hotkey_registry.js` FALLBACK **and** bind in `keyboard_nav.js`.
3. New Product Home → add breadcrumb MAP entry + satisfy checklist.
4. Prefer design tokens / `shell_design.css` over one-off glow styles.
5. Prefer `AriaUiPrefs.density` / appearance API over new localStorage keys.

## Operator guide

- **Where am I?** Breadcrumbs + active sidebar view
- **How do I act?** Ctrl+K
- **How do I find?** Search Product + sidebar search (Ctrl+Shift+F)
- **What needs attention?** Notifications (Ctrl+Shift+A)
- **What's running?** Job Center
- **Is the system healthy?** Mission Control (Ctrl+Shift+M)
- **How do I arrange chrome?** Layouts (Ctrl+Shift+L)
- **How do I customize look?** Settings → Appearance (theme, accent, density)

## Testing

`tests/test_shell_product.py` covers registry uniqueness, tokens, mental model, breadcrumbs MAP coverage, discoverability accuracy, bundle/script wiring, design CSS supersession, Product Home checklist.

## Success criteria

The interface feels like a premium professional desktop OS: calm, intentional, keyboard-first for experts, clear for new users — without movie Jarvis aesthetics.
