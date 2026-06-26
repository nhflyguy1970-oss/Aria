from jarvis.modules import image as img


def test_prompt_model_uses_general_in_uncensored(monkeypatch):
    monkeypatch.setenv("JARVIS_IMAGE_PROMPT_MODEL", "")
    monkeypatch.delenv("JARVIS_IMAGE_PROMPT_MODEL_UNCENSORED", raising=False)
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    monkeypatch.setattr("jarvis.model_store.get_models", lambda: {"general": "dolphin3:latest"})
    assert img.prompt_model_name() == "dolphin3:latest"


def test_prompt_model_standard_env_not_used_in_uncensored(monkeypatch):
    monkeypatch.setenv("JARVIS_IMAGE_PROMPT_MODEL", "qwen2.5:7b")
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    monkeypatch.setattr("jarvis.model_store.get_models", lambda: {"general": "dolphin3:latest"})
    assert img.prompt_model_name() == "dolphin3:latest"


def test_prompt_model_env_override_standard_only(monkeypatch):
    monkeypatch.setenv("JARVIS_IMAGE_PROMPT_MODEL", "custom:latest")
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: False)
    assert img.prompt_model_name() == "custom:latest"


def test_active_model_family_realvis(monkeypatch):
    monkeypatch.setattr(
        "jarvis.comfyui_settings.resolve_checkpoint_name",
        lambda: "RealVisXL_V5.0_fp16.safetensors",
    )
    assert img._active_model_family() == "sdxl"


def test_active_model_family_realistic_vision(monkeypatch):
    monkeypatch.setattr(
        "jarvis.comfyui_settings.resolve_checkpoint_name",
        lambda: "Realistic_Vision_V6.0_NV_B1_fp16.safetensors",
    )
    assert img._active_model_family() == "sd15"
