# Jarvis — Upgrade Roadmap

Per-function recommendations. See `DEPENDENCIES.md` for install commands.  
**Last synced:** 2026-06-14 — Iron Man build order complete; see **Future list** for deferred items only.

---

## Movie Jarvis — completed (2026-06-14)

| Item | Status |
|------|--------|
| Debug until tests pass (background job, no UI wedge) | Done |
| Document library semantic search (`documents_rag`, chat + API) | Done |
| Environment awareness layer (`environment.py`, `/api/environment`) | Done |
| Calendar in briefing (timed journal + optional `JARVIS_ICS_URL`) | Done |
| `good morning` → morning briefing | Done |
| Automation webhook expanded (briefing, run_script, wake, resources) | Done — `docs/automation-webhook.md` |
| Remote device control (whitelisted `data/scripts/`) | Done |
| Upgrade wizard restart hint + versioned snapshots | Done |
| GPU free VRAM + video preflight suggestions | Done |
| AnimateDiff OOM retry at 8 frames before Ken Burns | Done |
| HA Docker autostart with Jarvis | Done |

---

## Recently completed (this pass)

| Item | Status |
|------|--------|
| Config profiles (Work / Gaming / Offline) | Done |
| Prompt history + favorites | Done |
| Action history GUI | Done |
| Chat export PDF | Done |
| Git panel (status + diff + log) | Done |
| Per-chat model override (sidebar selector) | Done |
| Token stats in status bar (prompt/completion tokens) | Done |
| Chat multi-language hints | Done — `lang_util.py` |
| Long-task desktop notifications | Done — image, video, coding, podcast mix |
| Whisper default `small` on fresh installs | Done |
| Podcast / multi-track mix | Done — `/api/audio/podcast/mix` + Song Studio UI |
| Parallel background workers | Done — `JARVIS_PARALLEL_WORKERS` (default 2) |
| Branch trimmer | Done |
| Video safe/uncensored keyframe checkpoints | Done |
| Web search routing fixes | Done |
| Bullet journal fetch fix | Done |
| ROCm PyTorch install script | Done |
| Systemd user autostart | Done |

---

## Audio (Creative Sound Blaster AE-5 Plus)

**Done:** PipeWire routing, Piper TTS, auto-play, read-aloud, faster-whisper, live record, VU meter, diarization, wake word, Bark/XTTS, MusicGen, Song Studio, waveform trim, podcast mix, AE-5 EQ/VST.

| Upgrade | Status |
|---------|--------|
| Piper TTS | Done |
| Whisper model picker (tiny→large) | Done — Audio tab; default **small** |
| Voice cloning (XTTS) | Done (optional dep) |
| MusicGen | Done |
| ROCm PyTorch for GPU ML | Script — `./scripts/install-rocm-pytorch.sh` |
| AE-5 EQ / VST bridge | Done |
| Multi-track podcast editor | Done — two-track amix |

---

## Chat / General

| Upgrade | Status |
|---------|--------|
| Streaming tokens | Done |
| Chat branches + trimmer | Done |
| Personality presets | Done |
| RAG over project docs | Done |
| Web search | Done (disabled in Offline profile) |
| Conversation export MD/PDF | Done |
| Per-chat model override | Done — sidebar **Chat model** + `/api/chat/model` |
| Token/cost stats | Done — `inference_ms` + prompt/completion tokens |
| Multi-language auto-detect | Done — reply-language hint in chat context |

---

## Coding

| Upgrade | Status |
|---------|--------|
| Multi-file apply, git chat commands, pytest verify, rename, syntax, firejail, MCP, code index, LSP | Done |
| Git GUI panel | Done — status, diff, log in sidebar |

---

## Memory / Journal / Vision / Data

All major roadmap items **Done**. Journal includes daily weather (Charlestown, NH).

---

## Image generation

| Upgrade | Status |
|---------|--------|
| ComfyUI, Flux/SDXL, gallery, prompt history, inpaint/upscale | Done |

---

## Video studio

| Capability | Status |
|------------|--------|
| Video tab + gallery, upload/trim/analyze | Done |
| Text-to-video (AnimateDiff + Ken Burns fallback) | Done — auto tries SD1.5 AnimateDiff on 8GB, falls back |
| Full AnimateDiff / Wan at high res | **Limited** — 512×512 · 16 frames on RX 7600; upgrade for longer clips |

---

## GUI / UX

| Upgrade | Status |
|---------|--------|
| Tray, watchdog, themes, shortcuts, action history, mobile layout, chat stop | Done |
| Encrypted journal export | Done |
| CI (pytest + ruff) | Done |
| API rate limit (LAN) | Done |
| ComfyUI workflow picker | Done |
| Song Studio job cancel | Done |
| Long-task desktop notifications | Done — chat image/video/coding + audio jobs |

---

## Infrastructure

| Upgrade | Status |
|---------|--------|
| ROCm Ollama, model warm-up, backup/restore, systemd, LAN+API key, profiles | Done |
| Parallel background workers | Done — `JARVIS_PARALLEL_WORKERS=1-4` (audio jobs) |
| Ollama localhost bind | Script — `sudo ./scripts/bind-ollama-localhost.sh` |

---

## Recommended ops (your machine)

Run `./scripts/verify-setup.sh` to confirm status.

| Step | Notes |
|------|--------|
| Hard-refresh browser after updates | `Ctrl+Shift+R` for `app.js` / `journal.js` |
| Restart Jarvis after code changes | Desktop shortcut or `./scripts/launch-jarvis.sh` |
| `sudo ./scripts/bind-ollama-localhost.sh` | Ollama localhost-only |
| `./scripts/harden-security.sh` | Security audit |

See also: `DEPENDENCIES.md`, `README.md`, `docs/CONFIG.md`

---

## North Star — Iron Man Jarvis (RX 7600 / local)

**Goal:** As close to movie Jarvis as possible **on your machine** — natural, knows you, runs the lab, never dumb about context — without pretending you have Stark tower compute.

### What movie Jarvis *feels* like

| Movie trait | Local equivalent (honest) |
|-------------|---------------------------|
| Always there, calm voice | Tray + native window + TTS read-aloud + wake word (optional) |
| Knows Tony deeply | Profile + memory + journal + preference rules (Phase 1) |
| “Good morning, sir” briefing | Daily journal + weather + open tasks + calendar hook (future) |
| Sees & hears | Vision, OCR, whisper STT, image/video studio |
| Runs the lab | Coding agent, propose/apply, git, ComfyUI, pytest loop |
| Controls the house | Home Assistant / smart scenes (future, optional) |
| Never confuses test junk with life | Trust layer (Phase 1) — **non‑negotiable for “Jarvis feel”** |
| Upgrades himself with Tony’s OK | Upgrade wizard (Phase 3) — propose, test, Apply, never silent |
| Witty but brief when needed | Personality presets + preference learning |

### What we **cannot** replicate on 8GB local (and won’t fake)

- Holographic UI, suit fabrication, global satellite awareness  
- Dozens of parallel AI agents (“swarm”)  
- Instant 4K video / huge multimodal models always loaded  
- Fully autonomous rewrite of running code with no human gate  
- Cloud-scale always-on listening without latency/privacy tradeoffs  

**Rule:** One “heavy brain” at a time — queue image/video/coding jobs, fast 7B chat when GPU is busy.

### Already “Jarvis enough” today

- Local-only privacy (Ollama + your data on disk)  
- Chat, memory, bullet journal, coding with Apply/Undo  
- Vision, audio, music, data analysis, web search  
- Image/video/meme studio (ComfyUI, VRAM-aware fallbacks)  
- Cursor bridge, MCP, watchdog, profiles (Work / Gaming / Offline)  
- GPU detect, model recommendations, media job queue  

### Gap map → existing Future list

| Movie gap | Build from |
|-----------|------------|
| Remembers failures & how you like to work | **Priority 1:** failure/strategy memory |
| Reads warranty PDFs like a chief of staff | **Priority 2:** document/PDF pipeline |
| “Fix yourself” without breaking my journal | **Priority 3:** Upgrade Jarvis wizard |
| Knows machine state before offering Flux/video | Resource-aware routing + environment layer |
| Briefing when I open Jarvis | Environment layer + journal open tasks (+ calendar later) |
| House/lab automation | Home Assistant + webhooks + LAN laptop control |
| Voice-first “Jarvis?” | Wake word polish + push-to-talk default on 8GB |

### Phased path to “movie Jarvis” (your hardware)

**Phase A — Trust (feels like Jarvis, not a chatbot)**  
Phase 1 Future list: clean context, forget/correct, test isolation, failure/strategy memory.  
*Without this, nothing feels intelligent — just confident and wrong.*

**Phase B — Chief-of-staff (work + life)**  
Phase 2 + document priority: PDF/Word, long attachments, journal briefing line on launch.  
*“You have three open tasks; warranty doc X mentions clause Y.”*

**Phase C — Lab manager (engineering)**  
Phase 3 + coding agent polish: debug-until-green, Upgrade wizard, tool learning.  
*Movie Jarvis builds things — but Tony still says “run it.”*

**Phase D — Environment (house & hardware)**  
Operations section: VRAM routing, service health, LAN access, Home Assistant, automations.  
*“ComfyUI is up; GPU has 6GB free — want SDXL or fast 7B chat?”*

**Phase E — Presence (optional polish)**  
Better TTS voice, wake word, desktop notifications, native window always available.  
*Presence, not sci-fi holograms.*

### Suggested build order (single thread)

| # | Item | Status |
|---|------|--------|
| 1 | **Phase A — Trust** | **Done** |
| 2 | Morning briefing (journal + tasks + weather + headlines) | **Done** |
| 3 | PDF pipeline for warranty work | **Done** |
| 4 | Resource-aware routing (stop OOM, smart queues) | **Done** |
| 5 | Upgrade Jarvis wizard | **Done** |
| 6 | LAN + laptop browser to PC Jarvis | **Done** |
| 7 | Home Assistant / automation hooks | **Done** |

<details>
<summary>Phase A — Trust checklist</summary>

| Item | Status |
|------|--------|
| Test isolation (conftest + live data guard) | Done |
| Context gating (resume/journal “today”) | Done |
| Journal reload from disk | Done |
| Test-artifact filter + scrub on startup | Done |
| Failure + strategy memory types | Done |
| Forget with confirmation text | Done |
| Memory correct (`correct that …`) | Done |
| Default strategy seed + data layout hint | Done |
| Coding agent / fix-tests record failures | Done |
| Apply records verified fixes | Done |
| Memory UI: strategy/failure types + Scrub button | Done |
| Block storing test junk in live memory | Done |
| Removed broken_calc from suggestions/examples | Done |

</details>

Previously as list:

1. Phase A trust + failure/strategy memory  
2. Morning briefing (journal + tasks + weather — small UI hook)  
3. PDF pipeline for warranty work  
4. Resource-aware routing (stop OOM, smart queues)  
5. Upgrade Jarvis wizard  
6. LAN + laptop browser to PC Jarvis  
7. Home Assistant / automation hooks  

### Success criteria (“movie enough”)

- [x] General chat never surfaces stale test files or wrong “today” facts *(trust filters + context gating)*
- [x] “What do you remember about me?” is accurate and correctable *(memory_correct + forget lists removed items)*
- [x] “Summarize this warranty PDF” works without manual copy-paste *(document pipeline: attach PDF/DOCX, summarize + Q&A + follow-ups)*
- [x] “Debug until tests pass” runs without wedging the UI *(queued via coding_jobs; chat stays responsive)*
- [x] “Improve yourself” → proposal → tests → Apply — live journal untouched *(upgrade wizard)*
- [x] Image/video jobs queue cleanly on 8GB; Jarvis warns before heavy jobs *(resource_router + preflight + auto VRAM prep)*
- [x] Optional: one phrase from another room/device on LAN reaches the same Jarvis *(enable-lan.sh + API key modal + /api/lan)*
- [x] Optional: smart home from chat when Home Assistant is configured *(ha_status, control, scenes, inbound webhook)*

---

## Future list

Most Movie Jarvis items are **done**. Remaining deferred items only (portable SSD excluded per user request):

### Still deferred

| Item | Notes |
|------|--------|
| **Portable SSD** | Whole repo + optional `JARVIS_COMFYUI_ROOT` / `OLLAMA_MODELS` on external drive. |
| **Full AnimateDiff / Wan at high res** | Hardware-limited on RX 7600; 512² · 16 frames (8 on OOM retry). Longer clips need bigger GPU. |
| **Multi-agent swarm** | Not planned — single coding agent + human Apply is the local pattern. |

### Previously open — now done

<details>
<summary>Completed partial / open items (2026-06-14)</summary>

| Item | Notes |
|------|--------|
| Document library RAG | `jarvis/documents_rag.py`, `/api/documents/search` |
| Environment layer | `jarvis/environment.py`, briefing lab line |
| Calendar briefing | `daily_timeline`, ICS URL, monthly calendar notes |
| Automation framework | Inbound webhook actions + docs |
| Remote LAN control | `run_script`, `wake` via automation API |
| Upgrade guardrails | `requires_jarvis_restart`, snapshot version field |
| Resource-aware routing expand | `free_vram_mb`, preflight `suggested` video settings |
| Wake word UI | Already in Audio Advanced tab |
| Debug until tests pass | `coding_jobs.submit_fix_tests` |

</details>

### Legacy Future list (historical)

### High value (worth adding next)

| Item | Notes |
|------|--------|
| **Failure memory** | Remember what broke and what fixed it (e.g. pytest errors → successful patch). Don’t lose debugging lessons when the session ends. |
| **Strategy memory** | Remember *how* to work with this user/repo (minimal diffs, no test pollution in live journal/memory, etc.). |
| **Stronger preference learning** | Behavior rules, not just facts — e.g. “don’t inject stale checkpoints in general chat,” “birthday is June 9 not today.” |
| **Filesystem cognition (practical)** | Scoped awareness: `data/` vs `jarvis/` vs scripts; user data vs test artifacts; cleanup after manual/agent testing. |
| **Document understanding (upgrade)** | PDF/Word text extraction and Q&A — especially useful for warranty administration work. |
| **Resource-aware routing** | **Done** — preflight, queue advisories, auto Ollama unload, Ken Burns fallback, `/api/resources` |

### Phase 1 — Trust & cleanup

| Item | Status |
|------|--------|
| Test isolation | **Done** |
| Explicit forget / correct | **Done** (chat + Memory browser edit/delete + Scrub) |
| Failure + strategy notes in memory | **Done** |
| Context gating | **Done** |
| Journal reload from disk | **Done** |
| Filesystem cognition (data layout hint) | **Done** (strategy seed) |
| **Morning briefing** | **Done** — launch card + chat (`morning briefing`, `good morning`) |

### Phase 2 — Better documents

| Item | Notes |
|------|--------|
| PDF pipeline | **Done** — extract, summarize, Q&A; `data/documents/` library; chunked context |
| Office docs | **Done** — `.docx` read/summarize (`python-docx`) |
| Long-file attach | **Done** — chunk + rank excerpts; not full doc in every prompt |
| Document library | Optional index over `data/documents/` with semantic search (RAG). |
| **Learn about topic** | **Done** — `learn about: …` multi-search → `data/knowledge/<slug>.md` → inject in chat + optional remember key points. |

### Phase 3 — Safer self-improvement

| Item | Notes |
|------|--------|
| Propose-only self-changes | Jarvis proposes edits to its own repo; user Apply/Undo (already exists — extend and polish). |
| **Upgrade Jarvis wizard** | **Done** — propose → verify (pytest + ruff) → apply with snapshot; rollback; GUI modal + chat routes. |
| Self-repair guardrails | No silent edits to running server code; pytest + ruff gate before any apply to `jarvis/`. |
| Versioned self-modification | Tag/backup before “upgrade yourself” runs; one-click rollback. |

### Deferred (keep in mind)

| Item | Notes |
|------|--------|
| LAN access | **Done** — `./scripts/enable-lan.sh`, `JARVIS_HOST=0.0.0.0`, API key modal, `/api/lan`, Ollama stays localhost. |
| Portable SSD | Whole repo + optional `JARVIS_COMFYUI_ROOT` / `OLLAMA_MODELS` on external drive. |

### Operations, hardware & integration (new suggestions)

| Item | Notes |
|------|--------|
| **Resource-aware decision making** | Choose model, image size, video length, and parallel jobs based on free VRAM/RAM/CPU — skip or queue work before OOM. *Partial today:* VRAM detect, AnimateDiff fallback, media job queue, `JARVIS_PARALLEL_WORKERS`. |
| **Environment awareness layer** | Know context beyond chat: date/time, weather (journal), running services (Ollama/ComfyUI/Jarvis health), active profile (Work/Gaming/Offline), disk space under `data/`. Use for smarter defaults, not constant nagging. |
| **GPU / hardware awareness (expand)** | Richer preflight UI + routing: warn before Flux/inpaint/video; suggest smaller models on RX 7600; track “last successful” settings per task type. *Partial today:* `gpu.py`, model recommendations, ComfyUI settings. |
| **Smart device integration** | **Done** — `jarvis/home_assistant.py`: chat control/scenes/status, `/api/homeassistant/status`, HA→Jarvis webhook `/api/automation/inbound`. Run `./scripts/enable-home-assistant.sh`. |
| **Remote device control** | Control *your* machines from another device on LAN (laptop → PC Jarvis) or safe wake/trigger scripts. Ties to deferred **LAN access**; not open internet exposure. |
| **Automation framework integration** | Pluggable triggers/actions: Cursor Automations, cron, webhooks, n8n/Node-RED nodes calling Jarvis API (`/api/chat`, coding propose/apply, journal log). Jarvis as a step in larger workflows. |
| **Tool learning** | Remember which tools/APIs worked for recurring tasks (e.g. “warranty PDF → extract with X, summarize with Y”). Overlaps **failure/strategy memory** — implement as memory types, not a separate “engine.” |
| **Cognitive optimization engine** | *Defer as standalone* — buzzword name for things already planned: context gating, smaller prompts, RAG only when needed, token stats. Track as improvements under Phase 1 + resource-aware routing, not a new subsystem. |
| **Multi-agent swarm intelligence** | *Not planned* — multiple LLM agents coordinating in parallel. High cost, hard to debug on 8GB VRAM; existing **coding agent** + propose/apply is the right local pattern. |

### Priority tracks (all three matter)

Pick any order — each is a full product direction:

1. **Failure / strategy memory** — learns from mistakes; fewer repeated bugs and context pollution.
2. **Document / PDF pipeline** — warranty work, attachments, summarize without prompt bloat.
3. **Safer “upgrade yourself” flow** — self-mod with isolation, tests, and rollback; no touching user data.

### Not planned (buzzword / out of scope for now)

| Item | Why defer |
|------|-----------|
| World model layer | Research concept; no clear local product definition. |
| 3D model support | Niche; heavy GPU; unrelated to current use. |
| Full autonomous self-repair | Risky without human approve on every core change. |
| “Persistent knowledge structures” (abstract) | Memory + journal + code index exist — focus on *when* context is injected, not new ontology. |
| Multi-agent swarm intelligence | Cost, complexity, and VRAM; single coding agent + human Apply is sufficient locally. |
| Cognitive optimization engine (standalone) | Covered by context gating, RAG-on-demand, and resource-aware routing instead. |

