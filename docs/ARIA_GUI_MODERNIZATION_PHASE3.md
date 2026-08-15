# Aria GUI Modernization — Phase III

**Date:** 2026-07-25  
**Scope:** UI/UX only — no certification, no backend redesign, no architecture rewrite  
**Baseline:** Phase II build 5.16.141 → **5.16.150**  
**Theme:** World-class desktop AI operating environment (friction reduction, context, speed)

---

## Executive Summary

Phase III turns Aria from a polished desktop app into a **workflow-first AI OS shell**. Users can right-click almost anything, open **context-aware Ctrl+K**, switch **named workspace layouts**, run a **split dual-pane**, ask a **floating mini-chat** from any screen, triage noise in an **Activity Center**, resume work from a **smart welcome** card, and replay **recorded workflows**.

All new state stays in browser prefs (`aria_ui_prefs_v1`). No new backend services. Verified live: split panes isolate correctly after view switches; Activity Center, workspaces, mini-chat, history, and keyboard nav modules load; `tests/test_product_ui_api_wiring.py` **14/14** passed; Phase III JS modules pass `node --check`.

---

## Improvements by area

### 1. Universal context menus (`context_menus.js`)

| Before | After |
|---|---|
| Right-click mostly on tabs / favorites / dock | Object-aware menus across planner tasks, memory, gallery, fly patterns, projects, documents, journal, models, services, and chrome |

Typical actions (filtered per object): **Open**, **Open in new window**, **Split with Chat**, **Pin / Favorite**, **Copy**, **Copy deep link**, plus object-specific extras (export / properties / delete when wired).

Menus use `role="menu"`, Esc / outside-click dismiss, viewport clamping, and focus on the first item.

### 2. Context-aware command palette (`command_palette.js`)

Ctrl+K now prepends a **This page** group ranked above global actions:

| View | Context commands (examples) |
|---|---|
| Gallery | Generate, Compare, Focus prompt |
| Planner | New task, Pomodoro, Jump to today |
| Mission Control | Diagnostics, Jobs, Activity, Logs |
| Memory | Search, Recall, Export |
| Browser | Focus task, Research |
| Chat | Clear, Mini chat, Split Chat+Planner |
| Dashboard | Customize, Workspaces, Refresh welcome |
| Journal / Calendar / Fly Tying / Maker / Projects / Documents / Video / Audit | Page-specific focus + workflow shortcuts |

Global Phase III actions always available: Activity Center, Workspaces, Split, Mini chat, Workflows. Ranking boosts context (`+55`) so the active page wins. `openCommandPalette(prefill)` remains the Search Everything handoff from sidebar search.

### 3. Workspace layouts (`workspace_layouts.js`)

Presets: **Coding**, **Writing**, **Research**, **Fly Tying**, **Maker**, **Media**, **Planning**, **Dashboard**.

Each snapshot can remember favorites, dock/status visibility, sidebar width/collapse, dashboard layout, split pair, and last primary view. Users can **Save current** as a custom layout and switch instantly (**Ctrl+Shift+P** or chrome button).

### 4. Intelligent home dashboard (`smart_welcome.js` + planner dashboard)

Dashboard injects a **smart welcome** card:

- Time-aware greeting  
- Resume last view / recent prompt  
- Favorite workspace switcher  
- Light provider / Mission Control awareness hooks  
- Suggested next actions without nagging  

Widget customize (Phase II) remains; welcome sits above the living workspace content.

### 5. Global Activity Center (`activity_center.js`)

Central modal for notifications, warnings, errors, and job-ish events:

- Search + type filters  
- Clear / copy details / jump to source when available  
- Hooks toast `error`/`warn` into the feed  
- Status-bar badge / unread count (**Ctrl+Shift+A**)  
- Graceful job sync (404-safe)

### 6. Search Everything (bridge)

Unified path today:

1. Sidebar search (**Ctrl+Shift+F**) — views, settings, models, tools  
2. Last row → **Ctrl+K** with prefill → federated / knowledge commands  
3. Palette context group + history-backed recent searches  

Ranking already blends favorites, recent views, command usage, and context. A deeper single-index federated UI remains a future recommendation (see Deferred).

### 7. Split view (`split_view.js`)

Dual panes: drag resize, swap, exit, picker for secondary view.

- Primary / secondary remembered in prefs  
- `view_router` respects split (does not hide both panes)  
- Pane hygiene fix: switching views while split **moves stray panels back to `#mainContent`** so only the intended pair stays visible  

Shortcut: **Ctrl+\\**.

### 8. Floating mini chat (`mini_chat.js`)

FAB ✦ + dockable panel:

- Ask / quick prompts (summarize, memory, translate, explain code)  
- Sends into main chat pipeline  
- Hide preference + Dock to full Chat  
- **Ctrl+Shift+M**

### 9. Global history (`global_history.js`)

Tracks recent **views, commands, searches, prompts, models, workflows** via `AriaUiPrefs.pushRecent`. Palette and welcome consume lists for one-click resume.

### 10. Intelligent AI suggestions (`chat_suggestions.js`)

Contextual chips replace generic noise: Activity when alerts exist, Workspaces, Split, coding/projects, gallery after image work, etc. Seen/click prefs keep suggestions from becoming annoying.

### 11. Premium empty states

Design-system polish on `.empty-state` (dashed panel, circular icon plate). Activity Center empty feed uses the pattern. Broader illustration + Learn More sweep across every legacy list is deferred where content already has CTAs.

### 12. Keyboard-first experience (`keyboard_nav.js`)

| Shortcut | Action |
|---|---|
| Ctrl+1…9 | Jump Favorites (fallback ordered views) |
| Ctrl+Tab / Shift+Ctrl+Tab | Cycle primary views |
| Alt+← / Alt+→ | View history back / forward |
| Ctrl+Shift+P | Workspace layouts |
| Ctrl+Shift+A | Activity Center |
| Ctrl+Shift+M | Mini chat |
| Ctrl+\\ | Toggle split |
| Ctrl+, | Settings |
| Ctrl+/ | Shortcuts help |
| Ctrl+K | Command palette (existing) |
| Ctrl+Shift+F | Sidebar search (existing) |

Documented in Shortcuts UI / What's New; typing targets ignore navigation chords.

### 13. Workflow recording (`workflow_recorder.js`)

Record a sequence of view navigations → save named routine (e.g. Morning Routine) → one-click replay. Modal from chrome / palette.

### 14. Smart welcome experience

Covered in §4 — personalized resume, not a one-shot tour. Versioned What's New: `2026.07.25-gui-phase3`.

### 15–16. UI consistency & micro-polish

- Active tab underline accent  
- Context palette group accent color  
- Split resize handle hover → accent  
- Mini-chat / activity / welcome share radius, elevation, and card-in motion  
- Reduced-motion disables hover scale and entrance animations  
- Chrome buttons: Activity, Workspaces, Workflows aligned with existing ghost/icon language  

### 17. Performance

- No new polling loops beyond Activity’s opportunistic job sync (failure-safe)  
- Prefs localStorage only; history lists capped  
- Split DOM moves panels (no clone)  
- Animations are opacity/transform  
- Modules are small, deferred-friendly IIFEs; cache-bust **5.16.150** / per-module `?v=`  

### 18. Extra UX ideas shipped

- Status-bar Activity segment with unread hint  
- Split bar label (`Primary · Secondary`) + Exit / Swap / Pick  
- Workspace chips mark the active layout  
- Context menu “Split with Chat” from any view tab  
- Welcome card integrates workspace modal in one click  

---

## Screens / surfaces modified

| Surface | Changes |
|---|---|
| Global chrome | Activity / Workspaces / Workflows controls; mini-chat FAB; split bar/host; modals |
| Status bar | Activity unread segment |
| Command palette | Context group + Phase III global commands |
| Context menus | Expanded object coverage |
| Dashboard | Smart welcome inject |
| Chat | Smarter suggestion chips |
| Split host | Dual panes for any paired views |
| Settings / Shortcuts / What's New | Phase III discovery copy |
| `style.css` | Phase III block (~260 lines) |
| `index.html` | Markup + scripts; UI version **5.16.150** |

## New modules

| File | Global API |
|---|---|
| `global_history.js` | `AriaHistory` |
| `activity_center.js` | `AriaActivity` |
| `workspace_layouts.js` | `AriaWorkspaces` |
| `split_view.js` | `AriaSplitView` |
| `mini_chat.js` | `AriaMiniChat` |
| `keyboard_nav.js` | `AriaKeyboard` |
| `workflow_recorder.js` | `AriaWorkflows` |
| `smart_welcome.js` | `AriaSmartWelcome` |

Updated: `context_menus.js`, `command_palette.js`, `chat_suggestions.js`, `view_router.js`, `ui_prefs.js`, `discoverability.js`, `planner.js`, `index.html`, `style.css`.

---

## Before vs After (workflows)

| Workflow | Before | After |
|---|---|---|
| “I’m on Gallery — generate” | Hunt chat / remember prompts | Ctrl+K → Generate at top |
| Dual focus (Planner + Chat) | Tab flip constantly | Split + resize; remembered |
| Morning resume | Open Dashboard, guess next step | Welcome card: continue / workspace |
| Job / toast noise | Ephemeral toasts only | Activity Center searchable log |
| Coding day setup | Manually pin + hide chrome | Apply **Coding** workspace |
| Quick ask while in Maker | Leave Maker for Chat | Mini-chat FAB / Ctrl+Shift+M |
| Repeat morning path | Muscle memory | Record → Replay workflow |
| Right-click a task | Nothing / browser menu | Open / copy / related actions |

---

## Accessibility

- Context menus: `role="menu"` / `menuitem`, keyboard Esc, initial focus  
- Activity / workspace / workflow / split modals reuse existing dialog chrome patterns  
- Keyboard nav skips when focus is in inputs / contenteditable  
- Smart welcome actions are real buttons  
- Mini-chat compose is a labeled textarea + Send  
- `prefers-reduced-motion` honored for Phase III motion  

## Consistency improvements

Shared tokens (`--radius-*`, `--elev-*`, `--accent*`, health colors) applied to Activity items, welcome card, mini-chat, split handle. Empty-state language aligned with Phase II. Status/health colors unchanged so Mission Control and the footer still read as one system.

## User experience improvements

- Fewer mode switches for dual-task work  
- Faster discovery of page actions (context palette + menus)  
- Persistent personalization (workspaces + history) without accounts  
- Quieter cognitive load: Activity absorbs alerts; suggestions stay contextual  
- Keyboard parity with modern IDEs / Raycast-style muscle memory  

## Developer notes

- Pref keys added/used: `splitEnabled`, `splitPair`, `splitRatio`, `workspaceLayouts`, `activeWorkspace`, `recordedWorkflows`, `miniChatHidden`, history buckets via `pushRecent`  
- Integration event: `aria-view-change` (history, keyboard stack, split primary update, welcome refresh paths)  
- `AriaSplitView.getState()` drives `view_router` visibility  
- Toast interception in Activity must stay non-breaking if `showAriaToast` is redefined later  
- Cache-bust: bump `jarvis-ui-version` / `style.css?v=` and module `?v=` together when shipping  

## Verification

- Live browser: modules present (`AriaActivity`, `AriaWorkspaces`, `AriaSplitView`, `AriaMiniChat`, `AriaHistory`, `AriaSmartWelcome`, `AriaWorkflows`, `AriaKeyboard`)  
- Split: enable planner+chat → switch to dashboard → left=`dashboardView`, right=`chatView` only (pane hygiene)  
- `node --check` on all Phase III modules  
- `venv/bin/pytest tests/test_product_ui_api_wiring.py` → **14 passed**  

## Screenshots

Live smoke captured during Phase III verification (Chat + mini-chat FAB; split Planner|Chat with welcome; Activity badge on status bar). Store/share from the local browser session as needed; not committed as binary assets.

---

## Deferred / future recommendations

1. **True federated Search Everything UI** — one ranked list over memory, documents, gallery, planner, journal, chats (beyond palette + sidebar bridge)  
2. **Premium empty-state illustrations** on every legacy empty list (SVG set + Learn More links)  
3. **Workflow steps beyond navigation** — click targets, prompt fills, API actions with safe replay  
4. **Activity ↔ real `/api/jobs` deep sync** when endpoint contracts are stable  
5. **Server-side prefs sync** for workspaces/history across devices  
6. **Full emoji→SVG icon sweep** (carry-over from Phase II)  
7. **Assign custom shortcuts** from context menus  
8. **Split + multi-tab chrome** (more than two panes) only if demand proves out  

---

## Final checklist (design intent)

| Question | Answer after Phase III |
|---|---|
| Is every common task easy to discover? | Yes — context palette, menus, What's New, welcome |
| Reach important tools in 1–2 clicks? | Yes — dock, favorites, workspaces, Activity, mini-chat |
| Does every screen feel related? | Yes — shared chrome, tokens, breadcrumbs, accents |
| Is navigation effortless? | Yes — keyboard, history, split, search bridge |
| Visually cohesive? | Yes — Phase III CSS on existing Aria language |
| Enjoyable daily? | Yes — resume, record, reduce friction |

*Phase III complete for GUI modernization. Do not treat this doc as a product certification.*
