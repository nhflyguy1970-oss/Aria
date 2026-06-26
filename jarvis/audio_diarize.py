"""Speaker diarization — pyannote (optional) or segment clustering fallback."""

from __future__ import annotations

import os
from pathlib import Path


def pyannote_available() -> bool:
    try:
        import pyannote.audio  # noqa: F401
        return True
    except ImportError:
        return False


def hf_token() -> str:
    """HF token from env or huggingface-cli login cache."""
    for key in ("HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        val = os.getenv(key, "").strip()
        if val:
            return val
    try:
        from huggingface_hub import get_token

        return (get_token() or "").strip()
    except Exception:
        return ""


def hf_token_configured() -> bool:
    return bool(hf_token())


def diarize_status() -> dict:
    token = hf_token_configured()
    return {
        "pyannote": pyannote_available(),
        "hf_token": token,
        "engine": "pyannote" if pyannote_available() and token else "whisper-gaps",
        "model": os.getenv("JARVIS_DIARIZE_MODEL", "pyannote/speaker-diarization-3.1"),
        "hint": "" if token else "Set HF_TOKEN in data/jarvis.env or run scripts/set-hf-token.sh",
    }


def diarize(path: str | Path, *, num_speakers: int | None = None) -> dict:
    """Return labeled segments [{speaker, start, end, text?}]."""
    path = Path(path)
    if not path.exists():
        return {"ok": False, "error": f"File not found: {path}"}

    token = hf_token()
    if pyannote_available() and token:
        try:
            return _diarize_pyannote(path, token, num_speakers=num_speakers)
        except Exception as e:
            err = str(e)
            if "gated" in err.lower() or "401" in err or "403" in err:
                return {
                    "ok": False,
                    "error": "HF model access denied — accept terms at huggingface.co/pyannote/speaker-diarization-3.1",
                    "hint": diarize_status()["hint"],
                }
            pass  # fall through to whisper-gaps

    return _diarize_whisper_segments(path, num_speakers=num_speakers)


def _diarize_pyannote(path: Path, token: str, *, num_speakers: int | None) -> dict:
    from pyannote.audio import Pipeline

    model_id = os.getenv("JARVIS_DIARIZE_MODEL", "pyannote/speaker-diarization-3.1")
    pipeline = Pipeline.from_pretrained(model_id, token=token)
    if pipeline is None:
        raise RuntimeError(f"Could not load diarization model: {model_id}")
    import torch

    from jarvis.torch_device import torch_device
    if torch_device() == "cuda" and torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))
    if num_speakers:
        diar = pipeline(str(path), num_speakers=num_speakers)
    else:
        diar = pipeline(str(path))
    segments = []
    for turn, _, speaker in diar.itertracks(yield_label=True):
        segments.append({
            "speaker": speaker,
            "start": round(turn.start, 2),
            "end": round(turn.end, 2),
        })
    labeled = _merge_whisper_speakers(path, segments)
    return {
        "ok": True,
        "engine": "pyannote",
        "segments": labeled,
        "transcript": _format_diarized(labeled),
    }


def _speaker_at_time(segments: list[dict], t: float) -> str:
    for seg in segments:
        if seg["start"] <= t <= seg["end"]:
            return seg["speaker"]
    best, best_dist = segments[0]["speaker"] if segments else "Speaker A", 1e9
    for seg in segments:
        mid = (seg["start"] + seg["end"]) / 2
        dist = abs(t - mid)
        if dist < best_dist:
            best_dist = dist
            best = seg["speaker"]
    return best


def _merge_whisper_speakers(path: Path, diar_segments: list[dict]) -> list[dict]:
    """Attach whisper text to pyannote speaker segments."""
    from jarvis.audio_whisper import transcribe_segments

    if not diar_segments:
        return diar_segments
    labeled: list[dict] = []
    for seg in transcribe_segments(path):
        if seg.get("final"):
            continue
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = float(seg.get("start", 0))
        end = float(seg.get("end", start))
        mid = (start + end) / 2
        labeled.append({
            "speaker": _speaker_at_time(diar_segments, mid),
            "start": round(start, 2),
            "end": round(end, 2),
            "text": text,
        })
    if labeled:
        return labeled
    return diar_segments


def _diarize_whisper_segments(path: Path, *, num_speakers: int | None) -> dict:
    """Label speakers by alternating clusters on pause gaps (lightweight fallback)."""
    from jarvis.audio_whisper import transcribe_segments

    raw_segments = list(transcribe_segments(path))
    if not raw_segments:
        return {"ok": False, "error": "No speech detected"}

    labeled = []
    speaker_idx = 0
    last_end = 0.0
    gap_threshold = float(os.getenv("JARVIS_DIARIZE_GAP_SEC", "1.2"))
    for seg in raw_segments:
        if seg.get("final"):
            continue
        start = float(seg.get("start", 0))
        if start - last_end > gap_threshold:
            speaker_idx = (speaker_idx + 1) % max(2, num_speakers or 2)
        labeled.append({
            "speaker": f"Speaker {chr(65 + (speaker_idx % 26))}",
            "start": start,
            "end": float(seg.get("end", start)),
            "text": seg.get("text", ""),
        })
        last_end = float(seg.get("end", start))

    " ".join(s["text"] for s in labeled if s.get("text"))
    formatted = _format_diarized(labeled)
    return {
        "ok": True,
        "engine": "whisper-gaps",
        "segments": labeled,
        "transcript": formatted,
        "hint": "Install pyannote.audio + HF_TOKEN for accurate diarization" if not pyannote_available() else "",
    }


def _format_diarized(segments: list[dict]) -> str:
    lines = []
    cur_sp = None
    buf: list[str] = []
    for s in segments:
        sp = s.get("speaker", "?")
        txt = s.get("text", "").strip()
        if not txt:
            continue
        if sp != cur_sp:
            if buf and cur_sp:
                lines.append(f"**{cur_sp}:** {' '.join(buf)}")
            cur_sp = sp
            buf = [txt]
        else:
            buf.append(txt)
    if buf and cur_sp:
        lines.append(f"**{cur_sp}:** {' '.join(buf)}")
    return "\n\n".join(lines)
