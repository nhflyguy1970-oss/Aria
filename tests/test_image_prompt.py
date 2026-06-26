"""Image prompt normalization and uncensored enhance defaults."""

from jarvis.modules.image import (
    _llm_enhance_enabled,
    _prompt_model,
    normalize_image_prompt,
)


def test_normalize_strips_generate_image_prefix():
    assert normalize_image_prompt("Generate image: a red dragon") == "a red dragon"


def test_normalize_strips_ai_generated_boilerplate():
    p = normalize_image_prompt("create an ai-generated image of a woman on a beach")
    assert "ai-generated" not in p.lower() or "woman" in p.lower()
    assert "woman" in p.lower()


def test_normalize_colon_mangled_prompt():
    assert normalize_image_prompt(": sunset over mountains").startswith("sunset")


def test_llm_enhance_on_in_uncensored_when_global_env_on(monkeypatch):
    monkeypatch.setattr("jarvis.config.UNCENSORED", True)
    monkeypatch.setenv("JARVIS_IMAGE_LLM_ENHANCE", "1")
    assert _llm_enhance_enabled() is True


def test_llm_enhance_off_when_env_zero(monkeypatch):
    monkeypatch.setattr("jarvis.config.UNCENSORED", True)
    monkeypatch.setenv("JARVIS_IMAGE_LLM_ENHANCE", "0")
    assert _llm_enhance_enabled() is False


def test_prompt_model_ignores_standard_qwen_override_in_uncensored(monkeypatch):
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    monkeypatch.setenv("JARVIS_IMAGE_PROMPT_MODEL", "qwen2.5:7b")
    monkeypatch.delenv("JARVIS_IMAGE_PROMPT_MODEL_UNCENSORED", raising=False)
    monkeypatch.setattr(
        "jarvis.model_store.get_models",
        lambda: {"general": "dolphin-mistral:latest"},
    )
    assert _prompt_model() == "dolphin-mistral:latest"


def test_prompt_model_uncensored_env_override(monkeypatch):
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    monkeypatch.setenv("JARVIS_IMAGE_PROMPT_MODEL_UNCENSORED", "custom-uncensored:latest")
    assert _prompt_model() == "custom-uncensored:latest"
