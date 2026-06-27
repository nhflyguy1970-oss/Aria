"""HTTP client for native PySide widgets (talks to running ARIA server)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

log = logging.getLogger("jarvis.pyside.api")


def _request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    timeout: float = 10.0,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(url, method=method, data=b"" if method == "POST" else None)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        log.warning("HTTP %s %s: %s", exc.code, path, body[:200])
        return {"ok": False, "error": body or str(exc)}
    except Exception as exc:
        log.warning("Request failed %s: %s", path, exc)
        return {"ok": False, "error": str(exc)}


def fetch_dashboard(base_url: str) -> dict[str, Any]:
    info = _request(base_url, "/api/system-info")
    news = _request(base_url, "/api/curated-news?use_ai=true")
    presets = _request(base_url, "/api/scenes/presets")
    return {
        "info": info if info.get("ok", True) else {},
        "news": news if news.get("ok", True) else {},
        "presets": presets if presets.get("ok", True) else {},
    }


def activate_scene(base_url: str, preset_id: str) -> tuple[bool, str]:
    enc = urllib.parse.quote(preset_id, safe="")
    data = _request(base_url, f"/api/scenes/presets/{enc}/activate", method="POST")
    return bool(data.get("ok")), str(data.get("message") or data.get("error") or "done")
