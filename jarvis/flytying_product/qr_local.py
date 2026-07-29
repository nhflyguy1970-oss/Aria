"""Local QR generation (SVG preferred; PNG via qrcode if installed)."""

from __future__ import annotations

from html import escape
from typing import Any


def label_html(barcode: str, name: str = "", *, size: int = 180) -> str:
    """Printable material label with offline QR (no cloud QR APIs)."""
    code = (barcode or "").strip() or "FT:LABEL"
    label = (name or "").strip() or code
    qr = generate_qr(code, fmt="svg", size=size)
    svg = qr.get("svg") or ""
    # Inline SVG avoids external image fetches
    if not svg and qr.get("data_url"):
        img = f'<img src="{escape(qr["data_url"])}" width="{size}" height="{size}" alt="QR" />'
    elif svg:
        img = svg
    else:
        img = f'<div class="code">{escape(code)}</div>'
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Label — {escape(label)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 1.5rem; }}
.label {{ border: 2px solid #333; padding: 1rem; max-width: 14rem; text-align: center; }}
.name {{ font-weight: 700; font-size: 1rem; margin-bottom: 0.5rem; word-break: break-word; }}
.code {{ font-family: monospace; font-size: 0.85rem; margin-top: 0.5rem; }}
.label svg {{ width: {int(size)}px; height: {int(size)}px; }}
@media print {{ body {{ margin: 0; }} .label {{ border: 1px solid #000; }} }}
</style></head><body>
<div class="label">
  <div class="name">{escape(label)}</div>
  {img}
  <div class="code">{escape(code)}</div>
</div>
<p><button onclick="window.print()">Print</button></p>
</body></html>"""


def generate_qr(
    data: str,
    *,
    fmt: str = "svg",
    size: int = 180,
    border: int = 2,
) -> dict[str, Any]:
    """
    Generate a QR code locally.
    Prefers the optional `qrcode` package; otherwise returns a stdlib SVG
    using a compact byte-mode QR matrix for short payloads (labels / FT: codes).
    """
    payload = (data or "").strip()
    if not payload:
        return {"ok": False, "message": "data required"}
    fmt = (fmt or "svg").strip().lower()
    if fmt not in ("svg", "png", "matrix"):
        fmt = "svg"

    try:
        import qrcode  # type: ignore
        from qrcode.constants import ERROR_CORRECT_M  # type: ignore

        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=max(1, int(size) // 25),
            border=max(0, int(border)),
        )
        qr.add_data(payload)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        if fmt == "matrix":
            return {"ok": True, "format": "matrix", "modules": matrix, "data": payload, "engine": "qrcode"}
        if fmt == "png":
            from io import BytesIO
            import base64

            img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return {
                "ok": True,
                "format": "png",
                "mime": "image/png",
                "data_url": f"data:image/png;base64,{b64}",
                "data": payload,
                "engine": "qrcode",
            }
        return {
            "ok": True,
            "format": "svg",
            "mime": "image/svg+xml",
            "svg": _matrix_to_svg(matrix, size=size),
            "data": payload,
            "engine": "qrcode",
        }
    except Exception:
        pass

    try:
        matrix = _simple_qr_matrix(payload, border=max(0, int(border)))
    except ValueError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "hint": "Install optional `qrcode` package for full QR support",
            "fallback": True,
        }

    svg = _matrix_to_svg(matrix, size=size)
    if fmt == "matrix":
        return {"ok": True, "format": "matrix", "modules": matrix, "data": payload, "engine": "stdlib_svg"}
    if fmt == "png":
        return {
            "ok": True,
            "format": "svg",
            "mime": "image/svg+xml",
            "svg": svg,
            "data": payload,
            "engine": "stdlib_svg",
            "note": "PNG requires optional qrcode; returned SVG",
        }
    return {
        "ok": True,
        "format": "svg",
        "mime": "image/svg+xml",
        "svg": svg,
        "data": payload,
        "engine": "stdlib_svg",
    }


def _matrix_to_svg(matrix: list[list[bool]], *, size: int = 180) -> str:
    n = len(matrix)
    if n <= 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0"/>'
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(size)}" height="{int(size)}" '
        f'viewBox="0 0 {n} {n}" shape-rendering="crispEdges">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                parts.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="#000000"/>')
    parts.append("</svg>")
    return "".join(parts)


def _simple_qr_matrix(data: str, *, border: int = 2) -> list[list[bool]]:
    """
    Compact stdlib QR (byte mode, ECC M, versions 1–3) for short label payloads.
    For long payloads, callers should install the optional qrcode package.
    """
    raw = data.encode("utf-8")
    version = _select_version(len(raw))
    codewords = _build_byte_codewords(raw, version)
    size = 17 + 4 * version
    modules = [[False] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]
    _place_finders(modules, reserved, size)
    _place_timing(modules, reserved, size)
    # Dark module
    dy = 4 * version + 9
    if 0 <= dy < size:
        modules[dy][8] = True
        reserved[dy][8] = True
    _place_format(modules, reserved, size)  # mask 0 + ECC M
    _place_data(modules, reserved, codewords, size)
    b = max(0, border)
    out_n = size + 2 * b
    out = [[False] * out_n for _ in range(out_n)]
    for y in range(size):
        for x in range(size):
            out[y + b][x + b] = modules[y][x]
    return out


def _select_version(nbytes: int) -> int:
    # Conservative byte capacities ECC-M
    for version, cap in ((1, 14), (2, 26), (3, 42)):
        if nbytes <= cap:
            return version
    raise ValueError(f"payload too long for built-in QR ({nbytes} bytes); install qrcode")


# GF(256)
_GF_EXP = [0] * 512
_GF_LOG = [0] * 256


def _init_gf() -> None:
    x = 1
    for i in range(255):
        _GF_EXP[i] = x
        _GF_LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        _GF_EXP[i] = _GF_EXP[i - 255]


_init_gf()


def _gf_mul(x: int, y: int) -> int:
    if x == 0 or y == 0:
        return 0
    return _GF_EXP[(_GF_LOG[x] + _GF_LOG[y]) % 255]


def _gf_poly_mul(p: list[int], q: list[int]) -> list[int]:
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i + j] ^= _gf_mul(a, b)
    return r


def _rs_generator(nsym: int) -> list[int]:
    g = [1]
    for i in range(nsym):
        g = _gf_poly_mul(g, [1, _GF_EXP[i]])
    return g


def _rs_encode(data: list[int], nsym: int) -> list[int]:
    gen = _rs_generator(nsym)
    out = data + [0] * nsym
    for i in range(len(data)):
        coef = out[i]
        if coef != 0:
            for j in range(len(gen)):
                out[i + j] ^= _gf_mul(gen[j], coef)
    return data + out[len(data) :]


_ECC_N = {1: 10, 2: 16, 3: 26}
_TOTAL_N = {1: 26, 2: 44, 3: 70}


def _build_byte_codewords(raw: bytes, version: int) -> list[int]:
    total = _TOTAL_N[version]
    ecc_n = _ECC_N[version]
    capacity = total - ecc_n
    bits: list[int] = []

    def put(val: int, n: int) -> None:
        for i in range(n - 1, -1, -1):
            bits.append((val >> i) & 1)

    put(0b0100, 4)
    put(len(raw), 8)
    for b in raw:
        put(b, 8)
    put(0, min(4, capacity * 8 - len(bits)))
    while len(bits) % 8:
        bits.append(0)
    data: list[int] = []
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i : i + 8]:
            byte = (byte << 1) | bit
        data.append(byte)
    pads = (0xEC, 0x11)
    pi = 0
    while len(data) < capacity:
        data.append(pads[pi % 2])
        pi += 1
    return _rs_encode(data[:capacity], ecc_n)


def _place_finders(modules: list[list[bool]], reserved: list[list[bool]], size: int) -> None:
    def place(ox: int, oy: int) -> None:
        for y in range(-1, 8):
            for x in range(-1, 8):
                xx, yy = ox + x, oy + y
                if not (0 <= xx < size and 0 <= yy < size):
                    continue
                in_pat = 0 <= x <= 6 and 0 <= y <= 6
                dark = in_pat and (x in (0, 6) or y in (0, 6) or (2 <= x <= 4 and 2 <= y <= 4))
                if in_pat:
                    modules[yy][xx] = dark
                reserved[yy][xx] = True

    place(0, 0)
    place(size - 7, 0)
    place(0, size - 7)


def _place_timing(modules: list[list[bool]], reserved: list[list[bool]], size: int) -> None:
    for i in range(8, size - 8):
        modules[6][i] = i % 2 == 0
        modules[i][6] = i % 2 == 0
        reserved[6][i] = True
        reserved[i][6] = True


def _place_format(modules: list[list[bool]], reserved: list[list[bool]], size: int) -> None:
    # Format bits for ECC=M (01) + mask 0 (000) — BCH-encoded constant 0x5412
    bits = 0x5412
    coords_a = [
        (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
        (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8),
    ]
    coords_b = [
        (size - 1, 8), (size - 2, 8), (size - 3, 8), (size - 4, 8), (size - 5, 8),
        (size - 6, 8), (size - 7, 8),
        (8, size - 8), (8, size - 7), (8, size - 6), (8, size - 5),
        (8, size - 4), (8, size - 3), (8, size - 2), (8, size - 1),
    ]
    for i, (x, y) in enumerate(coords_a):
        val = bool((bits >> (14 - i)) & 1)
        modules[y][x] = val
        reserved[y][x] = True
    for i, (x, y) in enumerate(coords_b):
        val = bool((bits >> (14 - i)) & 1)
        modules[y][x] = val
        reserved[y][x] = True


def _place_data(modules: list[list[bool]], reserved: list[list[bool]], codewords: list[int], size: int) -> None:
    bits: list[int] = []
    for cw in codewords:
        for i in range(7, -1, -1):
            bits.append((cw >> i) & 1)
    bi = 0
    upward = True
    x = size - 1
    while x > 0:
        if x == 6:
            x -= 1
        y_range = range(size - 1, -1, -1) if upward else range(size)
        for y in y_range:
            for dx in (0, -1):
                xx = x + dx
                if reserved[y][xx]:
                    continue
                bit = bits[bi] if bi < len(bits) else 0
                if (y + xx) % 2 == 0:  # mask 0
                    bit ^= 1
                modules[y][xx] = bool(bit)
                bi += 1
        upward = not upward
        x -= 2
