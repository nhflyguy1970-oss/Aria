# Aria ↔ Ollama Pipeline RCA

**Date:** 2026-07-30  
**Prompt under study:** `What day is today?`  
**Baseline CLI:** `ollama run qwen2.5:7b` / `POST /api/chat` (healthy, ~1s when runner free)

---

## Executive verdict

**First divergence:** Before Aria ever sends the chat payload to Ollama, NLU runs a **semantic intent classifier** using the cached placement model **`llama3.2-vision:11b`**.

Measured on this host:

| Stage | Before fix | After fix |
|-------|------------|-----------|
| `route_via_nlu("What day is today?")` | **42 772 ms** (classifier `llama3.2-vision:11b`) | **0.1 ms** (`calendar_fact` short-circuit) |
| Full router → `chat` | Dominated by NLU | **~51 ms** |
| Direct Ollama chat (runner free) | ~1 s | unchanged |

CLI never runs an intent LLM. Aria did — and that call **evicted the chat model from VRAM**, so the subsequent chat looked like a “first-progress timeout” even though Ollama itself was healthy.

Provider Health was **not** the root cause. Timeouts were a symptom of a **pre-provider NLU model thrash**.

---

## Timeline (instrumented)

### Successful CLI (when runner idle)

```
API connect .............. <10 ms
Model already loaded ..... ~0–150 ms
First token .............. ~0.8–1.0 s
Completion ............... ~1.0–1.1 s
```

### Aria before fix

```
Browser/API .............. n/a (GUI down during RCA; assistant path used)
route() → route_via_nlu
  analyze_prompt()
    classify_semantic(llama3.2-vision:11b, amd)
      llm.ask_with_system(...) ..... ~42 279 ms   ← FIRST DIVERGENCE
  nlu_to_router_intent → calendar_fact / chat
Conversation build_context + ask_stream
  Ollama must reload qwen2.5:7b .... tens of seconds
First SSE token .................. often after FIRST_PROGRESS_TIMEOUT
```

Even though calendar-fact routing already forced `action=chat`, **semantic classification still ran first** and paid the vision-model cost.

---

## Side-by-side: CLI vs Aria request

| Field | CLI / direct `/api/chat` | Aria (conversation path) |
|-------|--------------------------|---------------------------|
| Endpoint | `http://127.0.0.1:11434/api/chat` | Same via `ollama` Python client |
| Model | `qwen2.5:7b` | `qwen2.5:7b` (general) after routing |
| Pre-call LLM | **None** | **`llama3.2-vision:11b` NLU classifier** ✗ |
| Messages | 1 user | system (`SYSTEM_PROMPT` ~563 chars) + user (+ context prefix) |
| Tools | none | none for plain chat (tool router may probe other models elsewhere) |
| Options | typically none / light | Gateway may add `num_ctx=8192`, `num_predict`, `num_gpu` on some paths |
| Streaming | yes | yes (`ask_stream`) |

**Required differences:** Aria’s system prompt and optional context prefix are intentional product behavior.  
**Defect:** Vision model intent classification before every NLU-routed turn.

---

## Context size (date prompt)

| Component | Observation |
|-----------|-------------|
| User prompt | ~18 chars |
| System prompt | ~563 chars (ARIA persona) |
| Memory / planner / knowledge injection | Present in `build_context_prefix` when those behaviors fire; not the primary stall |
| NLU classifier prompt | Separate full Ollama call with vision model — **this dominated latency** |

---

## Tool routing

`What day is today?` correctly ends as **`action=chat`** after calendar-fact guards. It should not invoke calendar/memory tools before the provider. The failure was **not** tool execution; it was **intent classification inference**.

---

## Secondary stall (regression path)

After rejecting the vision classifier, unclassified prompts (`What is 2+2?`) returned `None` from NLU and fell through to `llm.route_with_tools()` (`qwen2.5-coder:1.5b-base` + tools). That call failed after **~48 s** (`does not support tools`).

**Repair:** when semantic classification is skipped/empty, NLU defaults to **`chat`** instead of `None`, so the expensive tool-router LLM is not invoked for ordinary conversation.

---

## Root cause

1. `data/nlu_placement.json` selected **`llama3.2-vision:11b`** as the intent classifier (benchmark hint `llama3.2` matched a vision tag; accuracy was **0%**).
2. `route_via_nlu` → `analyze_prompt` → `classify_semantic` **always** invoked that model before deterministic calendar-fact short-circuit took effect.
3. Loading the vision model **unloaded `qwen2.5:7b`**, so chat first-token looked like a provider stall.

---

## Fix applied (only verified defects)

| Change | File | Why |
|--------|------|-----|
| Short-circuit calendar/clock facts **before** `analyze_prompt` | `jarvis/nlu/pipeline.py` | Never pay for a classifier LLM on deterministic date prompts |
| Reject vision/embed/multimodal models as NLU classifiers (cached + env + discover) | `jarvis/nlu/placement.py`, `jarvis/nlu/benchmark.py`, `jarvis/nlu/semantic.py` | Placement must not thrash VRAM with unsuitable models |
| Do not emit `nlu_clarify` when no live classifier ran | `jarvis/nlu/confidence.py` | Structure fallback must not trap “Hello” / “2+2” in clarification |
| Default to `chat` when semantic classify is skipped | `jarvis/nlu/pipeline.py` | Avoid falling through to `route_with_tools` (48 s failed tool model) |

**Not changed:** Provider Health timeouts, retries, architecture, conversation engine, Ollama adapter redesign.

---

## Regression checks

| Check | Result |
|-------|--------|
| `tests/test_nlu_routing.py` | **19 passed** |
| `tests/test_provider_health.py` | included in suite run |
| `route_via_nlu("What day is today?")` | **0.1 ms → chat / calendar_fact** |
| Warm `ask_stream` “Hello” / “2+2” (when runner free) | first token **~270–300 ms** |
| Live Ollama during late RCA | Contended by interactive `ollama run` + busy llama-server — environmental; not Aria adapter bug |

**Operator note:** Close idle interactive `ollama run` sessions; they can serialize/block HTTP generate while Aria chats.

---

## Remaining risks

- Background NLU rebenchmark may still run; discovery now excludes vision/embed tags.
- Cached `nlu_placement.json` still contains the bad model name but is **ignored** at runtime via unsuitable-model fallback (structure until a clean benchmark completes).
- If an interactive CLI session holds the runner, Aria will again appear slow — free the runner, then retest.

---

## Stop condition

✓ Divergence identified (pre-provider NLU vision classify).  
✓ Defect repaired (short-circuit + unsuitable classifier rejection).  
✓ Date prompt no longer burns ~42 s before chat.  
✓ No Provider Health redesign; no timeout inflation; no new product features.
