# Busy mode (background job queues)

When Jarvis generates images, video, memes, inpaints, or runs long **coding agent** tasks, work runs in **background queues** so the web UI and chat stay responsive.

## What you see

- **Desktop notification** when a job starts: “Jarvis busy — Image generation started…”
- **Status bar** shows `Busy · Video render · v3.1.0` while GPU work runs
- **Chat** returns immediately with “queued in the background” — result appears when the job finishes
- **Notification** when done: “Jarvis ready — Video render finished…”
- **VRAM preflight** warns before video generation on low VRAM (8GB GPUs)

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/media/status` | Media queue depth, active job label |
| `GET /api/media/job/{id}` | Poll media job progress/result |
| `POST /api/media/job/{id}/cancel` | Cancel media job (best-effort) |
| `GET /api/coding/status` | Coding agent queue status |
| `GET /api/coding/job/{id}` | Poll coding agent job |
| `GET /api/vram/preflight?action=video` | Warnings before heavy GPU work |
| `GET /api/metrics` | Uptime, queue stats, watchdog restarts |
| `GET /api/jobs` | **Unified job center** — media + coding + audio recent jobs |
| `GET /api/debug/bundle` | Diagnostics text (logs tail, metrics, environment) for support |

## Background actions (Phase 1)

These chat actions now queue on the **coding worker** instead of blocking chat:

- `document_summarize`
- `learn_about`

Open **Job center** in the sidebar to see status and cancel jobs.
| `POST /api/comfyui/settings` | Returns `job_id` — poll `/api/comfyui/settings/job/{id}` |
| `GET /api/health` | Fast probe; includes `busy` / `busy_job` |
| `GET /api/services` | Full Ollama/ComfyUI/GPU status (use for sidebar) |

## Queued actions

**Media (serial GPU queue):**

- `generate_image`, `generate_video`, `generate_meme`
- `upscale_image`, `inpaint_image`

**Coding (serial LLM queue):**

- `coding_agent` (non-stream chat)
- `resume task` / coding task resume

Prompt enhancement (`enhance_prompt`) stays instant (no GPU render).

## Tips on 8GB VRAM

- Use **Free VRAM** before video/AnimateDiff
- Video jobs may take **5–15 minutes** — Jarvis remains usable for chat
- Only **one media job runs at a time** (serial queue) to avoid OOM

## Config

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_MEDIA_JOB_TIMEOUT_SEC` | `900` | Max seconds per media job |
| `JARVIS_MEDIA_JOB_TTL_SEC` | `86400` | Purge finished job records after (seconds) |
| `JARVIS_CODING_JOB_TIMEOUT_SEC` | `1800` | Max seconds per coding agent job |
| `JARVIS_PARALLEL_WORKERS` | `2` | Audio background pool (media queue is always serial) |
| `JARVIS_HEALTH_FULL_CACHE_SEC` | `45` | How often full health details refresh in background |
| `JARVIS_COMFYUI_DOWNLOAD_TIMEOUT` | `120` | ComfyUI output download timeout (seconds) |

Job state is persisted to `data/media_jobs_state.json` for crash recovery logging.

See also `docs/CONFIG.md`.
