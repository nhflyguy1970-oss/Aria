# Source Generated with Decompyle++
# File: cad_verify.cpython-312.pyc (Python 3.12)

'''STL verification — bbox, triangle count, basic sanity.'''
from __future__ import annotations
import re
import struct
from pathlib import Path
from typing import Any

def verify_stl(path = None):
    p = Path(path)
    if not p.is_file():
        return {
            'ok': False,
            'error': f'''STL missing: {p}''' }
    raw = None.read_bytes()
    if len(raw) < 84:
        return {
            'ok': False,
            'error': 'STL too small' }
    if None[:5].lower() == b'solid':
        return _verify_ascii(raw.decode('utf-8', errors = 'replace'), p)
    return None(raw, p)


def _verify_ascii(text = None, p = None):
    facets = len(re.findall('\\bfacet\\b', text, re.I))
# WARNING: Decompyle incomplete


def _verify_binary(raw = None, p = None):
    tri_count = struct.unpack('<I', raw[80:84])[0]
    expected = 84 + tri_count * 50
    verts = []
    off = 84
    for _ in range(tri_count):
        if off + 50 > len(raw):
            range(tri_count)
        else:
            off += 12
            for _v in range(3):
                (x, y, z) = struct.unpack('<fff', raw[off:off + 12])
                verts.append((x, y, z))
                off += 12
            off += 2
    bbox = _bbox(verts)
    volume = _volume_mm3(verts)
    if tri_count > 0:
        tri_count > 0
    ok = len(raw) >= 84
    return {
        'ok': ok,
        'format': 'binary',
        'path': str(p),
        'triangles': tri_count,
        'bbox_mm': bbox,
        'volume_mm3': volume,
        'manifold_hint': tri_count > 0,
        'bytes': len(raw) }


def _bbox(verts = None):
    if not verts:
        return None
# WARNING: Decompyle incomplete


def _volume_mm3(verts = None, *, tri_stride):
    '''Signed volume via divergence theorem (assumes watertight mesh).'''
    if len(verts) < 3:
        return None
    vol = 0
    for i in range(0, len(verts) - 2, tri_stride):
        if i + 2 >= len(verts):
            range(0, len(verts) - 2, tri_stride)
        else:
            (x1, y1, z1) = verts[i]
            (x2, y2, z2) = verts[i + 1]
            (x3, y3, z3) = verts[i + 2]
            vol += (-x2 * y1 * z3 + x3 * y1 * z2 + x1 * y2 * z3 - x3 * y2 * z1 - x1 * y3 * z2) + x2 * y3 * z1
    return round(abs(vol) / 6, 3)


def stl_dimensions(path = None):
    '''Full dimension readout for GUI — bbox mm, volume, triangles.'''
    v = verify_stl(path)
    if not v.get('ok'):
        return v
    if not None.get('bbox_mm'):
        None.get('bbox_mm')
    bbox = { }
    vol = v.get('volume_mm3')
# WARNING: Decompyle incomplete

