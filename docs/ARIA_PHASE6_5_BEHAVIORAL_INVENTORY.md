# Phase 6.5 — Behavioral Migration Inventory

**Status:** Living checklist — interaction-level, not Room-level.  
**Law:** Original Aria is the specification. Living Workspace is the implementation. Presence is not certification; behavior is.  
**Method:** Exercise each interaction in Living Workspace (`?workspace=1`). On failure: stop → diagnose → repair → verify → regress → continue.

---

## Track A — Inert-shell House Controls (P0)

| Interaction | Original path | LW path | Status |
|---|---|---|---|
| Shortcuts modal (Ctrl+/) | `#shortcutsBtn` / modal | `AriaModalPortal` + `AriaActions.system.shortcuts` | Verified |
| Theme toggle | `#themeToggle` | `setAriaTheme` via `AriaActions.system.theme` | Verified |
| Free VRAM | `#freeVramBtn` | `freeJarvisVram` via `AriaActions.system.freeVram` | Verified |
| Uncensored unlock | `#uncensoredToggle` + auth modal | `toggleAriaUncensored` + portaled auth modal | Verified |
| Activity Center | `#activityCenterModal` | Portaled to `body`; focus works | Verified |
| Job Center | `#jobCenterModal` | Portaled; interactive | Verified |
| Layouts modal | `AriaLayouts.openModal` | Portaled `workspaceLayoutsModal` | Verified |
| Backup | `#backupDataBtn` | Direct API fallback when inert | Verified |
| Debug bundle | `#debugBundleBtn` | Direct API fallback when inert | Verified |
| Reload UI | `#reloadUiBtn` | `reloadJarvisUi` | Verified |
| Ctrl+Shift+F nav search | Sidebar search | Front Door open | Verified |
| Mini chat (Ctrl+Shift+K) | `AriaMiniChat.toggle` | Works while chat focused (modifier chords allowed); LW does not auto-close | Verified (API + chord policy) |
| Split view (Ctrl+\\) | Dual pane | Deferred toast in LW (furnish integrity) | Intentional |

---

## Track B — Stage ownership / furnish integrity

| Defect | Repair | Status |
|---|---|---|
| Living Room re-entered while converse activity active, restoring furnished panels into inert shell | `shouldBeInLivingRoom` + `enter` + `syncFromActivity` refuse when `dataset.furnished` and room ≠ chat | Verified — Mission/Fly stay on `#ariaStage` |
| Mission Recovery Scan & diagnose not visible (panel in shell) | Same Living Room steal fix | Verified — `#mcGuidedRepairScan` visible and clickable |
| Guided Repair scan (~6s) opens overlay | Button + `AriaGuidedRepair.scanAndShow` | Verified |

---

## Track C — Room behavioral samples

| Room / workflow | Behavior checked | Status |
|---|---|---|
| Chat / Living Room | Composer focus, immersion | Verified |
| Fly Tying | Recipe select → Export fetch → Print window | Verified |
| Health | 31 tabs; Print tab reachable | Verified |
| Mission | 20 tabs; Recovery; Scan & diagnose → overlay | Verified |
| Journal | Rapid log; print/export controls | Verified |
| Documents / Search / Memory | Surfaces + Memory dialog portaled | Verified |
| Automation | Dry-run control present | Verified |
| Gallery / Settings / Audio | Surfaces furnished | Verified |
| All registered Rooms | Enter → mounted visible panel (or Living Room for chat) | Verified (33 rooms) |

---

## Track D — Entry path parity

| Path | Example | Status |
|---|---|---|
| Front Door | Theme control (~79 catalog entries) | Verified |
| AriaHouse.enter | Room sweep | Verified |
| AriaActions | System House Controls | Verified |
| Keyboard | Ctrl+/, Ctrl+Shift+F; modifier chords while typing | Verified |

---

## Residual / intentional

- **Split view in Living Workspace:** deferred with user-visible toast — dual-pane would bypass furnish. Classic Aria retains split.
- **Command palette Ctrl+K:** Front Door owns this surface in LW (by design).
- **Scan latency:** Guided Repair scan API ~6s; UI must wait for overlay (not a migration loss).

---

*Updated with Phase 6.5 stop→repair loop evidence.*
