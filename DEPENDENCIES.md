# Jarvis — Dependencies Download List

Everything Jarvis can use, grouped by category. Use `./scripts/install-dependencies.sh` to install most items automatically.

---

## Quick install

```bash
cd /media/jeff/AI/jarvis
./scripts/install-dependencies.sh          # full install (sudo + downloads)
./scripts/install-dependencies.sh --skip-ollama   # skip large model pulls
```

After install:

```bash
source venv/bin/activate
source data/jarvis.env    # Piper + keep-alive settings
./scripts/launch-jarvis.sh
```

---

## 1. System packages (apt)

| Package | Purpose | Install |
|---------|---------|---------|
| `espeak-ng` | Text-to-speech (basic voice generation) | `sudo apt install espeak-ng` |
| `ffmpeg` | Audio edit/convert, format conversion | `sudo apt install ffmpeg` |
| `python3-venv` | Python virtual environment | `sudo apt install python3-venv` |
| `python3-dev` | Build Python extensions | `sudo apt install python3-dev` |
| `build-essential` | gcc/make for pip builds | `sudo apt install build-essential` |
| `curl` / `wget` | Download scripts & models | `sudo apt install curl wget` |
| `git` | Clone optional tools | `sudo apt install git` |
| `lsof` / `fuser` | Kill stale server on port 8765 | `sudo apt install lsof psmisc` |
| `libasound2` / `libasound2t64` | Audio playback libs (Noble/Zorin 18 uses `libasound2t64`) | `sudo apt install libasound2t64` |
| `libportaudio2` | Microphone/audio I/O | `sudo apt install libportaudio2` |
| `libpango-1.0-0`, `libpangocairo-1.0-0`, `libcairo2`, `libgdk-pixbuf-2.0-0` | WeasyPrint journal PDF export | `sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 shared-mime-info` |

**Already on your PC (detected):** `ffmpeg`, `rocm-smi`, `ollama`

**Missing (install script adds):** `espeak-ng`

---

## 2. Python packages (pip)

### Core (`requirements.txt`)

| Package | Purpose |
|---------|---------|
| `ollama` | Ollama Python client |
| `fastapi` | Web GUI API |
| `uvicorn` | ASGI server |
| `python-multipart` | File uploads in GUI |
| `pystray` | System tray icon |
| `Pillow` | Tray icon generation |

```bash
pip install -r requirements.txt
```

### Optional (`requirements-optional.txt`)

| Package | Purpose |
|---------|---------|
| `openai-whisper` | Speech-to-text transcription |
| `matplotlib` | Charts for data analysis (future) |
| `weasyprint` | Styled Bullet Journal PDF export (Print month layout) |
| `pandas` | Rich CSV/data handling (future) |
| `httpx` | HTTP client utilities |

```bash
pip install -r requirements-optional.txt
```

Whisper also pulls **PyTorch** automatically (~2GB).

---

## 3. Ollama (LLM runtime)

| Item | Purpose | Download |
|------|---------|----------|
| **Ollama** | Local LLM server | https://ollama.com/download |

Start: `ollama serve`

### Standard models (`./scripts/pull-models.sh`)

| Model | Role | Size (approx) |
|-------|------|---------------|
| `qwen2.5:14b` | Chat (quality) | ~9 GB |
| `qwen2.5-coder:14b` | Code | ~9 GB |
| `deepseek-r1:14b` | Project review | ~9 GB |
| `llava:13b` | Vision | ~8 GB |
| `moondream` | Fast vision | ~1.7 GB |
| `nomic-embed-text` | Memory embeddings | ~274 MB |

### Fast preset extras

| Model | Role | Size (approx) |
|-------|------|---------------|
| `qwen2.5:7b` | Fast chat | ~4.7 GB |
| `dolphin-mistral:latest` | Fast uncensored chat | ~4.1 GB |

### Uncensored models (`JARVIS_UNCENSORED=1 ./scripts/pull-models.sh`)

| Model | Role |
|-------|------|
| `dolphin3:latest` | Uncensored chat/review |
| `qwen2.5-coder:14b` | Code |
| `llava:13b` | Vision |
| `moondream` | Fast vision |
| `nomic-embed-text` | Embeddings |

```bash
ollama pull <model>    # or run pull-models.sh
```

---

## 4. Piper TTS (better voice generation)

Installed by `install-dependencies.sh` into project paths.

| Item | Path | Source |
|------|------|--------|
| Piper binary | `tools/piper/piper` | [GitHub release](https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz) |
| Voice model | `data/models/piper/en_US-lessac-medium.onnx` | [HuggingFace](https://huggingface.co/rhasspy/piper-voices) |
| Voice config | `data/models/piper/en_US-lessac-medium.onnx.json` | Same |

Env var (auto-written to `data/jarvis.env`):

```bash
export JARVIS_PIPER_MODEL="/media/jeff/AI/jarvis/data/models/piper/en_US-lessac-medium.onnx"
export PATH="/media/jeff/AI/jarvis/tools/piper:$PATH"
```

More voices: https://github.com/rhasspy/piper/blob/master/VOICES.md

---

## 5. Whisper models (speech-to-text)

Downloaded automatically on first transcription. Pre-download with install script.

| Model | Speed | Accuracy | VRAM/RAM |
|-------|-------|----------|----------|
| `tiny` | Fastest | Lowest | ~1 GB |
| `base` | Fast | Good | ~1 GB |
| `small` | Medium | Better | ~2 GB |
| `medium` | Slow | Best | ~5 GB |

```bash
export JARVIS_WHISPER_MODEL=base   # default
# Pre-download:
python -c "import whisper; whisper.load_model('base')"
```

Cache location: `~/.cache/whisper/`

---

## 6. GPU / ROCm (AMD RX 7600)

| Item | Status on your PC |
|------|-------------------|
| ROCm | Installed (`rocm-smi` works) |
| RX 7600 | Detected, ~8 GB VRAM |

Optional tuning:

```bash
export OLLAMA_KEEP_ALIVE=30m   # keep models loaded between chats
```

ROCm docs: https://ollama.com/blog/amd-preview

---

## 7. Environment variables (optional)

| Variable | Default | Purpose |
|----------|---------|---------|
| `JARVIS_PIPER_MODEL` | _(none)_ | Piper ONNX voice path |
| `JARVIS_TTS_VOICE` | espeak default | espeak voice name |
| `JARVIS_WHISPER_MODEL` | `base` | Whisper model size |
| `OLLAMA_KEEP_ALIVE` | `5m` | How long Ollama keeps models loaded |
| `JARVIS_UNCENSORED` | `0` | Uncensored mode |
| `JARVIS_PORT` | `8765` | GUI port |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama URL |

---

## 8. Future / not auto-installed

These were recommended but need separate setup:

| Item | Purpose | Download |
|------|---------|----------|
| **ComfyUI / Flux** | Real image generation | https://github.com/comfyanonymous/ComfyUI |
| **MusicGen (Hugging Face)** | Music generation | `pip install transformers scipy accelerate` |
| **AudioCraft** (legacy) | Alternate MusicGen backend | Often fails on Python 3.12 (spacy/thinc) |
| **Coqui XTTS** | Voice cloning | https://github.com/coqui-ai/TTS |
| **pytest** | Auto-test after code apply | `pip install pytest` |

---

## Disk space estimate

| Category | Approx size |
|----------|-------------|
| Python venv + Whisper/PyTorch | ~3–5 GB |
| Ollama standard models (all) | ~35–45 GB |
| Ollama fast extras | ~9 GB |
| Piper binary + one voice | ~65 MB |
| Whisper `base` model | ~150 MB |
| **Total (full install)** | **~45–55 GB** |

---

## Verify installation

```bash
source venv/bin/activate
source data/jarvis.env

which espeak-ng ffmpeg piper whisper ollama
python -c "from jarvis.gpu import detect_gpu; print(detect_gpu())"
curl -s http://127.0.0.1:11434/api/tags | head
```

Launch Jarvis:

```bash
./scripts/launch-jarvis.sh
```
