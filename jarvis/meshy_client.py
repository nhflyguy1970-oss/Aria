"""Meshy AI text-to-3D (optional cloud backend for Engineering lab)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

MESHY_API = "https://api.meshy.ai/openapi/v2/text-to-3d"
POLL_INTERVAL_S = 3.0
DEFAULT_TIMEOUT_S = 300


def meshy_api_key() -> str:
    return (os.getenv("JARVIS_MESHY_API_KEY") or os.getenv("MESHY_API_KEY") or "").strip()


def meshy_available() -> bool:
    return bool(meshy_api_key())


def _request(method: str, url: str, payload: dict | None = None, *, timeout: float = 60) -> dict[str, Any]:
    key = meshy_api_key()
    if not key:
        raise RuntimeError("Meshy API key not set — add JARVIS_MESHY_API_KEY to data/jarvis.env")
    data = None
    headers = {"Authorization": f"Bearer {key}"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(body)
            msg = err.get("message") or err.get("error") or body
        except Exception:
            msg = body or str(exc)
        raise RuntimeError(f"Meshy API error ({exc.code}): {msg}") from exc


def _download(url: str, *, timeout: float = 120) -> bytes:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def text_to_3d_preview(
    prompt: str,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> tuple[bytes, str, dict[str, Any]]:
    """Generate printable mesh via Meshy preview stage. Returns (stl_bytes, format, task_meta)."""
    clean = (prompt or "").strip()
    if len(clean) < 4:
        raise RuntimeError("Describe the part — Meshy needs a short text prompt")
    if len(clean) > 600:
        clean = clean[:600]

    created = _request(
        "POST",
        MESHY_API,
        {
            "mode": "preview",
            "prompt": clean,
            "ai_model": "latest",
            "should_remesh": True,
            "topology": "triangle",
            "target_polycount": 30000,
            "target_formats": ["stl", "glb"],
        },
    )
    task_id = created.get("result") or created.get("id") or created.get("task_id")
    if not task_id:
        raise RuntimeError(f"Meshy did not return a task id: {created!r}")

    deadline = time.time() + timeout_s
    task: dict[str, Any] = {}
    while time.time() < deadline:
        task = _request("GET", f"{MESHY_API}/{task_id}", timeout=30)
        status = str(task.get("status") or "").upper()
        if status in ("SUCCEEDED", "SUCCESS", "COMPLETED"):
            break
        if status in ("FAILED", "CANCELED", "CANCELLED"):
            err = task.get("task_error") or task.get("message") or status
            raise RuntimeError(f"Meshy generation failed: {err}")
        time.sleep(POLL_INTERVAL_S)
    else:
        raise RuntimeError("Meshy timed out — try again or use OpenSCAD (local) mode")

    urls = task.get("model_urls") or {}
    stl_url = (urls.get("stl") or "").strip()
    if stl_url:
        return _download(stl_url), "stl", task

    glb_url = (urls.get("glb") or "").strip()
    if glb_url:
        return _download(glb_url), "glb", task

    raise RuntimeError("Meshy finished but returned no STL/GLB download URL")
