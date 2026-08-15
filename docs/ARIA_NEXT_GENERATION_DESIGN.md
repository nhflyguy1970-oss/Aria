# Aria Next Generation
## Runtime Independence + Living Workspace
### Engineering Design Package (Architecture Phase)

**Status:** Design only — no implementation.  
**Date:** 2026-08-06  
**Superseded for authority by:** `docs/ARIA_NEXT_GENERATION_MASTER.md` (Master Engineering Directive package). This document remains as supporting draft detail.  
**Stance:** Evolution of the presentation layer. Backend, ACM, products, and APIs preserved where practical.  
**Companion evidence:**  
- `docs/ARIA_FRONTEND_FOUNDATION_REVIEW.md`  
- `docs/ARIA_FRONTEND_ARCHITECTURE_REVIEW.md`  
- `docs/ARIA_LIVING_ROOMS_EXPERIENCE_BRIEF.md`  
- `docs/ARIA_NEXT_GENERATION_MASTER.md`

---

## 0. Engineering law (adopted)

1. **Aria owns its runtime.** The finished product launches as Aria — not as a webpage in an externally installed browser.  
2. **HTML / CSS / JS remain acceptable** as implementation materials inside that runtime.  
3. **Externally installed Chrome / Firefox / Edge / Safari are not the target platform.** They may be optional **dev hosts** during transition only.  
4. **Rooms own experience. The Workspace quietly supports.**  
5. **Flagship destinations are Rooms. Everything else is Tools** (contextual, not permanent furniture).  
6. **No backend rewrite** to achieve this. Presentation evolves.

---

## 1. Vision document

### What Aria is becoming

Aria is a **local AI workspace** — a continuous home Jeff inhabits, not a site he browses.

| Old mental model | Next Generation |
|---|---|
| Browser app / pages | Self-contained desktop application |
| Dashboard of capabilities | Living Workspace of rooms |
| Tabs = products | Rooms = destinations; Tools = on demand |
| Shell dominates | Room owns first three seconds |
| “Open Health page” | “Enter the clinic” |
| Launch Chrome → URL | Launch **Aria** |

### The house

One home. Purpose-built rooms:

| Room | Metaphor | Hero |
|---|---|---|
| Chat | Living room | Conversation |
| Fly Tying | Streamside cabin | The fly |
| Health | Wellness clinic | Jeff’s today |
| Mission Control | NASA floor | The system |
| Documents | Private library | Knowledge |
| Planner | Leather notebook | Today’s page |
| Gallery | Museum | Artwork |
| Coding | Engineering studio | Current work |
| Search | Spotlight | Query + results |

### Success criteria

- Jeff never thinks “I’m changing pages.” He moves through a workspace.  
- Title removed → room still identifiable in three seconds.  
- One hour in any room feels calm, not tiring.  
- Launching Aria never surfaces “browser,” “HTML,” or “localhost.”  
- Architecture supports a decade of new rooms/tools without permanent chrome growth.

---

## 2. Runtime independence strategy

### Problem

Today the primary UX path is a **web UI hosted in whatever the OS browser / WebView / Electron / Fluent WebEngine provides**, with modes that still conceptually feel like “open a URL.” Default launcher paths include Chrome-app and PySide+WebEngine wrapping the same document. The **user-facing identity** remains browser-adjacent.

### Target

```
┌──────────────────────────────────────────┐
│              Aria Desktop App            │
│  (branded process, icon, window, update) │
│  ┌────────────────────────────────────┐  │
│  │  Owned runtime (bundled engine)    │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │ Living Workspace (JS/CSS/HTML│  │  │
│  │  │ or equivalent UI layer)      │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
│           ↕ localhost / IPC / socket     │
│  ┌────────────────────────────────────┐  │
│  │  Aria Backend (Python) — preserved │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### Principles

| Principle | Meaning |
|---|---|
| Bundle the engine | Rendering engine ships with Aria; no “install Chrome first” |
| Single product identity | One process tree Jeff recognizes as Aria |
| Backend stays local service | Same APIs; Workspace is a client |
| Dev browser optional | Engineers may still hit HTTP in a browser for speed — users never must |
| No browser workflows | No “open in new tab,” bookmarking the app URL, or extension dependency for core UX |
| Progressive ownership | Runtime independence can land before every room is redesigned |

### Phased runtime ownership

| Phase | User experience | Runtime |
|---|---|---|
| **R0 (today)** | Often browser / WebView / Electron / Fluent wrapping web UI | External or semi-bundled |
| **R1** | **Aria app window only** for daily use; browser deprecated for Jeff | Bundled runtime mandatory for “shipped” path |
| **R2** | Deep OS integration (tray, protocol handlers, file associations) | Same runtime + native host services |
| **R3** | Multi-window / stage manager optional | Workspace window model mature |

R1 is the minimum bar for “runtime independence.” R2–R3 deepen the living workspace without requiring a backend rewrite.

### What “owned runtime” does *not* require

- Rewriting products in Qt Widgets / SwiftUI / WinUI  
- Abandoning HTML/CSS/JS as the room authoring language  
- Replacing ACM, Health store, Fly Tying data, Mission Control aggregators  

---

## 3. Current frontend assessment (presentation layer)

*(Summary — full evidence in foundation/architecture reviews.)*

| Aspect | State | Implication for Next Gen |
|---|---|---|
| UI language | Vanilla HTML/CSS/JS monolith | Keep as materials; change composition |
| Composition | 32 hidden panels under mandatory chrome | **Incompatible** with Living Workspace |
| Navigation | Capability → permanent tabs/sidebar | Must become Rooms vs Tools |
| Hosts | Chrome app, Electron, pywebview, PySide+WebEngine | Consolidate to **one shipped runtime path** |
| Backend | Mature platform APIs | **Preserve** |
| Living Interface CSS | Paint only | Insufficient; rooms need layout ownership |

**Assessment:** Backend ready. Presentation composition and runtime packaging are the gap — not product domain logic.

---

## 4. Workspace architecture

### Definition

The **Workspace** is the continuous environment that owns application-level concerns. It is not a dashboard and not a tab strip of every capability.

### Workspace owns

| Concern | Notes |
|---|---|
| Window(s) | Framing, title, fullscreen, multi-monitor |
| Navigation | Move between rooms; invoke tools — not permanent product catalogs |
| Context | What Jeff is doing; active room; ambient awareness |
| Notifications / Activity | Polite arrival; not a status wallpaper |
| Voice presence | Transforms the active room; engineering controls are Tools |
| Global search / spotlight | Invoke, resolve, dismiss |
| Quick actions / command | Power without furniture |
| Status (minimal) | Health of house — glanceable, dismissible, room-overridable |
| Runtime chrome policy | Honors room requests for minimal / expanded / focus |

### Workspace does **not** own

- Room content hierarchy  
- Room visual identity / lighting / materials  
- Room-specific toolbars as permanent globals  
- Product business logic (stays in backend + room modules)

### Workspace adaptation

```
Jeff’s intent → Workspace mode
  exploring home     → gentle foyer / home stage
  deep in a room     → room-owned canvas, chrome retreats
  invoking a tool    → sheet / drawer / palette over room
  system incident    → Mission signal without ejecting from room
  speaking           → voice transforms active room atmosphere
```

---

## 5. Room architecture

### Definition

A **Room** is an immersive destination with purpose, hero, atmosphere, and layout ownership.

### Room contract (logical)

```
RoomDescriptor {
  id, metaphor, hero
  chromePolicy: minimal | standard | systems | focus
  layout: room-defined composition tree
  atmosphere: lighting, materials, density hints
  tools: allowlist of contextual tools
  emptyState, dailyWorkflow
  backend: API surface (existing products)
}
```

### Room rights

A room may request, without fighting the Workspace:

- Minimal chrome / expanded canvas  
- Alternate layout hierarchy  
- Alternate lighting / density  
- Alternate interaction style (notebook vs telemetry vs conversation)  
- Temporary tool surfaces  

### Room duties

- Pass **three-second** and **one-hour** tests  
- Expose entry points for Workspace navigation and deep links  
- Remain compatible with backend APIs  
- Prefer content over controls  

### Flagship room set (v1 destinations)

Chat, Fly Tying, Health, Mission Control, Documents, Planner, Gallery, Search, Coding — **one room at a time** after Workspace foundation exists (prior sequencing stands).

### Non-goals for rooms

- Each capability is not automatically a room  
- Rooms are not browser routes with different CSS variables only  

---

## 6. Tool architecture

### Definition

A **Tool** is a capability that supports work inside or across rooms. Tools appear when needed; they do not permanently occupy the primary canvas.

### Examples

OCR · Browser · Vision · Voice (engineering) · Docker · Git · Clipboard · Automation · Notifications center · Guided Repair · Production Integrity · Providers · Models routing · Cert runners · Connections diagnostics

### Tool surfaces

| Surface | Use |
|---|---|
| Command / spotlight | Invoke by intent |
| Contextual drawer / sheet | Beside active room |
| Transient HUD | Jobs, short status |
| Mission escalation | When tool reports house health issues |
| Room-embedded widget | Only when the room’s purpose requires it (e.g. git in Coding) |

### Rule

If a capability fails the test *“Would Jeff want to spend an hour here as a place?”* it is a **Tool**, not a Room.

---

## 7. Navigation philosophy

### Replace

- 32 always-visible view tabs  
- Sidebar as permanent multi-product control farm  
- Header buttons that only `switchToView` to other products  

### With

| Mechanism | Role |
|---|---|
| **Home / foyer** | Orient; enter rooms intentionally |
| **Room memory** | Resume last room / recent rooms |
| **Favorites** | Jeff’s short list — not the full catalog |
| **Spotlight / command** | Reach any room or tool by name/intent |
| **Spatial metaphor (light)** | Optional: feel of moving rooms — never a gimmick maze |
| **Deep links** | Backend/events open the right room + context |

### Cognitive rule

Navigation answers *“Where can I go?”* only when Jeff asks.  
While inside a room, navigation is quiet.

---

## 8. Context composition model

### Layers

```
1. House context     — who Jeff is, time, presence, quiet hours
2. Workspace context — active room, open tools, voice state, focus mode
3. Room context      — domain state (today’s health, pattern of the day, current project)
4. Turn context      — chat attachments, selection, clipboard offering
```

### Composition rules

- Lower layers may inform upper layers; upper layers must not dump controls into the room canvas  
- Context is **nearby** (palette, side glance, hearth adjacency) — not a competing hero  
- Tools consume context; they do not redefine the room’s hero  
- ACM / memory / backend remain sources of truth; Workspace composes presentation context only  

### Chat-specific

Conversation dominates. Composer = hearth. Attachments = objects on the table. Voice transforms the room. Context chips support — never equal the stream.

---

## 9. Window management model

### Primary

- **One primary Workspace window** branded as Aria  
- Room changes happen **inside** the window (no “new browser tab” mental model)

### Optional (later)

| Mode | Purpose |
|---|---|
| Focus window | Single room, extreme minimal chrome |
| Mission glance | Compact systems window / HUD |
| Detached tool | Rare — e.g. long job console |
| Multi-monitor stage | Mission + Coding side-by-side via Workspace, not OS browser windows |

### Explicit non-goals (user-facing)

- Depending on browser tab management  
- Requiring Jeff to arrange Chrome windows to use Aria  

---

## 10. Interaction model

| Pattern | Living Workspace meaning |
|---|---|
| Enter room | Atmosphere + hero immediately |
| Invoke tool | Sheet/drawer/command — dismissible |
| Speak | Room listens; voice UI is presence, not a permanent engineering strip |
| Notify | Polite; queue in Activity; never steal hero |
| Search | Spotlight over workspace; results jump into rooms |
| Escape / back | Leave tool → room; leave focus → room; leave room → foyer/home |
| Density | Room requests comfortable / standard / compact; Workspace honors |

### Anti-patterns (banned in Next Gen UX law)

Dashboards as identity · admin panels as home · widget walls · toolbar forests · feature explosions · implementation leakage (model IDs, STT backend selects as furniture) · pages pretending to be rooms  

---

## 11. Rendering model

### Logical model (technology-agnostic)

```
Workspace Shell (thin)
  └── Stage (canvas owned by active Room)
        ├── Room root layout (room-defined)
        ├── Contextual tool host (overlays/sheets)
        └── Ambient layer (atmosphere — subordinate to content)
```

### Requirements on the renderer

| Requirement | Why |
|---|---|
| Full room layout replacement | Cabin ≠ clinic ≠ living room |
| Efficient atmosphere | Cheap CSS/GPU; reduced-motion safe |
| Large imagery | Gallery / Fly Tying heroes |
| Overlay stack | Tools without destroying room |
| Text performance | Conversation + documents reading |
| Deterministic lifecycle | Mount/activate/deactivate/dispose room |

### Migration from today

Today: all rooms pre-mounted, `.hidden` toggle, shared outer chrome.  
Next Gen: **activate room into Stage**; deactivate/dispose or hibernate; chrome policy from RoomDescriptor — not a permanent outer stack.

HTML/CSS/JS may still produce room trees **inside the owned runtime**.

---

## 12. State management evolution

### Keep

- Backend as source of truth  
- Local prefs for chrome density, favorites, atmosphere opt-ins  
- Event signals for view/room changes  

### Evolve

| From | To |
|---|---|
| Flat `window.*` util graph | Explicit Workspace / Room / Tool modules |
| One prefs blob for everything | Namespaced: workspace, room, tool, atmosphere |
| 13 duplicated view registries | Single room+tool registry (Workspace-owned) |
| Panel hide/show as “state” | ActiveRoom + ToolStack + FocusMode |
| Chat as accidental util library | Shared kit owned by Workspace platform layer |

### Non-goals

- Rebuilding ACM in the UI  
- Global Redux-for-everything unless a chosen UI stack needs it  

---

## 13. Dependency analysis

### Preserve (foundational)

- Python backend, product APIs, ACM, Health PHR, Fly Tying data, Mission aggregators, Guided Repair, Production Integrity, auth, jobs  

### Evolve (presentation)

- Monolithic `index.html` panel farm  
- Mandatory chrome strips  
- Multi-host ambiguity as *shipped* UX  
- Living Interface as paint-only identity  

### Transition-only

- External browser as Jeff’s daily driver  
- Dev-only “open localhost in Chrome”  

### Decide later (see §17)

- Exact bundled runtime (Electron / Tauri / Qt WebEngine-only / other)  
- Exact UI authoring stack evolution (stay vanilla vs islands vs gradual components)  

---

## 14. Migration strategy

### Law

**Strangle the presentation. Do not freeze the backend. Do not big-bang rewrite rooms.**

### Tracks (parallelizable carefully)

**Track W — Workspace foundation**  
Room/Tool registry · Stage host · chrome policy · spotlight · foyer · tool sheets  

**Track R — Runtime independence**  
Pick and ship one bundled runtime path · Aria icon/process · deprecate external-browser daily use · optional OS integrations  

**Track D — Destinations**  
One room at a time (Chat → Fly Tying → Health → …) under Workspace Stage + chrome policy  

**Track T — Tool demotion**  
Move permanent capabilities (voice engineering, providers, integrity, repair, browser, OCR, …) into Tools  

**Track H — Hygiene**  
Deduplicate registries · split CSS by room · lazy load heavy assets · retire dead hosts from “supported daily” list  

### Compatibility gates

- Every backend API used today keeps working  
- Old “framed” mode available until rooms opt into immersive Stage  
- Dev browser host allowed behind a flag — not documented as the product  

### Sequencing recommendation

1. Agree this design package  
2. Track W Layer-1 (Stage + chrome policy) — unblocks destinations  
3. Track R to **R1** (Aria launches as Aria) — can overlap W  
4. Chat destination under Stage  
5. Continue rooms; demote tools continuously  

---

## 15. Risk analysis

| Risk | Severity | Mitigation |
|---|---|---|
| Runtime choice churn | High | Decide with spike criteria (§17); freeze one shipped path |
| Dual UI forever (old panels + Stage) | Medium | Time-box framed mode; migrate room-by-room |
| Host multiplicity (Electron + Fluent + Chrome) | Medium | One *supported* runtime; others legacy |
| Room redesign without Workspace | High | Forbidden — fails three-second test again |
| Over-building spatial metaphor | Medium | Prefer calm transitions over game navigation |
| Performance with rich rooms | Medium | Lazy activate; dispose; budget atmosphere |
| Scope creep into backend rewrite | High | Explicit non-goals; API compatibility tests |
| Jeff muscle-memory shock | Medium | Favorites + spotlight; progressive chrome retreat |

---

## 16. Estimated effort (order-of-magnitude)

| Workstream | Rough order |
|---|---|
| Workspace Stage + chrome policy + registry | S–M (weeks) |
| Runtime R1 (bundled app path, branding, deprecate browser-daily) | M (weeks–low months) depending on chosen stack maturity in-repo |
| Tool demotion wave 1 (voice eng, providers, integrity → tools) | M |
| Per destination room | M each (design + implement + live-in), sequential |
| Runtime R2 OS integrations | M |
| Hygiene / modularization | Ongoing |

**Critical path:** Workspace Stage before serious immersive Chat. Runtime R1 can parallelize once host choice is approved.

---

## 17. Technology options (tradeoffs — no single mandate)

> HTML/CSS/JS remain acceptable in all serious options below. The decision is **how Aria packages and owns the runtime**, and how aggressively the UI module system changes.

### Runtime packaging options

| Option | Idea | Advantages | Disadvantages | Fits engineering law? |
|---|---|---|---|---|
| **E1 — Electron (bundled Chromium)** | Ship Chromium with Aria | Mature; already partially in-repo; web UI reuse; strong desktop APIs | Heavier binary; Chromium updates ownership | **Yes** — owned runtime |
| **E2 — Tauri (bundled WebView + Rust shell)** | System webview or controlled sidecar depending on config; small host | Small host, modern tooling | WebView variance by OS if not pinned; Rust skill; less in-repo today | **Yes if** engine is pinned/bundled so external browser install isn’t required |
| **E3 — Qt WebEngine-only app (PySide path matured)** | Fluent/native chrome + WebEngine as *the* UI host | Already explored; Python-adjacent | Dual UI risk if native dashboard forks UX; Qt packing complexity; must kill “browser fallback” as product path | **Yes if** single Stage UI in WebEngine and no external browser dependency |
| **E4 — Custom CEF embed** | Embed Chromium Embedded Framework in a thin native host | Full control | Highest engineering cost; duplicate what Electron already packages | Yes, usually unnecessary |
| **E5 — Keep external Chrome `--app`** | Status quo convenience | Zero packaging | **Violates new engineering law** as shipped target | **No** (dev-only OK) |

**Selection criteria (when Jeff decides):**  
cold-start, binary size, update story, Linux reliability (Jeff’s OS), packaging effort vs in-repo assets, ability to present **one** Aria identity, long-term maintenance.

**Architect note:** E1 or a **pinned** E2/E3 are all compatible with Living Workspace. E5 is not a product target.

### UI authoring options (inside owned runtime)

| Option | Idea | Advantages | Disadvantages |
|---|---|---|---|
| **U1 — Evolved vanilla** | Stage + modules + room bundles, still no React | Matches current skill/code; fastest Workspace win | Requires discipline against global `window` soup |
| **U2 — Hybrid islands** | New rooms as components (Lit/React) in Stage | Encapsulation for new destinations | Dual paradigm risk |
| **U3 — Full UI framework migration** | Rewrite presentation in React/Vue/Svelte | Industry defaults | Does not create rooms by itself; high cost; defer unless U1 fails |

**Architect note:** Living Workspace success depends on **Stage + Room/Tool model + chrome policy**, not on U3. Prefer **U1**, hold **U2** if encapsulation demands it.

---

## 18. Proof: decade-ready Living Workspace

### Why this architecture supports the vision for ~10 years

| Pressure | How Next Gen absorbs it |
|---|---|
| Many new capabilities | Become **Tools** by default — chrome does not grow linearly |
| Flagship experiences | Become **Rooms** with owned Stage layouts |
| Rich media / CAD / vision | Room-expanded canvas + tool sheets; lazy activation |
| Voice / presence | Workspace-level presence transforming active room |
| Platform intelligence (ACM, jobs, integrity) | Backend preserved; Mission/tools surface signals without turning every room into admin |
| OS changes | Owned runtime updates with Aria — not “Jeff’s browser broke the app” |
| Design evolution | RoomDescriptor + chrome policy allow radical layouts without shell fights |

### Why continuing as a browser-targeted page farm cannot

- Mandatory shared chrome prevents three-second identity  
- Capability accretion → permanent tabs/sidebar  
- User mental model stays “website on localhost”  
- Atmosphere CSS cannot grant layout ownership  

### Falsifiable tests (adopt as acceptance)

1. **Launch test:** Cold start presents Aria branding only — no browser chrome, no “http://” as identity.  
2. **Three-second test:** Title hidden → room still identifiable.  
3. **Hour test:** Live-in each flagship room without fatigue from permanent unrelated controls.  
4. **Tool test:** OCR/Providers/Integrity reachable without permanent primary canvas occupation.  
5. **Addition test:** Adding a new capability does not add a permanent tab by default.  
6. **Backend test:** Existing product APIs remain green throughout presentation migration.

If tests 1–3 fail after Workspace+Runtime R1, the design is wrong — revisit, don’t paint.

---

## Design package map (deliverables checklist)

| # | Deliverable | Section |
|---|---|---|
| 1 | Vision | §1 |
| 2 | Runtime independence strategy | §2 |
| 3 | Current frontend assessment | §3 |
| 4 | Workspace architecture | §4 |
| 5 | Room architecture | §5 |
| 6 | Tool architecture | §6 |
| 7 | Navigation philosophy | §7 |
| 8 | Context composition | §8 |
| 9 | Window management | §9 |
| 10 | Interaction model | §10 |
| 11 | Rendering model | §11 |
| 12 | State evolution | §12 |
| 13 | Dependency analysis | §13 |
| 14 | Migration strategy | §14 |
| 15 | Risk analysis | §15 |
| 16 | Estimated effort | §16 |
| 17 | Technology options + tradeoffs | §17 |
| 18 | Decade proof | §18 |

---

## Decision gates (awaiting Jeff)

1. **Adopt** Living Workspace laws (Rooms vs Tools; Workspace vs Stage)?  
2. **Adopt** runtime independence law (bundled engine; browser = transition host only)?  
3. **Authorize** spikes against E1 / E2 / E3 using selection criteria — still no full implementation?  
4. **Confirm** migration order: Workspace Stage → Runtime R1 → Chat room → …  

**No implementation until these decisions are explicit.**

---

*End of engineering design package.*
