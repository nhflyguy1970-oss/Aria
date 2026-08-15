# Aria Next Generation — Official Engineering Charter
## Living Workspace · Version 2.0

**Status:** APPROVED  
**Effective:** 2026-08-06  
**Authority:** Final Approval & Engineering Charter (Jeff). Supersedes previous frontend direction. Preserves mature backend architecture.

Governing design package: `docs/ARIA_NEXT_GENERATION_MASTER.md`

---

## Official decisions (locked)

| Decision | Status |
|---|---|
| Living Workspace architecture | ✓ Approved |
| Runtime Independence (permanent law) | ✓ Approved |
| Activities as primary interaction model | ✓ Approved |
| Rooms as flagship destinations | ✓ Approved |
| Tools as contextual capabilities | ✓ Approved |
| Migration Phases 0–11 | ✓ Approved |
| Phase 1 Runtime Spikes | ✓ Authorized |
| Design-before-Code for every flagship room | ✓ Required |

Phase 0 (Architecture Validation) is **complete**.

---

## Product definition

Aria is officially a **Living Workspace** — the place Jeff spends his day.  
Not a browser application, dashboard, product catalog, or page farm.

**Target stack:** Backend → Owned Runtime → Workspace → Activities → Rooms → Tools → Jeff

---

## Engineering laws (normative)

1. **Living Workspace** — One continuous environment.  
2. **Runtime Independence** — Shipped product never requires an external browser. HTML/CSS/JS approved; Chrome/Firefox/Edge/Safari are not the target platform.  
3. **Rooms** — Flagships own experience.  
4. **Tools** — Appear only when needed.  
5. **Activity First** — Jeff performs activities; Workspace assembles rooms+tools. Inspectable, confirmable, overridable.  
6. **Invisible Computer** — Jeff thinks “Aria…”, not pages/products/routes/tabs/models/browsers.  
7. **Experience Before Implementation** — When UX and implementation disagree, question implementation first. No sunk-cost or fashion-driven tech.

---

## Implementation order (locked)

| Phase | Name | Status |
|---|---|---|
| 0 | Architecture Validation | ✓ Complete |
| 1 | Runtime Spikes | **In progress — only authorized work** |
| 2 | Workspace | Blocked until Phase 1 evidence + approval |
| 3 | Workspace Validation | |
| 4 | Runtime R1 | |
| 5 | Chat | Design-before-code; after Workspace |
| 6 | Fly Tying | |
| 7 | Health | |
| 8 | Mission Control | |
| 9 | Remaining flagship rooms | |
| 10 | Tool Demotion | |
| 11 | Polish | |

**Hard stop:** No Chat / Fly Tying / Health / room redesign / Workspace implementation until Phase 1 completes and runtime evidence is reviewed.

---

## Phase 1 mandate

Evaluate E1, E2, E3 (and superior alternatives only) equally on:

Startup · Memory · GPU · Rendering · Python integration · Packaging · Linux · Windows · Future macOS · Accessibility · Long-session stability · Local AI · Update model · Developer workflow · Five-year maintainability

**Runtime is not selected until evidence exists.**

Spike report: `docs/ARIA_PHASE1_RUNTIME_SPIKES.md`

---

## Success

Jeff launches Aria and feels he entered a place built for him.  
He says “Aria…” and begins his day.

Every future change answers:  
*Will this help Aria become a Living Workspace Jeff can live inside every day for the next decade?*
