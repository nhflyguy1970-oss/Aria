"""Vision action implementations — route through shared vision_product pipeline."""

from __future__ import annotations

from pathlib import Path

from jarvis import fs
from jarvis.behaviors.vision.context import VisionContext
from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.modules.vision import IMAGE_EXTENSIONS
from jarvis.response import err, ok

UPLOAD_DIR = DATA_DIR / "uploads"


class VisionActionEngine:
    @classmethod
    def _via_product(
        cls,
        ctx: VisionContext,
        *,
        path: str | None = None,
        path2: str | None = None,
        action: str = "describe",
        question: str = "",
        crop: dict | None = None,
        speak: bool = False,
    ) -> dict:
        from jarvis.vision_product.engine import analyze

        out = analyze(
            path=path,
            path2=path2,
            action=action,
            question=question,
            crop=crop,
            source="chat",
            assistant=getattr(ctx, "orchestrator", None) or getattr(ctx, "assistant", None),
            speak=speak,
            force=True,
        )
        if not out.get("ok"):
            return err(out.get("error") or out.get("message") or "Vision failed")
        extra: dict = {
            "pipeline": out.get("pipeline") or "vision_engine",
            "honesty": out.get("honesty"),
            "latency_ms": out.get("latency_ms"),
            "history_id": out.get("history_id"),
            "confidence": out.get("confidence"),
        }
        if out.get("image_path") or path:
            extra["image_path"] = out.get("image_path") or path
        if out.get("diff_path"):
            extra["diff_path"] = out["diff_path"]
        if out.get("compare_paths"):
            extra["compare_paths"] = out["compare_paths"]
        warnings = list(out.get("warnings") or [])
        if warnings:
            extra["warnings"] = warnings
        return ok(out.get("message") or out.get("analysis") or "", module="vision", **extra)

    @classmethod
    def describe_image(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Which image? Attach one or give me a path.")
        return cls._via_product(ctx, path=path, action="describe", question="Describe this image in detail.")

    @classmethod
    def analyze_image(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        question = params.get("question") or message
        if not path:
            return err("Which image?")
        return cls._via_product(ctx, path=path, action="describe", question=question)

    @classmethod
    def ocr_image(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Which image? Attach one or give me a path.")
        speak = bool(params.get("speak")) or "speak" in (message or "").lower()
        return cls._via_product(ctx, path=path, action="ocr", speak=speak)

    @classmethod
    def ocr_structured_image(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Which image? Attach one or give me a path.")
        return cls._via_product(ctx, path=path, action="ocr_structured")

    @classmethod
    def image_to_code(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Attach a UI screenshot to convert to code.")
        return cls._via_product(ctx, path=path, action="image_to_code")

    @classmethod
    def analyze_region(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Which image?")
        question = params.get("question") or message or "What is in this region?"
        return cls._via_product(
            ctx,
            path=path,
            action="region",
            question=question,
            crop=params.get("crop"),
        )

    @classmethod
    def compare_from_result(cls, ctx: VisionContext, payload: dict) -> dict:
        answer = payload.get("answer", "")
        if str(answer).startswith("ERROR:"):
            return err(answer)
        extra = {
            "compare_paths": [payload.get("path1"), payload.get("path2")],
            "action": "compare_images",
            "pipeline": "vision_engine",
        }
        if payload.get("diff_path"):
            extra["diff_path"] = payload["diff_path"]
        if payload.get("warnings"):
            extra["warnings"] = payload["warnings"]
        return ok(answer, module="vision", **extra)

    @classmethod
    def compare_images(cls, ctx: VisionContext, params: dict, message: str) -> dict:
        path1 = params.get("path1", "")
        path2 = params.get("path2", "")
        if not path1 or not path2:
            return err("Usage: compare <image1> with <image2>")
        question = params.get("question") or message
        return cls._via_product(
            ctx,
            path=path1,
            path2=path2,
            action="compare",
            question=question if question != message else "",
        )

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
        from jarvis.vision_product.batch import start_batch

        job = start_batch(
            [str(p) for p in images],
            action="describe",
            source="chat_batch",
            assistant=getattr(ctx, "orchestrator", None),
        )
        if not job.get("ok"):
            return err(job.get("error") or "Batch failed")
        return ok(
            f"Vision batch started ({len(images)} images). Track in Vision Home / Mission Control.",
            module="vision",
            job_id=(job.get("job") or {}).get("id"),
            pipeline="vision_engine",
        )
