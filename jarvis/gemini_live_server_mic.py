"""Server-side mic capture + speaker playback for Gemini Live (PySide-safe)."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import shlex
import shutil
import subprocess
import threading
import time

log = logging.getLogger("jarvis.gemini_live.mic")

_CHUNK_BYTES = 3200  # 100 ms @ 16 kHz mono s16


def server_audio_enabled() -> bool:
    if os.getenv("JARVIS_GEMINI_LIVE_SERVER_MIC", "1").strip().lower() in ("0", "false", "no", "off"):
        return False
    return bool(shutil.which("pw-record"))


def server_playback_enabled() -> bool:
    if os.getenv("JARVIS_GEMINI_LIVE_SERVER_SPEAK", "1").strip().lower() in ("0", "false", "no", "off"):
        return False
    return bool(shutil.which("pw-play"))


def _playback_tail_sec() -> float:
    try:
        return max(0.0, min(1.5, float(os.getenv("JARVIS_GEMINI_LIVE_MIC_TAIL_SEC", "0.35"))))
    except ValueError:
        return 0.35


def _capture_cmd() -> tuple[list[str], list[str] | None]:
    from jarvis.audio_device import _is_creative_input, effective_input_source, prepare_input_source

    source = (effective_input_source() or "").strip()
    if not source:
        raise RuntimeError("No capture source configured")
    if shutil.which("pactl"):
        prepare_input_source(source)
    stereo = _is_creative_input(source)
    rate = 48000 if stereo else 16000
    channels = 2 if stereo else 1
    pw = [
        "pw-record",
        "--target",
        source,
        "--rate",
        str(rate),
        "--channels",
        str(channels),
        "--format",
        "s16",
        "-",
    ]
    if stereo and shutil.which("ffmpeg"):
        ff = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "s16le",
            "-ar",
            str(rate),
            "-ac",
            str(channels),
            "-i",
            "pipe:0",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-f",
            "s16le",
            "pipe:1",
        ]
        return pw, ff
    if rate != 16000 or channels != 1:
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg required to resample capture for Gemini Live")
        ff = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "s16le",
            "-ar",
            str(rate),
            "-ac",
            str(channels),
            "-i",
            "pipe:0",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-f",
            "s16le",
            "pipe:1",
        ]
        return pw, ff
    return pw, None


class GeminiLiveServerAudio:
    """PipeWire capture → Gemini upstream; Gemini audio → PipeWire playback.

    Half-duplex: mic frames are dropped while the assistant is speaking so
    pw-record does not feed Gemini its own pw-play output (echo loop).
    """

    def __init__(self) -> None:
        self._capture_pw: asyncio.subprocess.Process | None = None
        self._capture_ff: asyncio.subprocess.Process | None = None
        self._play_proc: subprocess.Popen | None = None
        self._play_rate = 24000
        self._stopped = False
        self._lock = threading.Lock()
        self._speaking_until = 0.0
        self._tail_sec = _playback_tail_sec()
        self._dropped_while_speaking = 0

    def _mic_open(self) -> bool:
        with self._lock:
            return time.monotonic() >= self._speaking_until

    def _extend_speaking(self, pcm_bytes: int, rate: int) -> None:
        if pcm_bytes <= 0 or rate <= 0:
            return
        duration = pcm_bytes / (rate * 2)
        with self._lock:
            now = time.monotonic()
            self._speaking_until = max(self._speaking_until, now + duration + self._tail_sec)

    async def start_capture(self, send_audio_b64) -> None:
        pw_cmd, ff_cmd = _capture_cmd()
        if ff_cmd:
            pipeline = (
                " ".join(shlex.quote(x) for x in pw_cmd[:-1])
                + " - | "
                + " ".join(shlex.quote(x) for x in ff_cmd)
            )
            self._capture_pw = await asyncio.create_subprocess_shell(
                pipeline,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            read_stdout = self._capture_pw.stdout
        else:
            self._capture_pw = await asyncio.create_subprocess_exec(
                *pw_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            read_stdout = self._capture_pw.stdout

        if not read_stdout:
            raise RuntimeError("capture pipeline failed to start")

        log.info("Gemini Live server mic capture started (half-duplex tail=%.2fs)", self._tail_sec)
        while not self._stopped:
            chunk = await read_stdout.read(_CHUNK_BYTES)
            if not chunk:
                break
            if not self._mic_open():
                self._dropped_while_speaking += 1
                continue
            await send_audio_b64(base64.b64encode(chunk).decode("ascii"))

    def _ensure_player(self, rate: int) -> None:
        if self._play_proc and self._play_proc.poll() is None and self._play_rate == rate:
            return
        self._stop_player()
        self._play_rate = rate
        self._play_proc = subprocess.Popen(
            ["pw-play", "--rate", str(rate), "--channels", "1", "--format", "s16", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def play_pcm_b64(self, data_b64: str, *, rate: int = 24000) -> None:
        if not server_playback_enabled():
            return
        try:
            pcm = base64.b64decode(data_b64)
            if not pcm:
                return
            self._extend_speaking(len(pcm), rate)
            self._ensure_player(rate)
            if self._play_proc and self._play_proc.stdin:
                self._play_proc.stdin.write(pcm)
                self._play_proc.stdin.flush()
        except Exception as exc:
            log.debug("Gemini Live server playback: %s", exc)

    def stop_playback(self) -> None:
        """Stop speaker output and keep mic muted briefly (interrupt / barge-in)."""
        with self._lock:
            self._speaking_until = time.monotonic() + self._tail_sec
        self._stop_player()

    def _stop_player(self) -> None:
        proc = self._play_proc
        self._play_proc = None
        if not proc:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
            proc.wait(timeout=1)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    async def stop(self) -> None:
        self._stopped = True
        self._stop_player()
        proc = self._capture_pw
        self._capture_pw = None
        self._capture_ff = None
        if not proc:
            return
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
