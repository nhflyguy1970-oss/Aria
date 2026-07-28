# Voice Implementation

Aria's conversational voice product — one shared pipeline for every entry point.

## Product identity

**Voice owns conversation I/O:** speech-to-text, text-to-speech, push-to-talk, wake word, duplex, Cloud Live, voice profiles/settings, intent routing, status, recovery.

**Voice does not own:** Audio Studio (production), Chat UI, Memory, Documents, Mission Control, Gallery, Browser, Video, Image Generation, DAW editing, always-on cloud listening, silent Memory ingest.

Entry points (Chat mic, Voice strip, Voice tab, wake word, Cloud Live, Voice CLI, Automation, API) are **front doors** to the same engine — never separate implementations.

## Architecture

```
jarvis/voice_product/
  engine.py          # speak_text, process_utterance, begin_listen
  status_bus.py      # listening | thinking | speaking | idle | …
  settings.py        # unified settings store
  profiles.py        # Quiet Office, Hands-Free, Coding, …
  intent_router.py   # product commands without dumping into Chat
  speech_policy.py   # speak / mute / sanitize / censored presentation
  recovery.py        # diagnose + recovery actions
  mission_bridge.py  # Mission Control panel
  experimental.py    # opt-in flags (env)
  api.py             # /api/voice/*
```

Legacy modules (`voice_settings`, `voice_duplex`, `voice_only`, `cloud_live_voice`, `tts_stream`, `tts_playback_queue`) remain as adapters and are wired into the product package.

## One pipeline

```
PTT / Wake / Cloud Live / CLI / Automation / API
  → STT
  → Intent Router
  → Assistant (when conversational)
  → Speech Policy
  → TTS (chunked → playback queue)
  → Audio output
  → Activity / status
  → Completion
```

## Status bus

`emit_voice_state` / `set_voice_state` publish to:

- In-process event bus (`jarvis.events`)
- WebSocket hub (`/ws/events` → Voice strip, Voice tab, overlays)
- Mission Control `voice` panel

States: `idle`, `listening`, `thinking`, `speaking`, `muted`, `recording`, `wake`, `cloud-live`, `error`.

## Speak model

One coherent preference:

| Control | Behavior |
|---------|----------|
| Speak replies | Auto-speak Chat replies |
| Mute | Same preference off |
| Read last reply | One-shot speak (force) |
| Stop speaking | Clear TTS queue + stop playback |

No overlapping toggles or inverted labels.

## Duplex

- **Off** — wake ignored during TTS
- **Half** — stop playback, then listen (`before_listen`)
- **Full** — barge-in via `maybe_barge_in` (wired on PTT start)

Never advertise unsupported modes.

## Settings

Unified store: `data/voice_product/settings.json` (mirrors legacy `voice_settings.json` + duplex in `audio_settings`).

Persists: speak replies, server Whisper, STT/TTS, duplex, wake, cloud provider, latency/chunk prefs, active profile.

## Profiles

Built-ins: Quiet Office, Hands-Free, Coding, Presentation, Dictation, Accessibility, Cloud Live.

CRUD + import/export via `/api/voice/profiles*`. Activate applies settings atomically.

## Intent router

Structured commands (Gallery, Browser, Coding, Mission Control, HA, Projects, Planner, Documents, image/video generate, mute/speak) return navigation + spoken ack without forcing Chat.

## Cloud Live

- **Gemini Live** — production path when key configured
- **OpenAI Realtime** — hidden until `OPENAI_WEBRTC_CLIENT_READY` is true

Status reports `openai_hidden`, `providers_shown`, `active` sessions.

## Streaming TTS

`speak_text` chunks via `tts_stream.split_speak_chunks`, generates ahead, enqueues with `tts_playback_queue.enqueue_play`. Interruptible via `stop_speaking` / `clear_tts_queue`.

## Recovery advisor

`/api/voice/recovery` detects missing Whisper/Piper, cloud key, high queue depth, duplex mismatch. Actions: stop speaking, clear queue, switch to half duplex.

## Mission Control

`enrich_snapshot` attaches `voice` panel: Whisper/Piper health, Cloud Live, queue, duplex, recovery issues, deep links.

## Censored / uncensored

**One engine.** Differences only via response policy, safety policy, permitted actions, model selection.

Historical transcripts/audio are never regenerated or deleted when switching profiles — presentation may redact until reveal (`speech_policy.presentation_for_profile`).

## Accessibility

- Voice strip `role="status"` / `aria-live="polite"`
- Mute button `aria-pressed`
- Listening overlay live region
- Keyboard: palette actions for mute / stop / read aloud / Cloud Live
- Mic remains enabled when server Whisper works (no browser STT required)

## Testing

```bash
pytest tests/test_voice_product.py tests/test_voice_bar_batch.py tests/test_tts_playback_queue.py tests/test_voice_only.py -q
```

Coverage includes: status bus, settings unify, profiles, intent router, duplex honesty, Cloud Live honesty, speak policy, recovery, Mission Control bridge, TTS queue.

## API surface

| Route | Purpose |
|-------|---------|
| `GET /api/voice/product` | Full product status |
| `GET /api/voice/state` | Current status bus snapshot |
| `POST /api/voice/speak` | Shared speak |
| `POST /api/voice/stop` | Stop speaking |
| `POST /api/voice/utterance` | Shared pipeline |
| `GET/POST /api/voice/settings` | Unified settings |
| `GET/POST /api/voice/profiles*` | Profiles |
| `GET /api/voice/recovery` | Diagnose |
| `GET /api/voice/mission` | MC panel |
| `GET /api/voice/experimental` | Opt-in flags |

Chat continues to use `POST /api/audio/speak` which delegates to the same engine.

## Experimental (env-gated)

`JARVIS_VOICE_EXP_*` flags: continuous duplex, agent router, latency auto-tune, hybrid local/cloud, wake scene, context voices, adaptive TTS. All share the same engine when enabled.

## Roadmap

1. OpenAI Realtime WebRTC client (then un-hide provider)
2. Continuous local duplex VAD loop (experimental → production)
3. Per-project profile overlays
4. Latency graph in Voice tab / Mission Control
5. True Journal voice capture polish

## Do not build

Separate Chat/Cloud/Wake/CLI engines; always-on cloud listen; silent Memory ingest; fake duplex/status/latency; DAW features in Voice.
