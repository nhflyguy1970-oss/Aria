"""Route Jarvis audio playback/capture through the Creative Sound Blaster."""

import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path

# Sound Blaster AE-5 Plus / CA0132
CREATIVE_ALSA_CARD = os.getenv("JARVIS_ALSA_CARD", "Creative")
CREATIVE_ALSA_DEVICE = os.getenv("JARVIS_ALSA_DEVICE", "0")
CREATIVE_PATTERNS = (
    "creative",
    "ca0132",
    "sound blaster",
    "sound core3d",
    "ae-5",
    "recon3d",
)


def _run(cmd: list[str], timeout: int = 15, env: dict | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def _match_creative(text: str) -> bool:
    low = text.lower()
    if any(p in low for p in CREATIVE_PATTERNS):
        return True
    return "04_00.0" in low and "analog" in low


def _is_creative_input(source: str) -> bool:
    return _match_creative(source) and ".monitor" not in source


def _detect_pipewire_sink() -> str:
    env = os.getenv("JARVIS_AUDIO_SINK", "").strip()
    if env:
        return env
    code, out = _run(["pactl", "list", "short", "sinks"])
    if code != 0:
        return ""
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        _sink_id, sink_name = parts[0], parts[1]
        code2, detail = _run(["pactl", "list", "sinks"])
        if code2 == 0:
            block = ""
            for chunk in detail.split("Sink #"):
                if sink_name in chunk:
                    block = chunk
                    break
            if block and _match_creative(block):
                return sink_name
        if _match_creative(sink_name) or "04_00.0" in sink_name:
            return sink_name
    return ""


def _pulse_default_source() -> str:
    code, out = _run(["pactl", "get-default-source"])
    if code == 0:
        return out.strip()
    return ""


def list_input_sources() -> list[dict]:
    """All PipeWire/Pulse capture sources (non-monitor)."""
    code, out = _run(["pactl", "list", "short", "sources"])
    if code != 0:
        return []
    default = _pulse_default_source()
    sources: list[dict] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name = parts[1]
        if ".monitor" in name:
            continue
        state = parts[3] if len(parts) > 3 else ""
        label = name
        if "usb" in name.lower() and "mic" in name.lower():
            label = f"USB Microphone ({name.split('.')[-1]})"
        elif _is_creative_input(name):
            label = "Creative Sound Blaster (combo jack)"
        sources.append({
            "name": name,
            "label": label,
            "state": state,
            "is_default": name == default,
            "is_usb_mic": "usb" in name.lower() and "mic" in name.lower(),
        })
    return sources


def _auto_detect_input_source() -> str:
    """Prefer Creative analog line/mic; USB mics only when explicitly chosen in the GUI."""
    sources = list_input_sources()
    for s in sources:
        name = s.get("name", "")
        if _match_creative(name) and ".monitor" not in name:
            return name
    default = _pulse_default_source()
    if default and ".monitor" not in default:
        return default
    for s in sources:
        if not s.get("is_usb_mic"):
            return s["name"]
    return sources[0]["name"] if sources else ""


def effective_input_source() -> str:
    from jarvis.audio_settings import saved_input_source

    saved = saved_input_source()
    if saved:
        return saved
    env = os.getenv("JARVIS_AUDIO_SOURCE", "").strip()
    if env:
        return env
    auto = _auto_detect_input_source()
    if auto:
        return auto
    return ""


def _detect_pipewire_source() -> str:
    return effective_input_source()


def alsa_playback_device() -> str:
    env = os.getenv("JARVIS_ALSA_PLAYBACK", "").strip()
    if env:
        return env
    return f"plughw:CARD={CREATIVE_ALSA_CARD},DEV={CREATIVE_ALSA_DEVICE}"


def alsa_capture_device() -> str:
    env = os.getenv("JARVIS_ALSA_CAPTURE", "").strip()
    if env:
        return env
    return f"plughw:CARD={CREATIVE_ALSA_CARD},DEV={CREATIVE_ALSA_DEVICE}"


def detect_devices() -> dict:
    sink = _detect_pipewire_sink()
    alsa_play = alsa_playback_device()

    name = "Creative Sound Blaster"
    code, out = _run(["aplay", "-l"])
    if code == 0:
        for line in out.splitlines():
            if _match_creative(line):
                name = line.split(":", 2)[-1].strip()
                break

    backend = "pipewire" if shutil.which("pactl") else "alsa"
    if shutil.which("pw-play"):
        backend = "pipewire"

    return {
        "name": name,
        "backend": backend,
        "output_sink": sink or "alsa_output.pci-0000_04_00.0.analog-stereo",
        "input_source": _detect_pipewire_source(),
        "input_sources": list_input_sources(),
        "creative_mixer": creative_mixer_snapshot(),
        "mic_routing": mic_routing_status(),
        "alsa_playback": alsa_play,
        "alsa_capture": alsa_capture_device(),
        "auto_play": os.getenv("JARVIS_AUTO_PLAY", "1").lower() not in ("0", "false", "no"),
        "set_default_on_start": os.getenv("JARVIS_SET_DEFAULT_SINK", "1").lower() not in ("0", "false", "no"),
    }


def _should_set_default_source() -> bool:
    return os.getenv("JARVIS_SET_DEFAULT_SOURCE", "0").lower() not in ("0", "false", "no")


def creative_mixer_snapshot() -> dict:
    """Read-only Creative hardware routing (amixer sget only — never changes levels)."""
    info: dict[str, str] = {}
    for ctrl in ("Input Source", "Mic Boost", "Capture"):
        code, out = _run(["amixer", "-c", CREATIVE_ALSA_CARD, "sget", ctrl])
        if code != 0:
            continue
        for line in out.splitlines():
            if "Item0:" in line:
                info[ctrl.lower().replace(" ", "_")] = line.split(":", 1)[-1].strip().strip("'")
                break
    return info


def mic_routing_status() -> dict:
    """Compare saved mic profile to alsamixer Input Source (read-only)."""
    from jarvis.audio_settings import mic_profile_info

    profile = mic_profile_info()
    mixer = creative_mixer_snapshot()
    hardware = mixer.get("input_source", "")
    expected = profile.get("expected_input_source", "")
    if not hardware:
        return {
            "profile": profile["id"],
            "profile_label": profile["label"],
            "hardware_input_source": "",
            "routing_ok": None,
            "routing_hint": profile.get("hint", ""),
        }
    ok = hardware == expected
    hint = profile.get("hint", "")
    if not ok and hardware and expected:
        hint = (
            f"Profile is {profile['label']} but alsamixer Input Source is '{hardware}'. "
            f"Set Input Source to '{expected}' in alsamixer -c Creative (Jarvis will not change it)."
        )
    return {
        "profile": profile["id"],
        "profile_label": profile["label"],
        "hardware_input_source": hardware,
        "expected_input_source": expected,
        "mic_boost": mixer.get("mic_boost", ""),
        "routing_ok": ok,
        "routing_hint": hint,
    }


def capture_volume_for(source: str) -> str:
    """PipeWire capture gain per source (never touches ALSA mixer)."""
    from jarvis.audio_settings import (
        mic_profile_info,
        saved_capture_volume,
        saved_creative_capture_volume,
        saved_mic_profile,
    )

    if _is_creative_input(source):
        return (
            saved_creative_capture_volume()
            or os.getenv("JARVIS_CREATIVE_CAPTURE_VOLUME", "").strip()
            or mic_profile_info(saved_mic_profile()).get("default_capture_volume", "100%")
        )
    return (
        saved_capture_volume()
        or os.getenv("JARVIS_CAPTURE_VOLUME", "").strip()
        or "100%"
    )


def prepare_input_source(source: str) -> None:
    """Unmute and boost PipeWire capture volume for one source only (never opens ALSA)."""
    if not source or not shutil.which("pactl"):
        return
    _run(["pactl", "set-source-mute", source, "0"])
    _run(["pactl", "set-source-volume", source, capture_volume_for(source)])


def apply_system_default() -> str:
    """Set PipeWire default playback sink to Creative. Input source is left alone unless opted in."""
    dev = detect_devices()
    if not dev.get("set_default_on_start"):
        return "skipped (JARVIS_SET_DEFAULT_SINK=0)"

    msgs = []
    sink = dev.get("output_sink", "")

    if sink and shutil.which("pactl"):
        code, out = _run(["pactl", "set-default-sink", sink])
        if code == 0:
            msgs.append(f"default sink → {sink}")
        else:
            msgs.append(f"sink failed: {out.strip()}")

    if _should_set_default_source():
        source = dev.get("input_source", "")
        if source and shutil.which("pactl"):
            code, out = _run(["pactl", "set-default-source", source])
            if code == 0:
                msgs.append(f"default source → {source}")
            else:
                msgs.append(f"source failed: {out.strip()}")

    return "; ".join(msgs) if msgs else "no audio server found"


def play_file(path: str | Path, *, vst_chain: str | None = None) -> str:
    """Play an audio file through the Creative Sound Blaster (optional VST/EQ chain)."""
    path = Path(path)
    if not path.exists():
        return f"ERROR: File not found: {path}"

    chain = (vst_chain or "").strip().lower()
    if not chain:
        from jarvis.audio_settings import saved_vst_playback_chain

        chain = saved_vst_playback_chain() or os.getenv("JARVIS_VST_CHAIN", "").strip().lower()
    if chain and chain not in ("flat", "off", "none"):
        from jarvis.audio_vst import process_file

        processed = process_file(path, chain)
        if processed.startswith("ERROR:"):
            return processed
        path = Path(processed)

    dev = detect_devices()
    sink = dev.get("output_sink", "")
    errors: list[str] = []

    if shutil.which("pw-play") and sink:
        code, out = _run(["pw-play", "--target", sink, str(path)], timeout=600)
        if code == 0:
            return str(path)
        errors.append(f"pw-play: {out.strip()}")

    if shutil.which("paplay") and sink:
        code, out = _run(["paplay", f"--device={sink}", str(path)], timeout=600)
        if code == 0:
            return str(path)
        errors.append(f"paplay: {out.strip()}")

    if os.getenv("JARVIS_PLAYBACK_USE_ALSA", "").lower() in ("1", "true", "yes") and shutil.which("aplay"):
        alsa = dev.get("alsa_playback", alsa_playback_device())
        code, out = _run(["aplay", "-D", alsa, str(path)], timeout=600)
        if code == 0:
            return str(path)
        errors.append(f"aplay: {out.strip()}")

    return f"ERROR: Could not play audio. {' | '.join(errors)}"


def ffmpeg_env() -> dict[str, str]:
    """Environment for ffmpeg subprocesses (ALSA device hints)."""
    dev = detect_devices()
    env = os.environ.copy()
    env["AUDIODEV"] = dev.get("alsa_playback", alsa_playback_device())
    env["ALSA_PCM_CARD"] = CREATIVE_ALSA_CARD
    env["ALSA_PCM_DEVICE"] = CREATIVE_ALSA_DEVICE
    return env


def measure_levels_db(path: Path) -> dict[str, float | None]:
    """Peak and mean volume in dB from ffmpeg volumedetect."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not path.exists():
        return {"peak_db": None, "mean_db": None}
    code, out = _run(
        [ffmpeg, "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        timeout=60,
    )
    if code != 0:
        return {"peak_db": None, "mean_db": None}
    levels: dict[str, float | None] = {"peak_db": None, "mean_db": None}
    for line in out.splitlines():
        if "max_volume:" in line:
            m = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", line)
            if m:
                levels["peak_db"] = float(m.group(1))
        if "mean_volume:" in line:
            m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", line)
            if m:
                levels["mean_db"] = float(m.group(1))
    return levels


def measure_peak_db(path: Path) -> float | None:
    return measure_levels_db(path).get("peak_db")


def _speech_enhance_af(source: str) -> str:
    """ffmpeg -af chain: denoise + level speech without touching ALSA."""
    if "usb" in source.lower() and "mic" in source.lower():
        return (
            "highpass=f=150,lowpass=f=6000,"
            "afftdn=nf=-25,"
            "agate=threshold=-38dB:ratio=6:attack=12:release=180,"
            "acompressor=threshold=-24dB:ratio=3:makeup=6,"
            "loudnorm=I=-14:TP=-1:LRA=9"
        )
    if _is_creative_input(source):
        gate = os.getenv("JARVIS_CREATIVE_GATE_DB", "-34").strip() or "-34"
        nf = os.getenv("JARVIS_CREATIVE_DENOISE_NF", "-22").strip() or "-22"
        makeup = os.getenv("JARVIS_CREATIVE_MAKEUP_DB", "10").strip() or "10"
        loudness = os.getenv("JARVIS_PLAYBACK_LOUDNESS", "-14").strip() or "-14"
        return (
            "highpass=f=200,lowpass=f=5500,"
            f"afftdn=nf={nf}:nt=w,"
            f"agate=threshold={gate}dB:ratio=8:attack=8:release=180,"
            f"acompressor=threshold=-22dB:ratio=4:makeup={makeup}:attack=5:release=80,"
            f"loudnorm=I={loudness}:TP=-1:LRA=9"
        )
    return (
        "highpass=f=120,afftdn,"
        "dynaudnorm=f=120:g=12,"
        "alimiter=limit=0.92"
    )


def normalize_recording(path: Path, *, source: str = "") -> bool:
    """Denoise and level capture for playback and Whisper (in-place, software only)."""
    if os.getenv("JARVIS_RECORD_NORMALIZE", "1").lower() in ("0", "false", "no"):
        return True
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not path.exists():
        return False
    tmp = path.with_suffix(".norm.wav")
    af = _speech_enhance_af(source or effective_input_source())
    code, _ = _run(
        [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(path), "-ar", "16000", "-ac", "1", "-af", af, str(tmp),
        ],
        timeout=120,
    )
    if code == 0 and tmp.exists() and tmp.stat().st_size > 1000:
        tmp.replace(path)
        return True
    tmp.unlink(missing_ok=True)
    return False


def _silent_recording_message(source: str, peak: float, mean: float | None) -> str:
    mean_s = f", mean {mean:.1f} dB" if mean is not None else ""
    creative_hint = (
        " AE-5 combo jack: set alsamixer Input Source to Microphone (not Line In) for a mic, "
        "Mic Boost 20–30 dB, Capture unmuted."
        if _is_creative_input(source) else ""
    )
    return (
        f"ERROR: Mic level too low (peak {peak:.1f} dB{mean_s}) on `{source}`.{creative_hint}"
    )


def _finalize_recording(dest: Path, input_source: str, min_peak_db: float) -> str:
    normalize_recording(dest, source=input_source)
    levels = measure_levels_db(dest)
    peak = levels.get("peak_db")
    mean = levels.get("mean_db")
    if peak is not None and peak < min_peak_db:
        dest.unlink(missing_ok=True)
        return _silent_recording_message(input_source, peak, mean)
    return str(dest)


def _convert_to_whisper_wav(
    src: Path, dest: Path, sample_rate: int, *, source: str = "",
) -> tuple[bool, str]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False, "ffmpeg not found"
    src_name = source or effective_input_source()
    af = f"pan=mono|c0=0.5*c0+0.5*c1,{_speech_enhance_af(src_name)}"
    code, out = _run(
        [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(src),
            "-ar", str(sample_rate), "-ac", "1", "-af", af,
            str(dest),
        ],
        timeout=60,
    )
    if code != 0 or not dest.exists():
        return False, out.strip()[-400:]
    return True, str(dest)


def _use_creative_alsa_capture() -> bool:
    """Opt-in: record via arecord subprocess only — never calls amixer or changes defaults."""
    return os.getenv("JARVIS_CREATIVE_ALSA_CAPTURE", "0").lower() in ("1", "true", "yes")


def _record_alsa_arecord(
    dest: Path,
    duration_sec: float,
    *,
    sample_rate: int = 16000,
) -> tuple[bool, str]:
    """Direct card read via arecord (bypasses PipeWire node; does not touch mixer)."""
    arecord = shutil.which("arecord")
    if not arecord:
        return False, "arecord not found"
    alsa = alsa_capture_device()
    secs = max(1, int(round(duration_sec)))
    cmd = [
        arecord, "-q", "-D", alsa,
        "-f", "S16_LE", "-r", str(sample_rate), "-c", "1",
        "-d", str(secs), str(dest),
    ]
    code, out = _run(cmd, timeout=secs + 15)
    if code == 0 and dest.exists() and dest.stat().st_size > 1000:
        return True, str(dest)
    return False, out.strip()[-400:] or "arecord failed"


def _record_with_pw_record(
    dest: Path,
    duration_sec: float,
    source: str,
    *,
    sample_rate: int = 16000,
    stereo: bool = False,
) -> tuple[bool, str]:
    if not shutil.which("pw-record"):
        return False, "pw-record not available"
    tmp = dest.with_name(dest.stem + "_raw.wav")
    channels = "2" if stereo else "1"
    rate = "48000" if stereo else str(sample_rate)
    cmd = [
        "pw-record", "--target", source,
        "--rate", rate, "--channels", channels,
        "--format", "s16", str(tmp),
    ]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
    try:
        time.sleep(duration_sec)
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)
        tmp.unlink(missing_ok=True)
        return False, "pw-record timed out"
    err = (proc.stderr.read() if proc.stderr else "").strip()
    if not tmp.exists() or tmp.stat().st_size < 1000:
        tmp.unlink(missing_ok=True)
        return False, err[-400:] or "pw-record produced empty file"
    if stereo:
        ok, msg = _convert_to_whisper_wav(tmp, dest, sample_rate, source=source)
        tmp.unlink(missing_ok=True)
        return ok, msg
    if tmp != dest:
        tmp.replace(dest)
    return True, str(dest)


def record_to_file(
    dest: Path,
    duration_sec: float = 5.0,
    *,
    sample_rate: int = 16000,
    source: str | None = None,
    min_peak_db: float = -45.0,
) -> str:
    """Record via PipeWire (default). Optional arecord for Creative — never calls amixer."""
    ffmpeg = shutil.which("ffmpeg")
    if not shutil.which("pw-record") and not _use_creative_alsa_capture():
        return "ERROR: Need pw-record for PipeWire capture."

    duration_sec = max(0.5, min(float(duration_sec), 120.0))
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    input_source = (source or effective_input_source()).strip()
    if not input_source:
        return "ERROR: No capture source configured."

    errors: list[str] = []
    use_stereo = _is_creative_input(input_source)

    if _is_creative_input(input_source) and _use_creative_alsa_capture():
        ok, msg = _record_alsa_arecord(dest, duration_sec, sample_rate=sample_rate)
        if ok and dest.exists():
            return _finalize_recording(dest, input_source, min_peak_db)
        if msg:
            errors.append(f"arecord ({alsa_capture_device()}): {msg}")

    if shutil.which("pactl"):
        prepare_input_source(input_source)

    ok, msg = _record_with_pw_record(
        dest, duration_sec, input_source,
        sample_rate=sample_rate, stereo=use_stereo,
    )
    if ok and dest.exists():
        return _finalize_recording(dest, input_source, min_peak_db)
    if msg:
        errors.append(f"pw-record: {msg}")

    if ffmpeg:
        cmd = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "pulse", "-i", input_source,
            "-t", str(duration_sec),
            "-ar", str(sample_rate), "-ac", "1",
            str(dest),
        ]
        code, out = _run(cmd, timeout=int(duration_sec) + 30)
        if code == 0 and dest.exists():
            return _finalize_recording(dest, input_source, min_peak_db)
        errors.append(f"pulse ({input_source}): {out.strip()[-400:]}")

    backend = "arecord+PipeWire" if _use_creative_alsa_capture() else "PipeWire"
    return f"ERROR: Could not record from `{input_source}` ({backend}). {' | '.join(errors)}"


def probe_capture(source: str | None = None, duration_sec: float = 2.0) -> dict:
    """Short PipeWire capture test — returns levels without keeping the file."""
    import tempfile

    input_source = (source or effective_input_source()).strip()
    if not input_source:
        return {"ok": False, "message": "No capture source"}
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "probe.wav"
        result = record_to_file(dest, duration_sec, source=input_source, min_peak_db=-90)
        if result.startswith("ERROR:"):
            return {"ok": False, "message": result, "source": input_source}
        levels = measure_levels_db(dest)
        peak = levels.get("peak_db")
        return {
            "ok": True,
            "source": input_source,
            "peak_db": peak,
            "mean_db": levels.get("mean_db"),
            "pipewire_volume": capture_volume_for(input_source),
            "likely_ok": peak is not None and peak > -40,
            "mic_routing": mic_routing_status(),
        }


_active_ptt: dict[str, dict] = {}


def _ptt_record_cmd(dest: Path, source: str, *, sample_rate: int = 16000, stereo: bool = False) -> list[str]:
    channels = "2" if stereo else "1"
    rate = "48000" if stereo else str(sample_rate)
    return [
        "pw-record", "--target", source,
        "--rate", rate, "--channels", channels,
        "--format", "s16", str(dest),
    ]


def _cancel_stale_ptt_sessions() -> None:
    for sid, entry in list(_active_ptt.items()):
        proc = entry.get("proc")
        tmp = entry.get("tmp")
        try:
            if proc and proc.poll() is None:
                proc.kill()
                proc.wait(timeout=2)
        except Exception:
            pass
        if tmp and tmp.exists():
            tmp.unlink(missing_ok=True)
        _active_ptt.pop(sid, None)


def start_ptt_record(dest: Path, source: str | None = None) -> tuple[str, str]:
    """Start push-to-talk capture. Returns (session_id, error_or_empty)."""
    if not shutil.which("pw-record"):
        return "", "ERROR: pw-record not available"
    _cancel_stale_ptt_sessions()
    input_source = (source or effective_input_source()).strip()
    if not input_source:
        return "", "ERROR: No capture source configured."
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.stem + "_ptt_raw.wav")
    use_stereo = _is_creative_input(input_source)
    if shutil.which("pactl"):
        prepare_input_source(input_source)
    proc = subprocess.Popen(
        _ptt_record_cmd(tmp, input_source, stereo=use_stereo),
        stderr=subprocess.PIPE,
        text=True,
    )
    import uuid
    session_id = uuid.uuid4().hex[:12]
    _active_ptt[session_id] = {
        "proc": proc,
        "tmp": tmp,
        "dest": dest,
        "source": input_source,
        "stereo": use_stereo,
    }
    return session_id, ""


def stop_ptt_record(session_id: str, *, min_peak_db: float = -45.0) -> str:
    """Stop PTT session and finalize WAV."""
    entry = _active_ptt.pop(session_id, None)
    if not entry:
        return "ERROR: No active recording for that session."
    proc = entry["proc"]
    tmp: Path = entry["tmp"]
    dest: Path = entry["dest"]
    source: str = entry["source"]
    stereo: bool = entry["stereo"]
    try:
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
    except Exception:
        proc.kill()
    err = (proc.stderr.read() if proc.stderr else "").strip()
    if not tmp.exists() or tmp.stat().st_size < 500:
        tmp.unlink(missing_ok=True)
        return f"ERROR: Recording too short or empty. {err[-200:]}"
    if stereo:
        ok, msg = _convert_to_whisper_wav(tmp, dest, 16000, source=source)
        tmp.unlink(missing_ok=True)
        if not ok:
            return f"ERROR: {msg}"
    elif tmp != dest:
        tmp.replace(dest)
    return _finalize_recording(dest, source, min_peak_db)


def trim_silence_vad(
    src: Path,
    dst: Path | None = None,
    *,
    threshold_db: float = -40.0,
    min_silence_sec: float = 0.8,
    padding_sec: float = 0.15,
) -> str:
    """Trim leading/trailing silence after a max-duration capture."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return "ERROR: ffmpeg not found"
    src = Path(src)
    if not src.exists():
        return f"ERROR: File not found: {src}"
    out = Path(dst) if dst else src.with_name(f"{src.stem}_vad{src.suffix}")
    out.parent.mkdir(parents=True, exist_ok=True)
    thr = f"{threshold_db}dB"
    af = (
        f"silenceremove=start_periods=1:start_duration={padding_sec}:start_threshold={thr}:"
        f"stop_periods=1:stop_duration={min_silence_sec}:stop_threshold={thr}"
    )
    code, err = _run(
        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-af", af, str(out)],
        timeout=120,
        env=ffmpeg_env(),
    )
    if code != 0 or not out.exists():
        return f"ERROR: VAD trim failed: {err.strip()[-400:]}"
    if out != src:
        src.unlink(missing_ok=True)
    return str(out)
