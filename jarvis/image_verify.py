"""Count check for high-quality images, run on the RX 7600 helper.

Every model tested on the RTX 3060 (Qwen-Image, Flux.2 Klein, Flux Schnell) sometimes draws
4 objects when 5 were asked for (2026-10-14 seed study). A small vision model on the RX 7600
counted 14 of 16 test images correctly in ~2 s each (8 of 8 Qwen-Image renders). So after a
quality render, ARIA counts what the prompt asked for and, on a mismatch, renders once more
with a new seed while Qwen-Image is still loaded, keeping the closer attempt.

The check only ever runs on the helper lane: it is skipped (never moved to the RTX, which
would evict the image model) when the helper is down, busy, hot or lacks the model.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "a pair of": 2, "a couple of": 2}
_COUNTED = re.compile(
    r"\b(two|three|four|five|six|seven|eight|[2-8]|a\s+pair\s+of|a\s+couple\s+of)\s+"
    r"((?:[a-z]+(?:-[a-z]+)?\s+){0,2}?)([a-z]+(?:es|s))\b",
    re.IGNORECASE,
)
# Plural words that follow a number but are not countable picture objects.
_NOT_OBJECTS = {"times", "minutes", "seconds", "hours", "days", "weeks", "years", "steps", "percent", "degrees",
                "pixels", "inches", "feet", "meters", "miles", "ways", "colors", "colours", "styles", "kinds", "types",
                "sides", "corners", "versions", "variations", "options", "images", "pictures", "photos", "tones"}
MAX_CHECKS = 3


def vlm_model() -> str:
    env = os.getenv("JARVIS_IMAGE_COUNT_MODEL", "qwen3-vl:4b-instruct-q4_K_M").strip()
    return "" if env.lower() in ("", "0", "off", "false", "no") else env


def retries() -> int:
    try:
        return max(0, min(2, int(os.getenv("JARVIS_IMAGE_COUNT_RETRIES", "1"))))
    except ValueError:
        return 1


def expected_counts(prompt: str) -> list[tuple[int, str]]:
    """[(5, "witches"), (2, "pears")] — the explicit counts a prompt asks for."""
    out: dict[str, int] = {}
    for m in _COUNTED.finditer(prompt or ""):
        noun = m.group(3).lower()
        if noun in _NOT_OBJECTS:
            continue
        raw = re.sub(r"\s+", " ", m.group(1).lower())
        n = int(raw) if raw.isdigit() else _WORDS[raw]
        out.setdefault(noun, n)
    return list((n, noun) for noun, n in out.items())[:MAX_CHECKS]


def _jpeg_b64(path: str) -> str:
    from PIL import Image

    im = Image.open(path).convert("RGB")
    im.thumbnail((1024, 1024))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def count_objects(image_path: str, noun: str) -> int | None:
    """The helper VLM's count of `noun` in the image; None when the check cannot run there."""
    from jarvis import gpu_scheduler

    model = vlm_model()
    if not model or not gpu_scheduler.helper_ready() or gpu_scheduler.model_size(model) <= 0:
        return None
    options = {"num_ctx": 4096, "num_predict": 8, "temperature": 0}
    try:
        with gpu_scheduler.prefer_helper("image count check beside an RTX image job", required=True):
            with gpu_scheduler.admit_ollama(model, options, label=f"count:{noun}") as job:
                if job.kind != "helper":
                    return None  # never on the RTX: it would evict the loaded image model
                body = {"model": model, "stream": False, "think": False, "keep_alive": "5m", "options": options,
                        "messages": [{"role": "user", "images": [_jpeg_b64(image_path)],
                                      "content": f"Count the {noun} in this image. Look carefully at the whole "
                                                 "image, including small or partly hidden ones. Answer with only the number."}]}
                req = urllib.request.Request(f"{job.host}/api/chat", data=json.dumps(body).encode(),
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    text = json.loads(r.read())["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        logger.info("Image count check skipped: %s", exc)
        return None
    m = re.search(r"\d+", text or "")
    return int(m.group(0)) if m else None


def check(image_path: str, prompt: str) -> dict:
    """{"checked": [{"noun", "want", "got"}], "misses": n, "ran": bool}."""
    rows = []
    for want, noun in expected_counts(prompt):
        got = count_objects(image_path, noun)
        if got is None:
            return {"checked": rows, "misses": 0, "ran": False}
        rows.append({"noun": noun, "want": want, "got": got})
    return {"checked": rows, "misses": sum(r["got"] != r["want"] for r in rows), "ran": bool(rows)}


def summary(result: dict) -> str:
    """One line for the chat reply."""
    rows = result.get("checked") or []
    if not result.get("ran") or not rows:
        return ""
    parts = [f"{r['want']} {r['noun']} ✓" if r["got"] == r["want"] else f"{r['noun']}: asked {r['want']}, counted {r['got']}"
             for r in rows]
    attempts = result.get("attempts", 1)
    tail = f" (best of {attempts} attempts)" if attempts > 1 else ""
    return "Count check: " + "; ".join(parts) + tail


def set_aside(path: str) -> str:
    """Move a rejected attempt out of the gallery (kept, not deleted) and return its new path."""
    src = Path(path)
    dest_dir = src.parent.parent / "generated_rejected"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    src.replace(dest)
    return str(dest)
