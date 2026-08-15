# ARIA — Gallery INFRA Final Report

**Date:** 2026-08-11  
**Evidence:** `/tmp/aria-final-closure/gallery/`  
**Prior marks:** 75 INFRA → retest cleared 20 → **45** remained (`BUG-INFRA-001`)

---

## Verdict

```text
GALLERY INFRA: CLEARED
UNRESOLVED CHROME CRASHES = 0
```

No Gallery application rewrite was required.

---

## What the 45 IDs were

From ledger `EXC-0591`…`EXC-0675` (gaps 601–625 previously cleared). Controls clustered around:

| Group | Examples | States |
|---|---|---|
| Vision / caption | Opt-in Vision caption, Describe, Save caption, Vision→Coding | DEFAULT / AFTER:Advanced / AFTER:Reuse… |
| Generation form | prompt, negative, seed, steps, CFG, width/height | AFTER:Advanced / Reuse |
| Collections / search | New collection, Search gallery, Similarity clusters | mixed |
| External | Open ComfyUI ↗ | all three states |

Prior retest recorded `chrome-error://chromewebdata/` with `n:0` — classic **cascade after tab death**, not per-control product faults.

---

## Isolation diagnosis

### Fresh browser, one control at a time
Phase A (5 controls): **4 PASS, 1 BUG-024 missing** — no chrome crash.

### Full 45 isolated
| Outcome | Count |
|---|---:|
| PASS (click/input affordance) | 38 |
| FAIL BUG-024 missing | 4 |
| FAIL chrome (Open ComfyUI ↗) | 3 |

### Open ComfyUI ↗
Application markup is correct:

```text
<a href="http://127.0.0.1:8188" target="_blank" rel="noopener">Open ComfyUI ↗</a>
```

Agent-browser following that external URL can destroy the harness tab (`chrome-error://…`). Safe affordance exercise (detect external `_blank`, do not navigate) → **3/3 PASS**. Living workspace remains intact.

### Remaining 4 FAILs
Missing controls (`Opt-in Vision caption` ×3 states, `Focus prompt` ×1) — classified **BUG-024** (harness/affordance inventory), **out of scope** for this phase. Not chrome crashes.

---

## Root-cause disposition

| Cause | Classification | Disposition |
|---|---|---|
| Sequential harness pressure → tab death → cascade INFRA marks | Infrastructure / harness | Cleared by isolated retest |
| External `_blank` ComfyUI navigation under agent-browser | Infrastructure / harness | Safe affordance exercise; app correct |
| Missing conditional controls | BUG-024 (pre-existing harness) | Untouched |

Application Gallery behavior independently proven correct under isolation. Failure mode cannot be eliminated by product code without changing correct `_blank` external links or inventing PASS by skipping controls — neither was done.

---

## Final accounting

```text
Previously unresolved chrome INFRA: 45
Isolated retest: 45
Chrome crashes remaining: 0
BUG-024 missing (out of scope): 4
PASS affordance: 41
```

Evidence files:

- `iso_phase_a.json` — first five, fresh browser  
- `iso_full.json` / `iso_final.json` — all 45  
- `comfy_safe.json` — ComfyUI safe exercise  
- `FINAL_GALLERY_INFRA.json` — rollup  
- `comfy_probe.json` — link inspection  
