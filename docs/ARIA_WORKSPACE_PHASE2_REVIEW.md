# Aria Living Workspace — Phase 2 Review Package

**Status:** Ready for Jeff review  
**Runtime R1:** E1 Electron (frozen) — `docs/ARIA_RUNTIME_R1_DECISION.md`  
**Scope:** Workspace + Activity Engine only. **No room redesigns.**

---

## What was built

### Runtime host
- `scripts/electron-shell/main.js` — branded Aria window (no browser chrome theater)
- Default GUI mode → `electron` (`gui_launcher.py`, launch lib)
- `scripts/launch-aria-workspace.sh` — one-command Living Workspace launch
- URL forces `app=1&shell=electron&workspace=1`

### Workspace environment
| Module | Role |
|---|---|
| `workspace/contracts.js` | Room / Tool / Activity interfaces |
| `workspace/registry.js` | Catalog of activities, room adapters, tools |
| `workspace/chrome_policy.js` | Hide tabs / eng voice / capability walls per policy |
| `workspace/activity_engine.js` | Start/inspect/stop activities; recipes |
| `workspace/tools.js` | Contextual tool invoke |
| `workspace/spotlight.js` | Ctrl+K activity/tool summon |
| `workspace/workspace.js` | Orchestrator |
| `workspace/workspace.css` | Quiet chrome |

### UI furniture (minimal)
- `#wsBar` — activity label + recipe + Activity / Recipe buttons  
- `#wsToolTray` — contextual tool chips only when an activity needs them  
- `#wsSpotlight` — Ctrl+K  

Legacy 32-tab strip is **hidden under workspace chrome policies** (not deleted — adapters still work).

---

## How to use (review)

```bash
./scripts/launch-aria-workspace.sh
# or, server already up:
JARVIS_GUI_MODE=electron ./scripts/launch-jarvis.sh
```

Inside Aria:
1. You should see a quiet top bar: activity name + recipe  
2. **Ctrl+K** → pick an activity (Coding, Fly tying, Health check-in, …)  
3. **Recipe** button → inspect composition (never magical)  
4. Tool chips appear only for that activity  
5. Permanent view-tabs / STT engineering controls stay out of the way  

Browser host (dev only): open  
`http://127.0.0.1:8765/?app=1&workspace=1`

---

## Charter tests (self-check)

| Test | Expected now |
|---|---|
| Three Second | Activity label + room content; not a tab catalog |
| One Hour | Chrome policy keeps furniture quiet; Ctrl+K when needed |
| Invisible Computer | Window titled Aria; no URL bar; runtime not mentioned in UI |
| Living Workspace | Entering feels like an environment + activity, not “open a page” |
| Activity | Intent → composition with inspectable recipe |
| Context | Tool tray matches activity; capability walls hidden |

**Honest limit:** Room *interiors* are still the old panels (adapters). Immersive rooms are Phase 5+. Phase 2 delivers the **environment** they will inhabit.

---

## Explicitly not done (correct)

- Chat / Fly Tying / Health / Mission / Documents redesigns  
- New product features  
- Backend changes  
- Further runtime bake-offs  

---

## Approval gate

Reply: **Workspace approved — begin Chat** · **Revise Workspace: …** · **Not yet**

Until then, stop. No room implementation.
