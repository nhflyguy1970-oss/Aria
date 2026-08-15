# Aria GUI Modernization

**Date:** 2026-07-25  
**Scope:** User interface and experience only (no certification pass, no backend bug hunt, no architecture redesign)  
**Baseline:** Certified Aria GUI 3.1.0 / UI 5.16.x → modernized build **5.16.140**

---

## Executive summary

This pass makes Aria feel more like a mature desktop AI environment: compact by default, one-click favorites, an always-visible Restart Server control, rotating intelligent chat suggestions, clearer discoverability, a richer home dashboard, and a smarter Ctrl+K palette — while keeping Aria’s identity (DM Sans, warm accent, arc branding).

Users should notice immediately that:

- Navigation takes fewer clicks for daily tools
- The sidebar starts quiet instead of fully expanded
- Suggestions change across launches and contexts
- Important new capabilities are easy to find without nagging forever

---

## Screens modified

| Surface | Changes |
|---|---|
| Sidebar | Favorites, Restart Server, regrouped sections, collapse-by-default, width resize |
| View tabs | Pin ★ for current view |
| Chat composer | Dynamic rotating suggestion chips |
| Dashboard | Quick launch, recent views, provider health, What's New entry |
| Command palette | Pinned commands, usage weighting, Recent/Pinned groups |
| Global overlays | What's New modal, soft tip banner |
| Visual system | Spacing, hierarchy, badges, progress, hover/focus polish |

---

## UI improvements

### Sidebar

| Before | After | Why |
|---|---|---|
| Most sections expanded on launch | All expandable sections **collapsed by default**; state remembered per user (`aria_ui_prefs_v1` + migration `jarvis_sidebar_collapse_migrated_v2`) | Compact startup; less visual noise |
| Restart buried in Chat & data button grid | Dedicated **Restart Server** control directly above Mode, always visible, with icon, confirm, progress spinner, status, disable-while-busy | Operator action must be one click and feedback-rich |
| Flat/mixed grouping (Capabilities, Services, Video, Chat & data, Coding…) | Logical groups: **Favorites → Restart → Mode → AI → Workspaces → Media → Maker → System → Mission Control → Integrations → Agent tools → Smart Home → Settings → Developer → Model settings → Tips** | Matches how people work |
| No favorites | **Favorites** at top: pin/unpin, drag-reorder, remembered order, one-click remove | Daily tools in one click |
| Fixed 260px rail | Drag handle to resize; width remembered | Desktop QoL |

### Chat suggestions

| Before | After | Why |
|---|---|---|
| Same static six prompts every launch from `/api/suggestions` | Client-side **rotating pool** (shortcuts, workflows, time-of-day, context, features, inspiration) with anti-repetition and click learning | Feels alive; teaches the product |
| Chips only fill the prompt | Chips can open palette, views, What's New, or send short commands | Fewer steps |

### Discoverability

- **What's New** modal (once per modernization version; reopen from Settings / Dashboard)
- Soft tip banner that auto-hides after repeated exposure / dismiss
- Subtle **New** badges on Favorites / Restart / What's New until acknowledged
- Header ★ pin with hover titles

### Dashboard / home

Added:

- **Quick launch** from Favorites
- **Recent** views
- **Provider health** pill (Ollama healthy/degraded/unavailable + Aria ready)
- What's New button

Existing briefing, scenes, intel, and checklist remain.

### Command palette (Ctrl+K)

- **Pinned** commands (★ on each row)
- Stronger ranking for pins + usage counts
- Empty-query groups: Pinned → Recent → rest
- Prefs synced through `AriaUiPrefs`

---

## UX / workflow improvements

1. **One-click resume** of favorite views from sidebar or dashboard  
2. **Pin current view** without opening Settings  
3. **Collapse all / Expand sidebar** explicit controls  
4. **Restart** feedback loop: confirm → busy → wait for health → reload (or keep going if media job active)  
5. **Suggestion → action** without retyping  
6. **Palette pins** for repeated operator actions  
7. **View change events** (`aria-view-change`) feed recent views + suggestion context  

---

## New capabilities

| Module | Role |
|---|---|
| `ui_prefs.js` | Shared local preferences (favorites, collapse, width, recents, usage, tips) |
| `sidebar_favorites.js` | Favorites list, DnD, header pin sync |
| `sidebar_chrome.js` | Collapse defaults, resize, Restart Server UX, view-jump wiring |
| `chat_suggestions.js` | Dynamic suggestion engine (overrides `loadSuggestions`) |
| `discoverability.js` | What's New + soft tips + badges |

Preferences persist in the browser via `localStorage` key `aria_ui_prefs_v1` (workstation-local user prefs).

---

## Visual improvements

- Tighter sidebar section padding and hover borders
- Favorites rail with accent-tinted pinned section
- Restart button as a primary system control (not a tiny ghost button)
- Pill suggestion chips with category-tinted borders
- Dashboard quick-rail cards
- Command palette pin column
- Soft tip toast-like banner
- Sidebar resize affordance
- Respects `prefers-reduced-motion`

Identity preserved: warm gold accent, DM Sans / JetBrains Mono, deep panel background — no purple-on-white reskin.

---

## Accessibility improvements

- Restart status uses `aria-live`
- Favorites unpin buttons have aria-labels
- Pin control uses `aria-pressed`
- What's New is a proper dialog with labelled title
- Soft tips are `role="status"`
- Focus-visible styles on fav buttons and suggestion chips
- Resize handle exposed as `role="separator"`

---

## Performance improvements

- Sidebar starts collapsed → less layout/paint on first paint for heavy panels (HA, models, coding)
- Suggestion rotation pauses while `document.hidden` or not on Chat
- Health on dashboard is a single lightweight `/api/health` fetch
- No new polling loops beyond existing product patterns

---

## Reasons for every major change

| Change | Reason |
|---|---|
| Collapse-by-default | Premium apps open quiet; power panels stay available |
| Favorites | High-frequency tools should not compete with 21 tabs |
| Restart above Mode | Critical ops control was discoverability-failing |
| Dynamic suggestions | Static chips train users to ignore them |
| What's New once | Surface modernization without permanent clutter |
| Dashboard quick rail | Home should launch work, not only show news |
| Palette pins/usage | Ctrl+K becomes a personal launcher |
| Width memory | Desktop muscle memory |

---

## Deferred ideas / future recommendations

- Sync `aria_ui_prefs_v1` to a server-side profile for multi-device
- Collapse rarely used **view tabs** into a “More” menu while keeping Favorites primary
- Per-suggestion server personalization (beyond local click counts)
- Command aliases / custom named workflows in the palette
- Screenshot gallery in this doc (capture on live desktop when convenient)
- First-run interactive tour (optional, skippable)
- Remember last Mission Control tab and last Planner filter in the same prefs bag (hooks ready via `lastFilters`)

---

## Files touched (primary)

- `jarvis/gui/static/index.html`
- `jarvis/gui/static/style.css`
- `jarvis/gui/static/ui_prefs.js` *(new)*
- `jarvis/gui/static/sidebar_favorites.js` *(new)*
- `jarvis/gui/static/sidebar_chrome.js`
- `jarvis/gui/static/chat_suggestions.js` *(new)*
- `jarvis/gui/static/discoverability.js` *(new)*
- `jarvis/gui/static/command_palette.js`
- `jarvis/gui/static/view_router.js`
- `jarvis/gui/static/planner.js`
- `jarvis/gui/static/movie_tiers.js` (collapse/restart ownership moved to `sidebar_chrome.js`)
- `docs/ARIA_GUI_MODERNIZATION.md` *(this file)*

---

## Verification notes

Manual checks recommended after reload:

1. Sidebar opens compact; expand/collapse persists across reload  
2. Favorites pin/unpin/drag order persists  
3. Restart Server confirms, disables, shows progress, recovers  
4. Chat chips change after ~45s and across reloads  
5. Ctrl+K shows Pinned/Recent; ★ pins a command  
6. Dashboard shows favorites + health  
7. What's New appears once, then only via button  

No certification re-run was performed as part of this pass.
