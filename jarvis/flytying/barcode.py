"""Barcode lookup and mapping for fly-tying materials inventory."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from jarvis.config import DATA_DIR

BARCODE_MAP_FILE = DATA_DIR / "flytying_barcode_map.json"
_UPC_RE = re.compile(r"^\d{8,14}$")
_FT_PREFIX_RE = re.compile(r"^(?:FT|JARVIS-FT):", re.I)


def normalize_barcode(raw: str) -> str:
    """Normalize scanner input: trim, uppercase custom prefixes, digits-only for retail UPC/EAN."""
    s = (raw or "").strip()
    if not s:
        return ""
    if _FT_PREFIX_RE.match(s):
        return s.upper().replace("JARVIS-FT:", "FT:")
    digits = re.sub(r"\D", "", s)
    if not digits:
        return s
    if len(digits) == 11:
        digits = "0" + digits
    if len(digits) in (8, 12, 13, 14):
        return digits
    return digits if digits.isdigit() else s


def barcode_kind(code: str) -> str:
    c = normalize_barcode(code)
    if not c:
        return "unknown"
    if c.startswith("FT:"):
        return "custom"
    if _UPC_RE.match(c):
        n = len(c)
        if n in (12, 13):
            return "upc_ean"
        if n in (8, 14):
            return "ean"
    if len(c) > 20 or "://" in c:
        return "qr"
    return "code128"


def _read_map() -> dict[str, dict[str, Any]]:
    if not BARCODE_MAP_FILE.is_file():
        return {}
    try:
        data = json.loads(BARCODE_MAP_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, val in data.items():
        norm = normalize_barcode(str(key))
        if norm and isinstance(val, dict):
            out[norm] = val
        elif norm and isinstance(val, str) and val.strip():
            out[norm] = {"name": val.strip()}
    return out


def _write_map(data: dict[str, dict[str, Any]]) -> None:
    BARCODE_MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    BARCODE_MAP_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_barcode_mappings() -> dict[str, dict[str, Any]]:
    return _read_map()


def learn_barcode_mapping(
    barcode: str,
    name: str,
    *,
    brand: str = "",
    notes: str = "",
) -> dict[str, Any]:
    code = normalize_barcode(barcode)
    label = (name or "").strip()
    if not code:
        return {"ok": False, "message": "barcode required"}
    if not label:
        return {"ok": False, "message": "name required"}
    data = _read_map()
    entry = {
        "name": label,
        "brand": (brand or "").strip(),
        "notes": (notes or "").strip(),
        "learned_at": datetime.now(timezone.utc).isoformat(),
        "kind": barcode_kind(code),
    }
    data[code] = entry
    _write_map(data)
    return {"ok": True, "barcode": code, "mapping": entry}


def delete_barcode_mapping(barcode: str) -> dict[str, Any]:
    code = normalize_barcode(barcode)
    data = _read_map()
    if code not in data:
        return {"ok": False, "message": "not found"}
    data.pop(code, None)
    _write_map(data)
    return {"ok": True, "barcode": code}


def _local_lookup(code: str) -> dict[str, Any] | None:
    data = _read_map()
    hit = data.get(code)
    if not hit:
        return None
    name = str(hit.get("name") or "").strip()
    if not name:
        return None
    return {
        "found": True,
        "barcode": code,
        "name": name,
        "brand": str(hit.get("brand") or "").strip(),
        "source": "local_map",
        "kind": hit.get("kind") or barcode_kind(code),
        "notes": str(hit.get("notes") or "").strip(),
    }


def _http_json(url: str, *, headers: dict[str, str] | None = None, timeout: float = 8.0) -> dict | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JarvisFlyTying/1.0",
            "Accept": "application/json",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            return data if isinstance(data, dict) else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _lookup_open_food_facts(code: str) -> dict[str, Any] | None:
    if os.environ.get("JARVIS_UPC_LOOKUP", "1").strip().lower() in ("0", "false", "no"):
        return None
    data = _http_json(f"https://world.openfoodfacts.org/api/v2/product/{code}.json?fields=product_name,brands,quantity,categories")
    if not data or data.get("status") != 1:
        return None
    product = data.get("product") or {}
    name = str(product.get("product_name") or "").strip()
    if not name:
        return None
    brand = str(product.get("brands") or "").split(",")[0].strip()
    qty = str(product.get("quantity") or "").strip()
    display = name
    if brand and brand.lower() not in name.lower():
        display = f"{brand} — {name}"
    if qty:
        display = f"{display} ({qty})"
    return {
        "found": True,
        "barcode": code,
        "name": display,
        "brand": brand,
        "source": "open_food_facts",
        "kind": "upc_ean",
        "raw_name": name,
    }


def _lookup_upcitemdb(code: str) -> dict[str, Any] | None:
    if os.environ.get("JARVIS_UPC_LOOKUP", "1").strip().lower() in ("0", "false", "no"):
        return None
    key = (os.environ.get("JARVIS_UPCITEMDB_KEY") or "").strip()
    base = "https://api.upcitemdb.com/prod/v1/lookup" if key else "https://api.upcitemdb.com/prod/trial/lookup"
    url = f"{base}?upc={code}"
    headers: dict[str, str] = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = _http_json(url, headers=headers)
    if not data or str(data.get("code")).lower() not in ("ok", "200", "success"):
        items = data.get("items") if isinstance(data, dict) else None
        if not items:
            return None
    items = data.get("items") or []
    if not items:
        return None
    item = items[0] if isinstance(items[0], dict) else {}
    title = str(item.get("title") or item.get("description") or "").strip()
    if not title:
        return None
    brand = str(item.get("brand") or "").strip()
    display = f"{brand} — {title}" if brand and brand.lower() not in title.lower() else title
    return {
        "found": True,
        "barcode": code,
        "name": display,
        "brand": brand,
        "source": "upcitemdb",
        "kind": "upc_ean",
        "raw_name": title,
    }


def lookup_barcode(raw: str, *, online: bool = True) -> dict[str, Any]:
    code = normalize_barcode(raw)
    if not code:
        return {"ok": False, "found": False, "message": "empty barcode"}

    local = _local_lookup(code)
    if local:
        return {"ok": True, **local}

    kind = barcode_kind(code)
    if kind == "custom":
        return {
            "ok": True,
            "found": False,
            "barcode": code,
            "kind": kind,
            "message": "Unknown custom label — name this barcode once to remember it.",
        }

    if online and kind in ("upc_ean", "ean"):
        for fn in (_lookup_upcitemdb, _lookup_open_food_facts):
            hit = fn(code)
            if hit:
                return {"ok": True, **hit}

    return {
        "ok": True,
        "found": False,
        "barcode": code,
        "kind": kind,
        "message": "Barcode not in library — add a name to remember it, or check the retail package.",
    }


def decode_barcodes_from_image(image_bytes: bytes) -> list[str]:
    """Optional server-side decode via pyzbar (pip install pyzbar Pillow)."""
    try:
        from io import BytesIO

        from PIL import Image
        from pyzbar.pyzbar import decode as zbar_decode
    except ImportError:
        return []
    try:
        img = Image.open(BytesIO(image_bytes))
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        codes: list[str] = []
        seen: set[str] = set()
        for sym in zbar_decode(img):
            val = (sym.data or b"").decode("utf-8", errors="replace").strip()
            norm = normalize_barcode(val)
            if norm and norm not in seen:
                seen.add(norm)
                codes.append(norm)
        return codes
    except Exception:
        return []


def make_custom_barcode(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")[:40]
    if not slug:
        slug = "item"
    ts = datetime.now(timezone.utc).strftime("%y%m%d")
    return f"FT:{slug}-{ts}"
