import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from jarvis import fs, llm
from jarvis.audio_device import (
    apply_system_default,
    capture_volume_for,
    detect_devices,
    effective_input_source,
    ffmpeg_env,
    mic_routing_status,
    play_file,
    record_to_file,
    start_ptt_record,
    stop_ptt_record,
    trim_silence_vad,
)
from jarvis.audio_settings import (
    MIC_PROFILES,
    WHISPER_LANGUAGES,
    WHISPER_MODELS,
    saved_piper_speed,
    saved_whisper_language,
    saved_whisper_model,
)
from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.conversation import Conversation

AUDIO_DIR = DATA_DIR / "audio"
GENERATED_DIR = AUDIO_DIR / "generated"
EDITED_DIR = AUDIO_DIR / "edited"
RECORDINGS_DIR = AUDIO_DIR / "recordings"
AUDIO_LIBRARY_DIRS = {
    "recordings": RECORDINGS_DIR,
    "generated": GENERATED_DIR,
    "edited": EDITED_DIR,
}

def _song_base_stem(stem: str) -> str:
    for suffix in ("_inst", "_vocal", "_backing"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem

def delete_audio_file(path: str, *, category: str | None = None) -> str:
    """Delete an audio library file (and related song artifacts). Returns path or ERROR."""
    from jarvis.music_gen import MUSIC_DIR
    from jarvis.song_studio import SONGS_DIR

    allowed = {
        **AUDIO_LIBRARY_DIRS,
        "music": MUSIC_DIR,
        "songs": SONGS_DIR,
    }
    try:
        target = Path(path).expanduser().resolve()
    except OSError as e:
        log.error(f"Invalid path: {e}")
        return f"ERROR: Invalid path: {e}"
    data_root = DATA_DIR.resolve()
    if data_root not in target.parents and target != data_root:
        return "ERROR: Path must stay under data directory"

    roots = [allowed[category].resolve()] if category in allowed else [
        d.resolve() for d in (*AUDIO_LIBRARY_DIRS.values(), MUSIC_DIR, SONGS_DIR)
    ]
    if not any(str(target).startswith(str(root)) for root in roots):
        return "ERROR: File is not in an audio library folder"

    deleted: list[str] = []

    def _unlink(p: Path) -> None:
        if p.is_file():
            p.unlink(missing_ok=True)
            deleted.append(str(p))

    if str(target).startswith(str(SONGS_DIR.resolve())):
        base = _song_base_stem(target.stem)
        for sibling in SONGS_DIR.glob(f"{base}*"):
            _unlink(sibling)
    else:
        _unlink(target)
        for ext in (".txt", ".json", ".prompt.json"):
            _unlink(target.with_suffix(ext))

    if not deleted:
        return f"ERROR: File not found: {target}"
    return deleted[0]

SUPPORTED_AUDIO = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}

class AudioEngine:
    def __init__(self):
        self.conversation = Conversation(
            "You are Jarvis Audio Assistant. Help with transcription, generation, and editing audio."
        )
        self.last_transcript: str = ""
        self.last_output: str = ""
        self.devices = detect_devices()
        apply_system_default()

    def get_devices(self) -> dict:
        self.devices = detect_devices()
        return self.devices

    def play(self, path: str) -> str:
        """Play audio file through Creative Sound Blaster."""
        try:
            resolved = self._resolve_audio(path, base=DATA_DIR)
            result = play_file(resolved)
            if result.startswith("ERROR:"):
                log.error(f"Error playing file: {result}")
                return result
            return result
        except Exception as e:
            log.error(f"Exception in play(): {e}")
            return f"ERROR: {e}"

    def _should_auto_play(self) -> bool:
        return self.devices.get("auto_play", True)

    def _whisper_path(self) -> str | None:
        return shutil.which("whisper")

    def default_whisper_model(self) -> str:
        saved = saved_whisper_model()
        if saved:
            return saved
        return os.getenv("JARVIS_WHISPER_MODEL", "small").strip() or "small"

    def _ffprobe_path(self) -> str | None:
        return shutil.which("ffprobe")

    def _probe_duration(self, src: Path) -> float | None:
        ffprobe = self._ffprobe_path()
        if not ffprobe:
            log.warning("ffprobe not found")
            return None
        try:
            result = subprocess.run(
                [
                    ffprobe, "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(src),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                log.error(f"ffprobe error: {result.stderr}")
                return None
            return float(result.stdout.strip())
        except (ValueError, subprocess.SubprocessError) as e:
            log.error(f"Error probing duration: {e}")
            return None

    def status(self) -> dict:
        from jarvis.audio_diarize import diarize_status
        from jarvis.audio_whisper import whisper_backend
        from jarvis.config import piper_ready, piper_voice_label
        from jarvis.song_studio import melody_available

        tts = "piper" if piper_ready() else ("espeak" if self._espeak_path() else "none")
        return {
            "whisper_cli": bool(self._whisper_path()) or whisper_backend() == "faster-whisper",
            "whisper_backend": whisper_backend(),
            "whisper_model": self.default_whisper_model(),
            "whisper_language": saved_whisper_language(),
            "whisper_languages": list(WHISPER_LANGUAGES),
            "piper_speed": saved_piper_speed(),
            "melody_model": melody_available(),
            "diarize": diarize_status(),
            "torch_device": __import__("jarvis.torch_device", fromlist=["torch_device"]).torch_device(),
            "ffmpeg": bool(self._ffmpeg_path()),
            "ffprobe": bool(self._ffprobe_path()),
            "piper": piper_ready(),
            "piper_voice": piper_voice_label() if piper_ready() else "",
            "espeak": bool(self._espeak_path()),
            "tts_engine": tts,
            "devices": self.get_devices(),
            "input_sources": self.get_devices().get("input_sources", []),
            "capture_volume": capture_volume_for(effective_input_source()),
            "mic_routing": mic_routing_status(),
            "mic_profiles": MIC_PROFILES,
            "whisper_models": list(WHISPER_MODELS),
            "last_transcript_preview": (self.last_transcript[:240] + "…") if len(self.last_transcript) > 240 else self.last_transcript,
            "last_output": self.last_output,
            "supported_formats": sorted(SUPPORTED_AUDIO),
            "vst": __import__("jarvis.audio_vst", fromlist=["status"]).status(),
        }

    def record(self, duration_sec: float = 5.0, output: str | None = None, source: str | None = None) -> str:
        """Record from configured microphone to WAV."""
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        if output:
            out_path = fs.resolve_path(output, base=DATA_DIR)
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = RECORDINGS_DIR / f"recording_{stamp}.wav"
        result = record_to_file(out_path, duration_sec, source=source)
        if result.startswith("ERROR:"):
            log.error(f"Error recording file: {result}")
            return result
        self.last_output = result
        return result

    def record_and_transcribe(
        self,
        duration_sec: float = 5.0,
        model: str | None = None,
        source: str | None = None,
        language: str | None = None,
    ) -> tuple[str, str]:
        """Record, then transcribe. Returns (audio_path, transcript_or_error)."""
        path = self.record(duration_sec, source=source)
        if path.startswith("ERROR:"):
            log.error(f"Error in record_and_transcribe: {path}")
            return path, path
        text = self.transcribe(path, model=model, language=language)
        return path, text

    def _ffmpeg_path(self) -> str | None:
        return shutil.which("ffmpeg")

    def _espeak_path(self) -> str | None:
        return shutil.which("espeak-ng") or shutil.which("espeak")

    def _piper_path(self) -> str | None:
        from jarvis.config import piper_binary

        found = piper_binary()
        return str(found) if found else None

    def _resolve_audio(self, path: str, base: Path | None = None) -> Path:
        resolved = fs.resolve_path(path, base=base or PROJECT_ROOT)
        if resolved.suffix.lower() not in SUPPORTED_AUDIO:
            raise ValueError(f"Unsupported audio format: {resolved.suffix}")
        if not resolved.exists():
            raise FileNotFoundError(f"Audio file not found: {resolved}")
        return resolved

    def transcribe(self, path: str, model: str | None = None, language: str | None = None) -> str:
        from jarvis.audio_search import index_transcript
        from jarvis.audio_whisper import transcribe as fw_transcribe

        model = (model or self.default_whisper_model()).strip() or "base"
        lang = language or saved_whisper_language()
        try:
            resolved = self._resolve_audio(path)
            result = fw_transcribe(resolved, model=model, language=lang)
            if result.startswith("ERROR:"):
                log.error(f"Error transcribing file: {result}")
                return result
            self.last_transcript = result
            index_transcript(str(resolved), result, title=resolved.name)
            return result
        except Exception as e:
            log.error(f"Exception in transcribe(): {e}")
            return f"ERROR: {e}"

    def batch_transcribe(self, paths: list[str], model: str | None = None, language: str | None = None) -> list[dict]:
        out = []
        for p in paths:
            text = self.transcribe(p, model=model, language=language)
            out.append({"path": p, "ok": not text.startswith("ERROR:"), "transcript": text})
        return out

    def speak(self, text: str, output: str | None = None) -> str:
        return self.generate(text, output=output)

    def generate(
        self,
        text: str,
        output: str | None = None,
        voice: str | None = None,
        speed: int = 175,
        pitch: int = 50,
        amplitude: int = 100,
        fmt: str = "wav",
        auto_play: bool | None = None,
    ) -> str:
        """Generate speech audio from text (piper if available, else espeak)."""
        if not text or not text.strip():
            log.warning("No text provided for audio generation")
            return "ERROR: No text provided for audio generation"

        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        fmt = (fmt or "wav").lower().lstrip(".")
        if output:
            out_path = fs.resolve_path(output, base=DATA_DIR)
        else:
            stem = re.sub(r"[^\w\-]+", "_", text[:40].strip()).strip("_") or "speech"
            out_path = GENERATED_DIR / f"{stem}.{fmt}"

        out_path.parent.mkdir(parents=True, exist_ok=True)
        wav_path = out_path if fmt == "wav" else out_path.with_suffix(".wav")

        piper = self._piper_path()
        model_path = os.getenv("JARVIS_PIPER_MODEL", "")
        if piper and model_path and Path(model_path).exists():
            try:
                from jarvis.config import piper_runtime_env

                length_scale = 1.0 / max(0.5, saved_piper_speed())
                proc = subprocess.run(
                    [piper, "--model", model_path, "--output_file", str(wav_path), "--length_scale", f"{length_scale:.3f}"],
                    input=text,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=True,
                    env=piper_runtime_env(),
                )
                if proc.returncode != 0:
                    log.error(f"Piper error: {proc.stderr or proc.stdout}")
                    return f"ERROR: {proc.stderr or proc.stdout}"
            except Exception as e:
                log.error(f"Exception in Piper generation: {e}")
                return f"ERROR: Piper failed: {e}"
        else:
            espeak = self._espeak_path()
            if not espeak:
                log.warning("espeak not found")
                return "ERROR: espeak not found. Install: sudo apt install espeak-ng"

            cmd = [
                espeak,
                "-w", str(wav_path),
                "-s", str(max(80, min(450, speed))),
                "-p", str(max(0, min(99, pitch))),
                "-a", str(max(0, min(200, amplitude))),
            ]
            if voice:
                cmd.extend(["-v", voice])
            elif os.getenv("JARVIS_TTS_VOICE"):
                cmd.extend(["-v", os.getenv("JARVIS_TTS_VOICE", "")])
            cmd.append(text)

            try:
                subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True)
            except Exception as e:
                log.error(f"Exception in espeak generation: {e}")
                return f"ERROR: {e}"

        if fmt != "wav":
            converted = self.convert(str(wav_path), str(out_path))
            if converted.startswith("ERROR:"):
                log.error(f"Error converting audio format: {converted}")
                return converted
            if wav_path != out_path and wav_path.exists():
                wav_path.unlink(missing_ok=True)
            self.last_output = converted
            if auto_play is not False and (auto_play or self._should_auto_play()):
                play_file(converted)
            return converted

        self.last_output = str(wav_path)
        if auto_play is not False and (auto_play or self._should_auto_play()):
            play_file(wav_path)
        return str(wav_path)

    def _build_ffmpeg_edit_cmd(
        self,
        src: Path,
        dst: Path,
        *,
        start_sec: float | None = None,
        end_sec: float | None = None,
        duration_sec: float | None = None,
        volume_db: float = 0,
        speed: float = 1.0,
        fade_in_sec: float = 0,
        fade_out_sec: float = 0,
        normalize: bool = False,
        src_duration: float | None = None,
    ) -> list[str]:
        ffmpeg = self._ffmpeg_path()
        if not ffmpeg:
            raise RuntimeError("ffmpeg not found. Install: sudo apt install ffmpeg")

        cmd = [ffmpeg, "-y"]
        if start_sec is not None and start_sec > 0:
            cmd.extend(["-ss", str(start_sec)])

        cmd.extend(["-i", str(src)])

        if end_sec is not None:
            cmd.extend(["-to", str(end_sec)])
        elif duration_sec is not None:
            cmd.extend(["-t", str(duration_sec)])

        filters: list[str] = []
        if abs(speed - 1.0) > 0.01:
            tempo = max(0.5, min(2.0, speed))
            filters.append(f"atempo={tempo}")
        if volume_db:
            filters.append(f"volume={volume_db}dB")
        if fade_in_sec > 0:
            filters.append(f"afade=t=in:st=0:d={fade_in_sec}")
        if fade_out_sec > 0:
            dur = src_duration
            if dur is None or dur <= fade_out_sec:
                dur = fade_out_sec + 0.5
            fade_start = max(0.0, dur - fade_out_sec)
            filters.append(f"afade=t=out:st={fade_start}:d={fade_out_sec}")
        if normalize:
            filters.append("loudnorm")

        if filters:
            cmd.extend(["-af", ",".join(filters)])

        cmd.append(str(dst))
        return cmd

    def _parse_edit_instruction(self, instruction: str) -> dict:
        prompt = f"""Parse this audio edit request into JSON. Use null for unset values.
Supported fields: start_sec, end_sec, duration_sec, volume_db, speed, fade_in_sec, fade_out_sec, normalize (bool).

Examples:
- "trim first 10 seconds" -> {{"start_sec": 10}}
- "cut to 30 seconds" -> {{"duration_sec": 30}}
- "make it louder" -> {{"volume_db": 6}}
- "speed up 1.5x" -> {{"speed": 1.5}}
- "fade in and out" -> {{"fade_in_sec": 1, "fade_out_sec": 1}}
- "normalize volume" -> {{"normalize": true}}

Request: {instruction}

Respond with ONLY valid JSON."""

        try:
            raw = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])
            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```\w*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            parsed = json.loads(raw)
            return {k: v for k, v in parsed.items() if v is not None}
        except Exception as e:
            log.error(f"Exception parsing edit instruction: {e}")
            return {}

    def edit(
        self,
        path: str,
        output: str | None = None,
        instruction: str = "",
        *,
        start_sec: float | None = None,
        end_sec: float | None = None,
        duration_sec: float | None = None,
        volume_db: float = 0,
        speed: float = 1.0,
        fade_in_sec: float = 0,
        fade_out_sec: float = 0,
        normalize: bool = False,
    ) -> str:
        """Edit audio with ffmpeg (trim, volume, speed, fade, normalize)."""
        ffmpeg = self._ffmpeg_path()
        if not ffmpeg:
            log.warning("ffmpeg not found")
            return "ERROR: ffmpeg not found. Install: sudo apt install ffmpeg"

        try:
            src = self._resolve_audio(path)
            EDITED_DIR.mkdir(parents=True, exist_ok=True)

            if instruction and not any(
                v is not None and v != 0 and v is not False
                for v in (start_sec, end_sec, duration_sec, volume_db, speed, fade_in_sec, fade_out_sec, normalize)
            ):
                parsed = self._parse_edit_instruction(instruction)
                start_sec = parsed.get("start_sec", start_sec)
                end_sec = parsed.get("end_sec", end_sec)
                duration_sec = parsed.get("duration_sec", duration_sec)
                volume_db = parsed.get("volume_db", volume_db) or 0
                speed = parsed.get("speed", speed) or 1.0
                fade_in_sec = parsed.get("fade_in_sec", fade_in_sec) or 0
                fade_out_sec = parsed.get("fade_out_sec", fade_out_sec) or 0
                normalize = parsed.get("normalize", normalize) or False

            if output:
                dst = fs.resolve_path(output, base=DATA_DIR)
            else:
                suffix = src.suffix or ".wav"
                dst = EDITED_DIR / f"{src.stem}_edited{suffix}"

            dst.parent.mkdir(parents=True, exist_ok=True)
            src_duration = self._probe_duration(src) if fade_out_sec > 0 else None
            cmd = self._build_ffmpeg_edit_cmd(
                src,
                dst,
                start_sec=start_sec,
                end_sec=end_sec,
                duration_sec=duration_sec,
                volume_db=volume_db,
                speed=speed,
                fade_in_sec=fade_in_sec,
                fade_out_sec=fade_out_sec,
                normalize=normalize,
                src_duration=src_duration,
            )
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=ffmpeg_env())
            if result.returncode != 0:
                log.error(f"Error editing audio: {result.stderr or result.stdout}")
                return f"ERROR: {result.stderr or result.stdout}"

            self.last_output = str(dst)
            if self._should_auto_play():
                play_file(dst)
            return str(dst)
        except Exception as e:
            log.error(f"Exception in edit(): {e}")
            return f"ERROR: {e}"

    def analyze(self, path: str, model: str | None = None) -> dict:
        """Transcribe and LLM-summarize audio."""
        transcript = self.transcribe(path, model=model)
        if transcript.startswith("ERROR:"):
            log.error(f"Error analyzing file: {transcript}")
            return {"ok": False, "error": transcript}
        prompt = f"""Analyze this audio transcript. Summarize key points, tone, and action items.

TRANSCRIPT:
{transcript}
"""
        summary = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])
        return {"ok": True, "transcript": transcript, "summary": summary.strip()}

    def _extract_waveform_peaks(self, src: Path, samples: int = 200) -> list[float]:
        import struct
        import tempfile
        import wave

        samples = max(32, min(int(samples), 2000))
        wav_path = src
        tmp: Path | None = None
        if src.suffix.lower() != ".wav":
            ffmpeg = self._ffmpeg_path()
            if not ffmpeg:
                raise RuntimeError("ffmpeg required for waveform of non-WAV files")
            fd, tmp_name = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            tmp = Path(tmp_name)
            subprocess.run(
                [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-ac", "1", str(tmp)],
                capture_output=True,
                timeout=120,
                check=True,
                env=ffmpeg_env(),
            )
            wav_path = tmp
        try:
            with wave.open(str(wav_path), "rb") as wf:
                nframes = wf.getnframes()
                nch = wf.getnchannels()
                width = wf.getsampwidth()
                if nframes <= 0 or width not in (1, 2, 4):
                    log.warning("Invalid WAV file format")
                    return [0.0] * samples
                raw = wf.readframes(nframes)
            if width == 1:
                fmt = f"{nframes * nch}b"
                vals = struct.unpack(fmt, raw)
            elif width == 2:
                fmt = f"{nframes * nch}h"
                vals = struct.unpack(fmt, raw)
            else:
                fmt = f"{nframes * nch}i"
                vals = struct.unpack(fmt, raw)
            scale = float(2 ** (8 * width - 1))
            mono: list[float] = []
            for i in range(0, len(vals), nch):
                chunk = vals[i : i + nch]
                mono.append(max(abs(v) for v in chunk) / scale)
            bucket = max(1, len(mono) // samples)
            peaks: list[float] = []
            for i in range(0, len(mono), bucket):
                block = mono[i : i + bucket]
                peaks.append(max(block) if block else 0.0)
            return peaks[:samples]
        finally:
            if tmp and tmp.exists():
                tmp.unlink(missing_ok=True)

    def waveform(self, path: str, samples: int = 200) -> dict:
        try:
            src = self._resolve_audio(path)
            duration = self._probe_duration(src)
            peaks = self._extract_waveform_peaks(src, samples=samples)
            return {"ok": True, "path": str(src), "duration": duration, "samples": len(peaks), "peaks": peaks}
        except Exception as e:
            log.error(f"Exception in waveform(): {e}")
            return {"ok": False, "error": str(e)}

    def record_vad(
        self,
        max_duration_sec: float = 30.0,
        *,
        threshold_db: float = -40.0,
        min_silence_sec: float = 0.8,
        output: str | None = None,
        source: str | None = None,
    ) -> str:
        """Record up to max duration, then trim leading/trailing silence."""
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        if output:
            out_path = fs.resolve_path(output, base=DATA_DIR)
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = RECORDINGS_DIR / f"recording_vad_{stamp}.wav"
        raw_path = out_path.with_name(out_path.stem + "_raw.wav")
        result = record_to_file(raw_path, max_duration_sec, source=source)
        if result.startswith("ERROR:"):
            log.error(f"Error recording VAD: {result}")
            return result
        trimmed = trim_silence_vad(
            raw_path, out_path,
            threshold_db=threshold_db,
            min_silence_sec=min_silence_sec,
        )
        if trimmed.startswith("ERROR:"):
            if raw_path.exists():
                if out_path.exists():
                    out_path.unlink(missing_ok=True)
                raw_path.replace(out_path)
            self.last_output = str(out_path)
            return str(out_path)
        self.last_output = trimmed
        return trimmed

    def record_ptt_start(self, source: str | None = None) -> tuple[str, str]:
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = RECORDINGS_DIR / f"recording_ptt_{stamp}.wav"
        session_id, err = start_ptt_record(out_path, source=source)
        if err:
            log.error(f"Error starting PTT record: {err}")
            return "", err if err.startswith("ERROR:") else f"ERROR: {err}"
        return session_id, str(out_path)

    def record_ptt_stop(self, session_id: str) -> str:
        result = stop_ptt_record(session_id)
        if not result.startswith("ERROR:"):
            self.last_output = result
        log.info(f"PTT recording stopped: {result}")
        return result

    def transform_genre(
        self, path: str, genre_prompt: str, duration: int = 30, job_id: str | None = None,
    ) -> str:
        from jarvis.song_studio import transform_genre
        log.info(f"Transforming genre for {path}")
        return transform_genre(path, genre_prompt, duration=duration, job_id=job_id)

    def generate_full_song(
        self, topic: str, genre: str = "pop", mood: str = "uplifting",
        duration: int = 30, job_id: str | None = None,
    ) -> dict:
        from jarvis.song_studio import generate_full_song
        log.info(f"Generating full song with topic '{topic}'")
        return generate_full_song(topic, genre=genre, mood=mood, duration=duration, job_id=job_id)

    def voice_to_song(
        self, voice_path: str, *, lyrics: str = "", title: str = "", style: str = "pop ballad",
        genre: str = "pop", duration: int = 30, job_id: str | None = None,
    ) -> dict:
        from jarvis.song_studio import voice_to_song
        log.info(f"Converting voice to song with path '{voice_path}'")
        return voice_to_song(
            voice_path, lyrics=lyrics, title=title, style=style,
            genre=genre, duration=duration, job_id=job_id,
        )

    def diarize(self, path: str, num_speakers: int | None = None) -> dict:
        from jarvis.audio_diarize import diarize
        try:
            resolved = str(self._resolve_audio(path))
            log.info(f"Diarizing audio file: {resolved}")
            return diarize(resolved, num_speakers=num_speakers)
        except Exception as e:
            log.error(f"Exception in diarize(): {e}")
            return {"ok": False, "error": str(e)}

    def delete_file(self, path: str, *, category: str | None = None) -> str:
        log.info(f"Deleting audio file: {path}")
        return delete_audio_file(path, category=category)

    def convert(self, path: str, output: str) -> str:
        ffmpeg = self._ffmpeg_path()
        if not ffmpeg:
            log.warning("ffmpeg not found")
            return "ERROR: ffmpeg not found"

        try:
            src = self._resolve_audio(path, base=DATA_DIR if not Path(path).is_absolute() else None)
            dst = fs.resolve_path(output, base=DATA_DIR)
            dst.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [ffmpeg, "-y", "-i", str(src), str(dst)],
                capture_output=True,
                text=True,
                timeout=300,
                check=True,
                env=ffmpeg_env(),
            )
            self.last_output = str(dst)
            return str(dst)
        except Exception as e:
            log.error(f"Exception in convert(): {e}")
            return f"ERROR: {e}"

    def handle(self, prompt: str) -> bool:
        if prompt.lower() == "exit":
            log.info("Exiting audio module")
            return False

        if prompt.startswith("record "):
            dur = 5.0
            rest = prompt[7:].strip()
            if rest:
                try:
                    dur = float(rest.split()[0])
                except ValueError as e:
                    log.warning(f"Invalid duration: {e}")
                    pass
            result = self.record(dur)
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nRecorded: {result}\n")
            return True

        if prompt.startswith("record-transcribe ") or prompt == "record-transcribe":
            dur = 5.0
            if prompt.startswith("record-transcribe "):
                try:
                    dur = float(prompt.split()[1])
                except (IndexError, ValueError) as e:
                    log.warning(f"Invalid duration: {e}")
                    pass
            path, text = self.record_and_transcribe(dur)
            if path.startswith("ERROR:"):
                print(f"\n{path}\n")
            elif text.startswith("ERROR:"):
                print(f"\nRecorded {path}\n{text}\n")
            else:
                print(f"\nRecorded: {path}\n--- TRANSCRIPT ---\n{text}\n")
            return True

        if prompt.startswith("transcribe "):
            parts = prompt[11:].strip().split(maxsplit=1)
            path = parts[0]
            model = parts[1] if len(parts) > 1 else None
            result = self.transcribe(path, model)
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print("\n--- TRANSCRIPT ---\n")
                print(result)
                print()
            return True

        if prompt == "last":
            if self.last_transcript:
                print("\n--- LAST TRANSCRIPT ---\n")
                print(self.last_transcript)
                print()
            else:
                print("\nNo transcript available.\n")
            return True

        if prompt.startswith("play "):
            path = prompt[5:].strip() or self.last_output
            result = self.play(path)
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nPlaying on {self.devices.get('name', 'Creative')}: {result}\n")
            return True

        if prompt.startswith("generate "):
            text = prompt[9:].strip()
            result = self.generate(text)
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nGenerated + playing on Creative: {result}\n")
            return True

        if prompt.startswith("generate-to "):
            parts = prompt[12:].strip().split(maxsplit=1)
            if len(parts) < 2:
                print("\nUsage: generate-to <output.wav> <text>\n")
                return True
            result = self.generate(parts[1], output=parts[0])
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nGenerated audio: {result}\n")
            return True

        if prompt.startswith("speak "):
            text = prompt[6:].strip()
            result = self.speak(text)
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nAudio saved: {result}\n")
            return True

        if prompt.startswith("speak-to "):
            parts = prompt[9:].strip().split(maxsplit=1)
            if len(parts) < 2:
                print("\nUsage: speak-to <output.wav> <text>\n")
                return True
            result = self.speak(parts[1], parts[0])
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nAudio saved: {result}\n")
            return True

        if prompt.startswith("edit "):
            rest = prompt[5:].strip()
            if " :: " in rest:
                path, instruction = rest.split(" :: ", 1)
                result = self.edit(path.strip(), instruction=instruction.strip())
            else:
                parts = rest.split(maxsplit=1)
                path = parts[0]
                instruction = parts[1] if len(parts) > 1 else ""
                result = self.edit(path, instruction=instruction)
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nEdited audio: {result}\n")
            return True

        if prompt.startswith("convert "):
            parts = prompt[8:].strip().split(maxsplit=1)
            if len(parts) < 2:
                print("\nUsage: convert <input> <output>\n")
                return True
            result = self.convert(parts[0], parts[1])
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nConverted: {result}\n")
            return True

        if prompt.startswith("analyze "):
            path = prompt[8:].strip()
            result = self.transcribe(path)
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
                return True
            user_prompt = f"""Analyze this audio transcript. Summarize key points, tone, and action items.

TRANSCRIPT:
{result}
"""
            answer = llm.ask(llm.general_model(), [{"role": "user", "content": user_prompt}])
            print()
            print(answer)
            print()
            return True

        if prompt == "clear":
            self.conversation.clear()
            self.last_transcript = ""
            self.last_output = ""
            print("\nCleared.\n")
            return True

        self.conversation.add_user(prompt)
        answer = llm.ask(llm.general_model(), self.conversation.messages)
        self.conversation.add_assistant(answer)
        print()
        print(answer)
        print()
        return True

def main():
    engine = AudioEngine()
    print("\nJarvis Audio Module")
    print("Type 'exit' to quit.")
    print("Commands:")
    print("  record [seconds]              record from microphone")
    print("  record-transcribe [seconds]   record + Whisper transcribe")
    print("  transcribe <file> [model]     speech-to-text (whisper)")
    print("  last                          show last transcript")
    print("  play [file]                   play through Sound Blaster")
    print("  generate <text>               TTS + play on Creative card")
    print("  generate-to <out> <text>      TTS to specific file")
    print("  speak <text>                  alias for generate")
    print("  edit <file> <instruction>     edit audio (trim, volume, speed, fade)")
    print("  convert <in> <out>            convert format (ffmpeg)")
    print("  analyze <file>                transcribe + LLM summary")
    print("  clear                         reset state\n")

    while True:
        try:
            prompt = input("Audio > ")
            if not engine.handle(prompt):
                break
        except KeyboardInterrupt as e:
            log.info("Keyboard interrupt received, exiting...")
            print("\n")
            break
        except Exception as e:
            log.error(f"Exception in main loop: {e}")
            print(f"\nERROR: {e}\n")
