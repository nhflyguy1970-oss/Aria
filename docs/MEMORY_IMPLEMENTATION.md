# Memory Implementation (ACM)

## Executive Summary

Aria Memory is **autobiographical cognition** on **ACM PRIMARY** — not a CRUD database,
not a notes app, and not a vector store as source of truth.

This delivery transforms the product surface from “edit records” into
“understand what Aria knows, why, and how it changes,” while preserving
fail-closed authority and the Memory Design Principles constitution.

## ACM alignment

| Principle | Implementation |
|-----------|----------------|
| Memory ≠ storage | Cognitive Memory Home + chat recall |
| Remembering changes memory | Correct = revise with lineage |
| Soft forget | Cool / strong cool via ACM `cool_memory` |
| Knowledge ≠ memory | Candidates queue; Knowledge separated in UI |
| User controls autobiography | Adopt required for staged facts |
| Fail-closed PRIMARY | Unchanged; services encode only via store→ACM |

**Authority:** `data/acm/cognitive.db` via `aria_core.acm_bridge`.  
**Candidates:** `data/memory_candidates.json` — staging only, never SoT.

## Memory Home

Sections: About you · Safety & authority · Health · Sleep · Candidates ·
Conflicts · What changed · Beliefs · Stack prefs · Browse & tools.

Internal types (`strategy`, `failure`) are hidden from default browse filters.

## Adoption pipeline

| Source | Behavior |
|--------|----------|
| Chat “Remember that…” | User-initiated encode (explicit adopt) |
| Smart auto-memory | `propose_candidate` only |
| Journal ★ remember | Candidate + toast to review |
| Document/journal learn flags | Candidate-oriented settings copy |
| GUI New/Encode | Explicit user dialog → encode |

`POST /api/memory/candidates/{id}/adopt` encodes through `memory.add` (PRIMARY redirect).

## Forget workflow

1. `GET /api/memory/{id}/forget-preview`  
2. User chooses Cool / Correct / Erase  
3. `POST /api/memory/{id}/forget` with `confirm: true`

Erase = stronger cool (`steps=3`), not hard-delete of Experiences.

## Correction workflow

`action=correct` + `correction_text` → `primary_correct` / revise lineage.

## Provenance

Cards show source, why-remembered, learned time, tags (`source:*`, `adopted`).
Nothing appears without a plain-language why.

## Confidence

Projected from relevance/confidence fields when present; assistant flags low-trust autos.

## Associative recall

`GET /api/memory/associate?q=` — memory search + optional KG links (review only).

## Conflict coach

`GET /api/memory/conflict-coach` explains why/recommendation; UI Keep A/B cools the other.

## Sleep

Home surfaces plain-language outcomes from ACM dashboard metrics/events.
No internal implementation dump.

## Knowledge separation

Nightly research / knowledge topic dump removed from Memory Home.
Copy points users to Documents/Knowledge. Memory = autobiography only.

## Integrations

| System | Change |
|--------|--------|
| Journal | ★ → candidate |
| Chat auto | → candidate |
| Chat remember | still encode (explicit) |
| Import | requires `mode=merge\|replace` |
| Mission Control | observe-only (unchanged) |

## Accessibility & keyboard

Custom dialogs replace `prompt()`/`confirm()` for core flows.
`/` search · `N` new · `?` shortcuts · `Esc` close.
Dialogs participate in modal chrome Esc handling.

## Performance

Browse search refreshes **list only** (debounced), not full Home reload.
Home loads once per view open.

## Testing

```bash
./venv/bin/pytest tests/test_memory_cognitive.py -q
```

Plus existing ACM PRIMARY / retrieval suites remain the authority gates.

## Future roadmap

- Richer Sleep organ productization  
- Gallery → candidate with OCR review  
- Planner/Calendar confirm-to-candidate  
- Provenance timeline UI  
- Substrate retirement ops (vault/graph hygiene)

## Product philosophy (unchanged)

Memory is Aria’s heart: local-first autobiographical cognition under ACM.
The UI adapts to ACM. ACM never adapts to the UI.
