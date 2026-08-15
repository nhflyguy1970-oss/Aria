# Aria Next Generation — Runtime R1 Recommendation

**Phase:** 1 complete (Runtime Certification)  
**Date:** 2026-08-06  
**Charter:** `docs/ARIA_NEXT_GENERATION_CHARTER.md`  
**Status:** **RECOMMENDATION READY — awaiting Jeff approval**  
**Hard stop:** Do not begin Workspace / Chat / rooms until this recommendation is approved.

---

## Executive answer

### Recommended Runtime R1: **E1 — Bundled Chromium shell (Electron-class)**

**Not because Electron is popular.**  
Because on Jeff’s Linux machine, under live Aria certification, it:

1. Satisfies **Runtime Independence** unambiguously (engine ships with Aria).  
2. Hosts a **single Stage** without inheriting the Fluent dual-UI anti-pattern.  
3. Matched E3 on real-room memory and navigation (~747 MB peak vs ~754 MB).  
4. Kept backend healthy after a full room tour + idle soak.  
5. Offers the clearest decade path to “launch Aria, not a webpage” packaging.

### Not selected for R1

| Candidate | Disposition |
|---|---|
| **E3 Qt WebEngine (PySide)** | **Viable alternate** — Stage-only proven; reject as primary due to dual-UI gravity + packaging complexity |
| **E2 Tauri-class** | **Defer** — Law 2 not proven (OS WebKitGTK coupling); no live Aria cert |

---

## Certification evidence (live Aria)

Backend: `http://127.0.0.1:8765/` · version 3.1.0 · healthy before runs  
Harness: `scripts/phase1_runtime_certify.py`  
Raw: `docs/phase1_runtime_spikes/cert_*.json`

### Protocol

- Native Stage window (no browser chrome, no Fluent nav for E3)  
- Load live Aria  
- Tour: chat → health → flytying → workstation → planner → gallery → documents → coding → search → dashboard  
- Idle soak to ~180s total  
- Sample process-tree RSS + GPU  

### Results

| | E1 Electron | E3 Qt WebEngine Stage-only | E2 Tauri-class |
|---|---|---|---|
| Load live Aria | ✓ (~1.2s) | ✓ (~1.4s) | Not measured |
| Room tour (10) | ✓ | ✓ | — |
| Peak RSS (tree) | **~747 MB** | **~755 MB** | — |
| GPU during tour | Low util; ~560 MB VRAM used (shared host) | Same class | — |
| Backend after soak | ✓ | One end-of-run timeout (server recovered) | — |
| Law 2 | **Pass** (bundled Chromium) | **Pass** (embedded WebEngine) | **Incomplete** (WebKitGTK 2.52.3 OS-coupled) |
| Feels like browser? | Medium risk until branded/packaged | Medium risk (Chromium engine) but native window | Unknown |

Blank-window earlier spikes (~357 vs ~479 MB) do **not** dominate; under real Aria both converge ~0.75 GB.

---

## Per-candidate dossier

### E1 — Electron-class (RECOMMENDED R1)

**Strengths**
- Bundled Chromium → clear Law 2  
- Natural single-Stage model for Living Workspace  
- Live cert passed (rooms + soak + backend)  
- Strong Windows / future macOS shipping norms  
- Web UI materials (HTML/CSS/JS) unchanged — backend untouched  
- Update story is explicit (ship Chromium with Aria)

**Weaknesses**
- Heavy host (~283 MB dist floor before app assets)  
- Unpackaged Electron can *feel* like a webpage shell — branding/packaging mandatory  
- Chromium security/update cadence is an ongoing duty  
- Python remains out-of-process (HTTP/IPC) — acceptable, not intimate

**Architectural risks**
- Letting Electron APIs leak into product code (must forbid — Stage owns UX)  
- Treating “open DevTools” workflows as product identity  

**Living Workspace compatibility**
- **High** — Stage-first; chrome policy can hide host chrome  
- Must ship as **Aria** (icon, title, no URL bar, no default menu theater)

**Long-term maintenance**
- Predictable; large ecosystem; cost is Chromium bumps  

**Developer experience**
- Fast web iteration; Node toolchain already on machine; spike scaffold exists  

**Reasons to reject**
- If Jeff requires smallest possible binary above all else  
- If in-process Python UI bridging is a hard requirement  

**Reasons to adopt**
- Best balance of Law 2 + Stage purity + live evidence + shipping identity  
- Avoids fighting existing Fluent dual-surface design  

---

### E3 — Qt WebEngine / PySide (ALTERNATE — not R1 primary)

**Strengths**
- Already deepest in-repo desktop integration  
- Stage-only live cert passed (rooms + soak)  
- Same-venv Python affinity (future native helpers easier)  
- Law 2 satisfied without external Chrome  
- Default launcher lore already points Fluent/PySide  

**Weaknesses**
- Under load, **not lighter** than Electron (~755 MB)  
- PySide/Qt site footprint large (~649 MB dev tree)  
- Existing **FluentWindow + native dashboard + web panel** fights Living Workspace  
- Qt packaging/deploy on Linux is historically painful  
- NSS noise observed; occasional backend probe timeout under soak  

**Architectural risks**
- Re-expanding Fluent chrome “because it’s there”  
- Splitting identity: native Mission vs web Rooms  

**Living Workspace compatibility**
- **High only if Stage-only is mandatory law**  
- Fluent product chrome as shipped UX: **FAIL** charter tests  

**Long-term maintenance**
- Tied to Qt/PySide release trains; dual skill (Qt + web)

**Developer experience**
- Excellent for this repo’s Python center of gravity  

**Reasons to reject as R1 primary**
- Dual-UI gravity  
- No memory win vs E1 under live Aria  
- Packaging/ops complexity without compensating Living Workspace benefit  

**Reasons to keep as alternate**
- Proven Stage-only path if Electron packaging fails on Jeff’s Linux  
- Best option if future requires deep in-process Python UI bridges  

---

### E2 — Tauri-class (DEFER — not R1)

**Strengths**
- Potential smaller host  
- Rust security posture  
- Can host a Stage in principle  
- Toolchain present (cargo/rustc 1.95; WebKitGTK 2.52.3 on host)

**Weaknesses**
- **No live Aria certification**  
- Default Linux engine = **OS WebKitGTK** — not Aria-owned version  
- Windows WebView2 Evergreen may imply external runtime install — Law 2 risk  
- Python sidecar story must be built from scratch  

**Architectural risks**
- Shipping “depends on distro WebKit” as if it were Runtime Independence  
- Under-investing in polish due to thinner desktop web ecosystem  

**Living Workspace compatibility**
- Possible later; **not evidenced now**

**Reasons to reject for R1**
- Incomplete Law 2 proof  
- No live certification  
- Higher near-term delivery risk  

**Reasons to reopen later**
- After Workspace exists, if binary size / attack surface becomes the binding constraint **and** a pinned/bundled engine policy is proven on Linux+Windows+macOS  

---

## Failure-condition check (charter)

| Failure if… | E1 | E3 Stage-only | E2 |
|---|---|---|---|
| Feels like a browser | Mitigate via packaging/branding | Mitigate via Stage branding | Unknown |
| Shell around a webpage | Risk if unbranded | Risk if Fluent returns | — |
| Limits immersive rooms | No (Stage full canvas) | No (Stage-only) | Unknown |
| Unnecessary complexity | Low–med (Chromium updates) | Med (Qt + web + ban Fluent) | High now |
| Fights Living Workspace | No if Stage-only product law | **Yes if Fluent kept** | Law 2 incomplete |
| Permanent bad compromises | Avoid Electron API leakage | Avoid dual UI | OS webview drift |

---

## Local AI coexistence

Neither E1 nor E3 rewrote the backend. Both talked to existing `/api/live`. GPU VRAM during UI tour stayed modest vs 12 GB card — headroom for Ollama/Comfy remains a **process scheduling** concern, not a runtime disqualifier. Recommend post-R1 soak with image gen + voice + long chat under the chosen host.

---

## Recommendation conditions (must follow if E1 approved)

1. **Product identity:** ship as Aria (icon, title, protocol); never instruct Jeff to “open Chrome.”  
2. **Stage law:** all Living Workspace UI runs in one web Stage; no second native product surface.  
3. **No Electron religion:** forbid Electron-specific patterns from shaping Activities/Rooms/Tools.  
4. **Backend adapters only:** HTTP/IPC; no backend rewrite.  
5. **Update channel:** plan Chromium/Electron bumps as Aria updates.  
6. **Human soak:** Jeff should still live a morning in R1 before Phase 2 freezes assumptions.  
7. **E3 contingency:** keep Stage-only PySide spike scripts; do not delete the path.

---

## What Phase 1 intentionally did *not* do

- Workspace implementation  
- Chat / Fly Tying / Health / any room redesign  
- Runtime fashion advocacy  
- Declaring victory on blank-window benches alone  

---

## Decision gate for Jeff

- [ ] **Approve E1 as Runtime R1** (recommended)  
- [ ] Approve E3 Stage-only as R1 instead  
- [ ] Reject both — continue spikes (state what’s missing)  
- [ ] Explicitly defer E2  

**Until approval: stop. No Phase 2 Workspace coding.**

---

*Evidence over preference. Aria over Electron/Qt/Tauri.*
