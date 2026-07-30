# Aria Latency Observability

**Date:** 2026-07-30  
**Constraint:** Observability only — no routing, Provider Health timeout, or provider-adapter behavior changes beyond instrumentation.

## Architecture overview

```
Browser (request_id + optional JARVIS_LATENCY_DEV)
  → /api/chat SSE
      begin_trace(trace_id) ──► ContextVar + live map
      stages: routing → context → prompt_build → provider_stream
      done.latency { overlay, first_token_ms, budgets }
      complete_trace() → JSONL store + PH history mirror
  → Mission Control Latency panel
  → /api/latency/* diagnostics & export
  → Search corpus `latency`
```

New package: `jarvis/latency_observability/`

| Module | Role |
|--------|------|
| `trace.py` | Trace ID, stages, context inventory, stream/provider/model/cache fields |
| `store.py` | JSONL persistence + search filters |
| `budgets.py` | Warn-only performance budgets |
| `metrics.py` | Avg / P50 / P95 / P99 aggregates |
| `export.py` | JSON / CSV / waterfall / overlay / mission snapshot |
| `api.py` | HTTP routes |
| `mission_bridge.py` | Mission Control panel payload |

## Trace lifecycle

1. SSE chat creates `lt-…` via `begin_trace(request_id, conversation_id, prompt)`.
2. Status event includes `trace_id`.
3. Assistant notes `routing` ms after `route()`.
4. `build_context_prefix` attaches inventory (enabled/why/chars/tokens_est/latency).
5. Conversation notes `prompt_build` and provider/model; times first token.
6. SSE attaches `latency` summary on `done`.
7. `complete_trace` evaluates budgets, writes JSONL, mirrors compact event into Provider Health history.

## Metrics collected

- Stages: start/finish/elapsed (+ meta)
- Context sources: enabled, why, characters, tokens_est, latency, injected
- Provider: provider, model, role, prompt_chars
- Stream: first_token_ms, first_sse_ms, duration_ms, reason
- Model: model, role, load cold/warm (when set)
- Cache: hit/miss/saved_ms (API ready)
- Budgets: warn entries with responsible subsystem

## Dashboards / APIs

| Surface | Path |
|---------|------|
| Mission Control tab | `latency` |
| Mission panel API | `GET /api/mission-control/latency` |
| Live | `GET /api/latency/live` |
| Stats | `GET /api/latency/stats` |
| Diagnostics | `GET /api/latency/diagnostics` |
| Trace | `GET /api/latency/trace/{id}` |
| Search | `GET /api/latency/search?q=&provider=&model=&subsystem=&min_ms=` |
| Export | `GET /api/latency/export?trace_id=&format=json\|csv\|waterfall\|overlay\|mission` |

Provider Health `GET /api/provider/stats` now includes read-only `latency_history` (does not change watchdog/timeouts).

## Search integration

Corpus `latency` registered in `search_product.retrievers` and default enabled corpora.

## Developer mode

Set `localStorage.JARVIS_LATENCY_DEV=1` or `window.JARVIS_LATENCY_DEV=true`.  
On chat `done`, console prints the overlay and a toast shows elapsed / first-token.

## Performance budgets (warn only)

| Budget | Default |
|--------|---------|
| Routing | 20 ms |
| Context | 50 ms |
| Prompt build | 20 ms |
| Provider queue | 250 ms |
| First token | 2000 ms |
| Completion | 30000 ms (`JARVIS_LATENCY_BUDGET_COMPLETION_MS`) |

## Files modified / added

**Added:** `jarvis/latency_observability/*`, `tests/test_latency_observability.py`, this doc  
**Wired:** `gui/server.py`, `extra_routes.py`, `assistant.py`, `behaviors/conversation.py`, `mission_control_ops/enrich.py`, `mission_control.js`, `chat_send.js`, `provider_health/engine.py`, `search_product/{retrievers,settings}.py`

## Tests

`pytest tests/test_latency_observability.py`

## Before / after

| Question | Before | After |
|----------|--------|-------|
| Where did time go? | Guesswork | Per-stage waterfall + overlay |
| Why did context run? | Opaque | Inventory why/enabled/tokens |
| First token unexplained | Common | `stream.first_token_ms` + budgets |
| Find slow requests | Manual logs | Search + MC Latency + export |
