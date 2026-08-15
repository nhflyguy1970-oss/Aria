# Aria Next Generation — The Living Workspace
## Master Engineering & Design Package

**Status:** APPROVED (Phase 0 complete). Charter: `docs/ARIA_NEXT_GENERATION_CHARTER.md`.  
**Date:** 2026-08-06  
**Authority:** Master Engineering Directive + Final Approval. Supersedes prior frontend direction for presentation/runtime/UX. Does **not** replace backend architecture.  
**Phase 1:** Runtime R1 **APPROVED AND FROZEN** = E1 Electron (`docs/ARIA_RUNTIME_R1_DECISION.md`).  
**Phase 2:** Living Workspace **APPROVED** — see `docs/ARIA_WORKSPACE_PHASE2_REVIEW.md`.  
**Phase 3:** Living Room (Chat) **BUILT** — see `docs/ARIA_LIVING_ROOM_CERTIFICATION.md`.  
**Phase 3.5:** Immersion — see `docs/ARIA_LIVING_ROOM_IMMERSION.md`.  
**Phase 3.6:** Presence — see `docs/ARIA_LIVING_ROOM_PRESENCE.md`.  
**Phase 3.7:** Familiarity — see `docs/ARIA_LIVING_ROOM_FAMILIARITY.md`.  
**Phase 4:** **HOUSE BUILT** — complete Living Workspace Rooms — see `docs/ARIA_HOUSE_BUILD.md`.  
**House Integrity:** **COMPLETE** — legacy shell demolished from Living Workspace paint/layout — see `docs/ARIA_HOUSE_INTEGRITY.md`. Proof: `docs/_house_integrity_proof.json`.  
**Phase 5:** **FLAGSHIP NATIVE COMPLETE** (P1 + P2 + remaining registry Rooms) — see `docs/ARIA_PHASE5_NATIVE_ROOMS.md`. Proof: `docs/_phase5_flagship_proof.json`.  
**Phase 6:** **RESIDENCY ACTIVE** — Daily Driver Engineering. Operating law: `docs/ARIA_PHASE6_DAILY_DRIVER.md`. Backlog = `docs/ARIA_INTERRUPTION_LOG.md`.  
**Phase 6.1:** **FRONT DOOR COMPLETE** — discoverability + foyer arrival (6.1.1). `docs/ARIA_FRONT_DOOR.md`. Proofs: `_front_door_proof.json`, `_front_door_foyer_proof.json`. House icon · Rooms as doors · search quiet.  
**Phase 6.4:** **FURNISH THE HOUSE** — complete functional migration of original Aria surfaces into the Living Workspace. Inventory: `docs/ARIA_PHASE6_4_FURNISH_INVENTORY.md`. Certification: `docs/ARIA_PHASE6_4_FURNISH_CERTIFICATION.md`. Method: `AriaFurnish` mounts full `#*View` panels (Chat stays Living Room).  
**Evidence base:**  
- `docs/ARIA_FRONTEND_FOUNDATION_REVIEW.md`  
- `docs/ARIA_FRONTEND_ARCHITECTURE_REVIEW.md`  
- `docs/ARIA_LIVING_ROOMS_EXPERIENCE_BRIEF.md`  
- `docs/ARIA_NEXT_GENERATION_DESIGN.md` (supporting draft)  
- `docs/ARIA_NEXT_GENERATION_CHARTER.md` (official charter)

---

# PART A — Validation Verdict

## A.1 Can Aria become a Living Workspace on an owned runtime?

| Claim | Verdict | Basis |
|---|---|---|
| Backend is mature enough to preserve | **PASS** | Product APIs, ACM, Health, Mission, Integrity, etc. already ship |
| Current browser-shell presentation can deliver the vision as-is | **FAIL** | Mandatory chrome + page/panel model; proven by Living Interface failure mode |
| HTML/CSS/JS remain viable *materials* inside an owned runtime | **PASS** | Immersion blocked by composition & packaging, not by markup language |
| External browser as *shipped* runtime | **FAIL (law)** | Violates Runtime Independence |
| Rooms + Tools + Workspace is a coherent decade model | **PASS** | Scales capabilities without permanent chrome growth |
| **Activities** as primary interaction unit | **PASS with constraints** | Powerful; must be explicit, inspectable, and fail-soft (see §C challenges) |
| Ready to implement without further design gates | **FAIL** | Runtime spike + Workspace contract + per-room design packs still required |

**Overall:** The Master Directive is **architecturally sound**. The limiting layer is presentation composition and runtime packaging — not the backend, and not the choice of HTML/CSS/JS as languages.

---

# PART B — Mission & Laws (normative)

## B.1 Mission

Aria is no longer a website, dashboard, or product catalog.  
It becomes a **self-contained Living Workspace**: one continuous local AI environment Jeff inhabits daily for a decade — trustworthy, immersive, independent of any external browser.

## B.2 Goal (cognitive)

Jeff should not think “I’m opening Health / Planner / OCR / Search / Fly Tying.”  
He should think **“I’m asking Aria”** — and the Workspace assembles Activities, Rooms, and Tools.

## B.3 Engineering laws

| Law | Statement |
|---|---|
| **1 Living Workspace** | One continuous workspace — not pages, products, or dashboards. |
| **2 Runtime Independence** | Shipped Aria never depends on an externally installed browser. HTML/CSS/JS OK. Browser = optional transition host only. Aria owns its runtime. |
| **3 Rooms** | Flagship experiences are Rooms. Rooms own the experience. |
| **4 Tools** | Supporting capabilities are Tools. Appear only when needed. |
| **5 Activity First** | Jeff performs Activities. Rooms support Activities. Tools support Rooms. Workspace composes automatically. |
| **6 Invisible Computer** | Jeff must not think about products, routes, tabs, models, providers, frameworks, pages, or browsers. |

## B.4 Architecture shift

```
CURRENT                         TARGET
Backend                         Backend (preserved)
   ↓                               ↓
Browser                         Owned Runtime
   ↓                               ↓
Pages                           Workspace
   ↓                               ↓
Products                        Activities
   ↓                               ↓
Controls                        Rooms
                                   ↓
                                Tools
                                   ↓
                                  Jeff
```

---

# PART C — Challenge every assumption

Independent review must stress-test the directive — not rubber-stamp it.

| Assumption | Challenge | Resolution |
|---|---|---|
| “Jeff never opens products — only asks Aria” | Ambiguous activity (“help me”) must not teleport randomly | Activities are **named, confirmable compositions**. Voice/NLU proposes; Jeff can accept, pin, or override. Escape always returns to a calm foyer/Chat hearth. |
| “Workspace should disappear” | Zero chrome can strand power users and accessibility | Workspace is **quiet by default**, summonable (spotlight, gesture, voice, hotkey). Failure mode is *noticed chrome*, not *zero affordance*. |
| “Activities assemble environments automatically” | Magic assembly without transparency destroys trust | Every Activity has an **inspectable recipe**: rooms + tools + context sources. Guided Repair / Integrity stay explicit when stakes are high. |
| “All flagships are Rooms” | Some “products” fail the physical-place test | Room admission criteria (below). Failures demote to Tools. |
| “HTML/CSS/JS without browser” | Contradictory if misunderstood | Languages ≠ Chrome install. Owned runtime embeds an engine; Jeff never manages a browser. |
| “No backend changes” | Runtime IPC, deep links, update channel may need thin adapters | Allowed: **presentation/runtime adapters only**. No ACM/Health domain redesign unless forced — and then scoped. |
| “One hour comfort in every room” | Conflicts with Mission Control intensity | Comfort ≠ blandness. Mission may be *intense but clear*; Chat/Health/Fly must be *calm*. Test is fatigue from **chrome**, not from purposeful focus. |
| “Invisible models/providers” | Power users still need control sometimes | Models/providers are **Tools / settings drawers**, never permanent furniture. Invisible until Jeff asks or Activity requires choice. |
| “Spatial house metaphor” | Risk of gimmicky navigation | Prefer **continuity and atmosphere** over literal 3D mansion. Optional light transitions only. |
| “Decade-ready without framework rewrite” | Vanilla globals may rot | Living Workspace **requires** module boundaries (Stage, Room, Tool packages). Framework rewrite optional; **architectural contracts are not**. |

---

# PART D — Validated architecture

## D.1 Backend (preserve)

Preserve and treat as stable platforms/products: ACM, Memory, Health, Mission Control, Guided Repair, Production Integrity, Fly Tying, Documents, Coding, Gallery, Projects, Planner, Calendar, Search, Automation, Voice, Vision, and related APIs.

**Do not** redesign backend architecture unless a specific Runtime Independence adapter requires it.

## D.2 Runtime (validate independence — do not select)

### Requirement (normative)

- Shipped binary/process presents **Aria**, not a browser chrome or “open this URL.”  
- Rendering engine **bundled or otherwise owned** so Jeff need not install Chrome/Firefox/Edge/Safari for Aria to work.  
- Dev may use an external browser as a **host** under a flag — never as the product definition.

### Evaluation dimensions (mandatory before selection)

Startup · Memory · GPU · Rendering fidelity · Python integration · Packaging · Linux (primary) · Windows · future macOS · Accessibility · Long-running stability · Local AI integration · Update strategy · Maintainability · Developer workflow · Five-year outlook

### Candidate classes (unevaluated ranking — spikes required)

| ID | Class | Notes for Phase 1 spikes |
|---|---|---|
| E1 | Bundled Chromium shell (e.g. Electron-class) | Strong web-UI continuity; weight & update ownership |
| E2 | Lightweight native shell + pinned engine/webview policy (e.g. Tauri-class) | Size wins if **pinning** satisfies Law 2 on all target OSes |
| E3 | Qt WebEngine–centric app (mature in-repo Fluent path) | Viable if **single Stage UI** (no forked native dashboard identity) |
| E4+ | Other (CEF custom, etc.) | Only if superior on evaluation grid |

**This package does not select E1/E2/E3.** Phase 1 produces scored spike reports; Jeff approves selection.

### Validation of Law 2

| Question | Answer |
|---|---|
| Is Law 2 achievable without backend rewrite? | **Yes** — package a host around existing HTTP/IPC APIs |
| Is Law 2 achievable while keeping HTML/CSS/JS rooms? | **Yes** |
| Does any candidate violate Law 2 if mis-shipped as “use system Chrome”? | **Yes** — reject those configurations for R1 |

## D.3 Workspace

### Owns

Window · Presence · Notifications · Voice presence · Quick actions · Global search/spotlight · Navigation · Context composition · Status policy · Chrome policy enforcement · Activity lifecycle

### Owns nothing else

Room content, room hierarchy, room typography/lighting, tool internals, backend truth.

### Success criterion

If Jeff **notices** the Workspace during normal work, it has failed — unless he summoned it.

## D.4 Activities (primary interaction unit)

### Definition

An **Activity** is a purposeful mode of work Jeff is doing. It is the primary unit of interaction. The Workspace instantiates an Activity as a composition of Room(s) + Tool(s) + Context.

### Examples

Coding · Fly Tying · Doctor Visit · Planning · Research · Learning · Reading · Design · Image Creation · Home Automation · Certification · Repair

### Activity contract

```
Activity {
  id, title, intent_hints[]
  primary_room
  supporting_rooms[]          // optional, rare
  tools[]                     // contextual allowlist
  context_bindings[]          // ACM/memory/calendar/health/… keys
  chrome_policy               // default for this activity
  entry_cues                  // NLU, command, foyer cards — not permanent tabs
  exit_behavior               // where calm returns
  inspectable_recipe          // always user-visible on demand
}
```

### Assembly rules

1. NLU / command / foyer **proposes** an Activity.  
2. Workspace **activates** primary Room under Stage with chrome policy.  
3. Tools mount only from allowlist or Jeff’s explicit invoke.  
4. Jeff can **pin**, **switch**, or **dismiss** without trapped state.  
5. High-stakes Activities (Repair, Integrity, Doctor Visit) prefer **explicit confirmation**.

### Validation

Activities solve “I opened OCR as a page.”  
They fail if opaque. **Inspectability is mandatory.**

## D.5 Rooms

### Definition

Destinations with owned experience — not routes with accents.

### Room rights

Layout · Hierarchy · Atmosphere · In-room navigation · Spacing · Lighting · Typography · Interactions · Chrome requests

### Admission criteria (Room vs Tool)

A capability becomes a Room only if **all** hold:

1. Jeff would spend an hour there as a place (physical-place test)  
2. There is a clear **hero** distinct from controls  
3. Three-second identity works without title  
4. Purpose is destination-shaped, not utility-shaped  

### Flagship rooms (destinations)

| Room | Metaphor | Hero (validation) |
|---|---|---|
| Chat | Living room | Conversation / hearth |
| Fly Tying | Streamside cabin | Fly + recipe/workbench |
| Health | Wellness clinic | Today / person |
| Mission Control | NASA floor | System telemetry |
| Documents | Private library | Knowledge / shelves |
| Planner | Leather notebook | Today’s page |
| Gallery | Museum | Artwork |
| Search | Spotlight | Query + content results |
| Coding | Engineering studio | Current work |

**Design-before-code still applies:** concept art, mood board, experience brief, wireframe, interaction map, user journey — **per room** — before that room’s implementation phase.

## D.6 Tools

### Definition

Capabilities that support Activities/Rooms without being places.

### Examples

OCR · Voice (engineering) · Vision · Browser · Clipboard · Docker · Repair · Integrity · Notifications · Providers · Git · Automation · Models routing · Cert runners

### Surfaces

Spotlight · Contextual sheet/drawer · Transient HUD · Mission escalation · Room-embedded only when the room’s purpose requires (e.g. git in Coding)

### Validation

Tool demotion is how Aria avoids another 32-tab future.

## D.7 Experience laws (UX)

No dashboards-as-identity · No widget walls · No toolbar forests · No unnecessary chrome · No implementation leakage (models/providers/STT as furniture) · No browser thinking · No feature-first layouts  

**Content · Purpose · Experience — first.**

### Tests (gate every room)

| Test | Pass condition |
|---|---|
| Three Second | Title removed → still know the room |
| One Hour | Comfortable, purposeful, not exhausting from chrome |
| Physical Place | Would gladly spend an hour there |

---

# PART E — Rendering, state, navigation, windows

## E.1 Rendering model

```
Owned Runtime
 └── Workspace (thin, summonable)
      └── Stage
           ├── Active Room root (room-owned layout)
           ├── Tool host (overlays/sheets)
           └── Ambient layer (subordinate to content)
```

Replace “32 pre-mounted hidden panels under permanent chrome” with **activate / hibernate / dispose** room lifecycles on Stage.

## E.2 Navigation

Home/foyer · Recent/pinned Activities · Favorites · Spotlight/command · Deep links from backend events  

**Not:** permanent capability tab strips as identity.

## E.3 Context composition

House → Workspace → Activity → Room → Turn  

Nearby, not competing with heroes. ACM/backend remain truth.

## E.4 Window management

One primary Aria window. Room changes inside Stage. Optional later: focus window, mission glance, rare detached tool. **No** browser-tab workflow as product UX.

## E.5 State evolution

| From | To |
|---|---|
| Pages/products/controls | Activities / Rooms / Tools |
| Global `window` soup | Workspace platform modules + room packages |
| Duplicated view maps | Single registry (rooms, tools, activities) |
| Flat prefs | Namespaced workspace / activity / room / tool / atmosphere |

---

# PART F — Migration (evolution, not rewrite)

| Phase | Name | Outcome | Implementation? |
|---|---|---|---|
| **0** | Architecture validation | This package approved | **No code** |
| **1** | Runtime spikes | Scored E1/E2/E3/(E4+) report; recommendation | Spikes only |
| **2** | Workspace implementation | Stage, registry, chrome policy, spotlight, foyer | After Phase 0–1 approvals |
| **3** | Workspace verification | Three-second foyer; tool invoke; activity propose; long-session | Gate |
| **4** | Runtime R1 | Shipped path = owned runtime; external browser demoted | After spike choice |
| **5** | Chat | Living room destination | Design pack → approve → code |
| **6** | Fly Tying | Cabin | idem |
| **7** | Health | Clinic | idem |
| **8** | Mission Control | NASA floor | idem |
| **9** | Remaining flagship rooms | Library, notebook, museum, spotlight, studio | sequential |
| **10** | Tool demotion | Strip permanent chrome; capabilities → tools | continuous + concentrated |
| **11** | Polish | Atmosphere, a11y, perf, delight | after rooms stable |

### Every phase must include

Architecture review · UX review · Performance review · Accessibility review · Stress testing · Long-session testing · Memory testing · Repair testing · Production Integrity verification · **No regressions**

### Design-before-code (per room, Phases 5–9)

Concept art · Mood board · Experience brief · Wireframe · Interaction map · User journey → **approval** → implementation only for that room.

---

# PART G — Risks, effort, recommendation

## G.1 Risks

| Risk | Mitigation |
|---|---|
| Activity opacity / wrong assembly | Inspectable recipes; confirm high-stakes; easy override |
| Runtime thrash | Phase 1 scored spikes; freeze one R1 path |
| Dual UI (old panels + Stage) forever | Time-box framed compatibility |
| Host multiplicity | One supported shipped runtime |
| Room design without Workspace | Forbidden by phase order |
| Backend scope creep | Adapters only; Integrity/Repair gates |
| Invisible-computer vs accessibility | Summonable chrome; keyboard/screen reader plans per phase |

## G.2 Effort (order of magnitude)

Phase 1 spikes: short. Phase 2–3 Workspace: weeks. Phase 4 R1: weeks–low months (depends on spike winner). Each flagship room: design + implement + live-in (sequential, quality > speed). Tool demotion: ongoing.

## G.3 Long-term path recommendation (evidence-based)

**Recommend adopting this Master Package as the presentation/runtime north star.**

1. **Preserve backend.**  
2. **Do not** ship external browser as product runtime.  
3. **Do not** pick E1/E2/E3 until Phase 1 spikes complete against the evaluation grid.  
4. **Build Workspace (Stage + Activities + Rooms + Tools) before immersive Chat.**  
5. **Evolve vanilla/UI materials under contracts** — framework rewrite is optional and not the critical path.  
6. **One room at a time** with design-before-code and live-in gates.  
7. **Default new capabilities to Tools.**

This is the path that can serve Jeff daily for a decade while remaining local, trustworthy, immersive, and browser-independent.

### Explicitly not recommended

- Paint-only “Living Interface” as the strategy  
- Big-bang React rewrite as the first move  
- Implementing Chat cabin/clinic visuals while shell still owns the first seconds  
- Treating every API capability as a permanent page  

---

# PART H — Decade proof

| Future pressure | How Living Workspace absorbs it |
|---|---|
| More capabilities | Tools by default |
| Deeper flagships | Rooms with owned Stage |
| CAD / robotics / vision richness | Expanded canvas + tool sheets; lazy lifecycle |
| Voice-first days | Presence transforms active Activity/Room |
| Trust & safety | Integrity/Repair as tools + Mission signals; backend preserved |
| OS churn | Owned runtime updates with Aria |
| Jeff’s cognition | “Aria…” → Activity — Invisible Computer |

**Falsifiable acceptance (product-level):**

1. Launch identity is Aria only  
2. Three-second room tests pass  
3. One-hour live-in passes without chrome fatigue  
4. New capability adds no permanent tab by default  
5. External browser not required for daily use  
6. Backend product suites remain green  
7. Activity recipes are inspectable  

---

# PART I — Decision gates (stop here)

Jeff approval required before any implementation line:

- [ ] Adopt Laws 1–6 as normative  
- [ ] Approve Activity → Room → Tool composition model  
- [ ] Approve migration Phases 0–11 ordering  
- [ ] Authorize **Phase 1 runtime spikes only** (no R1 ship yet, no room builds)  
- [ ] Confirm design-before-code gate for each flagship room  

**Until then: no Workspace coding, no runtime packaging for ship, no room implementation.**

---

*End of Master Engineering & Design Package. Stopped for approval.*
