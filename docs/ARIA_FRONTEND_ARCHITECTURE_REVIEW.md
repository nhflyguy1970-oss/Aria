# Aria Frontend Architecture Review

**Date:** 2026-08-06  
**Scope:** Architecture only — no redesign, no CSS, no implementation.  
**Question:** Is the GUI framework now the bottleneck for immersive, content-first rooms?

---

## Verdict

### YES — for the destination / immersive goal.

The current frontend architecture **is the binding constraint** on becoming a home of purpose-built rooms. It is not primarily a taste problem. Living Interface (CSS rooms) cannot fix this because it only recolors and lightly animates the same forced structure.

**Nuance (not a rewrite mandate):**
- Products *inside* their panel can still diverge (Health is relatively decoupled; Search/Documents lean content-centric).
- Vanilla JS is not the problem. The **mandatory global shell contract** is.
- Evolution is realistic **without** a big-bang rewrite — but Chat-as-destination (and every later room) will fight the shell until that contract changes.

**One-sentence answer:**  
The architecture can evolve into immersive rooms, but **as it stands today it cannot produce them** — because every “room” is still a hidden panel under one always-on control frame, with no way to opt out.

---

## 1. Current frontend architecture

### Model

Single-document SPA. No React/Vue/Svelte. No web components. No template system. Classic scripts + `window.*` globals. One HTML file owns all product DOM.

```
┌─────────────────────────────────────────────────────────────────┐
│ body                                                             │
│  ┌──────────────┬──────────────────────────────────────────────┐│
│  │ aside.sidebar│ main#mainContent.chat-panel                  ││
│  │ 260px default│  ┌──────────────────────────────────────────┐││
│  │ 15 sections  │  │ quickDock (pref)                         │││
│  │ ALL products │  │ nav.view-tabs  ★ + 32 tabs  ALWAYS ON    │││
│  │ always in DOM│  │ breadcrumb (sometimes)                   │││
│  │              │  │ globalWorldStateBar         ALWAYS ON    │││
│  │              │  │ ariaVoiceStrip (9 controls) ALWAYS ON    │││
│  │              │  │ ariaVisionStrip             ALWAYS ON    │││
│  │              │  │ ┌──────────────────────────────────────┐ │││
│  │              │  │ │ 32 × .view-panel siblings            │ │││
│  │              │  │ │ only one not .hidden                 │ │││
│  │              │  │ │ (chatView default)                   │ │││
│  │              │  │ └──────────────────────────────────────┘ │││
│  │              │  │ + 56 crop-modals + dialogs in main       │││
│  └──────────────┴──┴──────────────────────────────────────────┘││
│  footer#ariaStatusBar (7 segments)                              │
│  miniChatFab / miniChatPanel / lightboxes / lockScreen          │
└─────────────────────────────────────────────────────────────────┘
```

### Routing

`view_router.js` (~93 lines): toggle `.hidden` on panels; hardcoded `if (view === …) window.initX?.()` for every product; rewrite hash; set Living Interface room; dispatch `aria-view-change`.

Not a router. A panel switcher with compile-time knowledge of every product.

### Dependencies (simplified)

```
index.html
  ├── style.css (7034 lines — ALL product CSS)
  ├── shell_design.css (token override / kill legacy body::before)
  ├── living_interface.css + living_atmosphere.css (body[data-room] paints)
  ├── 125 <script> tags (order = dependency graph)
  │     ├── product scripts (many BEFORE shell prefs exist)
  │     ├── /api/shell/bundle.js (9 chrome scripts concatenated)
  │     └── view_router.js LATE in the list
  └── window.* surface (~324 distinct names, 38 Aria* namespaces)
```

### State

- No app state store.
- `AriaUiPrefs`: one flat `localStorage` blob, 46 keys, whole-object save, one broadcast.
- Coupling: direct `window.fn` calls; only ~8 CustomEvent dispatch sites in ~45k JS lines; `aria-view-change` is the main bus (12 listeners).
- View registries duplicated across **13 files** (counts already drift: 32 / 37 / 31).

### Layout taxonomy

| Layer | Centricity |
|---|---|
| Shell | **Feature/capability-centric** (every capability gets a tab + often a sidebar section) |
| View panels | Mixed — Documents/Search lean **content**; Health/Gallery/Mission lean **control/toolbar** |
| Overall | **Page-centric** (show/hide pages), not **task-centric** or **content-centric** |

---

## 2. Strengths (keep)

| Strength | Evidence |
|---|---|
| Backend maturity independent of GUI | Products talk HTTP APIs; UI is not the source of truth |
| Fast local iteration | No build step for most UI; edit JS/HTML, reload |
| Some products already loosely coupled | Health: ~7 `window.*` reads, defines only `initHealth` |
| Content-leaning panels exist | Documents, Search — lower header cross-nav density |
| Pref-gated chrome exists | dock / status / mini-chat can hide globally |
| `aria-view-change` channel | Clean event already used by shell chrome |
| Shell bundle concept | Chrome scripts already aggregated server-side |

---

## 3. Weaknesses (architecture)

1. **One mandatory chrome for 32 products** — tabs, world HUD, voice strip, vision strip always above every room.
2. **No immersive / chromeless / room-owned layout mode** — codebase search for immersive/full-bleed/zen/hide-chrome: **zero matches**.
3. **Main is still `class="chat-panel"`** — historical chat-app skeleton.
4. **Sidebar is a permanent multi-product control farm** — 15 sections, product tools reachable while in unrelated rooms.
5. **32 always-visible view tabs** — navigation as a product catalog, not a home.
6. **CSS comment admits permanence:** `style.css` ~1562: *“Top systems HUD + voice controls (always visible, not Life-UI-only)”*.
7. **Monolithic DOM** — 3534-line `index.html`, 1343 IDs, all views mounted forever.
8. **Monolithic CSS** — all product styles in one 7034-line file; shell enumerates product IDs for overflow rules.
9. **Global coupling surface** — 273 `switchToView` call sites / 65 files; Chat defines utilities other products depend on.
10. **Living Interface cannot change composition** — only `body[data-room]` paints on `#mainContent`.

---

## 4. Technical debt (frontend)

| Debt | Proof |
|---|---|
| Incremental page accretion | 32 panels + 32 tabs 1:1 |
| View registry drift | 13 duplicated maps, inconsistent counts |
| Script order hazards | Shell prefs load after many products → optional chaining everywhere |
| Modal chaos | 3 mechanisms: `modal_chrome` array, `.hidden` divs, native `<dialog>`; incomplete Esc coverage |
| Class namespace leakage | `mc-*` used by Coding/Gallery; `planner-*` used across products; `flytying-col-subtitle` in Search |
| Dead / ghost selectors | e.g. `#smarthomeView` in CSS, no panel |
| Dual token sources | `/api/shell/design` unused by client; CSS hand-maintained |
| Three.js on every load | Maker vendor scripts in global HTML |
| Chat as utility library | `escapeHtml`, `formatMessage`, `jarvisAskAria` owned by chat, consumed elsewhere |

---

## 5. Architectural bottlenecks (ranked)

| # | Bottleneck | Blocks destinations because… |
|---|---|---|
| 1 | **Mandatory shared chrome** | Room cannot own first viewport; 3-second identity is “Aria admin app” |
| 2 | **Page = panel toggle** | Products are pages in a binder, not places |
| 3 | **Capability → always-visible nav** | Every capability earns a tab forever |
| 4 | **No room layout ownership** | Cannot hide tabs/voice/sidebar per room |
| 5 | **Global window coupling** | Hard to isolate Chat redesign without collateral |
| 6 | **CSS/DOM monolith** | Structural change touches everyone |

---

## 6. Coupling analysis

| Product | Cross-product globals | Orientation | Can differ inside panel? | Can escape shell? |
|---|---|---|---|---|
| Chat | Defines shared utils; 66% of chat IDs outside `chatView` | Content body, control-heavy surroundings | Partially | **No** |
| Health | Lowest coupling | Control-centric (30 tabs) | Yes | **No** |
| Fly Tying | Mostly `switchToView` | Mixed | Yes | **No** |
| Mission | Highest (~54 distinct globals) | Toolbar-as-router | Partially | **No** |
| Documents | Low–moderate | Content-centric | Yes | **No** |
| Planner | Reaches into Home helpers | Control-centric | Partially | **No** |
| Search | Low | Content-centric | Yes | **No** |
| Gallery | High cross-nav in header | Toolbar-as-router | Partially | **No** |
| Coding | Split: panel + sidebar `#codingPanel` | Toolbar-as-router | Partially | **No** |

**Answer to “Can Chat become completely different without affecting Health?”**  
Visually/inside-panel: mostly yes. Structurally (chrome, nav, voice, status, sidebar): **no — same cage**.

**Answer to “Can Fly Tying become immersive without rewriting the shell?”**  
**No.** Immersive requires shell evolution (chromeless / room chrome policy). Panel-only redesign still sits under 32 tabs + voice + world + sidebar.

---

## 7. Dependency graph (shell ↔ products)

```
                    ┌─────────────┐
                    │  index.html │
                    │  (monolith) │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
     style.css      view_router.js    shell bundle
     (all UI)       (knows every         (prefs,
           │         initX by name)     dock, status)
           │               │
           └───────┬───────┘
                   ▼
            window.switchToView  ←── 273 call sites
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
  chat_*        health.js    mission_control*
  (utils hub)   (isolated)   (high fan-in/out)
     │
     └──► documents, planner, coding, gallery (jarvisAskAria / escapeHtml / sendMessage)
```

---

## 8. Screen space — framework vs content

Measured defaults for **1920×1080** (CSS-derived):

| Region | Size | Share |
|---|---|---|
| Sidebar | 260px width | **13.5%** of width |
| Vertical main chrome (tabs + world + voice + vision) | ~144px | **~13.6%** of app height |
| Status bar | 24px | fixed |
| **Content viewport** | ~1660×912 | **~73%** of screen |
| **Framework-reserved** | — | **~27%** |

If the 32-tab row wraps (~2 rows), content drops to ~**70%**, framework ~**30%**.

This is before product-local toolbars (Health’s 30 tabs, Gallery header routers, Mission header). Framework tax is permanent even when the room wants full immersion.

**Always-visible control layers (count):**
1. Sidebar (multi-product)  
2. View tabs (32)  
3. World state bar  
4. Voice strip (~9 controls)  
5. Vision strip  
6. Status bar (7 segments)  
7. Optional: quick dock, breadcrumbs, mini-chat FAB  

**Permanent toolbars:** shell voice strip + per-product headers (many).  
**Navigation layers:** sidebar favorites/search + 32 tabs + breadcrumbs + command palette + in-header `switchToView` buttons + status segments.  
**Persistent status:** world bar + voice + vision + footer status bar (≥3–4 concurrent status surfaces).

---

## 9. Three-second test (architecture lens)

| Room | Identifiable without title today? | Why not (design vs architecture) |
|---|---|---|
| Chat | Weakly | Conversation competes with shell; composer exists but chrome wins first paint — **both**, shell-dominant |
| Health | No | 30-tab control strip is product design; shell still frames it as another page — **both** |
| Mission | Weakly | Cards help, but same tabs/voice/sidebar — **architecture dilutes** |
| Fly Tying | No | Content could look like a cabin; shell still screams “app with tabs” — **architecture** |
| Planner | No | Form rows + shell — **both** |
| Gallery | Weakly | Thumbs under same chrome — **architecture + product layout** |
| Documents | Weakly | Could feel library inside panel; shell prevents place — **architecture** |
| Search | Somewhat | Cleaner panel; still tabbed app — **architecture** |
| Coding | No | Forms + shell + sidebar coding drawer — **both** |

**Living Interface proved the distinction:** changing accents/atmosphere did not change room identity. That failure mode is **architectural**, not “need better gradients.”

---

## 10. UX analysis (Jeff)

| Why Jeff came | What architecture forces onto the page |
|---|---|
| Talk to Aria | 32 tabs, voice engineering controls, world HUD, sidebar coding/HA/tools |
| Tie flies | Same |
| Check health | Same + product’s own 30 tabs |
| Trust the system | Same — Mission is a tab among 31 others |
| Read documents | Same |

Architecture supports **capability access**, not **purpose immersion**.

---

## 11. Comparison to modern desktop architectures (structure only)

| Pattern (Arc / Linear / Things / Raycast / VS Code / Claude Desktop) | Aria today |
|---|---|
| Primary surface owns the viewport | Shell owns viewport; product is a slot |
| Complexity in command palette / context menus / transient panels | Complexity permanent in tabs + strips + sidebar |
| Sidebar is contextual or mode-based | Sidebar is global inventory |
| Views can go distraction-free / full editor | **No mode exists** |
| Extension UI sandboxed | All products share one DOM + CSS file |
| Navigation scales via search, not infinite tabs | **32 sticky tabs** |

They feel simple because **architecture hides complexity by default**. Aria’s architecture **surfaces capability by default**.

---

## 12. Can this architecture produce a cabin / clinic / library / NASA floor / living room?

| Destination | Without fighting the shell? |
|---|---|
| Fly tying cabin | **No** — cabin needs first-viewport ownership |
| Wellness clinic | **No** — clinic greeting cannot beat 32 tabs + voice STT selects |
| Private library | **No** — shelves lose to app chrome |
| Mission Control | **Partially** — telemetry cards can grow, but “NASA floor” needs chromeless stage |
| Living room (Chat) | **No** — conversation cannot be the only hero while shell is mandatory furniture |

**Therefore:** design-only room work will keep failing the physical-place test until shell policy evolves.

---

## 13. What can stay

- Backend APIs and product domain logic  
- Vanilla JS product modules (evolve boundaries gradually)  
- `AriaUiPrefs` concept (split keys later)  
- `aria-view-change` / Living Interface *as optional atmosphere*, not as the redesign  
- Pref-gated hide for dock/status/mini-chat (extend the idea to room chrome policies)  
- Health-style isolation pattern as a model for other rooms  

## 14. What must evolve

- **Room chrome policy:** which shell layers appear per room (including “none”)  
- **Navigation model:** away from 32 always-visible tabs toward home + command + contextual  
- **Layout ownership:** room owns first viewport; shell becomes optional frame  
- **Chat privilege:** stop treating `main` as `chat-panel`; stop chat-as-global-utils long-term  
- **DOM/CSS modularization:** progressive, not big bang  

---

## 15. Evolution roadmap (no rewrite)

### Layer 1 — Shell escape hatch (unblocks destinations)
- Add **room presentation modes**: `framed` (today) vs `room` (hide tabs/voice/vision/world by policy) vs `focus` (minimal).  
- Per-room chrome manifest (Chat: focus/living-room; Mission: systems; Fly: cabin).  
- Keep all products working in `framed` default.  
- **Effort:** S–M. **Risk:** Low–medium (CSS/JS class on `body`, no product rewrite).

### Layer 2 — Navigation de-escalation
- Collapse 32 sticky tabs into Home / Favorites / Command Palette as primary; tabs optional or overflow.  
- Move engineering voice controls to Voice room / overflow.  
- Sidebar becomes contextual to active room (or collapsible to icons).  
- **Effort:** M. **Risk:** Medium (muscle memory).

### Layer 3 — Room layout ownership
- Chat / Fly / Health implement destination layouts **inside** room mode (one at a time per prior strategy).  
- Shell no longer dictates equal toolbar gravity.  
- **Effort:** M per room. **Risk:** Low if Layer 1 done.

### Layer 4 — Structural hygiene
- Split CSS by room; reduce `window` utils into explicit modules; modal registry; dedupe view maps; lazy-load heavy scripts (Three.js).  
- **Effort:** L over time. **Risk:** Low if incremental.

**Order matters:** Layer 1 before serious Chat implementation — otherwise Chat redesign fights furniture.

---

## 16. Risk analysis

| Path | Risk |
|---|---|
| Design rooms only (no shell evolution) | **High failure** — repeats Living Interface disappointment |
| Big-bang rewrite (React SPA) | **High** — stops shipping; unnecessary for the bottleneck |
| Layer 1 chrome policy first | **Low–medium** — reversible via default `framed` |
| Hide too much chrome without command palette readiness | Medium — discoverability dip |

---

## 17. Estimated effort (architecture only)

| Layer | Rough effort |
|---|---|
| L1 Room chrome policy + Chat/Fly/Health manifests | 1–2 focused weeks |
| L2 Nav de-escalation | 2–4 weeks |
| L3 Per-room destination implementations | As already planned — one room at a time |
| L4 Hygiene | Ongoing background |

---

## 18. Proof index (primary evidence)

| Claim | Evidence |
|---|---|
| Single shared layout for all views | `index.html` — all panels under `#mainContent`; `view_router.js` hide/show |
| Always-visible systems HUD/voice | `style.css` ~1562 comment; strips in `index.html` ~613–636 |
| No immersive opt-out | Zero matches for immersive/chromeless/full-bleed/zen |
| 32 tabs always in DOM | `index.html` ~570–604 |
| Sidebar multi-product always present | `index.html` aside ~35–566; 15 sections |
| Main named chat-panel | `index.html` ~568 |
| Monolith sizes | index 3534 lines; style.css 7034; ~45k JS lines; 125 scripts |
| Router knows every product | `view_router.js` init chain |
| ~27% screen framework tax | Measurement section above |
| Living Interface is paint not structure | `living_interface.css` on `#mainContent::before`; no chrome removal |
| Coupling extremes | Health vs Mission Control global read counts (explore audit) |
| Chat UI outside chatView | Majority of chat-related IDs outside panel (explore audit) |

---

## Final answer

**YES — the current GUI architecture is fundamentally holding Aria back from immersive, room-based experience.**

Not because vanilla HTML/JS cannot do it.  
Because the shell **forbids rooms from owning the first seconds of attention**, and forces every destination into the same capability-centric control frame.

**It can evolve** (Layers 1–4). It cannot succeed by mockups and CSS alone.

---

*Stop. Awaiting Jeff’s decision. No implementation performed.*
