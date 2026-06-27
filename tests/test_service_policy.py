"""Lazy startup policy defaults."""

from jarvis.service_policy import (
    autostart_comfyui,
    autostart_ha,
    auto_pull_models_enabled,
    lazy_startup_enabled,
    model_warmup_enabled,
    router_warmup_enabled,
)


def test_lazy_defaults_on(monkeypatch):
    monkeypatch.delenv("JARVIS_LAZY_STARTUP", raising=False)
    assert lazy_startup_enabled() is True


def test_heavy_autostart_defaults_off(monkeypatch):
    for name in (
        "JARVIS_AUTOSTART_COMFYUI",
        "JARVIS_HA_AUTOSTART",
        "JARVIS_MODEL_WARMUP",
        "JARVIS_WARM_ROUTER",
        "JARVIS_AUTO_PULL_MODELS",
    ):
        monkeypatch.delenv(name, raising=False)
    assert autostart_comfyui() is False
    assert autostart_ha() is False
    assert model_warmup_enabled() is False
    assert router_warmup_enabled() is False
    assert auto_pull_models_enabled() is False
