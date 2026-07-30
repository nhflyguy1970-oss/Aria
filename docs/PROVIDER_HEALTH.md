# Provider Health

## Executive summary

Provider Health is Aria’s **reliability layer** over model providers.
It makes stream stalls, disconnects, and timeouts understandable, observable, and self-healing whenever safe.

**Providers still own inference.** Provider Health owns monitoring, classification, recovery, diagnostics, and health APIs.

## Root cause: `STREAM_IDLE_TIMEOUT`

### What operators saw

A simple prompt such as “What day is today?” could surface `STREAM_IDLE_TIMEOUT` with little guidance.

### Actual failure modes

1. **Misclassification (client bug)**  
   Before the first token, `readStreamChunk` always labeled timeouts as `STREAM_IDLE_TIMEOUT`.  
   First-token stalls are now `FIRST_PROGRESS_TIMEOUT`.

2. **Silent blocked inference (server gap)**  
   `/api/chat` streamed a single `Processing…` status, then blocked inside `process_stream` / Ollama generate with **no SSE traffic**.  
   The browser `ReadableStream` idle timer then fired even though Aria was still waiting on the provider.

### Fixes

| Layer | Change |
|-------|--------|
| Server | Emit `heartbeat` SSE events while waiting for the next inference event |
| Client | Treat heartbeats as keepalive (reset chunk idle; do not count as first token) |
| Client | Correct timeout codes (`FIRST_PROGRESS_TIMEOUT` vs `STREAM_IDLE_TIMEOUT`) |
| Recovery | On timeout, call `/api/provider/recover`, then auto-retry once when usable |
| UX | Rich recovery card: classification, steps tried, Retry / Restart / Switch Model / Diagnostics |

## Architecture

```
Chat UI (chat_send.js)
  → /api/chat stream (+ heartbeats)
  → assistant.process_stream → Ollama / gateway
  → on stall: /api/provider/recover
  → Provider Health (probe → reconnect → restart → classify)
  → Notifications (rate-limited) · Dashboard · Mission Control · Search
```

Package: `jarvis/provider_health/`

| Module | Role |
|--------|------|
| `watchdog.py` | Per-request timing (start, first/last token, heartbeats) |
| `classify.py` | Failure classes (not everything is STREAM_IDLE_TIMEOUT) |
| `probe.py` | Provider discovery + ping (wraps `ollama_health`) |
| `recovery.py` | Safe auto-heal pipeline |
| `prefs.py` | Idle / recovery preferences |
| `history.py` | JSONL diagnostics log |
| `api.py` | `/api/provider/*` |
| `engine.py` | Aggregated health / diagnostics |
| `notify.py` | Meaningful Notifications only |
| `dashboard_bridge.py` / `mission_bridge.py` | Home + MC consumers |

## Health states

`healthy` · `loading` · `generating` · `busy` · `recovering` · `disconnected` · `restarting` · `crashed` · `degraded` · `unknown`

## Failure classes

`provider_disconnected` · `provider_overloaded` · `model_loading` · `model_crashed` · `oom` · `context_too_large` · `gpu_unavailable` · `network_interruption` · `provider_unreachable` · `stream_stalled` · `first_token_timeout` · `unknown_timeout` · …

## Recovery pipeline

1. Ping provider (+ soft generate probe when available)  
2. Reconnect / `ensure_ollama` if down  
3. Restart/ensure when alive but wedged or stream stalled  
4. Mark client retry recommended  
5. Offer model switch alternatives when needed  
6. Escalate to operator UI only after safe attempts

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/provider/health` | Product status |
| `GET /api/provider/stats` | Watchdog counters |
| `GET /api/provider/diagnostics` | Full diagnostics panel payload |
| `GET /api/provider/providers` | Discovery |
| `GET /api/provider/models` | Models for provider |
| `POST /api/provider/recover` | Run recovery |
| `POST /api/provider/restart` | Confirmed restart |
| `GET/POST /api/provider/prefs` | Preferences |
| `POST /api/provider/classify` | Classify a failure |
| `GET /api/provider/history` | Recent events |
| `GET /api/provider/mission` | Mission Control panel |

## Integrations

| Product | Role |
|---------|------|
| Dashboard | Provider health summary widget (owned by Provider Health) |
| Mission Control | Displays status / history (ops console only) |
| Notifications | Rate-limited recovery / unavailable events |
| Search | Indexes provider health history |
| Settings | Indexes idle timeout / auto-restart prefs |

## Operator guide

1. If a reply stalls, wait for automatic recovery toast (“Provider recovered — retrying…”).  
2. If recovery fails, use the recovery card: Restart Provider, Switch Model, View Diagnostics.  
3. Mission Control → diagnostics for GPU/CPU/probe detail.  
4. Do not only lengthen timeouts — heartbeats + classification address the real stall.

## Testing

```bash
.venv/bin/pytest tests/test_provider_health.py -q
```

## Ownership

Provider Health **never** owns Models catalog, Chat history, Search index, Settings DB, Notifications delivery, Mission Control ops, or inference generation itself.
