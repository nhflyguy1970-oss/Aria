# Installation Guide

Install Aria on a **fresh Linux machine** (Ubuntu/Debian/Zorin recommended) without reading source code.

## Quick install

```bash
git clone https://github.com/nhflyguy1970-oss/Aria.git
cd Aria
./workstation install --developer
./workstation configure
./workstation verify
./workstation inventory
./workstation start
```

Install profiles: `--minimal`, `--developer` (default), `--full`, `--gpu`, `--headless`

Or via jarvis-ctl:

```bash
./scripts/jarvis-ctl.sh install --developer
```

Equivalent wrapper:

```bash
./workstation install --developer
./workstation configure
./workstation verify
./workstation start
```

## Co-install with AI-Platform

Clone both repos as siblings:

```
~/AI/
  Aria/          # this repo
  AI-Platform/   # platform services
```

`install.sh` detects `../AI-Platform`, runs `uv sync`, and `aiplatform init` when compose is missing.

Set in `data/jarvis.env`:

```bash
export AI_ROOT="/path/to/AI"
```

## What install does

1. Creates `venv/` and installs Python requirements
2. Runs `install-dependencies.sh` (apt tools, Piper, Whisper, Ollama pulls)
3. Creates `data/jarvis.env` from `jarvis.env.example`
4. Initializes AI-Platform compose (when present)

## Options

```bash
./scripts/install.sh --skip-deps          # pip/venv only
./scripts/install.sh --skip-platform      # no AI-Platform init
./scripts/install.sh --skip-ollama        # passed to install-dependencies.sh
```

## System requirements

- Python 3.11+
- 16GB+ RAM recommended
- GPU optional (NVIDIA for LLM, AMD for desktop/image — see DEPLOYMENT.md)
- ~20GB disk for models (more for ComfyUI checkpoints)

## After install

| Step | Command |
|------|---------|
| Configure | `./workstation configure` |
| Verify | `./workstation verify` |
| Start | `./workstation start` |
| Status | `./scripts/jarvis-ctl.sh status --full` |
| Stop | `./workstation stop` |

## Troubleshooting

- **venv missing** → re-run `./scripts/install.sh`
- **Ollama down** → `ollama serve` then `./scripts/pull-models.sh`
- **Platform doctor fails** → set `AI_ROOT`, run `python -m aiplatform.cli init`
- **Server won't start** → `./workstation doctor`

See also: [CONFIG.md](CONFIG.md), [DEPLOYMENT.md](DEPLOYMENT.md), [OPERATIONS.md](OPERATIONS.md)
