"""STL verification — bbox, triangle count, basic sanity."""

from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import Any


def verify_stl(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        return {"ok": False, "error": f"STL missing: {p}"}
    raw = p.read_bytes()
    if len(raw) < 84:
        return {"ok": False, "error": "STL too small"}
    if raw[:5].lower() == b"solid":
        return _verify_ascii(raw.decode("utf-8", errors="replace"), p)
    return _verify_binary(raw, p)


def _verify_ascii(text: str, p: Path) -> dict[str, Any]:
    facets = len(re.findall(r"\bfacet\b", text, re.I))
    return {
        "ok": facets > 0,
        "format": "ascii",
        "path": str(p),
        "triangles": facets,
        "bbox_mm": None,
        "volume_mm3": None,
        "manifold_hint": facets > 0,
        "bytes": len(text.encode("utf-8", errors="replace")),
    }


def _verify_binary(raw: bytes, p: Path) -> dict[str, Any]:
    tri_count = struct.unpack("<I", raw[80:84])[0]
    verts: list[tuple[float, float, float]] = []
    off = 84
    for _ in range(tri_count):
        if off + 50 > len(raw):
            break
        off += 12
        for _v in range(3):
            x, y, z = struct.unpack("<fff", raw[off : off + 12])
            verts.append((x, y, z))
            off += 12
        off += 2
    bbox = _bbox(verts)
    volume = _volume_mm3(verts)
    ok = len(raw) >= 84 and tri_count > 0
    return {
        "ok": ok,
        "format": "binary",
        "path": str(p),
        "triangles": tri_count,
        "bbox_mm": bbox,
        "volume_mm3": volume,
        "manifold_hint": tri_count > 0,
        "bytes": len(raw),
    }


def _bbox(verts: list[tuple[float, float, float]]) -> dict[str, float] | None:
    if not verts:
        return None
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return {
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys),
        "z_min": min(zs),
        "z_max": max(zs),
        "x_mm": round(max(xs) - min(xs), 3),
        "y_mm": round(max(ys) - min(ys), 3),
        "z_mm": round(max(zs) - min(zs), 3),
    }


def _volume_mm3(verts: list[tuple[float, float, float]], *, tri_stride: int = 3) -> float | None:
    if len(verts) < 3:
        return None
    vol = 0.0
    for i in range(0, len(verts) - 2, tri_stride):
        if i + 2 >= len(verts):
            break
        x1, y1, z1 = verts[i]
        x2, y2, z2 = verts[i + 1]
        x3, y3, z3 = verts[i + 2]
        vol += (
            -x2 * y1 * z3
            + x3 * y1 * z2
            + x1 * y2 * z3
            - x3 * y2 * z1
            - x1 * y3 * z2
            + x2 * y3 * z1
        )
    return round(abs(vol) / 6, 3)


def stl_dimensions(path: str | Path) -> dict[str, Any]:
    v = verify_stl(path)
    if not v.get("ok"):
        return v
    bbox = v.get("bbox_mm") or {}
    vol = v.get("volume_mm3")
    return {
        **v,
        "dimensions_mm": {
            "x": bbox.get("x_mm"),
            "y": bbox.get("y_mm"),
            "z": bbox.get("z_mm"),
        },
        "volume_mm3": vol,
    }
