# Aria Context Assembly Optimization

**Date:** 2026-07-30  
**Scope:** Lazy context assembly only — no routing, provider, or product removals.

## Problem

Simple prompts (`Hello`, `What day is today?`, `What is 2+2?`) still spent seconds in `ConversationEngine.build_context_prefix` before the provider was called. Profiling showed:

| Source | Symptom |
|--------|---------|
| Documents RAG | 3–20s, thousands of chars injected for greetings/math |
| Planning weather | Bare `\btoday\b` triggered weather API (~0.5–1s) for date questions |
| Project extras | Git/workspace scans on open chat (~1–2.5s) |
| `chat_busy_hint` | Full GPU/Ollama `snapshot()` every turn (~150–400ms) |
| Knowledge topics | Topic match (~1s) even when no topic hit |

## Approach

1. **Policy gate** (`jarvis/context/policy.py`) — decide which subsystems run per message.
2. **Lazy execution** in `build_context_prefix` — call only required behaviors; record inventory.
3. **Tighten detectors** — remove bare `today`/`tomorrow` weather triggers; document/weather/planner narrow paths.
4. **Cache** — language hint by detected language; busy-hint TTL (media queue only).
5. **Local clock** — date/time questions get a one-line local clock instead of weather/planner.

Capabilities (Memory, Search, Calendar/Planner, Vision, Weather, Documents, Fly Tying, Relationships) remain available when the request needs them.

## Latency breakdown (after)

Measured via `build_context_prefix` inventory on a live assistant (warm process):

| Prompt | Elapsed | Prefix chars | Injected sources |
|--------|---------|--------------|------------------|
| Hello | ~0–30ms | ~114 | language |
| What day is today? | ~0.1ms | ~162 | local_clock, language |
| What is 2+2? | ~0.1ms | ~114 | language |
| Explain recursion. | ~1ms warm | ~114 | language (+ optional busy_hint) |
| Schedule a meeting tomorrow. | ~planning I/O | minimal | planning (tasks if any) |
| What's the weather today? | ~weather API | ~180+ | planning weather |
| Summarize this PDF | ~docs RAG | thousands | knowledge documents |

### Before (same machine, eager path)

| Prompt | Typical | Notes |
|--------|---------|-------|
| Hello | 3–20s+ | Document library + fly recipes |
| What day is today? | ~1s+ | Weather API from bare `today` |
| What is 2+2? | multi-second | Document retrieval |
| Summarize this PDF | ~20s | Expected (capability retained) |

## Context inventory (simple vs complex)

**Hello**

| Source | Required? | Typical chars | Notes |
|--------|-----------|---------------|-------|
| Conversation history | session | (outside prefix) | unchanged |
| Memory | no | 0 | skipped |
| Planning / weather | no | 0 | skipped |
| Knowledge / docs / search | no | 0 | skipped |
| Project extras | no | 0 | skipped |
| Language lock | yes | ~114 | cached per language |
| Local clock | no | 0 | |

**What day is today?**

| Source | Required? | Notes |
|--------|-----------|-------|
| Local clock | yes | cheap datetime line |
| Weather | no | no longer triggered by `today` |

**What's the weather today?**

| Source | Required? | Notes |
|--------|-----------|-------|
| Weather | yes | forecast text |
| Documents / search / extras | no | narrow weather path |

**Summarize this PDF / warranty**

| Source | Required? | Notes |
|--------|-----------|-------|
| Documents | yes | library RAG + citations |
| Memory | yes | profile/prefs when present |

## Unnecessary work identified (and fixed)

- Weather fetched for date/chat containing `today`
- Document library for greetings, math, jokes
- Knowledge topic match for open educational chat with no saved topics
- Project git/workspace extras for every non-general turn
- Fly tying / relationships scans when message has no cues
- Full GPU snapshot inside `chat_busy_hint`
- Behavior module imports even when subsystem skipped (now import-inside-gate)

## Caches added

| Cache | Key | Invalidate |
|-------|-----|------------|
| Language reply hint | `lang:{code}` | process restart / `clear_stable_cache()` |
| Busy hint | TTL 2s | auto |
| Base system prompts | already module constants | personality/uncensored toggle |

## Lazy-loading changes

- `context_needs()` → `ContextNeeds` flags
- Lightweight short-circuit for greetings, thanks, trivial math, jokes, clock questions
- Narrow paths: weather-only, planner-only, documents-only
- `PlanningEngine.prepare_context(..., include_weather=, include_tasks=)`
- `KnowledgeEngine.prepare_context(..., include_topics=, include_documents=, include_web=)`
- Inventory via `last_inventory()` for diagnostics/tests

## Files modified

- `jarvis/context/policy.py` (new)
- `jarvis/behaviors/conversation.py`
- `jarvis/behaviors/planning/engine.py`
- `jarvis/behaviors/planning/__init__.py`
- `jarvis/behaviors/knowledge/engine.py`
- `jarvis/behaviors/knowledge/__init__.py`
- `jarvis/resource_router.py` (`chat_busy_hint`)
- `tests/test_context_policy.py` (new)
- `docs/CONTEXT_ASSEMBLY_OPTIMIZATION.md` (this report)

## Regression testing

```text
pytest tests/test_context_policy.py tests/test_chat_conversation.py -q
→ 17 passed
```

Complex paths still request documents/weather/planner when cues match. No products removed; routing and Provider Health untouched.

## Prompt composition notes

- System prompt base remains module-level constants (`SYSTEM_PROMPT_*`); personality/memory blocks still assembled in `build_system_prompt` when enabled.
- Tool schemas are not part of `build_context_prefix`; chat tool selection is unchanged by this work (no architecture change). Further tool-set trimming can be a follow-up without touching products.

## Success criteria

| Criterion | Status |
|-----------|--------|
| Simple chat: no weather/search/docs/planner | ✓ |
| Minimal prompt for greetings/math/clock | ✓ |
| Complex: weather/docs/schedule still assemble | ✓ |
| No feature removal | ✓ |
| Related tests pass | ✓ |
| No routing/provider redesign | ✓ |
