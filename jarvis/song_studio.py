"""Song studio — genre transform, voice→song, full lyrics+music generation."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from jarvis import llm
from jarvis.audio_device import ffmpeg_env
from jarvis.audio_progress import finish_job, update_job
from jarvis.config import DATA_DIR
from jarvis.music_gen import _generate_hf, _transformers_available, generate_music

SONGS_DIR = DATA_DIR / "audio" / "songs"
MELODY_MODEL_ID = os.getenv("JARVIS_MUSICGEN_MELODY_MODEL", "facebook/musicgen-melody")

_MELODY_MODEL = None
_MELODY_PROCESSOR = None


def melody_available() -> bool:
    if not _transformers_available():
        return False
    try:
        from transformers import MusicgenMelodyForConditionalGeneration  # noqa: F401
        return True
    except ImportError:
        return False


def _ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def _write_wav_int16(path: Path, audio, sample_rate: int) -> None:
    import numpy as np
    import scipy.io.wavfile

    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.clip(np.asarray(audio), -1.0, 1.0)
    scipy.io.wavfile.write(str(path), sample_rate, (arr * 32767).astype(np.int16))


def _load_mono(path: Path, target_sr: int = 32000):
    import librosa
    import numpy as np

    audio, sr = librosa.load(str(path), sr=target_sr, mono=True)
    return np.asarray(audio, dtype=np.float32), int(sr)


def _get_melody_model():
    global _MELODY_MODEL, _MELODY_PROCESSOR
    if _MELODY_MODEL is None:
        from transformers import AutoProcessor, MusicgenMelodyForConditionalGeneration

        from jarvis.torch_device import torch_device

        _MELODY_PROCESSOR = AutoProcessor.from_pretrained(MELODY_MODEL_ID)
        _MELODY_MODEL = MusicgenMelodyForConditionalGeneration.from_pretrained(MELODY_MODEL_ID)
        _MELODY_MODEL.to(torch_device())
    return _MELODY_MODEL, _MELODY_PROCESSOR


def unload_melody_model() -> None:
    global _MELODY_MODEL, _MELODY_PROCESSOR
    _MELODY_MODEL = None
    _MELODY_PROCESSOR = None
    from jarvis.ml_memory import release_torch_memory

    release_torch_memory()


def _melody_generate(
    audio_path: Path,
    prompt: str,
    duration: int,
    out_path: Path,
    *,
    on_progress: Callable[[int, str], None] | None = None,
) -> str:
    import torch

    if on_progress:
        on_progress(15, "Loading melody model…")
    model, processor = _get_melody_model()
    device = next(model.parameters()).device
    sr = processor.feature_extractor.sampling_rate
    if on_progress:
        on_progress(30, "Analyzing source audio…")
    audio, _ = _load_mono(audio_path, target_sr=sr)
    if on_progress:
        on_progress(45, f"Generating: {prompt[:60]}…")
    inputs = processor(audio=audio, sampling_rate=sr, text=[prompt], return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    max_new_tokens = int(min(max(duration, 5), 30) * 50)
    with torch.inference_mode():
        audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)
    if on_progress:
        on_progress(85, "Saving…")
    sampling_rate = model.config.audio_encoder.sampling_rate
    wav = audio_values[0, 0].detach().cpu().numpy()
    _write_wav_int16(out_path, wav, sampling_rate)
    return str(out_path)


def transform_genre(
    input_path: str,
    genre_prompt: str,
    duration: int = 30,
    output: str | None = None,
    *,
    job_id: str | None = None,
) -> str:
    """Re-imagine a song in a new genre using MusicGen-Melody."""
    if not melody_available():
        return "ERROR: MusicGen-Melody not available. pip install transformers scipy librosa"
    src = Path(input_path)
    if not src.exists():
        return f"ERROR: File not found: {src}"
    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    if output:
        out = Path(output)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = SONGS_DIR / f"genre_{stamp}.wav"
    prompt = genre_prompt.strip() or "upbeat electronic dance"
    def prog(p, m):
        return (update_job(job_id, p, m) if job_id else None)
    try:
        result = _melody_generate(src, prompt, duration, out, on_progress=prog)
        if job_id:
            finish_job(job_id, result={"audio_path": result})
        return result
    except Exception as e:
        if job_id:
            finish_job(job_id, error=str(e))
        return f"ERROR: Genre transform failed: {e}"


def generate_lyrics(topic: str, genre: str = "pop", mood: str = "uplifting") -> dict:
    prompt = f"""Write original song lyrics for a {genre} song.
Topic/theme: {topic}
Mood: {mood}

Return JSON only:
{{
  "title": "Song Title",
  "genre": "{genre}",
  "mood": "{mood}",
  "structure": ["verse1", "chorus", "verse2", "chorus", "bridge", "chorus"],
  "lyrics": "full lyrics with section labels like [Verse 1], [Chorus], etc.",
  "music_prompt": "short MusicGen prompt describing instrumentation, tempo, and vibe"
}}"""
    raw = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "title": topic[:48] or "Untitled",
            "genre": genre,
            "mood": mood,
            "lyrics": raw,
            "music_prompt": f"{mood} {genre}, vocals, {topic}",
        }


def mix_podcast_tracks(
    backing_path: str | Path,
    vocal_path: str | Path,
    *,
    vocal_gain_db: float = 2.0,
    title: str = "podcast_mix",
) -> str:
    """Mix two audio files (intro/music + voice) into one MP3/WAV under data/audio/songs."""
    backing = Path(backing_path).expanduser().resolve()
    vocal = Path(vocal_path).expanduser().resolve()
    if not backing.is_file():
        return f"ERROR: Backing track not found: {backing}"
    if not vocal.is_file():
        return f"ERROR: Vocal track not found: {vocal}"
    out_dir = DATA_DIR / "audio" / "songs"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.-]+", "_", title)[:48] or "podcast_mix"
    out = out_dir / f"{safe}_{int(time.time())}.wav"
    try:
        return _mix_tracks(backing, vocal, out, vocal_gain_db=vocal_gain_db)
    except Exception as exc:
        return f"ERROR: {exc}"


def _mix_tracks(backing: Path, vocal: Path | None, out: Path, vocal_gain_db: float = 2.0) -> str:
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        if vocal and vocal.exists():
            shutil.copy2(vocal, out)
        else:
            shutil.copy2(backing, out)
        return str(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if vocal and vocal.exists():
        cmd = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(backing), "-i", str(vocal),
            "-filter_complex",
            f"[1:a]volume={vocal_gain_db}dB[v];[0:a][v]amix=inputs=2:duration=longest:dropout_transition=2",
            str(out),
        ]
    else:
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(backing), str(out)]
    subprocess.run(cmd, capture_output=True, timeout=300, check=True, env=ffmpeg_env())
    return str(out)


def _sing_effect(voice: Path, out: Path, semitones: float = 2.0) -> str:
    """Pitch-shift and compress voice for a sung feel (lightweight fallback)."""
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        shutil.copy2(voice, out)
        return str(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pitch_ratio = 2 ** (semitones / 12.0)
    af = f"asetrate=44100*{pitch_ratio:.6f},aresample=44100,atempo={1/pitch_ratio:.6f},acompressor, loudnorm"
    if shutil.which("rubberband"):
        af = f"rubberband=pitch={pitch_ratio:.4f},acompressor,loudnorm"
    subprocess.run(
        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(voice), "-af", af, str(out)],
        capture_output=True, timeout=180, check=True, env=ffmpeg_env(),
    )
    return str(out)


def generate_full_song(
    topic: str,
    genre: str = "pop",
    mood: str = "uplifting",
    duration: int = 30,
    *,
    job_id: str | None = None,
) -> dict:
    """LLM lyrics + MusicGen instrumental (+ optional AI vocals)."""
    from jarvis.ml_memory import release_torch_memory, song_generation_plan, unload_ollama_models
    from jarvis.music_gen import unload_musicgen

    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan = song_generation_plan(duration)
    duration = plan["duration"]

    def prog(p, m):
        return (update_job(job_id, p, m) if job_id else None)

    try:
        if job_id and plan.get("warning"):
            prog(2, plan["warning"])
        if job_id:
            prog(5, "Writing lyrics…")
        meta = generate_lyrics(topic, genre=genre, mood=mood)
        title = re.sub(r"[^\w\- ]+", "", meta.get("title", "song"))[:40].strip() or "song"
        lyrics = meta.get("lyrics", "")
        music_prompt = meta.get("music_prompt") or f"{mood} {genre} with vocals and rich production"
        lyrics_path = SONGS_DIR / f"{title}_{stamp}.txt"
        lyrics_path.write_text(f"# {meta.get('title', title)}\n\n{lyrics}", encoding="utf-8")

        if plan["unload_ollama_before_music"]:
            if job_id:
                prog(18, "Freeing GPU memory (unloading Ollama)…")
            unload_ollama_models()
            release_torch_memory()

        if job_id:
            prog(25, f"Generating music ({duration}s)…")
        inst_path = SONGS_DIR / f"{title}_{stamp}_inst.wav"
        music_result = _generate_hf(
            f"{music_prompt}, instrumental backing track",
            duration,
            inst_path,
            on_progress=prog if job_id else None,
            device=plan["music_device"],
        )
        unload_musicgen()
        if music_result.startswith("ERROR:"):
            if job_id:
                finish_job(job_id, error=music_result)
            return {"ok": False, "error": music_result, "lyrics_path": str(lyrics_path), "meta": meta}

        vocal_path = SONGS_DIR / f"{title}_{stamp}_vocal.wav"
        mixed_path = SONGS_DIR / f"{title}_{stamp}.wav"
        vocal_result = "ERROR: skipped"
        if plan["allow_vocals"]:
            if job_id:
                prog(
                    70,
                    f"Generating AI vocals on {plan['vocal_device']} "
                    "(uses RAM, may take several minutes)…",
                )
            from jarvis.audio_vocals import generate_vocals_for_song, unload_vocal_models

            vocal_result = generate_vocals_for_song(
                lyrics, vocal_path, device=plan["vocal_device"],
            )
            unload_vocal_models()
        else:
            meta["vocal_note"] = plan.get("warning") or "AI vocals skipped (safe mode)"

        if job_id:
            prog(90, "Mixing…")
        if plan["allow_vocals"] and not vocal_result.startswith("ERROR:"):
            _mix_tracks(inst_path, vocal_path, mixed_path)
        else:
            shutil.copy2(inst_path, mixed_path)
            if vocal_result.startswith("ERROR:") and plan["allow_vocals"]:
                meta["vocal_note"] = vocal_result
        meta_path = SONGS_DIR / f"{title}_{stamp}.json"
        meta["safe_mode"] = plan["safe_mode"]
        meta["mode"] = plan["mode"]
        meta["duration_sec"] = duration
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        result = {
            "ok": True,
            "title": meta.get("title", title),
            "lyrics": lyrics,
            "lyrics_path": str(lyrics_path),
            "instrumental_path": str(inst_path),
            "audio_path": str(mixed_path),
            "meta_path": str(meta_path),
            "music_prompt": music_prompt,
            "safe_mode": plan["safe_mode"],
            "mode": plan["mode"],
            "instrumental_only": not plan["allow_vocals"],
            "vocal_device": plan["vocal_device"],
        }
        if job_id:
            finish_job(job_id, result=result)
        return result
    except Exception as e:
        try:
            from jarvis.music_gen import unload_musicgen

            unload_musicgen()
        except Exception:
            pass
        if job_id:
            finish_job(job_id, error=str(e))
        return {"ok": False, "error": str(e)}


def voice_to_song(
    voice_path: str,
    *,
    lyrics: str = "",
    title: str = "",
    style: str = "pop ballad",
    genre: str = "pop",
    duration: int = 30,
    job_id: str | None = None,
) -> dict:
    """Turn a voice recording into a sung song with AI backing."""
    from jarvis.audio_whisper import transcribe
    from jarvis.ml_memory import release_torch_memory, song_generation_plan, unload_ollama_models
    from jarvis.music_gen import unload_musicgen

    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    voice = Path(voice_path)
    if not voice.exists():
        return {"ok": False, "error": f"Voice file not found: {voice}"}
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan = song_generation_plan(duration)
    duration = plan["duration"]

    def prog(p, m):
        return (update_job(job_id, p, m) if job_id else None)
    try:
        if job_id and plan.get("warning"):
            prog(5, plan["warning"])
        if job_id:
            prog(10, "Processing voice…")
        if not lyrics.strip():
            if job_id:
                prog(20, "Transcribing voice…")
            lyrics = transcribe(voice)
            if lyrics.startswith("ERROR:"):
                lyrics = ""
        if not title:
            title = f"Voice Song {stamp}"
        safe_name = re.sub(r"[^\w\-]+", "_", title[:32]).strip("_") or "voice_song"
        sung_vocal = SONGS_DIR / f"{safe_name}_{stamp}_vocal.wav"
        if plan["allow_vocals"]:
            from jarvis.audio_vocals import bark_available, generate_vocals_for_song, unload_vocal_models, xtts_available

            if lyrics.strip() and (bark_available() or xtts_available()):
                vres = generate_vocals_for_song(
                    lyrics, sung_vocal, speaker_wav=str(voice), device=plan["vocal_device"],
                )
                unload_vocal_models()
                if vres.startswith("ERROR:"):
                    _sing_effect(voice, sung_vocal, semitones=1.5)
            else:
                _sing_effect(voice, sung_vocal, semitones=1.5)
        else:
            _sing_effect(voice, sung_vocal, semitones=1.5)

        if plan["unload_ollama_before_music"]:
            unload_ollama_models()
            release_torch_memory()

        prompt = f"{style}, {genre}, emotional vocals, full band production"
        backing = SONGS_DIR / f"{safe_name}_{stamp}_backing.wav"
        use_melody = melody_available() and plan["mode"] == "max"
        if use_melody:
            if job_id:
                prog(40, "Generating melody from your voice…")
            mel_result = _melody_generate(voice, prompt, duration, backing, on_progress=prog)
            unload_melody_model()
            if mel_result.startswith("ERROR:"):
                if job_id:
                    prog(50, "Melody model failed — using text-only music…")
                gen = generate_music(
                    prompt, duration=duration, output=str(backing),
                    on_progress=prog if job_id else None, device=plan["music_device"],
                )
                unload_musicgen()
                if gen.startswith("ERROR:"):
                    raise RuntimeError(gen)
        else:
            if job_id:
                prog(45, f"Generating backing track ({duration}s)…")
            gen = generate_music(
                prompt, duration=duration, output=str(backing),
                on_progress=prog if job_id else None, device=plan["music_device"],
            )
            unload_musicgen()
            if gen.startswith("ERROR:"):
                raise RuntimeError(gen)
        if job_id:
            prog(85, "Mixing vocal + backing…")
        mixed = SONGS_DIR / f"{safe_name}_{stamp}.wav"
        _mix_tracks(Path(backing), Path(sung_vocal), Path(mixed))
        lyrics_path = SONGS_DIR / f"{safe_name}_{stamp}.txt"
        lyrics_path.write_text(f"# {title}\n\n{lyrics or '(instrumental / hum)'}", encoding="utf-8")
        result = {
            "ok": True,
            "title": title,
            "lyrics": lyrics,
            "lyrics_path": str(lyrics_path),
            "vocal_path": str(sung_vocal),
            "backing_path": str(backing),
            "audio_path": str(mixed),
            "safe_mode": plan["safe_mode"],
        }
        if job_id:
            finish_job(job_id, result=result)
        return result
    except Exception as e:
        try:
            unload_musicgen()
            unload_melody_model()
        except Exception:
            pass
        if job_id:
            finish_job(job_id, error=str(e))
        return {"ok": False, "error": str(e)}
