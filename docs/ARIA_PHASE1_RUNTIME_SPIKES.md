# Aria Phase 1 — Runtime Spikes Report

**Status:** Phase 1 Certification complete — see **`docs/ARIA_RUNTIME_R1_RECOMMENDATION.md`**  
**Runtime selected?** **No — recommendation awaiting Jeff approval (E1 recommended).**  
**Charter:** `docs/ARIA_NEXT_GENERATION_CHARTER.md`  
**Date:** 2026-08-06  
**Host:** Linux · DISPLAY=:1 · NVIDIA RTX 3060 12GB  

This report obeys the charter: evaluate equally, do not choose on popularity, do not ship R1 until evidence is sufficient and **approved**.

---

## Live certification summary

| Candidate | Live Aria | Rooms toured | Peak RSS | Backend after | Law 2 |
|---|---|---|---|---|---|
| E1 Electron | ✓ | 10 | ~747 MB | ✓ | Pass (bundled) |
| E3 Qt Stage-only | ✓ | 10 | ~755 MB | timeout once / recovered | Pass (embedded) |
| E2 Tauri-class | ✗ | — | — | — | Incomplete (WebKitGTK OS) |

Harness: `scripts/phase1_runtime_certify.py` · JSON: `docs/phase1_runtime_spikes/cert_*.json`

---

## 1. Mandate

Runtime Independence is law. Evaluate E1 / E2 / E3 (and superior alternatives only) on:

Startup · Memory · GPU · Rendering · Python integration · Packaging · Linux · Windows · Future macOS · Accessibility · Long-session stability · Local AI · Update model · Developer workflow · Five-year maintainability

---

## 2. Candidate map

| ID | Class | In-repo today | Spike status |
|---|---|---|---|
| **E1** | Bundled Chromium (Electron-class) | `jarvis/electron_shell.py` + new `scripts/electron-shell/` spike | **Measured** on Linux |
| **E2** | Lightweight native shell + webview (Tauri-class) | Rust/cargo present; **no** product scaffold | **Qualitative + Law 2 risk** — needs hello-world if shortlisted |
| **E3** | Qt WebEngine via PySide6 | `jarvis/pyside_shell.py`, Fluent path, venv deps installed | **Measured** on Linux |
| **E4** | Custom CEF | None | Not spiked — higher cost, no superior evidence yet |
| **E5** | External Chrome `--app` | Historical launcher mode | **Disqualified** as shipped target (Law 2) |

---

## 3. Measured evidence (Linux)

Artifacts: `docs/phase1_runtime_spikes/measure_latest.json`  
Harness: `scripts/phase1_runtime_spike_measure.py`

### E3 — PySide6 + Qt WebEngine (about:blank)

| Metric | Value |
|---|---|
| Import time | ~135 ms |
| Show → event loop | ~362 ms |
| Self RSS after import | ~71 MB |
| Self peak RSS (ru_maxrss) | ~313 MB |
| **Process-tree RSS peak** (parent+children) | **~479 MB** |
| Load about:blank | OK |
| Site-packages PySide6 size | ~649 MB (dev install; ≠ final package) |

### E1 — Electron 37 spike (about:blank, auto-quit)

| Metric | Value |
|---|---|
| Wall time (launch→quit ~4s) | ~4.4 s |
| Process-tree RSS peak | **~357 MB** |
| Dist folder size | ~283 MB |
| Exit | 0 |
| Notes | Dev security warning (expected unpackaged); NSS root cert noise on this host |

### E2 — Tauri-class

| Metric | Value |
|---|---|
| cargo / rustc | 1.95.0 present |
| Measured window | **Not yet** |
| Law 2 note | Default Linux WebKitGTK is not “install Chrome,” but **engine version is OS-coupled** unless pinned/bundled — must be proven before E2 can be R1 |

**Interpretation (startup/memory only):** On this Linux host, cold blank-window memory is in the same ballpark (Electron tree ~357 MB vs Qt WebEngine tree ~479 MB). Neither is “light.” Packaging and Python integration matter more than this single RSS delta.

---

## 4. Evaluation matrix (evidence-weighted, not final scores)

Scale: **S** strong · **M** mixed · **W** weak · **?** unknown / needs spike · **X** fails law

| Criterion | E1 Electron | E2 Tauri-class | E3 Qt WebEngine |
|---|---|---|---|
| Startup (Linux blank) | M (measured OK) | ? | S–M (fast import; heavier tree RSS) |
| Memory | M (~357 MB tree) | ? (often smaller host; engine TBD) | M (~479 MB tree) |
| GPU / rich UI | S (Chromium) | M/? (webview-dependent) | S (Chromium-based QtWebEngine) |
| Rendering fidelity vs Aria HTML/CSS/JS | S | M/? | S |
| Python integration | M (HTTP/IPC; separate process) | M (HTTP/IPC; Rust bridge) | **S** (in-process with backend venv possible) |
| Packaging | M (mature; heavy) | S–M if pinned | M (Qt deploy complexity; already partial) |
| Linux (Jeff primary) | S (measured) | M (WebKitGTK coupling risk) | S (measured; available in venv) |
| Windows | S (mature) | S | S |
| Future macOS | S | S | S |
| Accessibility | S (Chromium a11y) | M/? | M–S (Qt + web a11y) |
| Long-session stability | S (widely proven) | M/? | M–S (must soak-test) |
| Local AI integration | M (via backend HTTP) | M | **S–M** (same process/venv affinity) |
| Update model | M (ship Chromium updates) | M (host + webview policy) | M (Qt/PySide updates) |
| Developer workflow | S (Node familiar; hot reload web) | M (Rust toolchain) | S for this repo (already used) |
| Five-year maintainability | S (large ecosystem) | M (younger; pinning discipline) | M–S (Qt/PySide longevity; dual-UI risk if Fluent forks) |
| **Law 2 Runtime Independence** | **S** (bundles Chromium) | **M until pinning proven** | **S** (embeds WebEngine; no Chrome install) |
| Living Workspace Stage fit | S | S if Law 2 cleared | S — **warn:** must be **single Stage UI**, not native dashboard + web fork |
| In-repo maturity | M (launcher existed; shell missing until spike) | W | **S** (Fluent/WebEngine paths exist) |

---

## 5. Architecture fit (charter-critical)

| Concern | Finding |
|---|---|
| HTML/CSS/JS as materials | All three can host Stage |
| Workspace must disappear | Host chrome must stay thin — Fluent native nav is a **risk** for Law “Workspace disappears” unless Stage owns 100% of canvas |
| Activities / Rooms / Tools | Runtime-neutral — contracts live in JS/workspace layer |
| Backend preserve | All OK via localhost/IPC; E3 can share venv most tightly |
| Dual identity risk | **E3 Fluent** currently has native dashboard tab + web panel — Next Gen requires **one Stage**. Spike recommendation: if E3 advances, **WebEngine-only Stage window** (no second UX) |

---

## 6. Challenges / open evidence gaps

1. **E2 unmeasured** — no hello-world RSS/startup/package size yet.  
2. **E2 Law 2** — pinning strategy for Linux/Windows/macOS not proven.  
3. **Long-session soak** — none of E1/E3 soaked for hours with full Aria UI yet.  
4. **GPU path** — blank window only; Gallery/Fly large imagery not stress-tested.  
5. **Packaging true ship size** — site-packages ≠ installer; Electron asar ≠ full Chromium audit.  
6. **Update channel** — none designed.  
7. **Accessibility** — no VoiceOver/Orca pass yet.  
8. **Python + GPU local AI** — side-by-side with WebEngine/Electron memory pressure untested.

---

## 7. What was built for Phase 1 (spikes only)

| Artifact | Purpose |
|---|---|
| `docs/ARIA_NEXT_GENERATION_CHARTER.md` | Official approved charter |
| `scripts/electron-shell/` | Minimal E1 spike host |
| `scripts/install-electron-shell.sh` | Install Electron spike |
| `scripts/phase1_runtime_spike_measure.py` | Measurement harness |
| `docs/phase1_runtime_spikes/measure_*.json` | Raw evidence |

**Not done (correctly blocked):** Workspace implementation, room redesigns, runtime selection, R1 packaging.

---

## 8. Preliminary recommendation posture (not a selection)

**Do not select yet.**

Evidence so far:

- **E1 and E3 are both Law-2-capable** on Linux with measured blank-window viability.  
- **E3** has deepest in-repo integration and Python affinity, but must shed dual-UI Fluent dashboard pattern for Living Workspace.  
- **E1** has clean “one web Stage” story and strong cross-OS Chromium consistency; heavier updates/binary.  
- **E2** remains interesting for size **only after** a pinned-engine Law-2 spike.

### Suggested next spike actions (still Phase 1)

1. **E3 Stage-only spike** — QMainWindow/WebEngine fullscreen Stage loading live Aria URL; no Fluent nav. Measure memory with real `#chat`.  
2. **E1 Stage spike** — load live Aria URL; measure memory + 30–60 min soak.  
3. **E2 hello-world** (optional shortlist) — Tauri blank + document webview provenance; Linux WebKitGTK vs pinned WebView2/WKWebView policy matrix.  
4. Scorecard after (1)–(3) with soak + packaging estimates → **then** Jeff selects R1.

---

## 9. Decision gate

| Gate | Status |
|---|---|
| Charter approved | ✓ |
| Phase 1 authorized | ✓ |
| Equal evaluation started | ✓ |
| Runtime selected | **✗ Not yet** |
| Phase 2 Workspace coding | **Blocked** |

---

*Phase 1 continues until soak/packaging/Law-2 gaps close enough for an evidence-based R1 choice.*
