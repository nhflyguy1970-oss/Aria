# ARIA — Real-World Root Cause Repair

**Engineering acceptance (unchanged):** `FINAL PASS`  
**Phase:** Human-use trust repair after Jeff real-world FAIL  
**Evidence (V1):** `/tmp/aria-jeff-realworld/`  
**Evidence (V2):** `/tmp/aria-realworld-v2/`  
**Report (V1):** `docs/ARIA_JEFF_REAL_WORLD_ACCEPTANCE.md`  
**Report (V2):** `docs/ARIA_JEFF_REAL_WORLD_ACCEPTANCE_V2.md`

---

## Bug → root-cause map

| Bugs | Root cause | Subsystem |
|---|---|---|
| RW-001, RW-002, RW-008 | **ROOT-CONTEXT-001** — Research turns not binding follow-ups; bare chat invents entities; corrections do not re-anchor research | `research_context`, `router._follow_up_route`, `conversation_pipeline.decorate_result`, `session.note_research` |
| RW-003, RW-004, RW-005 | **ROOT-MEMORY-001** — Lexical ranking / alias expansion / default-allow relevance let stale or nearby facts answer | `behaviors/memory/engine.py` |
| RW-011 | **ROOT-MEMORY-002** — Teaching recognition outranked forget; ack said “I’ll remember” | `nlu/mapping.resolve_memory_route`, `cognitive_presentation` |
| RW-009, RW-010 | **ROOT-ORCHESTRATION-001** — “forget the truck” → memory/research; “status update” note → `runtime_status` | `nlu/mapping`, `runtime_routing`, `orchestration_policy` |

Three architectural roots (context binding, memory authority/honesty, intent/orchestration), not nine unrelated patches.

---

## ROOT-CONTEXT-001

### Failure mode
Ubuntu / Ranger research succeeded, but short follow-ups (`that one`, `what tools`) routed to bare `chat` without active research entities. Transcript omitted web-search turns, so the LLM continued older chat history (e.g. dinner email). Explicit “I meant Ubuntu…” did not replace the active research entity.

### Repair
1. `is_research_followup()` — detect short research continuations.
2. `_follow_up_route` — with session research context, route follow-ups and “I meant …” corrections to `web_search` with `expand_followup_query`.
3. `decorate_result` — append successful `web_search` Q&A into the conversation transcript.
4. Subject-change clears `last_research_query` / `research_entities`.

### Before → after
| Prompt (after Ubuntu/Ranger research) | Before | After |
|---|---|---|
| “And when did that one come out?” | `chat` → Samsung Note Edge | `web_search` expanded with Ubuntu entities |
| “No — I meant the Ubuntu LTS…” | stale 20.04 chat | `web_search` + research correction |
| “What else should I have before I start?” | dinner email / wrong topic | `web_search` with Ranger entities |

---

## ROOT-MEMORY-001 / ROOT-MEMORY-002

### Failure mode
Fresh “prefer desktop for heavy AI” lost to older GPU/workstation memories. “What else about that?” dumped scraper fragments. Never-told fishing reel answered with buddy/compressor facts (`fishing` aliased to buddy/mike; relevance defaulted True). “Forget that I prefer…” hit teaching and answered “I’ll remember…”.

### Repair
1. Forget / subject-change before teaching in `resolve_memory_route`.
2. Suppress teaching ack on forget phrasing.
3. Lexical scoring: prefer explicit preference language; demote QA residue; add recency; stop fishing→buddy alias.
4. `_memory_answer_relevant` default-deny for specific personal asks; require reel/brand evidence; bind “about that” via `last_subject`.

### Before → after
| Prompt | Before | After |
|---|---|---|
| Fresh desktop preference recall | old RTX/Charlestown | preference-weighted ranking + subject binding |
| Never-told fishing reel brand | buddy/compressor | honest miss when no reel evidence |
| “Forget that I prefer…” | “I’ll remember…” | `memory_forget`, no teaching ack |

---

## ROOT-ORCHESTRATION-001

### Failure mode
“Forget the truck. Let’s work on the fly project.” matched memory/consequential vehicle cues → `memory_search` / `web_search`. “Write a … project note … status update” matched bare `status` → `runtime_status`.

### Repair
1. `_CONVERSATIONAL_SUBJECT_CHANGE` → chat; clear research context.
2. `is_writing_request()` excludes writing from runtime routing; policy override `runtime_*` → chat.
3. Policy skips research steal on subject-change discourse containing “truck”.

### Before → after
| Prompt | Before | After |
|---|---|---|
| “Okay, forget the truck. Let’s work on the fly project.” | `memory_search` / research | `chat` + cleared research |
| “Write me a one-paragraph project note … status update…” | `runtime_status` | `chat` |

---

## Files changed

| File | Role |
|---|---|
| `jarvis/research_context.py` | `is_research_followup`, Ubuntu/LTS entities |
| `jarvis/router.py` | research follow-up/correction; subject-change reset |
| `jarvis/conversation_pipeline.py` | transcript for web_search |
| `jarvis/nlu/mapping.py` | forget before teaching; subject-change; writing→chat |
| `jarvis/runtime_routing.py` | `is_writing_request` |
| `jarvis/orchestration_policy.py` | writing / subject-change overrides |
| `jarvis/behaviors/memory/engine.py` | ranking, relevance, subject bind |
| `jarvis/behaviors/memory/cognitive_presentation.py` | no teaching ack on forget |
| `tests/test_realworld_trust.py` | natural-language regressions |

---

## Targeted tests

`tests/test_realworld_trust.py` — natural wording, not hard-coded intent labels:

- Forget preference / take out of memory → `memory_forget`
- Subject change → not `memory_search`
- Writing note → not `runtime_*`
- Research follow-ups → `web_search` with context
- Memory relevance default-deny / preference accept
- Teaching ack suppressed on forget
- Destructive refusal still holds

Run: `./venv/bin/python -m pytest tests/test_realworld_trust.py -q`

---

## Preserved behaviors (do not regress)

Research (Ubuntu/Ranger → web_search), consequential torque (no invention), wipe `/` hard refusal, clarify, planner/settings persistence, model selection, Stop (no sticky), Gallery external ComfyUI link, BUG-024 untouched, engineering denominator unchanged.

---

## Dual status

```text
ENGINEERING ACCEPTANCE: FINAL PASS
REAL-WORLD ACCEPTANCE:  REAL-WORLD PASS
```

See `docs/ARIA_JEFF_REAL_WORLD_ACCEPTANCE_V2.md`. Soft notes only: research follow-up synthesis can cite an older LTS than the prior turn; bare “fly project” chat may invent the EDM band (routing correct).
