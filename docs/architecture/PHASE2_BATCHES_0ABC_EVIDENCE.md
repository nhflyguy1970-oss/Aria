# Phase 2 Evidence — Batches 0, A, B, C (STOP)

**Date:** 2026-07-31  
**Rule:** Stop after Batch C. Batch D is plan-only.

---

## Batch 0 — Measured health

Artifacts: `docs/architecture/batch0/`

| Metric | Measured |
|--------|----------|
| Python files | 929 |
| Python LOC | 162,929 |
| Products | 16 |
| Extensions | 11 |
| HTTP routes (decorator scan) | 1,088 |
| Bridge files | 63 |
| Compat-density files | 53 |
| God modules (≥1000 LOC) | 10 |
| Silent `except: pass` in extra_routes (pre-fix) | 14 |

---

## Batch A — Foundation

### A1 Fail-loud registration
- **Added:** `jarvis/product_registration.py`
- **Changed:** `jarvis/gui/extra_routes.py` — product mounts via `register_product()` (log + ledger; never silent `pass`)
- **Health:** `/api/health` → `product_registration: {ok: true, registered_count: 21, failed_count: 0}`

### A2 Auth zones
- **Changed:** `jarvis/auth.py`
- **Rule:** Only **loopback** is key-exempt; LAN IP of host is **not** local
- **Health:** `auth_zones.lan_requires_key_when_configured: true`
- **Live:** `api_key_configured: true` on this host

### A3 Outcome mutation helper
- **Added:** `jarvis/gui/static/aria_mutate.js` (`window.ariaMutate`)
- Wired into `index.html`

### Tests
`tests/test_architecture_batch_abc.py` — registration, auth loopback-only, activity (with B/C)

---

## Batch B — Conversation unify (partial, complexity-reducing)

- **Added:** `jarvis/conversation_pipeline.py`
  - `normalize_action_params`
  - `apply_editor_params_if_coding`
  - `dispatch_action` (shared queue/registry cascade)
  - `decorate_result`
- **Changed:** `jarvis/assistant.py`
  - Sync `_process_unlocked` uses shared pipeline (deleted ~120 lines of duplicate dispatch/decorate)
  - Stream path uses shared normalize + editor params (deleted duplicate normalize block)
- **Behavior:** Intentional no user-visible change; stream-specific SSE coding paths retained
- **Remaining debt (honest):** Stream still has specialized coding stream branches — further unify later without bundling

---

## Batch C — Activity server SoT

- **Added:** `jarvis/activity_inbox.py`, `jarvis/activity_api.py`
- **Persistence:** `data/activity/inbox.jsonl`
- **API:** `GET /api/activity/inbox`, `POST /api/activity/publish|dismiss|read`
- **Client:** `activity_store.js` — server authoritative; localStorage cache; sync on load; publish/dismiss hit server
- **Live proof:**
  - publish `phase2-ev1` → inbox count 1
  - dismiss → ok
  - unit test dismiss removes from active list

---

## Certification (evidence, not authority)

```
POST /api/certification/run/sync {"skip_image": true, "label": "Phase2 BatchABC"}
```

Expect **SMOKE_PASS** or **DO_NOT_SHIP** — **not** READY_TO_SHIP without image suite (gate honesty from prior harden).

---

## Complexity reduction (net)

| Change | Effect |
|--------|--------|
| Fail-loud registration | Removes silent failure class |
| Auth loopback-only | Removes LAN key-bypass hole |
| conversation_pipeline | Deletes duplicate sync dispatch/decorate |
| activity_inbox | One server SoT; ends localStorage authority claim |
| Batch 0 reports | Measurable baseline |

**Not done (correctly deferred):** ACM memory deletion (Batch D plan only), full stream/sync merge of coding SSE, HA/voice stack collapse.

---

## Architecture Bible updates required

See companion patch in `ARCHITECTURE_BIBLE.md` section notes:
- Product registration fail-loud
- Auth zones
- Activity SoT = server `activity_inbox`
- Conversation shared pipeline module

---

## STOP — Approval gate

**Batch D plan:** `docs/architecture/BATCH_D_MEMORY_TRANSITION_PLAN.md`

Reply to approve Batch D implementation phases (D1–D5) or request changes.  
**No Memory/ACM code changes until you approve.**
