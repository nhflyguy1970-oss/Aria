"""Song generation resource planning."""

from jarvis.ml_memory import song_generation_plan


def test_safe_mode_explicit(monkeypatch):
    monkeypatch.setenv("JARVIS_SONG_MODE", "safe")
    monkeypatch.setenv("JARVIS_SONG_VOCALS", "0")
    monkeypatch.setattr("jarvis.gpu.detect_gpu", lambda: {"vram_mb": 8176})
    monkeypatch.setattr("jarvis.gpu.is_low_vram", lambda threshold_mb=10240: True)
    monkeypatch.setattr("jarvis.ml_memory.system_ram_gb", lambda: 62.0)

    plan = song_generation_plan(30)
    assert plan["mode"] == "safe"
    assert plan["allow_vocals"] is False
    assert plan["duration"] == 15


def test_balanced_auto_on_8gb_64gb(monkeypatch):
    monkeypatch.delenv("JARVIS_SONG_MODE", raising=False)
    monkeypatch.delenv("JARVIS_SONG_SAFE", raising=False)
    monkeypatch.setenv("JARVIS_SONG_VOCALS", "1")
    monkeypatch.setattr("jarvis.gpu.detect_gpu", lambda: {"vram_mb": 8176})
    monkeypatch.setattr("jarvis.gpu.is_low_vram", lambda threshold_mb=10240: True)
    monkeypatch.setattr("jarvis.ml_memory.system_ram_gb", lambda: 62.0)

    plan = song_generation_plan(30)
    assert plan["mode"] == "balanced"
    assert plan["allow_vocals"] is True
    assert plan["vocal_device"] == "cpu"
    assert plan["music_device"] == "cuda"
    assert plan["duration"] == 30
    assert "Balanced mode" in plan["warning"]


def test_max_mode(monkeypatch):
    monkeypatch.setenv("JARVIS_SONG_MODE", "max")
    monkeypatch.delenv("JARVIS_SONG_VOCALS", raising=False)
    monkeypatch.setattr("jarvis.gpu.is_low_vram", lambda threshold_mb=10240: True)
    monkeypatch.setattr("jarvis.ml_memory.system_ram_gb", lambda: 62.0)

    plan = song_generation_plan(30)
    assert plan["mode"] == "max"
    assert plan["allow_vocals"] is True
    assert plan["duration"] == 30
