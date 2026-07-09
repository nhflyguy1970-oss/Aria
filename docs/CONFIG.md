# Jarvis configuration reference

Copy `jarvis.env.example` to `data/jarvis.env` and customize. Never commit secrets.

## Core / Ollama

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API URL |
| `JARVIS_GENERAL_MODEL` | _(model settings)_ | Override chat model |
| `JARVIS_CODER_MODEL` | _(model settings)_ | Override coding model |
| `JARVIS_REVIEW_MODEL` | _(model settings)_ | Override review model |
| `JARVIS_VISION_MODEL` | `moondream:latest` | Vision model |
| `JARVIS_IMAGE_MODEL` | `comfyui` | Image backend label |
| `JARVIS_EMBED_MODEL` | `nomic-embed-text` | Memory embeddings |
| `JARVIS_UNCENSORED_MODEL` | `dolphin3:latest` | Uncensored chat fallback |
| `JARVIS_UNCENSORED` | `0` | Enable at launch (`1` / `true`) |
| `JARVIS_UNCENSORED_PASSWORD` | _(none)_ | Unlock env uncensored / bootstrap password |
| `JARVIS_UNCENSORED_SESSION_HOURS` | `12` | Uncensored session TTL |
| `JARVIS_UNCENSORED_MAX_ATTEMPTS` | `5` | Failed unlock attempts before lockout |
| `JARVIS_UNCENSORED_LOCKOUT_SEC` | `300` | Lockout duration (seconds) |
| `JARVIS_MAX_MESSAGES` | `40` | Chat history message cap |
| `JARVIS_MAX_CONTEXT_CHARS` | `80000` | Context character cap |
| `JARVIS_MODEL_WARMUP` | `1` | Warm chat model on startup |
| `JARVIS_AUTO_PULL_MODELS` | `1` | Pull missing Ollama models on launch |

## Server / security

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_HOST` | `127.0.0.1` | Bind address (`0.0.0.0` for LAN) |
| `JARVIS_PORT` | `8765` | GUI port |
| `JARVIS_API_KEY` | _(none)_ | Require API key for `/api/*` (header: `Authorization: Bearer …` or `X-API-Key`) |
| `JARVIS_API_KEY_IN_QUERY` | `0` | Allow `?api_key=` (off — keys leak in logs/referrers) |
| `JARVIS_NETWORK_GUARD` | `1` | Block non-LAN IPs unless `JARVIS_ALLOW_REMOTE=1` |
| `JARVIS_ALLOW_REMOTE` | `0` | Allow public-internet clients (not recommended) |
| `JARVIS_TRUST_PROXY` | `0` | Trust `X-Forwarded-For` for rate limit / network guard |
| `JARVIS_RATE_LIMIT` | auto | `1` on / `0` off; auto-on when not localhost |
| `JARVIS_RATE_LIMIT_PER_MIN` | `180` | API requests per IP per minute |
| `JARVIS_AUTO_WEB_SEARCH` | `1` | Inject web search snippets into chat for factual questions |
| `JARVIS_PARALLEL_WORKERS` | `2` | Background job thread pool (audio jobs; max 4) |
| `JARVIS_VIDEO_DURATION` | _(settings file)_ | Override default clip length (seconds) |
| `JARVIS_VIDEO_PROMPT_MODEL` | _(auto)_ | LLM for video keyframe prompts |
| `JARVIS_NO_BROWSER` | `0` | Skip opening browser on launch |
| `JARVIS_GUI_MODE` | `app` | `app` (Chrome `--app` window, default), `browser`, `native` (legacy pywebview), or `auto` (same as `app`) |
| `JARVIS_APP_WINDOW` | `1` | Use Chrome app-window mode when opening the UI |
| `JARVIS_NATIVE_WIDTH` / `JARVIS_NATIVE_HEIGHT` | `1280` / `860` | Native window size |
| `JARVIS_NATIVE_DEBUG` | `0` | pywebview debug mode |
| `JARVIS_HEALTH_CACHE_SEC` | `8` | Legacy health cache TTL |
| `JARVIS_HEALTH_FULL_CACHE_SEC` | `45` | Full `/api/health` detail refresh interval |
| `JARVIS_SERVICES_CACHE_SEC` | `5` | Services status cache TTL |
| `JARVIS_SANDBOX` | `firejail` | Code sandbox (`0` to disable) |

## ComfyUI / images

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_COMFYUI_URL` | `http://127.0.0.1:8188` | ComfyUI API |
| `JARVIS_COMFYUI_ROOT` | `~/ComfyUI` | Install path |
| `JARVIS_COMFYUI_PYTHON` | _(auto)_ | Python for ComfyUI |
| `JARVIS_COMFYUI_CPU` | `0` | Force CPU mode |
| `JARVIS_COMFYUI_PORT` | `8188` | ComfyUI listen port |
| `JARVIS_COMFYUI_WORKFLOW` | _(none)_ | Custom workflow JSON path |
| `JARVIS_COMFYUI_CKPT` | _(none)_ | Force checkpoint filename |
| `JARVIS_COMFYUI_STEPS` / `CFG` / `SAMPLER` / `SCHEDULER` | model-dependent | Sampler overrides |
| `JARVIS_AUTOSTART_COMFYUI` | `1` | Auto-start ComfyUI |
| `JARVIS_ROCM_GFX` | `11.0.0` | AMD ROCm gfx override |
| `JARVIS_IMAGE_AUTO_ENHANCE` | `1` | Light prompt enhancement |
| `JARVIS_IMAGE_LLM_ENHANCE` | `1` | LLM prompt expansion |
| `JARVIS_IMAGE_PROMPT_MODEL` | _(auto)_ | Model for prompt expansion |
| `JARVIS_IMAGE_WIDTH` / `HEIGHT` | `0` | Force output size (0 = auto) |

GUI **Gallery → Image Engine** also persists checkpoint, device mode, and workflow in `data/comfyui_settings.json`.

## Audio / TTS / Whisper

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_PIPER_MODEL` | _(none)_ | Piper `.onnx` path |
| `JARVIS_TTS_VOICE` | `en-us` | espeak voice |
| `JARVIS_WHISPER_MODEL` | `base` | Whisper model size |
| `JARVIS_WHISPER_DEVICE` | auto | `cpu` / `cuda` |
| `JARVIS_WHISPER_LANGUAGE` | `auto` | `auto` or ISO code (`en`, `es`, …) |
| `JARVIS_WHISPER_COMPUTE` | `default` | faster-whisper compute type |
| `JARVIS_AUDIO_SINK` / `SOURCE` | _(auto)_ | PulseAudio device names |
| `JARVIS_AUTO_PLAY` | `1` | Play TTS automatically |
| `JARVIS_ALSA_*` | _(none)_ | ALSA card/device overrides |
| `JARVIS_VST_CHAIN` | _(none)_ | Default playback EQ: `voice`, `music`, `scout`, `gaming`, `flat` |
| `JARVIS_VST_PLUGIN_PATH` | _(none)_ | Optional VST3 plugin for `custom` chain (needs `pedalboard`) |
| `JARVIS_VRAM_GUARD` | `1` | Unload Ollama before ComfyUI/MusicGen (8GB GPUs) |
| `HSA_OVERRIDE_GFX_VERSION` | _(none)_ | RX 7600 ROCm gfx trick — use `11.0.0` |
| `HF_TOKEN` | _(none)_ | Hugging Face (pyannote diarization). Set with `./scripts/set-hf-token.sh` — kept in gitignored `data/jarvis.env` only |
| `JARVIS_LSP` | `1` | Enable language servers (diagnostics, go-to-def, refs, hover, format) |
| `JARVIS_LSP_SESSION_TTL` | `120` | Seconds to keep idle LSP server processes alive |
| `JARVIS_COMFYUI_INPAINT_WORKFLOW` | _(none)_ | Inpaint workflow JSON path |

## Song Studio / MusicGen

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_SONG_MODE` | `auto` | `safe` / `balanced` / `max` |
| `JARVIS_SONG_VOCALS` | `1` | Enable AI vocals |
| `JARVIS_SONG_VOCAL_DEVICE` | `cpu` | `cpu` / `cuda` |
| `JARVIS_SONG_MUSIC_DEVICE` | `auto` | MusicGen device |
| `JARVIS_SONG_MAX_DURATION` | `30` | Max seconds (safe caps at 15) |
| `JARVIS_MUSICGEN_MODEL` | `facebook/musicgen-small` | MusicGen model |
| `JARVIS_TORCH_DEVICE` | `cuda` | PyTorch device (ROCm uses `cuda`) |
| `JARVIS_VOCAL_ENGINE` | `auto` | Bark / XTTS selection |
| `JARVIS_XTTS_MODEL` / `XTTS_SPEAKER_WAV` | _(none)_ | Voice cloning |

## Vision

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_VISION_MAX_PIXELS` | `1280` | Max image dimension |
| `JARVIS_VISION_JPEG_QUALITY` | `85` | JPEG recompress quality |

Species / identification questions automatically use the quality vision tier when enabled in model settings.

## Journal / weather

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_WEATHER_LAT` / `LON` | _(none)_ | Coordinates |
| `JARVIS_WEATHER_LOCATION` | _(none)_ | Display label |
| `JARVIS_WEATHER_UNITS` | `fahrenheit` | `celsius` or `fahrenheit` |
| `JARVIS_WEATHER_IP_LOOKUP` | `1` | Fallback geo IP |
| `JARVIS_HOLIDAY_STATE` | _(auto)_ | US state for holidays |

Encrypted journal export uses `pip install cryptography` (in `requirements-optional.txt`).

## Wake word / browser

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_WAKEWORD` | `0` | Enable wake word |
| `JARVIS_WAKEWORD_MODEL` | `hey_jarvis` | openWakeWord model |
| `JARVIS_WAKEWORD_TO_CHAT` | `1` | Record → chat after wake |
| `JARVIS_BROWSER` | `google-chrome` | Browser for links |
| `JARVIS_BROWSER_PATH` | _(auto)_ | Flatpak/binary path |

## Web search / data

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_SEARXNG_URL` | `http://127.0.0.1:8080` | SearXNG instance |
| `JARVIS_DATA_MAX_ROWS` | `50000` | CSV row cap |

## Workstation / self-healing

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_AUTO_RECOVER` | `1` | Proactive scheduler runs diagnose + recover every 5 min |
| `JARVIS_AUTO_RECOVER_INTERVAL_MIN` | `5` | Auto-recover interval |
| `JARVIS_AUTO_RECOVER_OPTIONAL` | `0` | When `1`, diagnose optional managed docker services (postgres, redis, litellm, etc.) and allow auto-restart |
| `JARVIS_NIGHTLY_MAINTENANCE` | `1` | Run maintenance jobs via scheduler |
| `JARVIS_MAINTENANCE_SMOKE_TESTS` | `1` | Run pytest smoke subset during nightly maintenance |

See also `docs/PLATFORM_CUTOVER.md`, `DEPENDENCIES.md`, `UPGRADES.md`, and `README.md`.
