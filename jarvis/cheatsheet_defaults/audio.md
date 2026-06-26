# Audio — Quick Reference

Data: **`data/audio/`** · recordings · generated · edited · music · **songs/**

## Song Studio (new)

| You say / do | Result |
|--------------|--------|
| Attach song + "transform into heavy metal" | Genre remix (MusicGen-Melody) |
| "Write a song about summer love" | LLM lyrics + instrumental |
| Record voice → **Make my voice a song** | Pitch-treated vocal + AI backing |
| Audio tab → Song Studio section | Full GUI for all three |

## Chat examples

| You say | ARIA does |
|---------|-------------|
| Attach audio | Transcribe (faster-whisper or Whisper CLI) |
| "Summarize this audio" | Transcribe + LLM summary |
| "Record and transcribe" | Mic → Whisper |
| "Read aloud: …" | Piper TTS + Sound Blaster |
| "Generate music about rain" | MusicGen instrumental |

## GUI — Audio tab

- **faster-whisper** — 2–4× faster than CLI (auto if installed)
- **Language picker** — transcription language
- **Piper speed** — TTS rate
- **Song Studio** — genre transform, full songs, voice→song
- **Search** — indexed transcripts
- **Batch transcribe** — multiple paths at once
- Record modes: fixed · VAD · push-to-talk
- Waveform trim · edit · MusicGen
- **Live mode** — VU meter + partial transcript while recording
- **Advanced** — trim preview · diarize · SSE stream transcribe · wake word

## Advanced (optional deps)

| Feature | API / GUI | Optional install |
|---------|-----------|------------------|
| **VU + live transcript** | Record mode → Live | faster-whisper |
| **SSE stream transcribe** | Advanced → Stream transcribe file | faster-whisper |
| **Speaker diarization** | Advanced → Diarize | `pyannote.audio` + `HF_TOKEN` (else whisper-gap fallback) |
| **Wake word** | Advanced → Start wake word | `openwakeword`; auto-record on detect (`JARVIS_WAKEWORD_RECORD=1`) |
| **Bark / XTTS vocals** | Song Studio full song / voice→song | Bark or `TTS` (Coqui) |
| **GPU device** | `GET /api/audio/torch-device` | ROCm/CUDA PyTorch → `JARVIS_TORCH_DEVICE=cuda` |

## Requirements

| Tool | Purpose |
|------|---------|
| **faster-whisper** | Fast local STT (recommended) |
| **transformers** + **scipy** + **librosa** | MusicGen + melody genre remix |
| **ffmpeg** | Record, edit, mix |
| **Piper** | Natural TTS |

```bash
pip install -r requirements-optional.txt
```

## Env

| Variable | Purpose |
|----------|---------|
| `JARVIS_WHISPER_MODEL` / GUI | Whisper size |
| `JARVIS_WHISPER_LANGUAGE` / GUI | Transcription language |
| `JARVIS_MUSICGEN_MODEL` | `facebook/musicgen-small` |
| `JARVIS_MUSICGEN_MELODY_MODEL` | `facebook/musicgen-melody` |
| `JARVIS_TORCH_DEVICE` | `cuda` / `cpu` / `mps` for MusicGen + whisper |
| `JARVIS_WAKEWORD` | `1` = start listener in daemon |
| `JARVIS_WAKEWORD_MODEL` | openwakeword model (default `hey_jarvis` → say **Hey Jarvis**) |
| `JARVIS_WAKEWORD_TO_CHAT` | `1` = send wake-word transcript to Chat (GUI must be open) |
| `JARVIS_WAKEWORD_RECORD_MAX_SEC` | Max seconds after wake word (default `8`) |
| `JARVIS_WAKEWORD_SILENCE_SEC` | Stop after this much silence once you speak (default `0.9`) |
| `JARVIS_WAKEWORD_WHISPER_MODEL` | Fast transcribe model (default `small`) |
| `JARVIS_BROWSER` | Browser for GUI launch (default `google-chrome`) |
| `JARVIS_WAKEWORD_THRESHOLD` | Detection sensitivity (default `0.5`; lower = more sensitive) |
| `HF_TOKEN` | pyannote diarization |

Prefs in **`data/audio_settings.json`**. Session in **`data/audio/session.json`**.
