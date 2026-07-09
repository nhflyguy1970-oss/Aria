# Known Issues

Last updated: 2026-07-09

## Low priority (optional components)

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Home Assistant** not running | Smart-home features unavailable | Start manually if needed; not required for daily AI work |
| **LM Studio** not started | Optional local inference UI | Use Ollama (default) or start LM Studio on port 1234 |
| **n8n** container stopped | Workflow automation optional | `docker start ai-n8n` or `./workstation start` |
| **Open WebUI / MongoDB** containers stopped | Optional chat UIs | Not required when using Aria |
| **Ollama GPU indicator** shows CPU | Display-only; inference may still use GPU | Restart Ollama after heavy ComfyUI use if models are slow |

## Operational notes

| Issue | Impact | Workaround |
|-------|--------|------------|
| **`workstation start` exit code** may be non-zero while Aria is healthy | Scripting only | Check `./workstation acceptance` or `curl http://127.0.0.1:8765/api/health` |
| **First chat after cold start** can take 30–45s | One-time model load | Wait; warmup is enabled (`JARVIS_MODEL_WARMUP=1`) |
| **Platform cutover** verified but not enabled | By design | Stay in compatibility mode until you explicitly enable authoritative mode |

## Not bugs

- **447 memory entries** in legacy store; platform may have a few extra mirrored records — verified by cutover backfill
- **Semantic vectors** stored under `/media/jeff/AI/applications/aria/data/semantic-index/`
- **Continue, OpenHands, Hermes, Goose** — not installed; acceptance does not require them

## Requires Jeff (human action)

| Item | When |
|------|------|
| `claude login` | Claude CLI acceptance shows auth needed |
| `gemini auth login` | Gemini CLI acceptance shows auth needed |
| API keys in `data/jarvis.env` | External paid APIs only |
