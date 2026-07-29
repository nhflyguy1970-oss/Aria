"""Vision product — shared pipeline, OCR, import, profiles, honesty, a11y contracts."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_product_status_shape():
    from jarvis.vision_product.engine import product_status

    st = product_status()
    assert st["ok"] is True
    assert st["product"] == "Vision"
    assert "pipeline" in st
    assert "honesty" in st
    assert st["pipeline"][0] == "media_input"
    assert "vision_engine" in st["pipeline"]


def test_action_rail_complete():
    from jarvis.vision_product.engine import action_rail

    ids = {a["id"] for a in action_rail()}
    for needed in (
        "describe",
        "ocr",
        "ocr_structured",
        "tables",
        "identify",
        "compare",
        "image_to_code",
        "remember",
        "import",
        "translate",
        "summarize",
    ):
        assert needed in ids


def test_document_intel_ocr_uses_vision_product(tmp_path):
    from jarvis.intelligence import document_intel

    img = tmp_path / "x.png"
    img.write_bytes(b"not-a-real-png")
    with patch(
        "jarvis.vision_product.ocr.run_ocr",
        return_value={"ok": True, "text": "hello", "engine": "vlm", "confidence": 0.8},
    ):
        out = document_intel.ocr_image(img)
    assert out["ok"] is True
    assert out["text"] == "hello"


def test_vision_import_preview_from_path(tmp_path):
    from jarvis.vision_product.import_pipeline import vision_import

    img = tmp_path / "scan.png"
    img.write_bytes(b"x")
    with patch(
        "jarvis.vision_product.ocr.run_ocr",
        return_value={"ok": True, "text": "Buy milk\nCall mom", "engine": "vlm", "confidence": 0.7},
    ):
        out = vision_import(path=img, target="planner", source="test")
    assert out["ok"] is True
    assert out["pipeline"] == "vision_import"
    assert len(out["candidates"]) >= 2


def test_vision_import_pasted_ocr():
    from jarvis.vision_product.import_pipeline import vision_import

    out = vision_import(ocr_text="Meeting at 3pm\nBuy eggs", target="calendar", source="test")
    assert out["ok"] is True
    assert out["pipeline"] == "vision_import"
    assert out["requires_confirmation"] is True


def test_profiles_builtin_and_activate(tmp_path, monkeypatch):
    from jarvis.vision_product import profiles as vp
    from jarvis.vision_product import settings as vs

    monkeypatch.setattr(vp, "PROFILES_FILE", tmp_path / "profiles.json")
    monkeypatch.setattr(vs, "SETTINGS_FILE", tmp_path / "settings.json")
    with patch("jarvis.vision_product.settings.save_vision_quality"):
        with patch("jarvis.vision_product.settings.load_vision_quality", return_value="fast"):
            activated = vp.activate_profile("fast_scan")
    assert activated["id"] == "fast_scan"
    assert vs.load_settings().get("active_profile") == "fast_scan"


def test_profiles_include_required_builtins():
    from jarvis.vision_product.profiles import list_profiles

    ids = {p["id"] for p in list_profiles()}
    for needed in (
        "document_ocr",
        "research",
        "accessibility",
        "coding",
        "ui_review",
        "fast_scan",
        "deep_analysis",
        "naturalist",
    ):
        assert needed in ids


def test_history_redaction():
    from jarvis.vision_product.history import presentation_for_profile

    entry = {"analysis": "secret", "ocr": "secret ocr", "uncensored_origin": True, "prompt": "x"}
    open_v = presentation_for_profile(entry, censored=False)
    assert open_v["redacted"] is False
    closed = presentation_for_profile(entry, censored=True)
    assert closed["redacted"] is True
    assert "secret" not in closed["analysis"]


def test_honesty_report():
    from jarvis.vision_product.honesty import honesty_report

    with patch("jarvis.llm.vision_model_for_task", return_value="moondream:latest"):
        with patch(
            "jarvis.vision_product.settings.load_settings",
            return_value={"quality_mode": "fast", "ocr_mode": "auto", "warn_before_heavy": True},
        ):
            h = honesty_report(task="describe")
    assert h["ok"] is True
    assert h["model"]
    assert "estimated_vram_mb" in h
    assert "expected_latency" in h
    assert "fallback" in h


def test_analyze_describe_mocked():
    from jarvis.vision_product.engine import analyze

    assistant = MagicMock()
    assistant.vision.analyze.return_value = "A red cube."
    with patch(
        "jarvis.vision_product.engine.honesty_report",
        return_value={"model": "moondream", "warnings": [], "warn_before_heavy": False},
    ):
        with patch("jarvis.vision_product.engine.add_entry", return_value={"id": "abc"}):
            with patch("jarvis.vision_product.engine.set_vision_state"):
                with patch("jarvis.config.is_uncensored", return_value=False):
                    out = analyze(
                        path="/tmp/x.png",
                        action="describe",
                        assistant=assistant,
                        source="test",
                        force=True,
                    )
    assert out["ok"] is True
    assert "cube" in out["message"]
    assert out["pipeline"] == "vision_engine"


def test_analyze_ocr_uses_ocr_manager():
    from jarvis.vision_product.engine import analyze

    with patch(
        "jarvis.vision_product.engine.honesty_report",
        return_value={"model": "moondream", "warnings": [], "warn_before_heavy": False},
    ):
        with patch(
            "jarvis.vision_product.engine.run_ocr",
            return_value={"ok": True, "text": "Invoice 42", "confidence": 0.8, "engine": "vlm"},
        ):
            with patch("jarvis.vision_product.engine.add_entry", return_value={"id": "o1"}):
                with patch("jarvis.vision_product.engine.set_vision_state"):
                    with patch("jarvis.config.is_uncensored", return_value=False):
                        out = analyze(path="/tmp/x.png", action="ocr", force=True)
    assert out["ok"] is True
    assert out["ocr"] == "Invoice 42"


def test_hybrid_ocr_modes(tmp_path):
    from jarvis.vision_product import ocr as vo

    img = tmp_path / "t.png"
    img.write_bytes(b"x")
    with patch.object(vo, "classic_ocr_available", return_value=True):
        with patch.object(vo, "run_classic_ocr", return_value={"ok": True, "text": "AAAA", "engine": "classic", "confidence": 0.9}):
            with patch.object(vo, "run_vlm_ocr", return_value={"ok": True, "text": "BB", "engine": "vlm", "confidence": 0.6}):
                with patch("jarvis.vision_product.settings.load_settings", return_value={"ocr_mode": "hybrid", "confidence_threshold": 0.5}):
                    out = vo.run_ocr(img, mode="hybrid")
    assert out["ok"] is True
    assert out["engine"] == "hybrid"


def test_gallery_meta_stores_ocr():
    from jarvis.gallery_product import metadata as meta

    with patch.object(meta, "set_meta", side_effect=lambda name, patch, **kw: {"ok": True, "meta": patch}):
        with patch("jarvis.vision_product.engine.analyze") as an:
            an.side_effect = [
                {"ok": True, "message": "A sunset"},
                {"ok": True, "ocr": "HELLO", "message": "HELLO"},
            ]
            with patch("jarvis.gallery_product.visibility.is_restricted_for_viewer", return_value=False):
                out = meta.generate_vision_meta("a.png", "/tmp/a.png", assistant=MagicMock())
    assert out["ok"] is True
    assert out["meta"]["ocr_text"] == "HELLO"


def test_mission_panel():
    from jarvis.vision_product.mission_bridge import vision_mission_panel

    panel = vision_mission_panel()
    assert panel["product"] == "Vision"
    assert "deep_links" in panel


def test_batch_cancel_shape():
    from jarvis.vision_product.batch import cancel_job, start_batch

    with patch("jarvis.vision_product.batch.Path.is_file", return_value=False):
        job = start_batch([], action="describe")
    assert job["ok"] is True
    assert cancel_job(job["job"]["id"])["ok"] is True


def test_capability_inventory_not_comfyui():
    text = Path("/media/jeff/AI/jarvis/docs/aria_core/CAPABILITY_INVENTORY.md").read_text(encoding="utf-8")
    line = [ln for ln in text.splitlines() if "vision-media" in ln][0]
    assert "vision_media" in line or "modules/vision" in line
    assert "ollama" in line.lower() or "vlm" in line.lower()
    assert "not comfyui" in line.lower()


def test_terminology_boundaries():
    from jarvis.vision_product.terminology import BOUNDARIES

    assert "image_understanding" in BOUNDARIES["owns"]
    assert "image_generation" in BOUNDARIES["does_not_own"]
    assert "presence_gestures" in BOUNDARIES["does_not_own"]


def test_behavior_routes_through_product():
    from jarvis.behaviors.vision.engine import VisionActionEngine

    ctx = MagicMock()
    ctx.session.resolve_image.return_value = "/tmp/photo.png"
    with patch(
        "jarvis.vision_product.engine.analyze",
        return_value={"ok": True, "message": "line one", "pipeline": "vision_engine", "warnings": []},
    ) as an:
        result = VisionActionEngine.ocr_image(ctx, {}, "ocr")
    assert result.get("ok") is True
    assert "line one" in result.get("message", "")
    an.assert_called_once()
    assert an.call_args.kwargs.get("action") == "ocr"
    assert an.call_args.kwargs.get("source") == "chat"


def test_voice_bridge_requires_image():
    from jarvis.vision_product.voice_bridge import voice_vision_command

    with patch("jarvis.vision_product.voice_bridge.latest_upload_image", return_value=None):
        out = voice_vision_command("ocr")
    assert out["ok"] is False


def test_voice_intent_vision_route():
    from jarvis.voice_product.intent_router import route_utterance

    r = route_utterance("describe this image")
    assert r is not None
    assert r["product"] == "vision"
    assert r["action"] == "describe"


def test_experimental_gated():
    from jarvis.vision_product.experimental import experimental_status, temporal_compare

    st = experimental_status()
    assert st["experimental"] is True
    out = temporal_compare("/a.png", "/b.png")
    assert out["ok"] is False
    assert "disabled" in (out.get("error") or "")


def test_docs_exist():
    assert Path("/media/jeff/AI/jarvis/docs/VISION_IMPLEMENTATION.md").is_file()


def test_accessibility_action_rail_labels():
    from jarvis.vision_product.engine import action_rail

    for a in action_rail():
        assert a["label"]
        assert a["id"]
