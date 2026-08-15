# Aria House Integrity Report
## Demolish the legacy shell — Living Workspace IS Aria

**Date:** 2026-08-06  
**Status:** COMPLETE (layout/paint ownership). Remaining inventory blockers listed below.  
**Authority:** House Integrity stop-work directive — no polish until this report.  
**Proof artifact:** `docs/_house_integrity_proof.json` (headless Chromium, PASS)

---

## 1. Root cause

The Living Workspace was **not** an application. It was a **class-toggled CSS/JS skin** over the monolithic legacy Aria shell in `index.html`.

| Layer | What it did wrong |
|---|---|
| **DOM** | Full `.app` tree always mounted: sidebar, `nav.view-tabs` (~32 tabs), every `.view-panel`, status bar, startup overlay, toasts |
| **Paint timing** | `body.living-workspace` was applied at `DOMContentLoaded` from a late script — **after first paint** of legacy UI → flash of old Aria |
| **Hiding** | Rooms “owned” the experience by `display: none !important` on chrome — temporary tricks, not ownership |
| **Adapters** | `living_room.js` / `house_host.js` decorated panels **in place** inside `.app` — dual render trees |
| **Router** | `view_router.js` continued show/hiding all panels inside the legacy shell |

When Chat failed or lagged, CSS/JS that cloaked the shell had not yet applied (or the Room had not mounted). The legacy interface was still underneath. That is the defect.

**Verdict:** New Aria was painted *on top of* old Aria. The old house was never demolished.

---

## 2. Architecture — before / after

### Before (skin)

```
┌─────────────────────────────────────────────┐
│  body (+ living-workspace class, late)      │
│  ┌───────────────────────────────────────┐  │
│  │ .app  ← ALWAYS LAYOUT PARTICIPANT     │  │
│  │  sidebar · view-tabs · status bar     │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │ ALL view-panels (show/hide)     │  │  │
│  │  │ + Living Room CSS overrides     │  │  │
│  │  └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### After (one house)

```
┌─────────────────────────────────────────────┐
│  html.living-workspace  (pre-paint claim)   │
│  ┌───────────────────────────────────────┐  │
│  │ #ariaStage  ← ONLY paint root         │  │
│  │   exactly ONE Room panel mounted      │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │ .app#ariaLegacyShell                  │  │
│  │   display:none · inert · aria-hidden  │  │
│  │   inventory only (panels parked here) │  │
│  │   NEVER participates in layout/paint  │  │
│  └───────────────────────────────────────┘  │
│  #wsSpotlight (Ctrl+K) — outside shell     │
└─────────────────────────────────────────────┘
```

**Ownership rule now:** Workspace owns `#ariaStage`. House mounts one Room. Rooms own the visual tree on the stage. Legacy UI owns nothing in the painted tree.

---

## 3. What was removed from the Living Workspace runtime

### Legacy components removed from layout/paint

| Component | Action |
|---|---|
| `.app` shell (sidebar, tabs, main chrome grid) | `display:none` + `visibility:hidden` + `pointer-events:none` under `html.living-workspace`; marked `inert` + `aria-hidden` |
| `#ariaStatusBar` | Not painted (prepaint + shell demolition) |
| `#jarvisBootFlash` | Not painted under workspace |
| `#startupOverlay` | Gated off in `startup_overlay.js` when workspace claimed; also CSS-demolished |
| Toast container | Prepaint hide under workspace |
| Sidebar / view-tabs / quick dock | Demolished with `.app` (not merely Room CSS) |

### Legacy render trees removed

| Tree | Action |
|---|---|
| Dual Chat (stage + under shell) | Chat panel **moved** onto `#ariaStage` (not cloned). Only one `#chatView` in document |
| Multi-panel show/hide under workspace | `view_router.js` no longer toggles panels inside `.app` when Living Workspace is on — delegates to `AriaHouse.enter` |
| House / Living Room in-place decoration | Both mount through `AriaStage.mount` — exclusive stage child |

### Legacy CSS removed / superseded

| Change | File |
|---|---|
| Pre-paint claim + demolition rules | `index.html` (`#aria-house-integrity-prepaint`) |
| Stage as exclusive root | `workspace/workspace.css` v2.1.0-integrity |
| Dropped house `.app` grid patch (irrelevant once shell gone) | `rooms/house.css` |

### Legacy JavaScript removed / redirected

| Module | Change |
|---|---|
| `workspace/rooms/stage.js` | **NEW** — exclusive mount/clear/proof API |
| `workspace/rooms/house_host.js` | Mounts Rooms onto stage; `clearStage()` for Invisible Test; v4.1.0-integrity |
| `workspace/rooms/living_room.js` | Mounts `#chatView` onto stage on enter; v3.8.0-integrity |
| `workspace/workspace.js` | Claims `html`+`body`, inert legacy shell, enters via House; v2.1.0-integrity |
| `view_router.js` | Workspace path → House ownership (no legacy panel flip); v2.0.0-integrity |
| `startup_overlay.js` | Never shows overlay when Living Workspace claimed |

---

## 4. The Invisible Test

**Procedure:** With Living Workspace on, call `AriaHouse.clearStage()` (disables Chat / clears stage).

| Expected | Result |
|---|---|
| Empty Workspace (`#ariaStage` children = 0) | **PASS** |
| Stage background only (`rgb(10, 12, 16)`) | **PASS** |
| Legacy `.app` still `display: none` | **PASS** |
| No legacy `.view-panel` painted | **PASS** |
| Old Aria visible underneath | **FAIL mode — did not occur** |

Repeated for room walk: flytying → health → mission → chat — always **exactly one** stage child; legacy shell never displayed; no duplicate Chat.

---

## 5. Proof (measured)

From `docs/_house_integrity_proof.json` (PASS):

```
workspaceClaimed: true
legacyDemolished: true   (.app display:none)
chromeGone: true         (sidebar / tabs / status not visible)
chatOnStageOnly: true
invisibleEmpty: true
invisibleNoOldAria: true
noDuplicateChat: true
alwaysOneStageChild: true
```

Room walk mounts: `flytyingView` → `healthView` → `workstationView` → `chatView`.

---

## 6. Memory & startup

| Metric | Assessment |
|---|---|
| **Paint / layout** | Legacy shell no longer participates — major win vs dual trees fighting for layout |
| **First paint flash** | Eliminated by **pre-paint** `html.living-workspace` claim in `<head>` |
| **Startup overlay** | Skipped under workspace — no competing boot UI |
| **JS heap / DOM nodes** | Inactive Room panels still exist as **parked inventory** under inert `.app` (not painted). Full DOM deletion of unused Rooms is a remaining blocker (see §7) |
| **Duplicate listeners** | Panels are **moved**, not cloned — IDs and wired listeners preserved |

Honest memory claim: we demolished **paint and layout ownership**, not yet every inactive panel node from the document.

---

## 7. Remaining migration blockers

These are **not** “hide with CSS” leftovers for the painted tree. They are the next demolition steps:

1. **Inventory DOM** — Inactive `#*View` panels still live under `#ariaLegacyShell` until each Room has a native tree that does not require moving legacy markup.
2. **Content adapters** — Room *contents* (Health markup, Fly Tying cards, Mission widgets) are still the legacy panel implementations **relocated** to the stage. Architecture ownership of the shell is fixed; per-Room content rewrite is separate (polish gate remains closed until product asks for it).
3. **Script payload** — Legacy JS modules still load (chat_*, dashboard_*, etc.) because Rooms still call their `init*` / send pipelines. Dead-code elimination of unused views under workspace is a follow-on.
4. **wsBar / tool tray** — Still physically inside demolished `.app`. Spotlight (`#wsSpotlight`) remains outside and works. Re-homing Activity chrome onto the stage (if desired) is optional furniture — not a dual-app regression.
5. **`?workspace=0`** — Legacy browser mode still available; shell paints only when Living Workspace is not claimed.

---

## 8. Room verification matrix

| Room | Legacy shell painted? | Legacy CSS in layout? | Hidden legacy DOM mounted under stage? | Adapter wraps old panel? |
|---|---|---|---|---|
| Chat (Living Room) | No | No (shell demolished) | No under stage; inventory parked | Panel moved to stage (migration bridge for content IDs) |
| Fly Tying | No | No | No under stage | Same — content still legacy panel |
| Health | No | No | No under stage | Same |
| Mission | No | No | No under stage | Same |
| Other House rooms | No | No | No under stage | Same |
| Empty stage (Invisible Test) | No | No | Stage empty | N/A |

**Shell question answered:** Is any legacy **interface** still rendering underneath? **No.**  
**Content question (honest):** Are Room interiors still the migrated panel markup? **Yes** — until native Room trees replace them. That is content migration, not a second application under the Workspace.

---

## 9. Success criteria (directive checklist)

| Criterion | Status |
|---|---|
| One Living Workspace | **PASS** — `#ariaStage` |
| One active Room | **PASS** — exclusive mount |
| No hidden legacy application underneath | **PASS** — Invisible Test |
| No duplicate Chat / Nav / Sidebar / Status painted | **PASS** |
| Not “new Aria on top of old Aria” | **PASS** for shell/paint |
| Adapters removed where migration complete | **Shell adapters removed**; content bridges remain until Room native trees |

---

## 10. Files touched

- `jarvis/gui/static/index.html` — pre-paint claim, `#ariaStage`, cache busts
- `jarvis/gui/static/workspace/rooms/stage.js` — **new**
- `jarvis/gui/static/workspace/rooms/house_host.js`
- `jarvis/gui/static/workspace/rooms/living_room.js`
- `jarvis/gui/static/workspace/workspace.js` / `workspace.css`
- `jarvis/gui/static/workspace/rooms/house.css`
- `jarvis/gui/static/view_router.js`
- `jarvis/gui/static/startup_overlay.js`
- `docs/_house_integrity_proof.json`
- `docs/ARIA_HOUSE_INTEGRITY.md` (this report)

---

## 11. Stop-work note

**Polish remains stopped** until product accepts this report. The old house’s **painted existence under the Workspace is demolished.** Further Room aesthetic work must not reintroduce a second shell.
