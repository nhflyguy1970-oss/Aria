"""Tests for extended vision features."""

from pathlib import Path

import pytest
from jarvis.router import route
from jarvis.session import SessionContext
from jarvis.vision_media import (
    REGION_PRESETS,
    build_visual_diff,
    parse_region,
    parse_video_second,
)
from PIL import Image


@pytest.fixture
def session():
    return SessionContext()


def _png(path: Path, color: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32), color).save(path)


def test_structured_ocr_route(session):
    att = {"path": "/tmp/x.png", "kind": "image"}
    intent = route("Structured OCR — extract tables as markdown", session, att)
    assert intent["action"] == "ocr_structured_image"


def test_image_to_code_route(session):
    att = {"path": "/tmp/ui.png", "kind": "image"}
    intent = route("Convert this UI screenshot to HTML", session, att)
    assert intent["action"] == "image_to_code"


def test_region_route(session):
    att = {"path": "/tmp/x.png", "kind": "image"}
    intent = route("What's in the top-left region?", session, att)
    assert intent["action"] == "analyze_region"
    assert intent["params"]["crop"] == REGION_PRESETS["top left"]


def test_remember_image_route(session):
    att = {"path": "/tmp/x.png", "kind": "image"}
    intent = route("Remember what this screenshot says", session, att)
    assert intent["action"] == "remember_image"


def test_batch_vision_route(session):
    intent = route("analyze all images in data/uploads", session)
    assert intent["action"] == "batch_vision"


def test_parse_video_second():
    assert parse_video_second("analyze at 1:30") == 90.0
    assert parse_video_second("", explicit=12.5) == 12.5


def test_parse_region_bbox():
    crop = parse_region("check region 10,20,30,40")
    assert crop == {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}


def test_build_visual_diff(data_dir):
    a = data_dir / "uploads" / "da.png"
    b = data_dir / "uploads" / "db.png"
    _png(a, "red")
    _png(b, "blue")
    out = build_visual_diff(a, b, data_dir / "uploads")
    assert out is not None
    assert out.exists()


def test_vision_model_for_task(monkeypatch):
    from jarvis import llm

    monkeypatch.setattr(llm, "model_for", lambda role: "moondream:latest")
    monkeypatch.setattr("jarvis.config.load_vision_quality", lambda: "fast")
    assert llm.vision_model_for_task("describe") == "moondream:latest"
    assert llm.vision_model_for_task("ocr") == "moondream:latest"

    monkeypatch.setattr("jarvis.config.load_vision_quality", lambda: "quality")
    monkeypatch.setattr(
        "jarvis.model_store._installed",
        lambda: ["llama3.2-vision:11b", "moondream:latest"],
    )
    monkeypatch.setattr("jarvis.gpu.is_low_vram", lambda: True)
    monkeypatch.setattr("jarvis.ollama_health.supports_mllama", lambda refresh=False: True)
    assert "llama3.2-vision" in llm.vision_model_for_task("ocr")

    monkeypatch.setattr("jarvis.config.load_vision_quality", lambda: "custom")
    monkeypatch.setattr(
        "jarvis.model_store._installed",
        lambda: ["moondream:latest", "llava:13b"],
    )
    assert llm.vision_model_for_task("describe") == "moondream:latest"
    assert llm.vision_model_for_task("identify") == "llava:13b"


def test_vision_task_for_species_question():
    from jarvis.vision_media import build_vision_prompt, vision_task_for_question

    q = "what species is this"
    assert vision_task_for_question(q) == "identify"
    assert "scientific name" in build_vision_prompt(q, "identify").lower()
