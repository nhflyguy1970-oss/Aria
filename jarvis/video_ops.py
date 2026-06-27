"""FFmpeg helpers for Jarvis Video studio."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from jarvis.config import DATA_DIR
from jarvis.vision_media import VIDEO_EXTENSIONS

VIDEO_OUTPUT_DIR = DATA_DIR / "generated_videos"
VIDEO_UPLOAD_DIR = DATA_DIR / "videos"


def ensure_dirs() -> None:
    VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _ffmpeg() -> str | None:
    import shutil
    return shutil.which("ffmpeg")


def _ffprobe() -> str | None:
    import shutil
    return shutil.which("ffprobe")


def probe(path: str | Path) -> dict:
    """Return duration, width, height, fps for a video file."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return {"ok": False, "error": f"Not found: {p}"}
    ffprobe = _ffprobe()
    if not ffprobe:
        return {"ok": False, "error": "ffprobe not installed"}
    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(p),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            return {"ok": False, "error": (proc.stderr or proc.stdout or "ffprobe failed").strip()}
        data = json.loads(proc.stdout or "{}")
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError) as e:
        return {"ok": False, "error": str(e)}

    duration = float(data.get("format", {}).get("duration") or 0)
    width = height = fps = 0.0
    for stream in data.get("streams", []):
        if stream.get("codec_type") != "video":
            continue
        width = int(stream.get("width") or 0)
        height = int(stream.get("height") or 0)
        rate = stream.get("r_frame_rate") or stream.get("avg_frame_rate") or "0/1"
        if "/" in str(rate):
            num, den = str(rate).split("/", 1)
            fps = float(num) / float(den or 1) if float(den or 1) else 0.0
        else:
            fps = float(rate or 0)
        break
    return {
        "ok": True,
        "path": str(p),
        "name": p.name,
        "duration": round(duration, 3),
        "width": width,
        "height": height,
        "fps": round(fps, 3),
    }


def trim(path: str | Path, start: float, end: float | None = None, duration: float | None = None) -> str:
    """Trim video to [start, end) or start+duration. Returns output path or ERROR:."""
    src = Path(path).expanduser().resolve()
    if not src.is_file():
        return f"ERROR: Not found: {src}"
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        return "ERROR: ffmpeg not installed"
    start = max(0.0, float(start))
    if end is not None:
        length = max(0.1, float(end) - start)
    elif duration is not None:
        length = max(0.1, float(duration))
    else:
        return "ERROR: Provide end time or duration"
    ensure_dirs()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = VIDEO_OUTPUT_DIR / f"trim_{src.stem}_{stamp}.mp4"
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-ss", str(start), "-i", str(src), "-t", str(length),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not out.exists():
        err = (proc.stderr or proc.stdout or "trim failed").strip()
        return f"ERROR: {err[:300]}"
    return str(out)


def _remux_mp4_web(src: Path, out: Path) -> bool:
    """Copy/re-encode to browser-friendly MP4 (yuv420p, faststart moov atom)."""
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        import shutil
        try:
            shutil.copy2(src, out)
            return out.is_file()
        except OSError:
            return False
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", str(src),
        "-c:v", "libx264", "-profile:v", "main", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "20",
        "-movflags", "+faststart",
        "-an",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return proc.returncode == 0 and out.is_file()


def ensure_mp4(path: str | Path) -> str:
    """Return an MP4 path, converting GIF/WebP via ffmpeg when needed."""
    src = Path(path).expanduser().resolve()
    if not src.is_file():
        return f"ERROR: Not found: {src}"
    if src.suffix.lower() == ".mp4":
        stamp = time.strftime("%Y%m%d_%H%M%S")
        if "generated_videos" in str(src.parent):
            ensure_webm(src)
            return str(src)
        out = VIDEO_OUTPUT_DIR / f"motion_{src.stem}_{stamp}.mp4"
        ensure_dirs()
        if not _remux_mp4_web(src, out):
            return f"ERROR: Could not prepare MP4 for playback"
        ensure_webm(out)
        return str(out)
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        return f"ERROR: ffmpeg not installed (needed to convert {src.suffix})"
    ensure_dirs()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = VIDEO_OUTPUT_DIR / f"motion_{src.stem}_{stamp}.mp4"
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", str(src),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-profile:v", "main",
        "-preset", "fast", "-crf", "20", "-movflags", "+faststart",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not out.exists():
        err = (proc.stderr or proc.stdout or "mp4 convert failed").strip()
        return f"ERROR: {err[:300]}"
    ensure_webm(out)
    return str(out)


def image_to_motion_video(
    image_path: str | Path,
    *,
    duration: float = 4.0,
    fps: int = 8,
    width: int = 768,
    height: int = 768,
) -> str:
    """Ken-burns style motion clip from a still image (low VRAM)."""
    src = Path(image_path).expanduser().resolve()
    if not src.is_file():
        return f"ERROR: Not found: {src}"
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        return "ERROR: ffmpeg not installed"
    ensure_dirs()
    duration = min(max(2.0, float(duration)), 12.0)
    fps = min(max(6, int(fps)), 16)
    frames = int(duration * fps)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = VIDEO_OUTPUT_DIR / f"motion_{src.stem}_{stamp}.mp4"
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='min(zoom+0.0012,1.25)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height},fps={fps}"
    )
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(src), "-vf", vf,
        "-t", str(duration), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-profile:v", "main",
        "-preset", "fast", "-crf", "20", "-movflags", "+faststart",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not out.exists():
        err = (proc.stderr or proc.stdout or "motion encode failed").strip()
        return f"ERROR: {err[:300]}"
    ensure_webm(out)
    return str(out)


def storyboard_ken_burns(
    image_paths: list[str | Path],
    *,
    sec_per_slide: float = 3.5,
    width: int = 768,
    height: int = 768,
) -> str:
    """Concatenate Ken Burns clips from multiple stills (8GB-safe storyboard)."""
    paths = [Path(p).expanduser().resolve() for p in image_paths if str(p).strip()]
    paths = [p for p in paths if p.is_file()]
    if not paths:
        return "ERROR: No valid image paths for storyboard"
    if len(paths) > 12:
        paths = paths[:12]
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        return "ERROR: ffmpeg not installed"
    ensure_dirs()
    clips: list[Path] = []
    for i, src in enumerate(paths):
        clip = image_to_motion_video(
            src,
            duration=sec_per_slide,
            width=width,
            height=height,
        )
        if clip.startswith("ERROR:"):
            for c in clips:
                try:
                    c.unlink(missing_ok=True)
                except OSError:
                    pass
            return clip
        clips.append(Path(clip))
    if len(clips) == 1:
        return str(clips[0])
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = VIDEO_OUTPUT_DIR / f"storyboard_{stamp}.mp4"
    list_file = VIDEO_OUTPUT_DIR / f"storyboard_{stamp}.txt"
    try:
        lines = [f"file '{c}'" for c in clips]
        list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0 or not out.is_file():
            err = (proc.stderr or proc.stdout or "concat failed").strip()
            return f"ERROR: {err[:300]}"
        return str(out)
    finally:
        try:
            list_file.unlink(missing_ok=True)
        except OSError:
            pass


def ensure_webm(mp4_path: str | Path) -> str:
    """VP9 WebM sidecar for in-app playback (Qt WebEngine often cannot decode H.264)."""
    src = Path(mp4_path).expanduser().resolve()
    if not src.is_file():
        return f"ERROR: Not found: {src}"
    if src.suffix.lower() != ".mp4":
        return f"ERROR: WebM sidecar requires MP4 source"
    out = src.with_suffix(".webm")
    if out.is_file() and out.stat().st_mtime >= src.stat().st_mtime:
        return str(out)
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        return f"ERROR: ffmpeg not installed (needed for WebM playback)"
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", str(src),
        "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0",
        "-row-mt", "1", "-an",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not out.is_file():
        err = (proc.stderr or proc.stdout or "webm convert failed").strip()
        return f"ERROR: {err[:300]}"
    return str(out)


def list_videos(limit: int = 50) -> list[dict]:
    ensure_dirs()
    files: list[Path] = []
    for root in (VIDEO_OUTPUT_DIR, VIDEO_UPLOAD_DIR):
        if root.exists():
            files.extend(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    names = {p.name for p in files}
    shown: list[Path] = []
    for path in files:
        if path.suffix.lower() == ".webm" and path.with_suffix(".mp4").name in names:
            continue
        shown.append(path)
    return [{"name": f.name, "path": str(f)} for f in shown[:limit]]


def safe_video_name(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", Path(name).name)[:200]
