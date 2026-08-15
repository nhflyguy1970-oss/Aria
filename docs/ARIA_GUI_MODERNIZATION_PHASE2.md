# Aria GUI Modernization — Phase II

**Date:** 2026-07-25  
**Scope:** UI/UX only — no certification, no backend redesign, no architecture rewrite  
**Baseline:** Phase I modernized build 5.16.140 → **5.16.141**

---

## Executive Summary

Phase II elevates Aria from a polished application into a premium desktop environment. The headline additions are a **universal sidebar search**, a **Quick Access Dock**, a **live status bar**, **accent color themes**, a **customizable dashboard**, **breadcrumbs**, **right-click context menus**, and **collapsible view panels** — all remembered per user, all respecting reduced-motion, and all verified live in the browser against the running server.

A first-time user can now: type three letters to reach any view or setting, see provider health at a glance without opening Mission Control, and shape the dashboard and chrome to their own workflow.

---

## Improvements by area

### 1. Universal search (`sidebar_search.js`, new)

| Before | After |
|---|---|
| Navigation required scanning 21 tabs or knowing Ctrl+K | Persistent search field at the top of the sidebar filters views, settings, models, and tools as you type |

- Instant fuzzy matching with `<mark>` highlighting of the matched substring
- Ranks results by favorites, recent views, and command usage (personalization)
- Full keyboard support: ↑/↓, Enter, Esc; **Ctrl+Shift+F** focuses it from anywhere
- Last result row hands off to Ctrl+K (“Search everything for …”) which now accepts a prefill query and immediately runs federated knowledge search
- Settings results deep-open and flash the right sidebar section

Verified live: typing “plan” returned Planner first; Enter navigated and breadcrumb updated to *Workspace › Planner*.

### 2. Customizable dashboard (`dashboard_widgets.js`, new)

- All seven dashboard cards (Quick launch, Provider health, Today at a glance, Home scenes, System intelligence, News briefing, Try asking Aria) are now **hideable and reorderable** via **Customize…**
- Layout persists in `aria_ui_prefs_v1.dashboardLayout`; Reset restores defaults
- Cards fade in with a subtle animation (disabled under reduced motion)

Verified live: hid the briefing card, saved, confirmed the DOM class applied, then reset.

### 3. Accent themes (`theme.js` extended)

- Eight swatches in Settings: **gold (default), blue, green, purple, orange, red, teal, amber**
- Accents override only `--accent`, `--accent-glow`, `--accent-dim` — highlights, selection, buttons, focus rings, status accents. No full recolor.
- Explicit accents intentionally outrank the legacy HUD-blue mode (specificity fix verified live: teal → `#5ec4b6`); choosing gold/default defers to the active theme
- Persisted via prefs; light/dark toggle unchanged

### 4. Icon consistency

- New chrome icons (search, restart) use one style: 24-viewBox, stroke 2, round caps/joins — matching the existing attach/mic/send set
- Chevrons unified: sidebar sections and collapsible panel headers share the same rotating `▾`
- Deferred: full sweep of legacy emoji-glyph buttons (see Deferred)

### 5. Breadcrumbs (`breadcrumbs.js`, new)

- Every major view shows `Section › Page` under the tab bar (AI › Chat, Workspace › Planner, Media › Gallery, Maker › CAD Lab, System › Audit & Repair…)
- Clicking the parent opens and flashes the matching sidebar group (or Dashboard for Home)
- `aria-current="page"` on the leaf for assistive tech

### 6. Collapsible panels (`collapsible_panels.js`, new)

- Dashboard checklist/skills/security sections and Planner’s four columns now collapse from their `h3` headers (click or Enter/Space)
- State remembered per panel in prefs (`panelCollapsed`)
- Generic mechanism re-enhances on view switches; more views can opt in by adding a target selector

### 7. Status bar (`status_bar.js`, new)

- Fixed 24px footer: **provider health** (healthy/degraded/unavailable, color-coded), **active chat model** (tooltip lists code/vision models), **GPU/CPU mode + VRAM**, **background jobs**, **version**
- Segments are buttons: provider → Mission Control Inference, model → Model settings, jobs → Job center
- Polls `/api/health` every 60s, pauses while hidden; jobs reuse the existing badge (no extra request)
- Hideable (“Hide status bar” in Settings); the app grid reclaims the space when hidden

Verified live: showed “Ollama · degraded”, `qwen2.5:7b`, “GPU idle 8GB”, “idle”, “v3.1.0”.

### 8. Sidebar context menus (`context_menus.js`, new)

- Right-click on view tabs, Favorites rows, and dock chips: **Open**, **Open in new window** (app-mode popup), **Pin/Unpin Favorites**, **Copy deep link** (`…/#view`)
- Positioned within the viewport, Esc/outside-click dismissal, `role="menu"`, subtle scale-in

### 9. Empty states

- Standardized `.empty-state` classes (icon, title, actions) added to the design system for future views
- Existing Phase-1 empty-state CTAs (projects, suggestions, scene presets, Kasa) left intact — they already follow the explanation + primary action pattern

### 10. Micro-interactions

- View panels cross-fade on switch; sidebar bodies and dashboard cards ease in; toasts slide up; context menus scale in
- Unified 0.15s `--transition-fast` on buttons, chips, swatches
- Focus-visible rings standardized on accent color
- All animation disabled under `prefers-reduced-motion`

### 11. Quick Access Dock (`quick_dock.js`, new)

- Favorites render as one-click chips beneath the title area, current view highlighted with accent
- Fully favorites-integrated: pin/unpin/reorder in the sidebar and the dock follows instantly (`aria-ui-prefs` event)
- Right-click chip: unpin, copy deep link, hide dock; “Hide dock / Show dock” toggle in Settings
- Hidden automatically when there are no favorites

### 12. Smart personalization

- Search ranking boosts favorites, recent views, frequent commands, and frequently used models
- Palette pins/usage (Phase I) now also feed sidebar-search ranking
- All signals stay in browser `localStorage` (`aria_ui_prefs_v1`) — nothing leaves the machine

### 13–15. Visual polish, cognitive load, consistency

- New chrome uses the shared radius/elevation tokens (`--radius-sm/md`, `--elev-1/2`)
- Status/health colors consistent everywhere: green `#7eb87a`, amber `#e8b84a`, red `#d47b6a`
- Section labels tightened (“Accent color” mini-label pattern)
- Progressive disclosure preserved: advanced panels stay collapsed until opened; new chrome (dock, status bar) individually dismissible
- Light-theme variants added for search field, dock, and status bar

---

## Screens modified

Sidebar, view-tab strip, Chat (breadcrumb + suggestions area), Dashboard, Planner (collapsible columns), Settings section, global chrome (status bar, context menus, What's New).

## Performance impact

- One `/api/health` poll per minute for the status bar (cached endpoint, pauses when hidden)
- Search index built lazily on keystroke from in-DOM data — no network
- Animations are opacity/transform only (compositor-friendly)
- No new dependencies; +7 small JS modules (~1.3k lines total), cache-busted

## Accessibility

- Search: `role="combobox"`, `aria-controls`, listbox options with `aria-selected`
- Dock: `role="toolbar"`; status bar: `role="status"`; menus: `role="menu"/"menuitem"`
- Collapsible headers keyboard-operable with `aria-expanded`
- Breadcrumb leaf uses `aria-current="page"`
- Focus-visible rings on all new interactive elements; reduced-motion respected throughout

## Developer notes

- All prefs flow through `AriaUiPrefs` (`aria_ui_prefs_v1`); new keys: `dockHidden`, `statusBarHidden`, `accent`, `dashboardLayout`, `panelCollapsed`
- `window.openCommandPalette(prefill)` opens Ctrl+K with a query and triggers knowledge search
- `aria-view-change` remains the integration point (breadcrumbs, dock, panels, personalization all subscribe)
- Verified: `node --check` on all touched modules, `tests/test_product_ui_api_wiring.py` 14/14 passed, zero console errors in live smoke test

## Deferred ideas

- Full icon sweep of legacy emoji-glyph buttons (⚡ ✦ ⧉ ↻) to a single SVG set
- Drag-and-drop reorder inside the Customize dialog (currently ↑/↓ buttons)
- Resizable dashboard widgets (grid spans)
- Collapsible panels for Mission Control tab internals (owned by `mission_control.js` renderers)
- Notification count segment in the status bar (needs a notification center source)
- “Assign shortcut” context-menu action (needs a shortcut-registry)

## Future recommendations

- Server-side profile sync for `aria_ui_prefs_v1` (multi-device)
- Command aliases in Ctrl+K
- Optional compact density mode (smaller paddings globally)
- Global drag-and-drop file targets per view with a drop-zone overlay
