# Integration Test Plan — Aria ACM Replacement

**Status:** DESIGN ONLY  
**Policy:** Include **Supremacy compliance** as a hard gate.  
**Related:** ACM `docs/COGNITIVE_MEMORY_TEST_STRATEGY.md` · Aria `docs/COGNITIVE_MEMORY_TEST_STRATEGY.md` (if present) · `tests/test_memory*.py`

---

## Quantified gates (locked design defaults)

| Gate | Metric | Threshold |
|------|--------|-----------|
| Shadow agreement (M1) | Normalized answer agree rate on golden set (N≥100) | ≥ **85%** before M2; ≥ **92%** before M3 |
| Recall latency | `what_do_i_remember` / façade p95 | ≤ **max(1.25 × legacy p95, legacy p95 + 150ms)** on same hardware |
| Encode latency | `encode` p95 | ≤ **500ms** local durable (no network LLM) |
| Shadow overhead (M1) | Extra wall ms vs legacy-only | ≤ **100ms** p95 |
| Migration completeness | P0 `legacy_id` coverage | ≥ **99.5%** |
| UAT preference pack | Human agree | ≥ **95%** (N≥20) |
| Rollback drill | Flag flip restores legacy | **100%** on rehearsal |
| Supremacy | Parallel SoT writes when PRIMARY | **0** |
| CoT / content leak | Trace/MC payloads | **0** content or prompts |

**Answer normalizer (Shadow):** lowercase; strip punctuation; equate synonym booleans (yes/no); compare extracted slot values for fact questions (`favorite coffee` → beverage token); journal megablobs never required for agree on fact Qs.

---

## Gate 0 — Supremacy compliance

| Test ID | Expect |
|---------|--------|
| `SUP-01` | Runtime imports vendored `aria_acm` only |
| `SUP-02` | When PRIMARY: legacy store write count = 0 (except rollback mode) |
| `SUP-03` | Static inventory: no Aria class reimplements Activate/Remember organs |
| `SUP-04` | Façades call `CognitiveEngine`; Trace shows `acm_verb` |
| `SUP-05` | No site-packages `aria-cognitive-memory` resolution for cognition |

Fail ⇒ **do not advance phase**.

---

## Suites by phase

### M0 — Import / packaging

| ID | Focus |
|----|-------|
| `M0-01` | `VERSION.json` pin matches tree hash |
| `M0-02` | Import authority CI |
| `M0-03` | Smoke: tmp CognitiveEngine encode/remember |

### M1 — Shadow

| ID | Focus |
|----|-------|
| `M1-01` | Dual-call; `authoritative=legacy`; `user_visible_changed=false` |
| `M1-02` | Agreement rate vs golden set (closes ACM cert Condition 1 vs **real** Aria) |
| `M1-03` | Shadow latency overhead |
| `M1-04` | MC shows agreement counters (no content) |

### M2 — Harvest migrate

| ID | Focus |
|----|-------|
| `M2-01` | Completeness / provenance / idempotency |
| `M2-02` | Supersede → revise lineage |
| `M2-03` | Identity assent high-impact |
| `M2-04` | Journal/project/preference spot packs |

### M3 — ACM primary

| ID | Focus |
|----|-------|
| `M3-01` | Cap Bus remember/recall from ACM |
| `M3-02` | MemoryBehavior action matrix → ACM path |
| `M3-03` | Correction / soft forget |
| `M3-04` | prepare_context ACM, no CoT |
| `M3-05` | Latency SLO |
| `M3-06` | Rollback drill green within window |

### M4 — Removal

| ID | Focus |
|----|-------|
| `M4-01` | Grep/CI forbid retired SoT writers |
| `M4-02` | DualWrite authority disabled |
| `M4-03` | Specialized modules gone or ACM clients |

---

## Behavioral / regression

- Cap Bus parity scenarios vs golden intents (`tests/test_memory_retrieval_quality.py` patterns rewritten for façades).  
- Each MemoryBehavior action → ACM path (table in API mapping).  
- Event contracts emit ids only.  
- REST `/api/memory*` smoke.

---

## Memory correctness

- Experience immutability under correction.  
- Reconciliation retains competing evidence.  
- Confidence evolves on conflict/corroboration.  
- Prediction/simulation marked hypothetical (reality wall).

---

## Performance

- encode / remember / flush p95 vs thresholds above.  
- Storage growth after harvest recorded (baseline + % alert, not hard fail unless >10× anomaly).

---

## Rollback tests

| ID | Expect |
|----|--------|
| `RB-01` | `ARIA_ACM_PRIMARY=false` + `ROLLBACK=true` → Cap Bus legacy answers |
| `RB-02` | Legacy checksum match |
| `RB-03` | ACM data retained for forensics |
| `RB-04` | Rehearsal on staging before first M3 |

---

## Long-duration / Daily Use

| ID | Script |
|----|--------|
| `DU-01` | Multi-day soak staging (≥ 72h) |
| `DU-02` | Daily Use: remember, recall, correct, forget, journal, project checkpoint, sleep |
| `DU-03` | UAT human checklist (about-me, preferences, forget precision) |

---

## User acceptance

- “What do you know about me?” quality (human rubric).  
- Preference continuity.  
- Forget precision (topic tokens).  
- No prompt/CoT in user-visible memory explanations.

---

## CI job names (design)

| Job | Runs |
|-----|------|
| `aria-acm-import-authority` | M0+ |
| `aria-acm-supremacy` | M1+ |
| `aria-acm-shadow-golden` | M1–M2 |
| `aria-acm-migration-report` | M2 |
| `aria-acm-primary-regression` | M3+ |
| `aria-acm-rollback-drill` | pre-M3 + scheduled |

---

## Removal readiness (M4)

See [`REMOVAL_PLAN.md`](REMOVAL_PLAN.md) operator checklist + CI forbid-imports.
