# Phase 6.5 — Unpack the Last Boxes — Certification

**Date:** 2026-08-07  
**Runtime:** Living Workspace (`?workspace=1`), Playwright chromium headless against local Aria (`:8765`).

---

## Certification statement

**The Living Workspace is now a complete functional replacement for the original Aria for user-facing House Controls, Room furniture, and the interaction paths exercised in this phase.**

Every capability that was proven missing or broken under `#ariaLegacyShell[inert]` has been repaired, verified, and regression-tested. Furnished Rooms remain on `#ariaStage`. Dialogs that must be used from House Controls are portaled out of the inert shell. Modifier keyboard chords work while the Living Room composer is focused.

Where behavior differs from classic Aria, the difference is intentional and user-visible:

- **Split view** in Living Workspace shows a toast and stays deferred (dual-pane would bypass furnish). Classic Aria retains split.
- **Front Door** owns navigation search (Ctrl+Shift+F) and command entry formerly tied to the inert sidebar / palette.

---

## Defects found and repaired

| # | Defect | Repair |
|---|---|---|
| 1 | House Control modals opened under `inert` (Activity, Jobs, Shortcuts, Layouts, Uncensored auth) — unusable | `workspace/modal_portal.js` moves dialogs to `document.body` on LW enable |
| 2 | `AriaActions.system.*` used inert `.click()` for theme/VRAM/backup/debug/reload/uncensored | Direct APIs: `setAriaTheme`, `freeJarvisVram`, `reloadJarvisUi`, backup/debug fetch, `toggleAriaUncensored` |
| 3 | Ctrl+Shift+F focused inert sidebar search | Opens Front Door in LW |
| 4 | Keyboard chords ignored while `#messageInput` focused | `keyboard_nav`: allow modifier chords when typing; capture-phase listener |
| 5 | Mini chat auto-closed on chat surface in LW | `mini_chat.js`: do not auto-close in Living Workspace |
| 6 | Living Room re-entered while converse still “current”, restoring furnished panels into inert shell (Mission Scan invisible) | `living_room.js`: refuse enter/sync when `dataset.furnished` and room ≠ chat |
| 7 | Split view bypassed furnish | Toast deferral in LW (`keyboard_nav` + `split_view.js`) |

---

## Verification evidence

- **P0 House Controls:** shortcuts, activity focus, job center, theme, free VRAM, uncensored auth focus, backup/debug invoke, Front Door via Ctrl+Shift+F — PASS  
- **Room residency:** 33 rooms enter with visible stage mount (Chat = Living Room) — PASS  
- **Mission Scan & diagnose:** visible on stage; click opens Guided Repair overlay (~6s scan) — PASS  
- **Fly export/print:** recipe select → export API + print window — PASS  
- **Regression:** portals + theme/VRAM after Living Room steal fix — PASS  

Inventory: `docs/ARIA_PHASE6_5_BEHAVIORAL_INVENTORY.md`.

---

## Whole-house residency

An uninterrupted Living Workspace walk covering House Controls, Front Door, full Room enter sweep, Mission Guided Repair, and Fly export/print completed without discovering a remaining missing original capability in those paths. Known intentional deferral: split view.

---

## Files touched (primary)

- `jarvis/gui/static/workspace/modal_portal.js` (new)
- `jarvis/gui/static/workspace/workspace.js`
- `jarvis/gui/static/aria_actions.js`
- `jarvis/gui/static/activity_center.js`
- `jarvis/gui/static/modules/jobs.mjs`
- `jarvis/gui/static/movie_tiers.js`
- `jarvis/gui/static/keyboard_nav.js`
- `jarvis/gui/static/sidebar_search.js`
- `jarvis/gui/static/split_view.js`
- `jarvis/gui/static/uncensored_mode.js`
- `jarvis/gui/static/mini_chat.js`
- `jarvis/gui/static/workspace/rooms/living_room.js`
- `jarvis/gui/static/workspace/rooms/furnish.js`
- `jarvis/gui/static/index.html` (script tags / cache bumps)

---

*Phase 6.5 complete under the behavioral certification law.*
