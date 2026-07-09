"""Audio action implementations — transcription, TTS, VST, and music."""

from __future__ import annotations

import re
from pathlib import Path

from jarvis import llm
from jarvis.behaviors.audio.context import AudioContext
from jarvis.response import err, ok


class AudioActionEngine:
    @classmethod
    def transcribe(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_audio(params.get("path", ""))
        if not path:
            return err("Which audio file should I transcribe? Attach one or record first.")
        model = params.get("model") or None
        result = ctx.audio.transcribe(path, model=model)
        if result.startswith("ERROR:"):
            return err(result)
        return ok(f"Here's the transcript:\n\n{result}", module="audio", audio_path=path, transcript=result)

    @classmethod
    def record_transcribe(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        duration = float(params.get("duration") or 5)
        path, text = ctx.audio.record_and_transcribe(duration, model=params.get("model"))
        if path.startswith("ERROR:"):
            return err(path)
        if text.startswith("ERROR:"):
            return err(text)
        ctx.session.note_audio(path)
        return ok(
            f"**Recorded** `{path}`\n\n**Transcript:**\n\n{text}",
            module="audio",
            audio_path=path,
            transcript=text,
        )

    @classmethod
    def analyze_audio(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_audio(params.get("path", ""))
        if not path:
            return err("Which audio file?")
        transcript = ctx.audio.transcribe(path)
        if transcript.startswith("ERROR:"):
            return err(transcript)
        answer = llm.ask(
            llm.general_model(),
            [{
                "role": "user",
                "content": f"Summarize this transcript. Key points and action items.\n\n{transcript}",
            }],
        )
        return ok(
            f"**Summary:**\n\n{answer}\n\n---\n\n**Transcript:**\n{transcript[:2000]}",
            module="audio",
            audio_path=path,
        )

    @classmethod
    def generate_audio(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        text = params.get("text") or message
        text = re.sub(
            r"^(please\s+)?(generate|create|make|read|speak|say)\s+(an?\s+)?(audio|voice|speech|recording\s+)?(that\s+)?(says?|reading?|of)?\s*[:\-]?\s*",
            "",
            text,
            flags=re.I,
        ).strip()
        if not text:
            return err("What should the audio say?")
        result = ctx.audio.generate(
            text,
            voice=params.get("voice") or None,
            speed=int(params.get("speed") or 175),
            fmt=params.get("format") or "wav",
        )
        if result.startswith("ERROR:"):
            return err(result)
        ctx.session.note_audio(result)
        played = ""
        if ctx.audio.devices.get("auto_play"):
            play_result = ctx.audio.play(result)
            if not play_result.startswith("ERROR:"):
                played = f"\n\nPlaying on **{ctx.audio.devices.get('name', 'Creative Sound Blaster')}**."
        return ok(f"Generated audio saved to `{result}`{played}", module="audio", audio_path=result)

    @classmethod
    def speak(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        return cls.generate_audio(ctx, params, message)

    @classmethod
    def play_audio(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_audio(params.get("path", "")) or ctx.audio.last_output
        if not path:
            return err("No audio file to play. Generate or attach one first.")
        if path.endswith(".txt") or not Path(path).exists():
            return cls.generate_audio(ctx, {"text": message or params.get("text", "")}, message)
        result = ctx.audio.play(path)
        if result.startswith("ERROR:"):
            return err(result)
        return ok(
            f"Playing on **{ctx.audio.devices.get('name', 'Creative Sound Blaster')}**: `{result}`",
            module="audio",
            audio_path=result,
        )

    @classmethod
    def process_audio_vst(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_audio(params.get("path", "")) or ctx.audio.last_output
        if not path:
            return err("Which audio file? Attach one or generate speech first.", module="audio")
        chain = (params.get("chain") or params.get("preset") or "voice").strip().lower()
        from jarvis.audio_settings import save_settings
        from jarvis.audio_vst import list_chains, process_file

        valid = {item["id"] for item in list_chains()}
        if chain not in valid:
            chain = "voice"
        if params.get("set_playback"):
            save_settings({"vst_playback_chain": chain})
        result = process_file(path, chain)
        if result.startswith("ERROR:"):
            return err(result, module="audio")
        ctx.session.note_audio(result)
        label = next((item["label"] for item in list_chains() if item["id"] == chain), chain)
        return ok(f"Applied **{label}** → `{Path(result).name}`", module="audio", audio_path=result)

    @classmethod
    def set_vst_live(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        preset = (params.get("preset") or params.get("chain") or "off").strip().lower()
        lower = (message or "").lower()
        if "off" in lower or "direct" in lower or "disable" in lower:
            preset = "off"
        elif "music" in lower:
            preset = "music"
        elif "scout" in lower or "surround" in lower:
            preset = "scout"
        elif "gaming" in lower or "game" in lower:
            preset = "gaming"
        elif "voice" in lower or "podcast" in lower:
            preset = "voice"

        from jarvis.audio_vst_live import activate_live, deactivate_live, install_filter_configs

        if preset in ("off", "none", "direct"):
            success, msg = deactivate_live()
        else:
            if params.get("install"):
                install_filter_configs()
            success, msg = activate_live(preset)
        if not success:
            return err(msg, module="audio")
        return ok(msg, module="audio")

    @classmethod
    def edit_audio(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_audio(params.get("path", ""))
        if not path:
            return err("Which audio file should I edit? Attach one or give me a path.")
        instruction = params.get("instruction") or message
        result = ctx.audio.edit(path, instruction=instruction)
        if result.startswith("ERROR:"):
            return err(result)
        ctx.session.note_audio(result)
        return ok(f"Edited audio saved to `{result}`", module="audio", audio_path=result)

    @classmethod
    def generate_music(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        from jarvis import music_gen

        prompt = params.get("prompt") or re.sub(
            r"^(generate|create|make)\s+(?:some\s+)?music\s+(?:about|for|of)?\s*[:\-]?\s*",
            "",
            message,
            flags=re.I,
        ).strip()
        if not prompt:
            return err("What kind of music should I generate?")
        duration = int(params.get("duration") or 10)
        result = music_gen.generate_music(prompt, duration=duration)
        if result.startswith("ERROR:"):
            return err(result)
        if not result.lower().endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a")):
            return err(f"Music output is not audio: {result}")
        ctx.session.note_audio(result)
        return ok(f"Music saved to `{result}`", module="audio", audio_path=result)

    @classmethod
    def transform_genre(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_audio(params.get("path", ""))
        if not path:
            return err("Attach a song or give me an audio path.")
        genre = params.get("genre") or params.get("prompt") or message
        genre = re.sub(
            r"^(turn|transform|convert|remix|make)\s+(?:this|it|the song)?\s*(?:into|as|to)?\s*",
            "",
            genre,
            flags=re.I,
        ).strip() or "jazz"
        duration = int(params.get("duration") or 30)
        result = ctx.audio.transform_genre(path, genre, duration=duration)
        if result.startswith("ERROR:"):
            return err(result)
        ctx.session.note_audio(result)
        return ok(
            f"Genre remix saved to `{result}`\n\n**Style:** {genre}",
            module="audio",
            audio_path=result,
        )

    @classmethod
    def generate_song(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        topic = params.get("topic") or params.get("prompt") or message
        topic = re.sub(
            r"^(write|compose|create|generate)\s+(?:a\s+)?song\s+(?:about|on)?\s*",
            "",
            topic,
            flags=re.I,
        ).strip()
        if not topic:
            return err("What should the song be about?")
        genre = params.get("genre") or "pop"
        mood = params.get("mood") or "uplifting"
        duration = int(params.get("duration") or 30)
        result = ctx.audio.generate_full_song(topic, genre=genre, mood=mood, duration=duration)
        if not result.get("ok"):
            return err(result.get("error", "Song generation failed"))
        ctx.session.note_audio(result.get("audio_path", ""))
        lyrics = result.get("lyrics", "")
        return ok(
            f"**{result.get('title', 'Song')}**\n\n{lyrics}\n\nSaved: `{result.get('audio_path')}`",
            module="audio",
            audio_path=result.get("audio_path"),
            transcript=lyrics,
        )

    @classmethod
    def voice_to_song(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_audio(params.get("path", "")) or ctx.audio.last_output
        if not path:
            return err("Record your voice first or attach a vocal recording.")
        lyrics = params.get("lyrics") or ""
        title = params.get("title") or ""
        style = params.get("style") or "pop ballad"
        genre = params.get("genre") or "pop"
        duration = int(params.get("duration") or 30)
        result = ctx.audio.voice_to_song(
            path,
            lyrics=lyrics,
            title=title,
            style=style,
            genre=genre,
            duration=duration,
        )
        if not result.get("ok"):
            return err(result.get("error", "Voice-to-song failed"))
        ctx.session.note_audio(result.get("audio_path", ""))
        return ok(
            f"**{result.get('title', 'Your song')}**\n\n{result.get('lyrics', '')}\n\n"
            f"Mixed track: `{result.get('audio_path')}`",
            module="audio",
            audio_path=result.get("audio_path"),
            transcript=result.get("lyrics", ""),
        )

    @classmethod
    def diarize_audio(cls, ctx: AudioContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_audio(params.get("path", ""))
        if not path:
            return err("Which audio file should I diarize?")
        speaker_count = int(params.get("num_speakers") or 0) or None
        result = ctx.audio.diarize(path, num_speakers=speaker_count)
        if not result.get("ok"):
            return err(result.get("error", "Diarization failed"))
        text = result.get("transcript") or ""
        segments = result.get("segments", [])
        lines = [
            f"- **{segment.get('speaker')}** ({segment.get('start')}s–{segment.get('end')}s): {segment.get('text', '')}"
            for segment in segments[:20]
        ]
        body = text or "\n".join(lines)
        hint = f"\n\n_{result.get('hint')}_" if result.get("hint") else ""
        return ok(
            f"**Speakers** ({result.get('engine', 'unknown')}):\n\n{body}{hint}",
            module="audio",
            audio_path=path,
            transcript=body,
        )
