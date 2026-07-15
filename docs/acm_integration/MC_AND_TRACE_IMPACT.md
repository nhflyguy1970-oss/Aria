# Mission Control & Conversation Trace — Integration Impact

**Status:** M1–M3 IMPLEMENTED (observables live) · No UI redesign
**Parts:** 5 (Mission Control) · 6 (Conversation Trace)

M1 delivered:

- `mission_control_panel()["shadow"]` agreement counters / authoritative route (legacy|acm|rollback)
- Trace `memory_operation` additive `schema=memory_operation.v2`, `authoritative`, `shadow_agree`, `acm_verb`
- M3: when PRIMARY, `authoritative=acm` and primary op counters; ROLLBACK restores legacy

---

## Part 5 — Mission Control (impact only)

### Touchpoints

| Layer | Path | Role today |
|-------|------|------------|
| Aria entry | `jarvis/mission_control.py` | Host entry to platform aggregator |
| Aggregator | AI-Platform `mission_control/aggregator.py` `_memory_panel()` | Calls Aria Core |
| Panel source | `aria_core.memory.mission_control_panel()` | CRUD/health/history/latency proxies |

### Impact matrix (no layout redesign)

| Component | Today | After ACM cutover | Change type | Payload notes |
|-----------|-------|-------------------|-------------|---------------|
| Memory panel entrypoint | `mission_control_panel` | Same function name; body from ACM | INTERFACE | Stable host contract |
| Memory health | store stats / fragmentation proxy | `verify_persistence` + experience/concept counts + ValidationHarness | INTERFACE | counts/flags only |
| Counters | CRUD op history ring | lifecycle verb counts (encode/remember/cool/sleep/learn) | INTERFACE | |
| Latency | retrieval decision ms | CognitiveTrace / Activation latency_ms; Shadow ms (M1) | INTERFACE | |
| Confidence | sparse | Confidence organ aggregates (`how_certain_am_i` samples) | INTERFACE display | no content |
| Provenance | rare | stamp counts / sampled ids | INTERFACE display | no content |
| Agreement (Shadow M1) | N/A | shadow agree/disagree / authoritative | Engineering visibility | M1–M2 only |
| Learning / cognition tabs | host learning history | adaptation counts from ACM Learning + host coordinator status | INTERFACE | |
| Content display | avoided | Still avoided | No redesign | |

### Phase flag behavior

| Phase | MC authority signal |
|-------|---------------------|
| M0–M2 | `authoritative=legacy`; optional Shadow metrics row |
| M3 | `authoritative=acm`; legacy health hidden or forensic |
| M4 | legacy metrics removed |

### Aggregator note

AI-Platform MC aggregator keeps calling Aria façades — **no ACM import inside AI-Platform**. If DualWrite panel exists, mark as non-authoritative / retirement pending.

---

## Part 6 — Conversation Trace (impact only)

### Current

- `aria_core/conversation_trace.py`  
- `organs.memory`: inferred read/write from action names  
- `memory_operation`: `{ action, retrieval }` from ranking diagnostics  
- Policy: **no memory contents**; ids/scores/flags only  
- Platform bridge aggregates organ use counts

### Required field extensions (observables only)

| Field | Type | Meaning |
|-------|------|---------|
| `acm_verb` | string | encode / remember / sleep / learn / reconcile / assess / cool / revise / reflect / predict / simulate / … |
| `attention_class` | string | Attention organ class |
| `reconsolidation` | string\|null | light / contest / null |
| `confidence` | number\|object | assessed summary |
| `provenance_count` | int | stamps touched |
| `ambiguous` | bool | remembering ambiguity |
| `authoritative` | `legacy`\|`acm` | phase-dependent |
| `shadow_agree` | bool\|null | M1 only |
| `experience_ids` | string[] | ids only, not text |
| `hypothetical` | bool | prediction/simulation |

Schema version: bump Trace schema `memory_operation.v2` (additive); old consumers ignore unknown fields.

### Cognitive event → Trace map

| Cognitive event | Trace signal |
|-----------------|--------------|
| Remembering | `acm_verb=remember` + activation size |
| Learning | `learn` + adaptation ids/counts |
| Reflection | reflective experience id |
| Prediction | `predict`; `hypothetical=true` |
| Simulation | `simulate`; `hypothetical=true` |
| Reconciliation | reconcile status |
| Confidence | assess / confidence deltas |
| Provenance | stamp ids/counts |
| Offline sleep | `sleep` + proposal counts |

### Writer call sites (design)

| Site | Change |
|------|--------|
| MemoryEngine / Cap Bus façades | emit `acm_verb` after bridge call |
| `acm_bridge` Shadow compare | emit `shadow_agree` |
| consolidate / sleep path | emit sleep |
| Learning Manager commit | emit learn/assent |

### Privacy / retention

Unchanged: **no prompts, no chain-of-thought, no memory contents** in Trace payloads. Retention follows existing Trace policy.

### Out of scope

Trace UI redesign · new Mission Control tabs · embedding ACM inside AI-Platform.
