"""Local object edits: change one kind of object and keep every other pixel.

Benchmark, 2026-10-14 (remove one of three helicopters from a 1344x768 Qwen-Image render):

* whole-image FLUX.2 Klein edit (ARIA's edit until now): removed all three, redrew the whole
  picture (24.6 dB PSNR outside the target), and was downscaled to 1024 px;
* OpenCV inpaint: a smeared band; SDXL (Juggernaut) inpaint: a dark rectangle;
* Klein editing only a crop around the object, pasted back through a feathered mask: the
  helicopter gone and the lightning behind it continued, 3 of 3 runs, every pixel outside
  the mask identical; 12-14 s warm, 23-27 s with the model load.

So: the RX 7600 helper VLM locates the objects (qwen3-vl, 3-6 s), Klein edits a crop of each
chosen one on the RTX 3060, the masked area goes back into the full-resolution original, and
the helper counts again. Uncensored mode keeps its own model: the active SDXL checkpoint
(Lustify) fills the masked crop, as Klein was never trained on explicit content.
"""
from __future__ import annotations

import json
import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path

from jarvis.image_edit_plan import EditPlan

logger = logging.getLogger(__name__)

GROW = {"remove": 0.18, "replace": 0.28, "change": 0.10, "move": 0.18}
# Change detection: the masked area is cut down to the pixels the editor really changed (after a
# light blur, any channel differing by more than DIFF_T levels), closed and grown a little. A long
# diagonal fishing rod then costs a thin band, not its whole bounding rectangle.
DIFF_T = 26
RETRY_GROW = 0.32
CONTEXT = 2.2          # crop side = object side x CONTEXT, so the editor sees its surroundings
MIN_CROP = 384         # px (short side) — small objects still get enough context
EDIT_LONG = 1024       # crop is scaled to this long side for the editor
Box = tuple[float, float, float, float]
# ComfyUI saves each crop render into the gallery folder; "tmp_" keeps one the Gallery hides
# (gallery_product.inventory) if an edit is interrupted before it is deleted.
WORK_PREFIX = "tmp_aria_edit_work"


@dataclass
class Outcome:
    path: str = ""              # edited full-resolution image; "" when nothing was changed
    message: str = ""           # what was done, or why not
    handled: bool = True        # False: not a local edit after all — use the whole-image editor
    question: bool = False      # nothing changed; ARIA needs an answer first
    before: int | None = None
    after: int | None = None
    expected: int | None = None
    detail: dict = field(default_factory=dict)


def _count_word(n: int, noun: str) -> str:
    return f"{n} {noun}" + ("" if n == 1 else ("es" if noun.endswith(("s", "sh", "ch", "x")) else "s"))


def _position(box: Box, boxes: list[Box] | None = None) -> str:
    """"the smallest one, middle right" — enough to recognise which object changed."""
    cx = (box[0] + box[2]) / 2
    where = ("far left", "left", "middle left", "middle", "middle right", "right", "far right")[
        min(6, int(cx * 7))]
    area = lambda b: (b[2] - b[0]) * (b[3] - b[1])  # noqa: E731
    if boxes and len(boxes) > 1:
        if area(box) == min(map(area, boxes)):
            return f"the smallest one, {where}"
        if area(box) == max(map(area, boxes)):
            return f"the largest one, {where}"
    return where


def choose(boxes: list[Box], which: str, k: int) -> list[Box]:
    """The k boxes the instruction means; with no position word, the least prominent (smallest)."""
    area = lambda b: (b[2] - b[0]) * (b[3] - b[1])  # noqa: E731
    cx = lambda b: (b[0] + b[2]) / 2  # noqa: E731
    cy = lambda b: (b[1] + b[3]) / 2  # noqa: E731
    keys = {
        "left": cx, "leftmost": cx, "right": lambda b: -cx(b), "rightmost": lambda b: -cx(b),
        "top": cy, "topmost": cy, "upper": cy, "bottom": lambda b: -cy(b), "lower": lambda b: -cy(b),
        "middle": lambda b: abs(cx(b) - 0.5), "center": lambda b: abs(cx(b) - 0.5), "centre": lambda b: abs(cx(b) - 0.5),
        "largest": lambda b: -area(b), "biggest": lambda b: -area(b), "big": lambda b: -area(b),
        "large": lambda b: -area(b), "closest": lambda b: -area(b), "nearest": lambda b: -area(b),
        "foreground": lambda b: -area(b),
    }
    key = keys.get(which, area)  # smallest / distant / farthest / background / extra / none
    return sorted(boxes, key=key)[:k]


def dominant(boxes: list[Box], ratio: float = 4.0) -> Box | None:
    """The object "the <noun>" obviously means: one at least ``ratio`` x larger than every other
    (live 2026-10-14: "the lighthouse" — a large red one, plus a tiny beacon on the breakwater)."""
    area = lambda b: (b[2] - b[0]) * (b[3] - b[1])  # noqa: E731
    ranked = sorted(boxes, key=area, reverse=True)
    if len(ranked) == 1 or (len(ranked) > 1 and area(ranked[0]) >= ratio * area(ranked[1])):
        return ranked[0]
    return None


def _px(box: Box, w: int, h: int) -> tuple[float, float, float, float]:
    return box[0] * w, box[1] * h, box[2] * w, box[3] * h


def crop_window(box_px, w: int, h: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box_px
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    cw = min(w, max((x2 - x1) * CONTEXT, MIN_CROP * 4 / 3))
    ch = min(h, max((y2 - y1) * CONTEXT, MIN_CROP))
    left = int(max(0, min(w - cw, cx - cw / 2)))
    top = int(max(0, min(h - ch, cy - ch / 2)))
    return left, top, int(min(w, left + cw)), int(min(h, top + ch))


def mask_for(box_px, w: int, h: int, grow: float):
    from PIL import Image, ImageDraw, ImageFilter

    x1, y1, x2, y2 = box_px
    gx, gy = (x2 - x1) * grow, (y2 - y1) * grow
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle([x1 - gx, y1 - gy, x2 + gx, y2 + gy], fill=255)
    feather = max(3.0, 0.06 * min(x2 - x1, y2 - y1))
    return mask.filter(ImageFilter.GaussianBlur(feather))


def _edit_size(cw: int, ch: int) -> tuple[int, int]:
    scale = EDIT_LONG / max(cw, ch)
    return max(256, int(cw * scale) // 16 * 16), max(256, int(ch * scale) // 16 * 16)


def _work_dir() -> Path:
    from jarvis.config import DATA_DIR

    d = DATA_DIR / "edit_work"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _prompt_for(plan: EditPlan, extras: list[str] | None = None) -> str:
    # Neutral wording: "fill it with storm clouds" made Klein paint a cloud blob where the
    # helicopter was; "Remove the helicopter" continued the sky and lightning behind it.
    what = plan.target
    if plan.op == "replace":
        return f"Replace the {what} with {plan.replacement}. Keep everything else exactly the same."
    if plan.op == "change":
        return f"Make the {what} {plan.replacement}. Keep everything else exactly the same."
    if plan.op == "move":
        how = f"{plan.amount} " if plan.amount else ""
        return f"Move the {what} {how}to the {plan.direction}. Keep everything else exactly the same."
    if extras:
        parts = [e.replace(f" of the {what}", "") for e in extras]
        return f"Remove the {what} and its {', '.join(parts)}. Keep everything else exactly the same."
    return f"Remove the {what}. Keep everything else exactly the same."


def _sdxl_workflow(image_name: str, mask_name: str, plan: EditPlan, seed: int) -> dict:
    """Uncensored mode: the active SDXL checkpoint fills the masked crop (VAEEncode + noise mask)."""
    from jarvis.comfyui import _find_checkpoint, _sampler_settings
    from jarvis.comfyui_settings import recommended_uncensored_checkpoint
    from jarvis.image_safety import with_minor_negative

    ckpt = _find_checkpoint()
    if "flux" in ckpt.lower() or "z_image" in ckpt.lower():
        ckpt = recommended_uncensored_checkpoint() or ckpt
    steps, cfg, sampler, scheduler = _sampler_settings(ckpt)
    if plan.op == "replace":
        positive, negative = f"{plan.replacement}, photorealistic, matching lighting", plan.noun
    elif plan.op == "change":
        positive, negative = f"{plan.replacement} {plan.target}, photorealistic, matching lighting", ""
    else:
        positive, negative = "empty background, seamless continuation of the surroundings, photorealistic", \
            f"{plan.noun}, object, person, text"
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "10": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "11": {"class_type": "LoadImage", "inputs": {"image": mask_name}},
        "12": {"class_type": "ImageToMask", "inputs": {"image": ["11", 0], "channel": "red"}},
        "13": {"class_type": "VAEEncode", "inputs": {"pixels": ["10", 0], "vae": ["4", 2]}},
        "14": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["13", 0], "mask": ["12", 0]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": with_minor_negative(negative), "clip": ["4", 1]}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": steps, "cfg": cfg, "sampler_name": sampler,
                                                   "scheduler": scheduler, "denoise": 1.0, "model": ["4", 0],
                                                   "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["14", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": WORK_PREFIX, "images": ["8", 0]}},
    }


def _engine() -> str:
    """"klein" (Regular), "sdxl" (Uncensored), or "" when the mode's editor is missing."""
    from jarvis.comfyui_edit import klein_installed
    from jarvis.config import is_uncensored

    if is_uncensored():
        return "sdxl"
    return "klein" if klein_installed() else ""


def _union(boxes: list[Box]) -> Box:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def changed_mask(before, after, hard):
    """``hard`` (L image) cut down to where ``after`` really differs from ``before``, feathered."""
    import numpy as np
    from PIL import Image, ImageFilter

    a = np.asarray(before.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.int16)
    b = np.asarray(after.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.int16)
    diff = Image.fromarray(((np.abs(a - b).max(axis=2) > DIFF_T) * 255).astype(np.uint8))
    side = max(before.size)
    k = max(3, min(15, int(side * 0.008)) | 1)  # odd kernel, ~0.8% of the crop
    grown = diff.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
    cut = np.minimum(np.asarray(grown), np.asarray(hard))
    return Image.fromarray(cut.astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(1.5, k / 3)))


def _edit_region(run, orig, boxes: list[Box], plan: EditPlan, engine: str, grow: float, seed: int,
                 extras: list[str] | None = None):
    """Edit the area of ``boxes`` (the object, plus what goes with it); returns
    (full-size edited image, final mask) or an ERROR string."""
    from PIL import Image, ImageChops

    from jarvis.comfyui import upload_image

    w, h = orig.size
    left, top, right, bottom = crop_window(_px(_union(boxes), w, h), w, h)
    tw, th = _edit_size(right - left, bottom - top)
    work = _work_dir()
    stamp = f"{int(time.time() * 1000)}_{seed % 100000}"
    crop_path = work / f"crop_{stamp}.png"
    orig.crop((left, top, right, bottom)).resize((tw, th), Image.LANCZOS).save(crop_path)
    hard = Image.new("L", (w, h), 0)
    for b in boxes:
        hard = ImageChops.lighter(hard, mask_for(_px(b, w, h), w, h, grow).point(lambda v: 255 if v > 8 else 0))
    temp = [crop_path]
    try:
        name = upload_image(crop_path)
        temp.append(_comfy_path("input", name))
        if engine == "klein":
            from jarvis.comfyui_edit import build_klein_edit_workflow

            wf = build_klein_edit_workflow(name, _prompt_for(plan, extras), tw, th, seed=seed)
            wf["9"]["inputs"]["filename_prefix"] = WORK_PREFIX
        else:
            soft = mask_for(_px(_union(boxes), w, h), w, h, grow)
            cm = ImageChops.lighter(soft, hard).crop((left, top, right, bottom)).resize((tw, th), Image.LANCZOS)
            mask_path = work / f"mask_{stamp}.png"
            Image.merge("RGB", (cm, cm, cm)).save(mask_path)
            temp.append(mask_path)
            mask_name = upload_image(mask_path)
            temp.append(_comfy_path("input", mask_name))
            wf = _sdxl_workflow(name, mask_name, plan, seed)
        out = run(wf, WORK_PREFIX)
        if out.startswith("ERROR:"):
            return out
        # The raw crop is working material, never a gallery image — nor kept in ComfyUI's output.
        temp += [Path(out), _comfy_path("output", Path(out).name)]
        fill = Image.open(out).convert("RGB").resize((right - left, bottom - top), Image.LANCZOS)
    finally:
        for p in temp:
            try:
                p.unlink()
            except OSError:
                pass
    crop_box = (left, top, right, bottom)
    local = changed_mask(orig.crop(crop_box), fill, hard.crop(crop_box))
    fill = match_tone(orig.crop(crop_box), fill, local)
    full = orig.copy()
    full.paste(fill, (left, top))
    mask = Image.new("L", (w, h), 0)
    mask.paste(local, (left, top))
    return Image.composite(full, orig, mask), mask


def match_tone(before, after, mask):
    """Shift ``after``'s colour to ``before``'s in the ring just outside ``mask``: Klein's fill can
    come back a few levels brighter, which left a faint ghost of a removed gull (live 2026-10-14)."""
    import numpy as np
    from PIL import ImageFilter

    m = np.asarray(mask) > 8
    if not m.any():
        return after
    k = max(5, min(31, int(max(before.size) * 0.03)) | 1)
    ring = (np.asarray(mask.filter(ImageFilter.MaxFilter(k))) > 8) & ~m
    if ring.sum() < 50:
        return after
    a = np.asarray(before, dtype=np.float32)
    b = np.asarray(after, dtype=np.float32)
    offset = (a[ring] - b[ring]).mean(axis=0)
    return __import__("PIL.Image", fromlist=["Image"]).fromarray(np.clip(b + offset, 0, 255).astype(np.uint8))


def crosses_edge(silhouette, box: Box, w: int, h: int, band: float = 0.06, side_hit: float = 0.01) -> bool:
    """True when the removal also changed pixels along two or more sides of the object's padded
    box: then something else runs through it (live 2026-10-14: a white sailboat's box held another
    boat's mast — moving the cut-out dragged the mast along and garbled both). A free-standing
    object's removal leaves that edge band unchanged."""
    import numpy as np

    x1, y1, x2, y2 = _px(box, w, h)
    gx, gy = (x2 - x1) * GROW["remove"], (y2 - y1) * GROW["remove"]
    l, t, r, b = (int(max(0, x1 - gx)), int(max(0, y1 - gy)), int(min(w, x2 + gx)), int(min(h, y2 + gy)))
    m = np.asarray(silhouette)[t:b, l:r] > 64
    if m.shape[0] < 8 or m.shape[1] < 8:
        return False
    bw, bh = max(2, int(m.shape[1] * band)), max(2, int(m.shape[0] * band))
    sides = (m[:bh, :], m[-bh:, :], m[:, :bw], m[:, -bw:])
    return sum(float(side.mean()) > side_hit for side in sides) >= 2


def _move_region(run, orig, old: Box, new: Box, plan: EditPlan, engine: str, seed: int):
    """Move an object: Klein removes it (it does not move things: live 2026-10-14 it changed 0.1 % of
    the picture and left the boat where it was), the pixels that removal changed are the object's
    silhouette, and the original object is pasted through that silhouette at the new place."""
    from dataclasses import replace

    from PIL import Image

    res = _edit_region(run, orig, [old], replace(plan, op="remove"), engine, GROW["remove"], seed)
    if isinstance(res, str):
        return res
    removed, silhouette = res
    w, h = orig.size
    if crosses_edge(silhouette, old, w, h):
        return "OVERLAP"

    dx, dy = round((new[0] - old[0]) * w), round((new[1] - old[1]) * h)
    moved_obj = Image.new("RGB", (w, h))
    moved_obj.paste(orig, (dx, dy))
    moved_mask = Image.new("L", (w, h), 0)
    moved_mask.paste(silhouette, (dx, dy))
    out = Image.composite(moved_obj, removed, moved_mask)
    from PIL import ImageChops

    return out, ImageChops.lighter(silhouette, moved_mask)


def _edit_box(run, orig, box: Box, plan: EditPlan, engine: str, grow: float, seed: int):
    return _edit_region(run, orig, [box], plan, engine, grow, seed)


def _comfy_path(folder: str, name: str) -> Path:
    """ComfyUI's own copy of a file this edit uploaded or rendered (deleted with the work files)."""
    from jarvis.comfyui_settings import COMFY_ROOT

    return COMFY_ROOT / folder / Path(name).name


def _save(image, src: Path, meta: dict) -> str:
    from PIL.PngImagePlugin import PngInfo

    from jarvis.comfyui import OUTPUT_DIR

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    taken = {p.name for p in OUTPUT_DIR.glob("jarvis_edit_local_*_.png")}
    n = len(taken) + 1
    while f"jarvis_edit_local_{n:05d}_.png" in taken:
        n += 1
    out = OUTPUT_DIR / f"jarvis_edit_local_{n:05d}_.png"
    info = PngInfo()
    info.add_text("aria_edit", json.dumps({**meta, "source": src.name}))
    # Write then rename: an interruption never leaves a half-written image in the gallery.
    part = out.with_name(f"tmp_{out.stem}.part.png")
    image.save(part, pnginfo=info)
    os.replace(part, out)
    return str(out)


def _sweep_stale_work(max_age_s: float = 3600) -> None:
    """Remove working files an interrupted edit left behind (crop renders, masks, checks)."""
    from jarvis.comfyui import OUTPUT_DIR

    now = time.time()
    for pattern, root in ((f"{WORK_PREFIX}_*", OUTPUT_DIR), ("tmp_jarvis_edit_local_*.part.png", OUTPUT_DIR),
                          ("*", _work_dir())):
        for p in root.glob(pattern):
            try:
                if p.is_file() and now - p.stat().st_mtime > max_age_s:
                    p.unlink()
            except OSError:
                pass


def _report(pct: int, message: str) -> None:
    try:
        from jarvis.comfyui import _report as report
        from jarvis.media_jobs import current_job_id

        report(pct, message, current_job_id())
    except Exception:  # noqa: BLE001
        pass


def _cancelled() -> bool:
    try:
        from jarvis.comfyui import _cancel_check_default

        return bool(_cancel_check_default())
    except Exception:  # noqa: BLE001
        return False


def _how_many(plan: EditPlan, found: int, boxes: list[Box] | None = None) -> tuple[int, str, bool]:
    """(objects to remove, reason not to edit, whether that reason asks the owner something)."""
    n = _count_word
    seen = f"I count {n(found, plan.noun)} in this image" + (
        f", not {plan.claimed_total}" if plan.claimed_total not in (None, found) else "")
    if plan.remove_all:
        return found, "", False
    if plan.target_total is not None:
        k = found - plan.target_total
        if plan.count is not None and plan.count != k:
            return 0, (f"{seen}. Removing {plan.count} would leave {found - plan.count}, not {plan.target_total}, "
                       "so I left the image unchanged. Tell me how many to remove, or which ones."), True
        if k <= 0:
            return 0, f"{seen} — already {plan.target_total} or fewer, so I left the image unchanged.", False
        return k, "", False
    if plan.count is not None:
        if plan.count > found:
            return 0, f"{seen}, so I can't remove {plan.count}. Tell me which ones to remove.", True
        return plan.count, "", False
    if found == 1 or plan.which:
        return 1, "", False
    if boxes is not None and dominant(boxes):
        return 1, "", False
    return 0, f"{seen}. Which one should I remove? (for example: left, middle, right, smallest, largest)", True


_SHIFT = {"a little": 0.5, "slightly": 0.5, "a bit": 0.5, "far": 1.5, "a lot": 1.5, "further": 1.5}


def moved_box(box: Box, direction: str, amount: str = "") -> Box | None:
    """Where "move it to the left" puts the object: one object-width over (half for "a little"),
    kept inside the picture. None when there is no room to move that way."""
    k = _SHIFT.get(amount, 1.0)
    w, h = box[2] - box[0], box[3] - box[1]
    dx = {"left": -w, "right": w}.get(direction, 0.0) * k
    dy = {"up": -h, "down": h}.get(direction, 0.0) * k
    dx = max(-box[0], min(1 - box[2], dx))
    dy = max(-box[1], min(1 - box[3], dy))
    if abs(dx) < 0.3 * w * k and abs(dy) < 0.3 * h * k:
        return None
    return (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)


def _pick_one(plan: EditPlan, boxes: list[Box]) -> tuple[Box | None, str]:
    """The single object a change/replace/move means, or the question to ask."""
    if plan.which:
        return choose(boxes, plan.which, 1)[0], ""
    if len(boxes) == 1 or (main := dominant(boxes)):
        return (boxes[0] if len(boxes) == 1 else main), ""
    return None, (f"I count {_count_word(len(boxes), plan.noun)}. Which one should I {_VERB[plan.op]}? "
                  "(for example: left, middle, right, smallest, largest)")


_VERB = {"remove": "remove", "replace": "replace", "change": "change", "move": "move"}


def run(src: str | Path, plan: EditPlan) -> Outcome:
    """Carry out ``plan`` on ``src``. ``handled=False`` means: not done locally (``message`` says why)."""
    from PIL import Image

    from jarvis.comfyui import image_session, is_available, workflow_ram_mib
    from jarvis.image_verify import ask_yes_no, locate, locate_attached

    t0 = time.monotonic()
    src = Path(src)
    _sweep_stale_work()
    engine = _engine()
    if not engine:
        return Outcome(handled=False, message="the local editor model is not installed")
    if plan.op == "move" and engine != "klein":
        return Outcome(handled=False, message="moving an object needs FLUX.2 Klein, which Uncensored mode does not use")
    _report(4, f"Finding the {plan.target} on the RX 7600…")
    boxes = locate(str(src), plan.target)
    if boxes is None:
        return Outcome(handled=False, message="the RX 7600 vision model is unavailable, so I cannot find the object")
    found = len(boxes)
    if found == 0:
        return Outcome(handled=False, before=0, message=f"I couldn't find a {plan.target} in this image")
    regions: list[tuple[list[Box], list[str]]] = []  # (boxes edited together, attached-part labels)
    new_box = None
    if plan.op == "remove":
        k, why, ask = _how_many(plan, found, boxes)
        if not k:
            return Outcome(message=why, question=ask, before=found)
        main = dominant(boxes) if plan.count is None and not plan.which and not plan.remove_all else None
        targets = [main] if main and k == 1 and found > 1 else choose(boxes, plan.which, k)
        expected = found - k
        for box in targets:
            extra = locate_attached(str(src), plan.target, box) if plan.with_attached else None
            regions.append(([box] + [b for b, _ in extra or []], [lbl for _, lbl in extra or []]))
    else:
        one, why = _pick_one(plan, boxes)
        if one is None:
            return Outcome(message=why, question=True, before=found)
        targets = [one]
        expected = found
        if plan.op == "move":
            new_box = moved_box(one, plan.direction, plan.amount)
            if new_box is None:
                return Outcome(message=f"The {plan.target} is already at the {plan.direction} edge of the picture, "
                                       "so there is no room to move it that way.", before=found)
            regions.append(([one, new_box], []))
        else:
            regions.append(([one], []))
    if _cancelled():
        return Outcome(path="", message="ERROR: Cancelled by user")

    from jarvis.services import ensure_comfyui_nvidia

    if not is_available():
        ensure_comfyui_nvidia(block=True, timeout=30)
    if not is_available():
        return Outcome(handled=False, message="ComfyUI is not running")

    orig = Image.open(src).convert("RGB")
    seeds: list[int] = []
    probe = _sdxl_workflow("x", "y", plan, 0) if engine == "sdxl" else None
    if probe is None:
        from jarvis.comfyui_edit import build_klein_edit_workflow

        probe = build_klein_edit_workflow("x", "x", 512, 512, seed=0)
    after = None
    attempts = 0
    verified: bool | None = None
    edited = orig
    mask_px = 0
    try:
        with image_session("jarvis_edit_local", ram_mib=workflow_ram_mib(probe), timeout_sec=420) as run_wf:
            for i, (rboxes, extras) in enumerate(regions):
                if _cancelled():
                    return Outcome(message="ERROR: Cancelled by user")
                _report(20 + int(50 * i / len(regions)),
                        f"Editing {plan.target} {i + 1} of {len(regions)} on the RTX 3060…")
                seed = secrets.randbelow(2**31)
                seeds.append(seed)
                if plan.op == "move":
                    res = _move_region(run_wf, edited, rboxes[0], rboxes[1], plan, engine, seed)
                    if res == "OVERLAP":
                        return Outcome(message=(
                            f"I didn't move the {plan.target}: other things run through it (for example a mast or "
                            "a person in front of it), so cutting it out would drag parts of them along. I can "
                            f"only move an object that stands clear of others — removing the {plan.target} or "
                            "changing its colour still works."), before=found)
                else:
                    res = _edit_region(run_wf, edited, rboxes, plan, engine, GROW[plan.op], seed, extras)
                if isinstance(res, str):
                    return Outcome(message=res)
                edited = res[0]
                mask_px += sum(1 for v in res[1].getdata() if v > 8)
            attempts = 1
            check = _work_dir() / f"check_{int(time.time() * 1000)}.png"
            edited.save(check)
            _report(80, "Checking the result on the RX 7600…")
            if plan.op == "remove":
                again = locate(str(check), plan.target)
                after = len(again) if again is not None else None
                if after is not None and after > expected and not _cancelled():
                    # One bounded retry on the objects that are still there, larger mask, new seed.
                    still = [b for b in again if any(_overlap(b, t) > 0.3 for t in targets)][: after - expected]
                    for box in still:
                        seed = secrets.randbelow(2**31)
                        seeds.append(seed)
                        res = _edit_region(run_wf, edited, [box], plan, engine, RETRY_GROW, seed)
                        if isinstance(res, str):
                            break
                        edited = res[0]
                    if still:
                        attempts = 2
                        edited.save(check)
                        again = locate(str(check), plan.target)
                        after = len(again) if again is not None else after
            elif plan.op == "change" and any(c in plan.replacement.split() for c in COLOR_WORDS):
                verified = ask_yes_no(str(check), f"Is the {plan.target} {plan.replacement}?", targets[0])
            elif plan.op == "move":
                again = locate(str(check), plan.target) or []
                verified = _moved(targets[0], new_box, again, plan.direction) if again else None
            try:
                check.unlink()
            except OSError:
                pass
    except Exception as exc:  # noqa: BLE001 — GpuUnavailable and ComfyUI failures become a reply
        reason = getattr(exc, "reason", None) or str(exc)
        return Outcome(message=f"ERROR: Image edit not started: {reason}")

    attached = [lbl for _, lbls in regions for lbl in lbls]
    meta = {"op": plan.op, "target": plan.target, "instruction": plan.instruction[:500], "engine": engine,
            "boxes": [[round(v, 4) for v in b] for rb, _ in regions for b in rb], "attached": attached,
            "seeds": seeds, "before": found, "after": after, "expected": expected, "attempts": attempts,
            "verified": verified, "mask_fraction": round(mask_px / (orig.size[0] * orig.size[1]), 4)}
    path = _save(edited, src, meta)
    took = time.monotonic() - t0
    where = "; ".join(_position(b, boxes) for b in targets)
    msg = _describe(plan, targets, where, found, after, expected, verified, attached)
    logger.info("local edit %s in %.1fs: %s", path, took, meta)
    return Outcome(path=path, message=msg, before=found, after=after, expected=expected,
                   detail={**meta, "seconds": round(took, 1)})


COLOR_WORDS = set(__import__("jarvis.image_edit_plan", fromlist=["COLORS"]).COLORS)


def _moved(old: Box, new: Box, found: list[Box], direction: str) -> bool:
    """Did an object end up nearer the target position than where it started?"""
    cx = lambda b: ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)  # noqa: E731
    (ox, oy), (nx, ny) = cx(old), cx(new)
    best = min(found, key=lambda b: (cx(b)[0] - nx) ** 2 + (cx(b)[1] - ny) ** 2)
    bx, by = cx(best)
    gone_from_old = not any(_overlap(b, old) > 0.6 for b in found)
    return gone_from_old and (bx - nx) ** 2 + (by - ny) ** 2 < (bx - ox) ** 2 + (by - oy) ** 2


def _describe(plan, targets, where, found, after, expected, verified, attached) -> str:
    keep = "everything outside the edited area is unchanged pixel for pixel"
    if plan.op == "remove":
        what = _count_word(len(targets), plan.target)
        with_ = f" together with its {', '.join(a.replace(f' of the {plan.target}', '') for a in attached)}" \
            if attached else ""
        note = (f"I counted {found}, not {plan.claimed_total}. "
                if plan.claimed_total not in (None, found) else "")
        if after is not None and after > expected:
            # Never report a removal the recount contradicts (live: "Removed 1 …" while it was still there).
            return (f"{note}I tried to remove {what} ({where}){with_}, but the count check still finds {after} "
                    f"(expected {expected}) — the edit may not have worked; {keep}")
        check = ("count check unavailable" if after is None else f"count check: {after} left ✓" if after == expected
                 else f"count check: expected {expected}, counted {after}")
        return f"{note}Removed {what} ({where}){with_}; {keep} ({check})"
    if plan.op == "replace":
        return f"Replaced the {plan.target} ({where}) with {plan.replacement}; {keep}"
    if plan.op == "change":
        tail = "" if verified is None else " (check: looks " + plan.replacement + " ✓)" if verified else \
            f" (check: the vision model does not see it as {plan.replacement} — the edit may not have worked)"
        return f"Made the {plan.target} ({where}) {plan.replacement}; {keep}{tail}"
    tail = "" if verified is None else " (check: moved ✓)" if verified else \
        " (check: the vision model does not find it at the new place — the move may not have worked)"
    return f"Moved the {plan.target} ({where}) {plan.amount + ' ' if plan.amount else ''}to the {plan.direction}; {keep}{tail}"


def _overlap(a: Box, b: Box) -> float:
    """Intersection over the smaller box (a re-detected object may be boxed a little differently)."""
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return ix * iy / small if small > 0 else 0.0
