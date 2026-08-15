# Aria Design System

**Version:** 1.0 · **UI build:** 5.16.160 · **Date:** 2026-07-27  
**Scope:** Visual language and interaction rules for `jarvis/gui/static`. Future UI work must follow this document.

---

## Principles

1. **One product** — every screen shares tokens, button classes, dialog chrome, and status colors.
2. **Reduce friction** — prefer fewer clicks, clearer copy, and progressive disclosure.
3. **Aria, not Jarvis** — user-facing strings say **Aria**; `jarvis*` remains for paths/APIs/env only.
4. **Local-first polish** — prefs stay in `aria_ui_prefs_v1`; no new backend for chrome.
5. **Accessible by default** — keyboard, focus rings, `aria-*`, reduced motion.

---

## Color

| Token | Role |
|---|---|
| `--bg-deep` / `--bg-panel` / `--bg-elevated` / `--bg-hover` | Surfaces |
| `--border` | Hairlines, dividers |
| `--text` / `--text-muted` | Primary / secondary copy |
| `--accent` / `--accent-glow` / `--accent-dim` | Brand actions, focus, selection |
| `--status-ok` / `--status-warn` / `--status-err` / `--status-info` | Semantic feedback |
| Module hues (`--coding`, `--general`, `--vision`, …) | Domain chips only — not chrome |

Accent themes (Settings) may override `--accent*` only. Do not invent ad-hoc hex for toasts, status, or focus.

---

## Typography

| Token | Use |
|---|---|
| `--font` (DM Sans) | UI |
| `--mono` (JetBrains Mono) | Code, paths, times |
| `--text-xs` … `--text-xl` | Scale: labels → titles |

Section labels: uppercase, ~0.65–0.68rem, letter-spacing ~0.09em, muted color.

---

## Spacing & radius

| Token | Value |
|---|---|
| `--space-1` … `--space-6` | 4px → 32px scale |
| `--radius-sm` / `--radius-md` / `--radius-lg` | 8 / 12 / 16 |
| `--radius` | Alias of `--radius-md` |

Sidebar default width: `260px` (`--sidebar-width`). Touch / click targets should aim for `--touch-min` (44px) where practical.

---

## Elevation & motion

| Token | Use |
|---|---|
| `--elev-1` / `--elev-2` | Toasts, floating panels |
| `--transition-fast` / `--transition-med` | Hover, panel enter |
| `--focus-ring` / `--focus-offset` | Focus-visible only |

Respect `@media (prefers-reduced-motion: reduce)` — disable scale/entrance animations.

---

## Components

### Buttons

| Class | Intent |
|---|---|
| `apply-btn` | Primary commit / confirm (one per action group) |
| `ghost-btn` | Secondary / cancel / tertiary |
| `icon-btn` | Icon-only; **requires `aria-label`** |
| `preset-btn` | Compact toggles / presets |

Sizes: default, `.small`, `.tiny`. Never use `apply-btn` for every row action.

### Forms

Inputs/selects/textareas use shared border, elevated background, accent focus ring. Labels sit above or beside — keep muted helper text under the control.

### Cards / panels

Prefer section surfaces (`sidebar-section`, dashboard widgets) over nested “card stacks.” Border + subtle fill; radius `--radius-md`.

### Dialogs

- `role="dialog"` + `aria-modal="true"` + `aria-labelledby`
- Registered in `modal_chrome.js` `MODAL_IDS` for Esc + Tab trap
- Primary action: `apply-btn`; dismiss: `ghost-btn` or Esc
- One clear dismiss path (avoid duplicate Got it / Close)

### Context menus

`.aria-context-menu` / `.aria-context-item`, `role="menu"` / `menuitem`, viewport clamp, Esc/outside dismiss.

### Navigation

View tabs, sidebar sections, Favorites, Quick Dock, breadcrumbs, status bar. Deep links: `#viewId`.

### Empty states

Use `.empty-state` + `.empty-state-icon` + `.empty-state-title` + `.empty-state-actions`:

1. Icon / illustration  
2. What is empty  
3. Primary CTA  
4. Secondary CTA / related workflow  

### Notifications

`.aria-toast` + `--ok|--err|--warn|--info` borders using status tokens. Activity Center is the durable log; toasts are ephemeral.

### Status indicators

Healthy / degraded / unavailable map to `--status-*`. Status bar segments are buttons that jump to the relevant surface.

---

## Interaction guidelines

- Prefer keyboard paths documented in Shortcuts (`Ctrl+/`).
- Page-specific actions belong in Ctrl+K **This page** group.
- Right-click menus only show actions relevant to the target.
- Polling must no-op or pause when `document.hidden`.
- Errors: **what happened · why · how to fix · retry** — never bare “Error” / “Failed”.

---

## Naming

| Layer | Convention |
|---|---|
| View ids | lowercase (`chat`, `workstation`, `flytying`) |
| User labels | Title Case product names (`Mission Control`, `Activity Center`) |
| Prefs | camelCase in `aria_ui_prefs_v1` |
| Globals | `Aria*` for UI modules; `jarvis*` legacy chat helpers |

Mission Control view id remains `workstation`; sidebar label for the overview is **Console** (not “Dashboard”, which is the home view).

---

## Living Interface (Experience Design)

Aria is **one home**; each product is a **room**. Shared shell (nav, buttons, typography, spacing, dialogs) stays constant. Atmosphere changes with `body[data-room]`.

| Room (`data-room`) | Views | Feeling |
|---|---|---|
| `chat` / `home` | chat, dashboard, settings | Warm welcome |
| `mission` | workstation | Aerospace glass / precision |
| `health` | health | Calm clinic |
| `flytying` | flytying | Bench by the stream |
| `coding` | coding, models, projects, maker | Engineering studio |
| `documents` | documents, memory | Private library |
| `search` | search | Spotlight / effortless |
| `gallery` | gallery, video, meme, vision | Museum light |
| `planner` / `calendar` | planner, journal, calendar | Paper planner |
| `voice` | voice, audio | Warm companion |
| `browser` | browser | Research desk |
| `repair` | audit, security | Calm technician |
| `integrity` | certification | Quiet guardian |
| `presence` | presence, automation, integrations | Smart home |

**Files:** `living_interface.css` (after `shell_design.css`), `living_interface.js` (sets room on view change), `living_atmosphere.css` (Phase 2 life).

### Phase 2 — Atmosphere

Rooms keep their palettes; atmosphere adds almost-imperceptible life.

| Layer | Mechanism | Default |
|---|---|---|
| Time of day | `body[data-tod]` morning / afternoon / evening / night | On |
| Season | `body[data-season]` spring / summer / autumn / winter | On (quiet tint) |
| Weather | `body[data-weather]` from dashboard home (~hourly) | On |
| Room breath | Mission glow, fly water shimmer, docs grain, gallery fade, planner today, voice waveform | On |
| Soft UI sounds | `AriaLivingInterface.playCue` (Web Audio) | **Off** |
| Kill switch | `body[data-atmosphere="off"]` or Settings → Atmosphere | Prefs |

**Prefs** (`ui_prefs.js`): `atmosphereEnabled`, `weatherAtmosphere`, `seasonAtmosphere`, `ambientSound`.

**Rules:**
1. Extend room tokens — do not invent one-off hex in product CSS.
2. Atmosphere washes live on `#mainContent` (shell clears `body::before`).
3. Do not redesign Living Interface — only deepen atmosphere (Phase 2).
4. Respect `prefers-reduced-motion` (static tints OK; motion off).
5. Empty states use `.empty-state*` and teach + invite.
6. Light and dark are both intentional; light is warm paper, not flat white.
7. Never cyberpunk / neon / RGB / particles / “AI dashboard” chrome.
8. Atmosphere must stay cheap; sound stays muted unless Jeff opts in.
9. Function always wins over decoration.

---

## Future UI rules

1. Extend tokens before adding one-off CSS colors.  
2. Reuse `ghost-btn` / `apply-btn` / empty-state / modal chrome.  
3. Register every new overlay in `modal_chrome.js`.  
4. Ship `aria-label` with every icon-only control.  
5. Document user-visible changes in What's New when shipping chrome.  
6. Prefer refinement over new surface area.
7. When entering a product, Jeff should feel the room before reading the title.

See also: `docs/ARIA_FINAL_PRODUCT_POLISH.md`, Phase I–III modernization docs.
