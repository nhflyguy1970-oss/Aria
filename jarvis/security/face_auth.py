# Source Generated with Decompyle++
# File: face_auth.cpython-312.pyc (Python 3.12)

'''Face auth — optional MediaPipe; histogram fallback.'''
from __future__ import annotations
import base64
import json
import struct
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.p4_flags import face_auth_enabled
FACE_FILE = DATA_DIR / 'security' / 'face_profile.json'
FACE_IMG = DATA_DIR / 'security' / 'face_enroll.jpg'

def _mediapipe_available():
    
    try:
        import mediapipe
        return True
    except ImportError:
        return False



def face_status():
    return {
        'enabled': face_auth_enabled(),
        'enrolled': FACE_FILE.is_file(),
        'mediapipe': _mediapipe_available() }


def _decode_image_b64(data = None):
    if not data:
        data
    raw = ''.strip()
    if ',' in raw:
        raw = raw.split(',', 1)[1]
    return base64.b64decode(raw)


def _mediapipe_fingerprint(img_bytes = None):
    if not _mediapipe_available():
        return None
# WARNING: Decompyle incomplete


def _histogram_fingerprint(img_bytes = None):
    pass
# WARNING: Decompyle incomplete


def _compare(a = None, b = None):
    pass
# WARNING: Decompyle incomplete


def enroll_face(image_b64 = None):
    if not face_auth_enabled():
        return {
            'ok': False,
            'error': 'Face auth disabled' }
    img = None(image_b64)
    mp_fp = _mediapipe_fingerprint(img)
    if not mp_fp:
        mp_fp
    fp = _histogram_fingerprint(img)
    method = 'mediapipe' if mp_fp else 'histogram'
    FACE_FILE.parent.mkdir(parents = True, exist_ok = True)
    FACE_FILE.write_text(json.dumps({
        'fingerprint': fp,
        'method': method }, indent = 2), encoding = 'utf-8')
    FACE_IMG.write_bytes(img)
    return {
        'ok': True,
        'enrolled': True,
        'method': method }


def verify_face(image_b64 = None, *, threshold):
    if not face_auth_enabled():
        return {
            'ok': False,
            'error': 'Face auth disabled' }
    if not None.is_file():
        return {
            'ok': False,
            'error': 'Face not enrolled' }
    
    try:
        ref = json.loads(FACE_FILE.read_text(encoding = 'utf-8'))
        img = _decode_image_b64(image_b64)
        mp_fp = _mediapipe_fingerprint(img)
        if not mp_fp:
            mp_fp
        fp = _histogram_fingerprint(img)
        if not ref.get('method'):
            ref.get('method')
        method = 'histogram'
        if not ref.get('fingerprint'):
            ref.get('fingerprint')
        ref_fp = []
        if method == 'mediapipe':
            if mp_fp:
                score = _compare(ref_fp, mp_fp)
                match_threshold = 0.82
            elif not _mediapipe_available():
                if not FACE_IMG.is_file():
                    return {
                        'ok': False,
                        'error': 'Face enrolled with MediaPipe but MediaPipe is unavailable — re-enroll face',
                        'method': method }
                ref_hist = None(FACE_IMG.read_bytes())
                cand_hist = _histogram_fingerprint(img)
                score = _compare(ref_hist, cand_hist)
                match_threshold = threshold
                method = 'histogram_fallback'
            else:
                return {
                    'ok': False,
                    'error': 'No face detected',
                    'method': method }
            score = None(ref_fp, fp)
            match_threshold = threshold
            return {
                'ok': score >= match_threshold,
                'score': round(score, 3),
                'match': score >= match_threshold,
                'method': method }
        except (json.JSONDecodeError, OSError):
            return 


