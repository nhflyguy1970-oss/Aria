# Weather Pipeline RCA — FIRST_PROGRESS_TIMEOUT

**Date:** 2026-07-30  
**Prompt:** `What is the weather today?`  
**Constraint:** No Provider Health changes, no timeout increases, no architecture redesign.

## Executive verdict

Weather requests were **mis-routed to `chat` / Ollama** by NLU `structure_default_chat`, which **shadowed** the existing `_quick_route` → `weather_forecast` pattern.

The Open-Meteo call itself is fine (~0.5–0.7s, ~50–70 chars of forecast).  
The stall was **waiting for the first Ollama chat token** (measured **~67–125s** on this host when VRAM contended), which exceeds `first_progress_ms` (45s) → `FIRST_PROGRESS_TIMEOUT`.

**Root cause:** NLU returned `action=chat` before `_quick_route` weather matching could run.  
**Repair:** Deterministic weather short-circuit in NLU (same pattern as calendar facts) → `weather_forecast` action (Open-Meteo only, no LLM).

---

## Instrumented timeline

### Before fix

| Stage | Latency | Notes |
|-------|---------|-------|
| `route()` | ~56 ms | `action=chat`, `rule_matched=structure_default_chat` |
| Status `Gathering context…` | ~5.1 s | Includes `check_ollama` (~5 s cold) |
| Weather API (in context) | ~0.55–0.70 s | Open-Meteo daily high/low only |
| Context prefix | ~169 chars | Forecast line + language lock |
| Prompt to LLM | ~1.3k chars | Small — not the bottleneck |
| `ask_stream` first token | **~98–125 s** | Ollama / VRAM — triggers FIRST_PROGRESS |
| FIRST_PROGRESS_TIMEOUT | 45 s | Fires before first token |

### After fix

| Stage | Latency | Notes |
|-------|---------|-------|
| `route()` | ~45 ms | `action=weather_forecast`, `rule_matched=weather_forecast` |
| Open-Meteo | ~0.5–0.7 s | Same compact daily payload |
| SSE | single `done` | **~0.77 s end-to-end** |
| Ollama | **not called** | No first-token wait |

---

## Weather API verification

| Field | Value |
|-------|-------|
| Provider | Open-Meteo (`api.open-meteo.com`) |
| Endpoint | `/v1/forecast` daily: `temperature_2m_max/min`, `weathercode` |
| Geocode | `JARVIS_WEATHER_LAT/LON` when set; else city / IP lookup |
| Timeout | 12 s per HTTP call |
| Retries | none |
| Response used | **one day** high/low/condition — not hourly dump |
| Injected text example | `**Today** in Charlestown, NH — Rain · H 76°F / L 63°F` (~53–65 chars) |

Weather API latency is **not** the timeout cause.

---

## Context inventory (chat path — before fix)

| Source | Required | Chars | Latency |
|--------|----------|-------|---------|
| Planning / weather | yes | ~53 | ~555 ms |
| Language lock | yes | ~114 | ~2 ms |
| Memory / docs / search / extras | no | 0 | skipped (lazy policy) |
| Final prefix | | ~169 | |

Prompt size was minimal. Provider never needed to run for a factual forecast.

---

## Parallelism

Weather retrieval blocked the chat stream thread **before** Ollama only by ~0.7s — irrelevant vs 45s. No parallelization required once routing is correct.

---

## Root cause (exact)

1. `route()` prefers `route_via_nlu` when NLU is enabled.
2. For weather, classifier was skipped → `structure_default_chat` → **`action=chat`**.
3. `_quick_route` weather → `weather_forecast` **never ran**.
4. Chat path called Ollama; first token arrived after `first_progress_ms` → `FIRST_PROGRESS_TIMEOUT`.

---

## Minimal repair

| Change | File |
|--------|------|
| `is_weather_forecast_question()` + map to `weather_forecast` | `jarvis/nlu/mapping.py` |
| Short-circuit before `analyze_prompt` | `jarvis/nlu/pipeline.py` |
| Skip clarification for weather | `jarvis/nlu/confidence.py` |
| Cache forecast (5 min) + IP location (1 h) | `jarvis/journal_weather.py` |

**Not changed:** Provider Health, timeouts, chat architecture, unrelated router tables.

---

## Regression tests

`tests/test_weather_forecast_routing.py` — weather detector, NLU short-circuit, router action ≠ chat, compact forecast text.

---

## Success criteria

| Criterion | Status |
|-----------|--------|
| Exact reason for FIRST_PROGRESS identified | ✓ misroute to Ollama chat |
| Weather API ruled out as primary stall | ✓ |
| Weather completes without LLM | ✓ ~0.8 s |
| Complex chat / other routes untouched | ✓ |
| Timeouts / Provider Health unchanged | ✓ |
