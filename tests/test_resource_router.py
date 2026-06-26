"""Resource-aware routing tests."""

import pytest

from jarvis.resource_router import (
    check_media_enqueue,
    preflight,
    record_media_outcome,
    routing_enabled,
    suggested_for_action,
)


def test_routing_enabled_default():
    assert routing_enabled() is True


def test_preflight_low_vram(monkeypatch):
    monkeypatch.setattr("jarvis.resource_router.detect_gpu", lambda **k: {"vram_mb": 8176, "ollama_using_gpu": True})
    monkeypatch.setattr("jarvis.resource_router.is_low_vram", lambda threshold_mb=10240: True)
    monkeypatch.setattr("jarvis.resource_router.ollama_loaded_models", lambda: [{"name": "qwen2.5:14b"}])
    monkeypatch.setattr("jarvis.resource_router.snapshot", lambda: {
        "low_vram": True,
        "vram_mb": 8176,
        "ollama_models_loaded": 1,
        "media_queue": {"busy": False, "pending": 0, "queue_depth": 0},
        "ram_available_gb": 32,
    })
    monkeypatch.setattr("jarvis.vram_guard.recommendations", lambda: ["Use 7B models"])
    pf = preflight("generate_video")
    assert pf["allow"] is True
    assert any("Ollama" in w for w in pf["warnings"])
    assert pf["adjustments"]


def test_check_media_enqueue_blocked_when_strict(monkeypatch):
    monkeypatch.setattr("jarvis.resource_router.strict_queue", lambda: True)
    monkeypatch.setattr("jarvis.resource_router.max_media_queue", lambda: 2)
    monkeypatch.setattr("jarvis.resource_router.preflight", lambda action: {
        "allow": False,
        "blocked": True,
        "warnings": ["Queue full"],
        "adjustments": [],
        "resources": {"media_queue": {"busy": True, "pending": 2, "queue_depth": 3, "label": "Video"}, "low_vram": True},
    })
    check = check_media_enqueue("generate_image")
    assert check["allowed"] is False
    assert check["blocked"] is True


def test_record_and_suggest_settings(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.resource_router._SETTINGS_FILE", data_dir / "resource_settings.json")
    monkeypatch.setattr("jarvis.resource_router.detect_gpu", lambda **k: {"vram_mb": 8176})
    monkeypatch.setattr("jarvis.resource_router.is_low_vram", lambda threshold_mb=10240: True)
    record_media_outcome("generate_video", ok=True, method="ken_burns", detail="ok")
    last = suggested_for_action("generate_video")
    assert last.get("method") == "ken_burns"


def test_prepare_for_media_job(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.resource_router.routing_enabled", lambda: True)
    monkeypatch.setattr("jarvis.resource_router.is_low_vram", lambda threshold_mb=10240: True)
    monkeypatch.setattr("jarvis.vram_guard.vram_guard_enabled", lambda: True)
    monkeypatch.setattr("jarvis.vram_guard.prepare_for_comfyui", lambda: {"ok": True, "unloaded_ollama": ["m"]})
    from jarvis.resource_router import prepare_for_media_job

    result = prepare_for_media_job("generate_image")
    assert result.get("prepared") is True
