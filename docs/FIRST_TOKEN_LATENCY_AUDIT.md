# Aria First-Token Latency Audit

**Date:** 2026-07-30  
**Scope:** Platform-wide first-token latency — no timeout increases, no retries, no prompt-specific hacks.

## Executive verdict

`FIRST_PROGRESS_TIMEOUT` is not one bug. It is the visible failure when **any** of these systemic stalls consume the first-progress budget before a model token (or a non-chat `done`) arrives:

| Rank | Systemic cause | Class | Affects |
|------|----------------|-------|---------|
| 1 | **Wedged Ollama stream never checks cancel** → request lock held forever | **Bug** | Every subsequent request |
| 2 | **Soft generate probe on chat hot path** (~5s, contends with real inference) | **Redundant / Bug** | All chat streams |
| 3 | **Silent work before first SSE event** (route / health / context) | **Lazy-load / parallelize** | All streams |
| 4 | **Interactive `ollama run` holding the model** (env) | **Required env** | All chat LLM turns |
| 5 | Eager context (docs/weather/extras) — largely addressed earlier | Cacheable / lazy | Open chat |

Provider Health timeouts were **symptoms**, not root causes. They were not changed.

---

## Request matrix (structural)

Measured with tags-only health, early SSE statuses, and wall deadlines when the provider was degraded (`/api/ps` empty while interactive `ollama run qwen2.5:7b` held the runner).

| Category | Route action | Pre-provider | First progress | Largest Aria delay |
|----------|--------------|--------------|----------------|--------------------|
| Greeting | `greeting` | ~0.1s status | `done` ~0.1s | None (no LLM) |
| Simple math/chat | `chat` | status <1ms | token only if Ollama free | **Provider** (50–120s when wedged) |
| Date/time | `chat` | local clock / light ctx | same | **Provider** |
| Weather | `weather_forecast` | Open-Meteo ~0.5–0.7s | `done` ~0.65s | Weather API (required) |
| Knowledge | `chat` | context varies | provider | Provider + optional search |
| Search | `chat`/`web_search`* | — | provider / search | Provider or search I/O |
| Documents | docs-gated chat | RAG when needed | provider | RAG (required when used) |
| Planner | planner/chat | planning I/O | action or provider | Journal/planner I/O |
| Memory | memory verbs / chat | memory lookup | action or provider | Memory I/O |
| Smart home | HA action* | — | `done` or error | HA API |
| Coding | coding_* | — | agent stream | Agent/tools |
| Fly tying | fly / chat | fly ctx when cued | provider | Recipe lookup when cued |

\*Exact action depends on NLU/`_quick_route`; audit focuses on shared stalls, not per-prompt routing tables.

### Soft probe vs tags (same machine)

| Check | Latency | State |
|-------|---------|-------|
| `check_ollama(soft_probe=True)` | **~5089 ms** | `degraded` (generate timeout) |
| `check_ollama(soft_probe=False)` | **~3–25 ms** | `degraded`/`healthy` from cache |

Running a soft probe **immediately before** chat was burning first-progress budget and competing for the same GPU/runner.

---

## Waterfall (chat path — systemic)

```
Browser POST /api/chat
  → SSE "Processing…"                          (server; immediate)
  → process_stream acquire request lock        ★ can block forever (before fix)
  → status "Routing…"                          (after fix: immediate)
  → route()                                    usually <50ms (NLU structure)
  → execute_stream
       status "Checking provider…"
       check_ollama(soft_probe=False)          ★ was soft_probe=True (~5s)
       status "Gathering context…"
       build_context_prefix                    lazy policy (prior work)
       status "Calling model…"
       ask_stream → Ollama                     ★ cancel only between chunks (before fix)
       first token SSE
  → Browser render
```

Non-chat actions (`greeting`, `weather_forecast`, …) emit `done` without tokens; client treats `done` as progress. They must not sit behind a lock held by a wedged chat.

---

## Delay classification

| Operation | Class | Notes |
|-----------|-------|-------|
| Soft generate probe on every chat | **Bug / redundant** | Fixed: tags-only on chat path |
| Blocking stream ignoring cancel | **Bug** | Fixed: cancellable iterator |
| Infinite request-lock wait | **Bug** | Fixed: acquire timeout (default 3s) |
| Early SSE silence | **Lazy-load candidate** | Fixed: Routing / Checking / Calling statuses |
| Ollama tags HTTP | **Cacheable** | Fixed: 15s tags cache |
| Open-Meteo / RAG / HA | **Required** when routed there | Not removed |
| Interactive `ollama run` | **Environmental** | Unload/stop runner; Aria cannot invent VRAM |
| NLU structure fallback logs | **Optional** | Cheap; unsuitable vision classifier already rejected |

---

## Model usage

| Stage | Model | Notes |
|-------|-------|-------|
| Health soft probe (old chat path) | `general_model()` via `/api/generate` | Contended with chat |
| Chat | `qwen2.5:7b` (typical) | First token 1s healthy / 50–120s wedged |
| NLU classifier | skipped when unsuitable | Structure fallback |
| Weather | none | Open-Meteo only |

---

## Root causes (platform)

1. **Cancel was ineffective while Ollama blocked on the first chunk** → FIRST_PROGRESS cancelled the request_id, but the stream thread never noticed → **lock never released** → weather/greetings/`Hello` after a stuck chat also hung.
2. **Chat called `check_ollama()` with soft probe** → up to 5s generate before the real chat started.
3. **No SSE until after health/route** → looks like a dead stream even when work is progressing.
4. **Host runner contention** (`ollama run` interactive + empty `/api/ps`) → true provider stall across all chat categories.

---

## Fixes applied (systemic only)

| Change | File |
|--------|------|
| Chat uses `check_ollama(soft_probe=False)` | `jarvis/behaviors/conversation.py` |
| Early status events (provider / context / model) | `jarvis/behaviors/conversation.py` |
| Early `Routing…` + `Running {action}…` | `jarvis/assistant.py` |
| Request lock acquire timeout | `jarvis/assistant.py` |
| Cancellable blocking stream iterator | `jarvis/llm.py` |
| Tags list TTL cache (15s) | `jarvis/ollama_health.py` |
| Empty-stream NameError `model` → `chat_model` | `jarvis/behaviors/conversation.py` |

**Not changed:** Provider Health prefs/timeouts, retries, prompt-specific routing hacks.

---

## Before / after (Aria-side)

| Scenario | Before | After |
|----------|--------|-------|
| Chat health gate | ~5s soft probe | ~3–25ms tags |
| Stuck chat then weather | weather waits on lock indefinitely | cancel releases lock (~0.3s); lock timeout fails fast |
| Greeting / weather | fast when lock free | greeting ~0.14s, weather ~0.65s |
| First SSE | after health+route | immediate Routing/Checking statuses |

Provider first-token when Ollama is healthy remains a property of the runner; Aria no longer adds multi-second redundant work or lock death spirals in front of it.

---

## Regression

```text
pytest tests/test_first_token_latency.py -q
→ 3 passed
```

Also green with context/weather/ollama health suites exercised during this work.

---

## Operator note

If chat first-token stays >45s with Aria fixes applied, check for interactive `ollama run` / ComfyUI VRAM holders and clear them. Aria heartbeats and FIRST_PROGRESS still correctly classify a wedged provider — they must not be weakened.
