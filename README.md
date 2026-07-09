# ARIA

**ARIA** — *Adaptive Reasoning Intelligence Assistant* — a local AI assistant powered by [Ollama](https://ollama.com). Modular CLI tools for coding, chat, audio, vision, image generation, memory, and data analysis.

## Setup

**Fresh machine?** See **[docs/INSTALL.md](docs/INSTALL.md)** and run:

```bash
./workstation install && ./workstation configure && ./workstation verify && ./workstation start
```

Manual setup:
cd /media/jeff/AI/jarvis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-optional.txt   # whisper, charts, etc.
./scripts/install-dependencies.sh            # system tools + Piper + models
```

See **`DEPENDENCIES.md`** for downloads and **`UPGRADES.md`** for the roadmap.

**Cheatsheets** live in memory (namespace `cheatsheet`) — say **"list cheatsheets"** or **"memory cheatsheet"**, or open the Memory tab → Cheatsheets. Edit there anytime; **reset memory cheatsheet** restores defaults.

**v3.0:** Bullet Journal, memory browser, gallery, RAG, git, charts, personalities, themes, export.

**Media jobs:** Image/video/meme/inpaint run in a background queue so the UI stays responsive. See `docs/BUSY_MODE.md`.

Install Ollama, then pull recommended models:

```bash
ollama serve                  # if not already running
./scripts/pull-models.sh      # standard set (~16GB VRAM)
JARVIS_UNCENSORED=1 ./scripts/pull-models.sh   # uncensored set
```

Ask ARIA **what models should I use?** in the GUI for a full hardware guide.

### Models (optimized for your PC)

Pre-configured in `data/model_settings.json` for **RX 7600 8GB + 62GB RAM**:

| Mode | Chat | Code | Review | Vision |
|------|------|------|--------|--------|
| Standard | `qwen2.5:14b` | `qwen2.5-coder:14b` | `deepseek-r1:14b` | `moondream:latest` |
| Uncensored | `dolphin3:latest` | `qwen2.5-coder:14b` | `dolphin3:latest` | `moondream:latest` |

Change models in the GUI sidebar under **Model settings**. Settings persist across restarts.

Optional system tools:

- **Audio**: `whisper` (pip install openai-whisper), `ffmpeg`, `espeak-ng`; optional `piper` for better TTS (`JARVIS_PIPER_MODEL`)
- **Vision**: llava or another vision model via Ollama

## Usage

### System tray (recommended)

Runs ARIA in the background with a system tray icon, auto-starts Ollama, and restarts the server if it crashes:

```bash
python main.py tray                  # standard mode
python main.py tray-uncensored       # uncensored mode
./scripts/launch-jarvis.sh           # same as tray (used by desktop shortcut)
```

Right-click the tray icon: **Open ARIA**, **Restart server**, **Quit**.

### GUI only

```bash
python main.py gui                  # standard mode
python main.py gui-uncensored       # uncensored mode
```

Or use desktop shortcuts:

```bash
./scripts/install-desktop-shortcuts.sh
```

Opens **ARIA** and **ARIA (Uncensored)** on your desktop/app menu.

**GUI features:** Fast/Quality model presets, pull missing models, GPU/ROCm status, chat progress indicator, **Stop** button while answering, mobile sidebar menu.

Talk naturally:
- "Fix the bugs in coding/main.py" → then "apply it"
- "Review this project"
- "What do you remember about me?"
- Attach files — images, audio, CSV auto-detected
- Use mic button for voice input, speaker for read-aloud

**Uncensored mode** uses unrestricted local models (default: `dolphin3:latest`). Toggle in the GUI sidebar or launch the uncensored shortcut.

### GPU acceleration (AMD)

ARIA shows GPU/ROCm status in the sidebar. For AMD RX 7600, install [ROCm for Ollama](https://ollama.com/blog/amd-preview) so models run on GPU instead of CPU.

### CLI modules

```bash
python main.py coding
python main.py general
python main.py audio
python main.py vision
python main.py image
python main.py memory
python main.py data
```

Or run a module directly:

```bash
python coding/main.py
python general/main.py
```

## Modules

| Module | Purpose |
|--------|---------|
| **coding** | Code assistant: read/fix/improve files, project indexing, architecture review |
| **general** | General-purpose chat with memory integration |
| **audio** | Transcription (Whisper), TTS generation, audio editing (ffmpeg), conversion |
| **vision** | Image analysis via Ollama vision models |
| **image** | Image prompt generation and enhancement |
| **memory** | Persistent JSON memory store |
| **data** | CSV/JSON loading and LLM-powered analysis |

## Configuration

Copy `jarvis.env.example` to `data/jarvis.env` for local overrides. Never commit secrets (`HF_TOKEN`, `JARVIS_UNCENSORED_PASSWORD`, `JARVIS_API_KEY`).

**Full reference:** [docs/CONFIG.md](docs/CONFIG.md) — all `JARVIS_*` variables, ComfyUI, audio, Song Studio, security, and journal settings.

Common overrides:

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_GENERAL_MODEL` | `qwen2.5:14b` | Chat model (or use GUI Model settings) |
| `JARVIS_UNCENSORED` | `0` | Enable uncensored mode at launch |
| `JARVIS_HOST` / `JARVIS_PORT` | `127.0.0.1` / `8765` | Server bind |
| `JARVIS_API_KEY` | _(none)_ | LAN API authentication |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |

Persisted GUI state: `data/model_settings.json`, `data/comfyui_settings.json`, `data/app_settings.json` (uncensored toggle).

## Project Structure

```
jarvis/
├── jarvis/           # Shared library
│   ├── config.py, model_store.py, assistant.py
│   ├── gpu.py, daemon.py, tray.py, watchdog.py
│   ├── gui/          # FastAPI web UI + static assets
│   └── modules/      # Module implementations
├── scripts/          # launch-jarvis.sh, pull-models.sh
├── desktop/          # .desktop shortcuts
├── coding/
├── general/
├── audio/
├── vision/
├── image/
├── memory/
├── data/
├── data/             # Runtime data (memory, audio, generated images)
├── main.py           # Module router
└── requirements.txt
```
