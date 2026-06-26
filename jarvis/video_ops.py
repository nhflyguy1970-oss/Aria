# Source Generated with Decompyle++
# File: video_ops.cpython-312.pyc (Python 3.12)

'''FFmpeg helpers for Jarvis Video studio.'''
from __future__ import annotations
import json
import os
import re
import subprocess
import time
from pathlib import Path
from jarvis.config import DATA_DIR
from jarvis.vision_media import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
VIDEO_OUTPUT_DIR = DATA_DIR / 'generated_videos'
VIDEO_UPLOAD_DIR = DATA_DIR / 'videos'
_STORYBOARD_IMAGE_EXTS = IMAGE_EXTENSIONS

def ensure_dirs():
    VIDEO_OUTPUT_DIR.mkdir(parents = True, exist_ok = True)
    VIDEO_UPLOAD_DIR.mkdir(parents = True, exist_ok = True)


def _ffmpeg():
    import shutil
    return shutil.which('ffmpeg')


def _ffprobe():
    import shutil
    return shutil.which('ffprobe')


def probe(path = None):
    '''Return duration, width, height, fps for a video file.'''
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return {
            'ok': False,
            'error': f'''Not found: {p}''' }
    ffprobe = None()
    if not ffprobe:
        return {
            'ok': False,
            'error': 'ffprobe not installed' }
    cmd = [
        None,
        '-v',
        'quiet',
        '-print_format',
        'json',
        '-show_format',
        '-show_streams',
        str(p)]
    
    try:
        proc = subprocess.run(cmd, capture_output = True, text = True, timeout = 60)
        if proc.returncode != 0:
            if not proc.stderr:
                proc.stderr
                if not proc.stdout:
                    proc.stdout
            return {
                'ok': False,
                'error': 'ffprobe failed'.strip() }
        if not proc.stdout:
            proc.stdout
        data = None.loads('{}')
        if not data.get('format', { }).get('duration'):
            data.get('format', { }).get('duration')
        duration = float(0)
        width = 0
        height = 0
        fps = 0
        for stream in data.get('streams', []):
            if stream.get('codec_type') != 'video':
                continue
            if not stream.get('width'):
                stream.get('width')
            width = int(0)
            if not stream.get('height'):
                stream.get('height')
            height = int(0)
            if not stream.get('r_frame_rate'):
                stream.get('r_frame_rate')
                if not stream.get('avg_frame_rate'):
                    stream.get('avg_frame_rate')
            rate = '0/1'
            if '/' in str(rate):
                (num, den) = str(rate).split('/', 1)
                if not den:
                    den
                fps = float(num) / float(1) if float(1) else 0
            elif not rate:
                rate
            fps = float(0)
            data.get('streams', [])
        return {
            'ok': True,
            'path': str(p),
            'name': p.name,
            'duration': round(duration, 3),
            'width': width,
            'height': height,
            'fps': round(fps, 3) }
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError):
        e = None
        del e
        return None
        None = 
        del e



def trim(path = None, start = None, end = None, duration = (None, None)):
    '''Trim video to [start, end) or start+duration. Returns output path or ERROR:.'''
    src = Path(path).expanduser().resolve()
    if not src.is_file():
        return f'''ERROR: Not found: {src}'''
    ffmpeg = None()
    if not ffmpeg:
        return 'ERROR: ffmpeg not installed'
    start = max(0, float(start))
# WARNING: Decompyle incomplete


def ensure_mp4(path = None):
    '''Return an MP4 path, converting GIF/WebP via ffmpeg when needed.'''
    src = Path(path).expanduser().resolve()
    if not src.is_file():
        return f'''ERROR: Not found: {src}'''
    if None.suffix.lower() == '.mp4':
        stamp = time.strftime('%Y%m%d_%H%M%S')
        if 'generated_videos' in str(src.parent):
            return str(src)
        out = None / f'''motion_{src.stem}_{stamp}.mp4'''
        ensure_dirs()
        import shutil
        shutil.copy2(src, out)
        return str(out)
    ffmpeg = None()
    if not ffmpeg:
        return f'''ERROR: ffmpeg not installed (needed to convert {src.suffix})'''
    None()
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = VIDEO_OUTPUT_DIR / f'''motion_{src.stem}_{stamp}.mp4'''
    cmd = [
        ffmpeg,
        '-y',
        '-loglevel',
        'error',
        '-i',
        str(src),
        '-pix_fmt',
        'yuv420p',
        '-c:v',
        'libx264',
        '-preset',
        'fast',
        '-crf',
        '20',
        str(out)]
    proc = subprocess.run(cmd, capture_output = True, text = True, timeout = 300)
    if not proc.returncode != 0 or out.exists():
        if not proc.stderr:
            proc.stderr
            if not proc.stdout:
                proc.stdout
        err = 'mp4 convert failed'.strip()
        return f'''ERROR: {err[:300]}'''
    return None(out)


def image_to_motion_video(image_path = None, *, duration, fps, width, height):
    '''Ken-burns style motion clip from a still image (low VRAM).'''
    src = Path(image_path).expanduser().resolve()
    if not src.is_file():
        return f'''ERROR: Not found: {src}'''
    ffmpeg = None()
    if not ffmpeg:
        return 'ERROR: ffmpeg not installed'
    ensure_dirs()
    duration = min(max(2, float(duration)), 12)
    fps = min(max(6, int(fps)), 16)
    frames = int(duration * fps)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = VIDEO_OUTPUT_DIR / f'''motion_{src.stem}_{stamp}.mp4'''
    vf = f'''scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,zoompan=z=\'min(zoom+0.0012,1.25)\':d={frames}:x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':s={width}x{height},fps={fps}'''
    cmd = [
        ffmpeg,
        '-y',
        '-loglevel',
        'error',
        '-loop',
        '1',
        '-i',
        str(src),
        '-vf',
        vf,
        '-t',
        str(duration),
        '-pix_fmt',
        'yuv420p',
        '-c:v',
        'libx264',
        '-preset',
        'fast',
        '-crf',
        '20',
        str(out)]
    proc = subprocess.run(cmd, capture_output = True, text = True, timeout = 300)
    if not proc.returncode != 0 or out.exists():
        if not proc.stderr:
            proc.stderr
            if not proc.stdout:
                proc.stdout
        err = 'motion encode failed'.strip()
        return f'''ERROR: {err[:300]}'''
    return None(out)


def resolve_storyboard_image(raw = None):
    '''Resolve a gallery/chat path to an on-disk image for storyboard builds.'''
    PROJECT_ROOT = PROJECT_ROOT
    import jarvis.config
    if not raw:
        raw
    text = ''.strip()
    if not text:
        return None
    p = Path(text).expanduser()
    candidates = []
    if p.is_absolute():
        candidates.append(p.resolve())
    else:
        norm = text.replace('\\', '/').lstrip('/')
        if norm.startswith('data/'):
            candidates.append((PROJECT_ROOT / norm).resolve())
        candidates.append((DATA_DIR / norm).resolve())
        candidates.append((DATA_DIR / 'generated' / norm).resolve())
        candidates.append((DATA_DIR / 'generated' / 'memes' / norm).resolve())
        candidates.append((DATA_DIR / 'uploads' / norm).resolve())
        if '/' in norm:
            candidates.append((DATA_DIR / 'generated' / Path(norm).name).resolve())
        candidates.append((DATA_DIR / 'generated' / p.name).resolve())
        candidates.append((DATA_DIR / 'generated' / 'memes' / p.name).resolve())
        candidates.append((DATA_DIR / 'uploads' / p.name).resolve())
    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file() and candidate.suffix.lower() in _STORYBOARD_IMAGE_EXTS:
            
            return candidates, candidate
    return None
    except OSError:
        continue


def resolve_storyboard_images(raw_paths = None):
    '''Resolve user-supplied image references (paths, basenames, gallery subdirs).'''
    resolved = []
    for raw in raw_paths:
        path = resolve_storyboard_image(raw)
        if not path:
            continue
        resolved.append(str(path))
    return resolved


def storyboard_ken_burns(image_paths = None, *, sec_per_slide, width, height):
    '''Concatenate Ken Burns clips from multiple stills (8GB-safe storyboard).'''
    pass
# WARNING: Decompyle incomplete


def list_videos(limit = None):
    ensure_dirs()
    files = []
    for root in (VIDEO_OUTPUT_DIR, VIDEO_UPLOAD_DIR):
        if not root.exists():
            continue
        (lambda .0: pass# WARNING: Decompyle incomplete
)(root.iterdir()())
    files.sort(key = (lambda p: p.stat().st_mtime), reverse = True)
# WARNING: Decompyle incomplete


def safe_video_name(name = None):
    return re.sub('[^\\w.\\-]+', '_', Path(name).name)[:200]

