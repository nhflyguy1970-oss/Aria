"""Face auth — optional MediaPipe; histogram fallback."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.p4_flags import face_auth_enabled

FACE_FILE = DATA_DIR / "security" / "face_profile.json"
FACE_IMG = DATA_DIR / "security" / "face_enroll.jpg"


def _mediapipe_available() -> bool:
    try:
        import mediapipe  # noqa: F401

        return True
    except ImportError:
        return False


def face_status() -> dict[str, Any]:
    return {
        "enabled": face_auth_enabled(),
        "enrolled": FACE_FILE.is_file(),
        "mediapipe": _mediapipe_available(),
    }


def _decode_image_b64(data: str | None) -> bytes:
    raw = (data or "").strip()
    if "," in raw:
        raw = raw.split(",", 1)[1]
    return base64.b64decode(raw)


def _histogram_fingerprint(img_bytes: bytes) -> list[float]:
    if not img_bytes:
        return [0.0] * 16
    hist = [0] * 16
    step = max(1, len(img_bytes) // 4096)
    for b in img_bytes[::step]:
        hist[b % 16] += 1
    total = sum(hist) or 1
    return [h / total for h in hist]


def _mediapipe_fingerprint(img_bytes: bytes) -> list[float] | None:
    if not _mediapipe_available():
        return None
    try:
        import mediapipe as mp
        import numpy as np

        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        # JPEG/PNG decode via cv2 if available
        try:
            import cv2

            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                return None
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception:
            return None
        with mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) as mesh:
            results = mesh.process(rgb)
            if not results.multi_face_landmarks:
                return None
            pts = results.multi_face_landmarks[0].landmark
            return [round(p.x, 4) for p in pts[:32]] + [round(p.y, 4) for p in pts[:32]]
    except Exception:
        return None


def _compare(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    diff = sum((float(a[i]) - float(b[i])) ** 2 for i in range(n))
    return max(0.0, 1.0 - diff**0.5)


def enroll_face(image_b64: str | None) -> dict[str, Any]:
    if not face_auth_enabled():
        return {"ok": False, "error": "Face auth disabled (set JARVIS_FACE_AUTH=1)"}
    try:
        img = _decode_image_b64(image_b64)
    except Exception as exc:
        return {"ok": False, "error": f"Invalid image data: {exc}"}
    if len(img) < 100:
        return {"ok": False, "error": "Image too small"}
    mp_fp = _mediapipe_fingerprint(img)
    fp = mp_fp if mp_fp else _histogram_fingerprint(img)
    method = "mediapipe" if mp_fp else "histogram"
    FACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    FACE_FILE.write_text(json.dumps({"fingerprint": fp, "method": method}, indent=2), encoding="utf-8")
    FACE_IMG.write_bytes(img)
    return {"ok": True, "enrolled": True, "method": method}


def verify_face(image_b64: str | None, *, threshold: float = 0.75) -> dict[str, Any]:
    if not face_auth_enabled():
        return {"ok": False, "error": "Face auth disabled"}
    if not FACE_FILE.is_file():
        return {"ok": False, "error": "Face not enrolled"}
    try:
        ref = json.loads(FACE_FILE.read_text(encoding="utf-8"))
        img = _decode_image_b64(image_b64)
        method = ref.get("method") or "histogram"
        ref_fp = list(ref.get("fingerprint") or [])
        mp_fp = _mediapipe_fingerprint(img)
        if method == "mediapipe" and mp_fp:
            score = _compare(ref_fp, mp_fp)
            match_threshold = 0.82
        elif method == "mediapipe" and not _mediapipe_available() and FACE_IMG.is_file():
            ref_hist = _histogram_fingerprint(FACE_IMG.read_bytes())
            cand_hist = _histogram_fingerprint(img)
            score = _compare(ref_hist, cand_hist)
            match_threshold = threshold
            method = "histogram_fallback"
        else:
            fp = mp_fp if mp_fp else _histogram_fingerprint(img)
            if method == "mediapipe" and not mp_fp:
                return {"ok": False, "error": "No face detected", "method": method}
            score = _compare(ref_fp, fp)
            match_threshold = threshold if method == "histogram" else 0.82
        matched = score >= match_threshold
        return {
            "ok": matched,
            "score": round(score, 3),
            "match": matched,
            "method": method,
        }
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": str(exc)}
