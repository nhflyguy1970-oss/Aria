"""Vision action implementations — OCR, analysis, compare, and batch."""

from __future__ import annotations

from pathlib import Path

from jarvis import fs, llm
from jarvis.behaviors.vision.context import VisionContext
from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.modules.vision import IMAGE_EXTENSIONS
from jarvis.response import err, ok
from jarvis.vision_media import apply_crop_bytes, parse_region

UPLOAD_DIR = DATA_DIR / "uploads"


class VisionActionEngine:
    @classmethod
    def _vision_warnings(cls, ctx: VisionContext) -> list[str]:
        model = llm.vision_model().lower()
        if ctx.orchestrator._vision_llava_warned:
            return []
        heavy = "llava" in model and "13" in model
        big_llama = "llama3.2-vision" in model or "llama3.2-vision" in model.replace("_", ".")
        if not heavy and not big_llama:
            return []
        ctx.orchestrator._vision_llava_warned = True
        if heavy:
            return [
                "Vision is using llava:13b — heavy on 8GB GPUs. "
                "Use Fast mode (moondream) or llama3.2-vision:11b if you see freezes.",
            ]
        return [
            "Vision is using llama3.2-vision:11b — moderate VRAM use on 8GB. "
            "Switch to Fast mode if responses stall.",
        ]

    @classmethod
    def _vision_ok(cls, ctx: VisionContext, answer: str, *, image_path: str | None = None) -> dict:
        extra: dict = {}
        if image_path:
            extra["image_path"] = image_path
        warnings = cls._vision_warnings(ctx)
        if warnings:
            extra["warnings"] = warnings
        return ok(answer, module="vision", **extra)

    @classmethod
    def describe_image(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Which image? Attach one or give me a path.")
        answer = ctx.vision.analyze("Describe this image in detail.", path)
        if answer.startswith("ERROR:"):
            return err(answer)
        return cls._vision_ok(ctx, answer, image_path=path)

    @classmethod
    def analyze_image(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        from jarvis.vision_media import build_vision_prompt, vision_task_for_question

        path = ctx.session.resolve_image(params.get("path", ""))
        question = params.get("question") or message
        if not path:
            return err("Which image?")
        task = vision_task_for_question(question)
        prompt = build_vision_prompt(question, task)
        answer = ctx.vision.analyze(prompt, path, task=task)
        if answer.startswith("ERROR:"):
            return err(answer)
        return cls._vision_ok(ctx, answer, image_path=path)

    @classmethod
    def ocr_image(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Which image? Attach one or give me a path.")
        answer = ctx.vision.ocr(path)
        if answer.startswith("ERROR:"):
            return err(answer)
        return cls._vision_ok(ctx, answer, image_path=path)

    @classmethod
    def ocr_structured_image(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Which image? Attach one or give me a path.")
        answer = ctx.vision.ocr_structured(path)
        if answer.startswith("ERROR:"):
            return err(answer)
        return cls._vision_ok(ctx, answer, image_path=path)

    @classmethod
    def image_to_code(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Attach a UI screenshot to convert to code.")
        answer = ctx.vision.image_to_code(path)
        if answer.startswith("ERROR:"):
            return err(answer)
        return cls._vision_ok(ctx, answer, image_path=path)

    @classmethod
    def analyze_region(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Which image?")
        crop = parse_region(message, params.get("crop"))
        analyze_path = path
        if crop:
            try:
                cropped = apply_crop_bytes(Path(path).read_bytes(), crop)
                region_file = UPLOAD_DIR / f"region_{Path(path).stem}.jpg"
                region_file.write_bytes(cropped)
                analyze_path = str(region_file)
            except Exception as exc:
                return err(str(exc))
        question = params.get("question") or message or "What is in this region?"
        answer = ctx.vision.analyze(question, analyze_path, task="region")
        if answer.startswith("ERROR:"):
            return err(answer)
        return cls._vision_ok(ctx, answer, image_path=analyze_path)

    @classmethod
    def compare_from_result(cls, ctx: VisionContext, payload: dict) -> dict:
        answer = payload.get("answer", "")
        if answer.startswith("ERROR:"):
            return err(answer)
        extra = {
            "compare_paths": [payload.get("path1"), payload.get("path2")],
            "action": "compare_images",
        }
        if payload.get("diff_path"):
            extra["diff_path"] = payload["diff_path"]
        warnings = cls._vision_warnings(ctx)
        if warnings:
            extra["warnings"] = warnings
        return ok(answer, module="vision", **extra)

    @classmethod
    def compare_images(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path1 = params.get("path1", "")
        path2 = params.get("path2", "")
        if not path1 or not path2:
            return err("Usage: compare <image1> with <image2>")
        question = params.get("question") or message
        result = ctx.vision.compare(
            path1,
            path2,
            question if question != message else None,
            uploads_dir=UPLOAD_DIR,
        )
        answer = result.get("answer", "")
        if answer.startswith("ERROR:"):
            return err(answer)
        return cls.compare_from_result(ctx, result)

    @classmethod
    def batch_vision(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        folder = params.get("folder", "")
        try:
            root = fs.resolve_path(folder, base=PROJECT_ROOT)
        except fs.PathError as exc:
            return err(str(exc))
        if not root.is_dir():
            return err(f"Not a folder: {folder}")
        images = sorted(
            path for path in root.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )[:15]
        if not images:
            return err(f"No images found in {folder}")
        lines = []
        for image in images:
            description = ctx.vision.analyze(
                "Briefly describe this image in 2-3 sentences.",
                str(image),
                task="batch",
            )
            if description.startswith("ERROR:"):
                lines.append(f"**{image.name}**: (failed)")
            else:
                lines.append(f"**{image.name}**: {description}")
        return ok("\n\n".join(lines), module="vision")
