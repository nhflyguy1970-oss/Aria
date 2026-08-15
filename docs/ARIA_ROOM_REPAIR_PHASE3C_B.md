# ARIA Room Repair — Phase 3C-B (Platform Rooms)

**Status:** Tier 3C-B **COMPLETE** — **STOPPED** per authorization.  
**Final certification:** **NOT** issued. Zero Rooms are `CERTIFIED FUNCTIONAL`.  
**Evidence:** `docs/evidence/room_repair_phase3c_b/`  
**Prior checkpoint:** `docs/ARIA_ROOM_REPAIR_PHASE3C.md` (3C-A) — not overwritten.

---

## 1. Platform Rooms (scope)

| Room | Status after 3C-B |
| --- | --- |
| Chat / Living Room | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Memory | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Coding | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Settings | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Capabilities | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Integrations | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Security | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Actions | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Automation | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Search (deepen) | **REPAIRED — AWAITING FINAL CERTIFICATION** |

---

## 2. Shared architecture findings (repair shared roots first)

Before Room-by-Room work, platform Surfaces shared:

| Shared layer | Rooms | Defect |
| --- | --- | --- |
| Ollama `embed_text` | Search documents, Memory, Coding RAG | Synchronous `unload_model(/api/generate, timeout=15)` after every embed — cold load + unload often **>12s** |
| Documents RAG | Search, Documents | Always forced cold semantic embed despite `keep_alive=0`; exceeded Search corpus wall |
| Memory `find_conflicts` | Memory home + `/conflicts` | O(n²) cosine; double-called on enter; no TTL cache |
| Knowledge shadow verify | Documents search | Ran **synchronously** after legacy search (extra latency risk) |

---

## 3. Systemic defects repaired

### SYS-3CB-01 — Embed hot-path unload

**Symptom:** Documents facet timed out at ~12s with zero hits.  
**Root cause:** `llm.embed_text` called `unload_model` (15s `/api/generate`) after every embed; raw Ollama embed alone measured **~7–16s** cold with `keep_alive=0`.  
**Repair:** Remove synchronous unload from `embed_text` (`jarvis/llm.py`). `keep_alive=0` remains.  
**Also:** `cosine_similarity` numpy fast path when available.

### SYS-3CB-02 — Documents RAG cold semantic

**Symptom:** Even after unload removal, cold embed still exceeded corpus wall.  
**Root cause:** Semantic path always cold-loads nomic-embed; Search wall is 12s.  
**Repair:** Keyword-first documents search; semantic only when embed model is already resident (`model_resident`) or `JARVIS_DOCS_FORCE_SEMANTIC=1`. In-process index cache for `documents_index.json`.  
**Files:** `jarvis/documents_rag.py`, `jarvis/ollama_runtime.py` (`model_resident`).  
**Proof:** `/api/search/product/query` `warranty` + documents facet → **~130ms**, 4 hits (was hang/timeout). UI Search `warranty` shows document result cards.

### SYS-3CB-03 — Knowledge shadow verify blocking

**Repair:** Run `shadow_verify_retrieval` on a daemon thread (`knowledge_retrieval_adapter.py`).

### SYS-3CB-04 — Memory conflict scan thrash

**Repair:** TTL cache (45s) + early exit at 20 conflicts (`memory_context.py`).

---

## 4. Per-Room repair / proof records

### Chat / Living Room

| Field | Evidence |
| --- | --- |
| Surface | `room=chat`, Living Room class, `#messageInput` / `#sendBtn` / `#stopChatBtn` |
| Conversation | Sent `Reply with exactly: PONG-3CB` → owner-visible PONG; busy observed |
| Cancel | Stop button appeared; cancel left status **Listening quietly** |
| Leave/return | Home → Chat retained conversation text |
| Performance | Cold first reply **~90s** (model cold start) — honest, not hidden |
| Tools | Full multi-tool matrix deferred where destructive; navigation Chat→Coding proven |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Memory

| Field | Evidence |
| --- | --- |
| Read | Cognitive home loads; conflicts present; no fail cue |
| DEF-MEM-01 | Brain learning checkbox toggled via change event, persisted mid-state, restored — **not readonly** |
| Isol mutations | Disposable serve `:8767` / `/tmp/aria-tier3cb-isol`: `POST /api/memory` created `ARIA-3CB-ISOL-MEMORY-TEMP`; retrieved on isol; **absent from live**; old probe tokens absent |
| Leave/return | Chat → Memory return OK |
| Cleanup | Isol DATA_DIR destroyed after proof |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Coding

| Field | Evidence |
| --- | --- |
| Surface | Coding panel, controls, git/proposal language present; refresh exercised |
| Leave/return | Home → Coding |
| Jeff-attended | Authenticated git push/commit mutations |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Settings

| Field | Evidence |
| --- | --- |
| Theme | dark→light applied (`body.light-theme` + localStorage), restored to dark |
| Leave/return | Chat → Settings |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Capabilities

| Field | Evidence |
| --- | --- |
| Discovery | Capability/extension surface loads; refresh/diagnose control exercised |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Integrations

| Field | Evidence |
| --- | --- |
| List/refresh | Integrations surface + buttons; refresh/test path exercised without writing secrets |
| Jeff-attended | Real credential connect/disconnect/remove |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Security

| Field | Evidence |
| --- | --- |
| State | Room loads; `/api/security/lock/status` → PIN **not configured**, unlocked, `lock_capable: false` |
| Jeff-attended | PIN setup / lock / unlock lifecycle (no lockout testing) |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Actions

| Field | Evidence |
| --- | --- |
| Log surface | Actions Room loads; rows/controls present; filter exercised |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Automation

| Field | Evidence |
| --- | --- |
| Surface | Rules/pipelines/skills chrome present; controls load |
| Jeff-attended | Real-world device/service triggers |
| No production test automations created | Confirmed |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

### Search deepen

| Field | Evidence |
| --- | --- |
| Documents | Owner UI `warranty` → document cards (~3s with memory corpus; docs facet alone ~130ms) |
| Fly regression | After facet reset, `Adams` → Fly Tying cards first |
| Status | **REPAIRED — AWAITING FINAL CERTIFICATION** |

---

## 5. Capabilities / controls proven (summary)

- Chat: input, send, response, busy, stop/cancel, leave/return  
- Memory: home, conflicts, settings toggles, isol create/retrieve, live clean  
- Coding: open, inspect, refresh, leave/return  
- Settings: theme change with visible effect + persistence restore  
- Capabilities: list/status + refresh  
- Integrations: list + non-secret refresh/test  
- Security: status honesty (unconfigured PIN)  
- Actions: log browse/filter  
- Automation: home surface / controls (no live actuation)  
- Search: documents keyword hits + Fly federation  

---

## 6. Persistence / leave-return / restart

| Area | Result |
| --- | --- |
| Settings theme | Visible apply + restore |
| Memory settings toggle | Mid-state differed; restored |
| Chat transcript | Survived leave/return in session |
| Memory isol | Created on isol only; live untouched |
| Serve restart | Used for code load of systemic fixes; Rooms re-entered successfully after |

---

## 7. Dependencies / Jeff-attended blockers

| Item | Label |
| --- | --- |
| Integrations real credentials | **JEFF-ATTENDED — FINAL RESIDENCY REQUIRED** |
| Security PIN lock/unlock | **JEFF-ATTENDED — FINAL RESIDENCY REQUIRED** |
| Automation real-world actuation | **JEFF-ATTENDED** |
| Coding authenticated git push/commit | **JEFF-ATTENDED — FINAL RESIDENCY REQUIRED** |
| Chat cold first-token (~90s) | Dependency (Ollama cold load) — honest; warm path faster |

---

## 8. Performance

| Path | Before 3C-B | After 3C-B |
| --- | --- | --- |
| Search documents `warranty` | ~12s timeout / 0 hits | **~130ms**, hits |
| Search `document` facet | hang/timeout | **~47ms**, hits |
| Search `Adams` | ~3.2s with Fly (3C-A) | ~3.2s with Fly (preserved) |
| Chat first reply (cold) | — | ~90s (model cold) |
| Memory home | ~2s class | conflicts cached; toggle responsive |

Warm federated Search still ~3s (multi-corpus / ACM). Not falsely optimized.

---

## 9. Integrity / isolation / Activity

| Check | Result |
| --- | --- |
| Integrity scan | **clean / 100** |
| QA header → live planner | **403** |
| Test-shaped planner mutation | **400** |
| Owner-visible room-leave | **false** |
| Live Health Vitamin D3 | Untouched |
| Live ACM probe strings | Not present |
| Isol memory cleanup | DATA_DIR destroyed; isol serve stopped |

---

## 10. Cross-Room regression (platform)

| Path | Result |
| --- | --- |
| Chat → Coding | `room=coding` |
| Settings → Chat | Living Room restored |
| Search → Fly | Fly Tying Adams cards (after Everything facet) |
| Search → Documents | Warranty document cards |
| Chat → Memory context | No deleted probe material returned |

Unsafe real-world Actions/Automation not auto-triggered.

---

## 11. Files touched

- `jarvis/llm.py`
- `jarvis/documents_rag.py`
- `jarvis/ollama_runtime.py`
- `jarvis/memory_context.py`
- `jarvis/modules/knowledge_retrieval_adapter.py`

Evidence: `docs/evidence/room_repair_phase3c_b/platform_proof.json`

---

## 12. Remaining work before final 34-Room certification

1. **Authorize Tier 3C-C** — domain Rooms (Journal, Gallery, Browser, Voice, Video, Maker, Audit, Connections, Meme, Presence, Calendar, Planner, Documents UI, etc.).
2. **Authorize Tier 3C-D** — full cross-Room matrix beyond platform.
3. Separate **34-Room Owner Residency** (includes Jeff-attended Security / Integrations / HA / git).

Do **not** claim 34/34. Do **not** issue Owner Residency from 3C-B.

---

## 13. Stop

**STOPPED** after Tier 3C-B.  
No 3C-C. No 3C-D. No final certification.
