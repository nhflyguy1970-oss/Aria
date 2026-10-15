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


# Per-item counts ("two arms and two legs each") describe every subject, not the scene: the
# check compared them with scene totals ("arms: asked 2, counted 8"), forced a needless
# re-render, and used up MAX_CHECKS before "three helicopters" was ever counted (2026-10-14).
_BODY_PARTS = {"arms", "legs", "hands", "feet", "eyes", "ears", "wings", "fingers", "toes", "horns", "heads",
               "paws", "tails", "antennae", "teeth", "lips", "wheels", "engines", "rotors", "blades", "doors",
               "windows", "letters", "words"}
_PER_ITEM = re.compile(r"^[^.;:]{0,60}?\b(?:each|apiece|per\s+\w+|on\s+each|for\s+each)\b", re.IGNORECASE)


def expected_counts(prompt: str) -> list[tuple[int, str]]:
    """[(5, "witches"), (2, "pears")] — the explicit counts a prompt asks for."""
    out: dict[str, int] = {}
    for m in _COUNTED.finditer(prompt or ""):
        noun = m.group(3).lower()
        if noun in _NOT_OBJECTS or noun in _BODY_PARTS:
            continue
        if _PER_ITEM.match((prompt or "")[m.end():]):
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


def _ask_helper(image_b64: str, prompt: str, *, num_predict: int, label: str) -> str | None:
    """One question to the helper VLM about an image; None when it cannot run on the RX 7600
    (the RTX is never used — it holds the image model)."""
    from jarvis import gpu_scheduler

    model = vlm_model()
    if not model or not gpu_scheduler.helper_ready() or gpu_scheduler.model_size(model) <= 0:
        return None
    options = {"num_ctx": 4096, "num_predict": num_predict, "temperature": 0}
    try:
        with gpu_scheduler.prefer_helper("image question beside an RTX image job", required=True):
            with gpu_scheduler.admit_ollama(model, options, label=label[:40]) as job:
                if job.kind != "helper":
                    return None
                body = {"model": model, "stream": False, "think": False, "keep_alive": "5m", "options": options,
                        "messages": [{"role": "user", "images": [image_b64], "content": prompt}]}
                req = urllib.request.Request(f"{job.host}/api/chat", data=json.dumps(body).encode(),
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    return json.loads(r.read())["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        logger.info("Helper image question skipped: %s", exc)
        return None


def locate(image_path: str, target: str) -> list[tuple[float, float, float, float]] | None:
    """Boxes (x1, y1, x2, y2 as 0-1 fractions) of every ``target`` the helper VLM finds;
    None when it cannot run there.

    Measured 2026-10-14 on a 1344x768 render: qwen3-vl 4B boxed all three helicopters,
    including a small distant one, tightly in 3-6 s."""
    prompt = (f"Locate every {target} in this image, including small, distant or partly hidden ones. "
              'Reply with only a JSON list like [{"bbox_2d": [x1, y1, x2, y2], "label": "...."}]. '
              "Reply [] if there is none.")
    text = _ask_helper(_jpeg_b64(image_path), prompt, num_predict=600, label=f"locate:{target}")
    return None if text is None else parse_boxes(text)


# Never part of an object, however close: what it stands on, floats in or is in front of.
_SURROUNDINGS = re.compile(r"\b(?:water|sea|ocean|lake|river|wave|ground|floor|road|street|pier|dock|deck|jetty|"
                           r"grass|sand|beach|sky|cloud|background|building|wall|house|table|tree|horizon|"
                           r"railing|post|boat|ship|car|person|man|woman|people|child)s?\b", re.IGNORECASE)


_WORN = re.compile(r"\b(?:hat|cap|helmet|hood|jacket|coat|shirt|t-shirt|sweater|vest|pants|trousers|jeans|shorts|"
                   r"dress|skirt|shoes?|boots?|socks?|gloves?|glasses|sunglasses|goggles|scarf|tie|belt|armou?r|"
                   r"uniform|clothes|clothing|hair|beard|mask|watch|necklace|earrings?)\b", re.IGNORECASE)


def locate_attached(image_path: str, target: str, box: tuple[float, float, float, float]):
    """[(box, label)] for what belongs to the object in ``box`` and should go with it when it is
    removed — what it holds, carries or is tied to, its shadow, its reflection. None when the helper
    cannot run. Only parts touching or near the object are kept, never the surroundings.

    Live 2026-10-14: removing a fisherman left his rod floating. qwen3-vl 4B returns [] when asked to
    find "everything that belongs to it" in one go, but names what a person holds ("fishing rod, hat,
    jacket", 0.3 s) and then boxes each named thing (0.6 s), so it is asked in two steps."""
    b = [round(v * 1000) for v in box]
    named = _ask_helper(_jpeg_b64(image_path),
                        # Measured wording: "What is it holding…" got "nothing" for a man with a fishing rod.
                        f"Look at the {target} at bbox_2d {b}. What is the {target} holding, carrying or using? "
                        "List at most 3 objects as short names separated by commas, or reply nothing.",
                        num_predict=30, label=f"held:{target}")
    if named is None:
        return None
    names = [n.strip(" .\n\"'").lower() for n in re.split(r",|\band\b", named)]
    names = [n for n in names if n and n != "nothing" and len(n) < 40 and not _WORN.search(n)
             and not _SURROUNDINGS.search(n)][:3]
    queries = names + [f"shadow of the {target}", f"reflection of the {target}"]
    tw, th = box[2] - box[0], box[3] - box[1]
    out: list[tuple[tuple[float, float, float, float], str]] = []
    for q in queries:
        found = locate(image_path, q)
        for cand in found or []:
            cw, ch = cand[2] - cand[0], cand[3] - cand[1]
            gap_x = max(0.0, max(cand[0], box[0]) - min(cand[2], box[2]))
            gap_y = max(0.0, max(cand[1], box[1]) - min(cand[3], box[3]))
            # A held object's box often stops short of the hand that holds it.
            near = gap_x <= max(0.06, 0.6 * max(tw, th)) and gap_y <= max(0.06, 0.6 * max(tw, th))
            inside = _covered(cand, box) > 0.8  # already part of the object's own box
            if near and not inside and cw * ch <= 6 * tw * th and not any(_iou(cand, o[0]) > 0.6 for o in out):
                out.append((cand, q))
    return out


def _covered(inner, outer) -> float:
    """How much of ``inner`` lies inside ``outer`` (0-1)."""
    ix = max(0.0, min(inner[2], outer[2]) - max(inner[0], outer[0]))
    iy = max(0.0, min(inner[3], outer[3]) - max(inner[1], outer[1]))
    area = (inner[2] - inner[0]) * (inner[3] - inner[1])
    return ix * iy / area if area > 0 else 0.0


def ask_yes_no(image_path: str, question: str, box=None) -> bool | None:
    """The helper VLM's yes/no answer about the image (or the region ``box``); None if unavailable."""
    from PIL import Image

    im = Image.open(image_path).convert("RGB")
    if box is not None:
        w, h = im.size
        pad_x, pad_y = (box[2] - box[0]) * 0.15, (box[3] - box[1]) * 0.15
        im = im.crop((int(max(0, box[0] - pad_x) * w), int(max(0, box[1] - pad_y) * h),
                      int(min(1, box[2] + pad_x) * w), int(min(1, box[3] + pad_y) * h)))
    im.thumbnail((1024, 1024))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    text = _ask_helper(base64.b64encode(buf.getvalue()).decode(), f"{question} Answer with only yes or no.",
                       num_predict=4, label="verify")
    if text is None:
        return None
    t = text.strip().lower()
    return True if t.startswith("yes") else False if t.startswith("no") else None


def parse_boxes(text: str) -> list[tuple[float, float, float, float]]:
    """Qwen-VL grounding JSON (0-1000 coordinates) → de-duplicated 0-1 boxes."""
    boxes: list[tuple[float, float, float, float]] = []
    for b, _ in parse_rows(text):
        if not any(_iou(b, k) > 0.7 for k in boxes):
            boxes.append(b)
    return boxes


def parse_rows(text: str) -> list[tuple[tuple[float, float, float, float], str]]:
    """[(0-1 box, label)] from Qwen-VL grounding JSON (0-1000 coordinates)."""
    start, end = (text or "").find("["), (text or "").rfind("]")
    try:
        rows = json.loads(text[start:end + 1]) if start >= 0 and end > start else []
    except json.JSONDecodeError:
        rows = [{"bbox_2d": [int(v) for v in g]} for g in re.findall(r"\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]", text or "")]
    out: list[tuple[tuple[float, float, float, float], str]] = []
    for row in rows if isinstance(rows, list) else []:
        raw = row.get("bbox_2d") if isinstance(row, dict) else row
        try:
            x1, y1, x2, y2 = (min(1.0, max(0.0, float(v) / 1000.0)) for v in raw[:4])
        except (TypeError, ValueError):
            continue
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))
        if x2 - x1 < 0.004 or y2 - y1 < 0.004:
            continue
        out.append(((x1, y1, x2, y2), str(row.get("label") or "") if isinstance(row, dict) else ""))
    return out


def _iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


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
