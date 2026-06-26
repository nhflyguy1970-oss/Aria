"""Model settings — missing-model detection for Ollama pulls."""

from jarvis.model_store import get_missing_models, is_ollama_pullable


def test_is_ollama_pullable_skips_image_backends():
    assert is_ollama_pullable("qwen2.5:7b") is True
    assert is_ollama_pullable("comfyui") is False
    assert is_ollama_pullable("") is False


def test_get_missing_models_excludes_comfyui(monkeypatch):
    monkeypatch.setattr(
        "jarvis.model_store.get_models",
        lambda: {
            "general": "qwen2.5:7b",
            "coder": "qwen2.5-coder:14b",
            "review": "qwen2.5:7b",
            "vision": "moondream:latest",
            "image": "comfyui",
            "embed": "nomic-embed-text",
        },
    )
    monkeypatch.setattr(
        "jarvis.model_store._installed",
        lambda: ["qwen2.5:7b", "qwen2.5-coder:14b", "moondream:latest", "nomic-embed-text:latest"],
    )
    assert get_missing_models() == []


def test_vision_fallback_when_mllama_unsupported(monkeypatch):
    from jarvis.model_store import get_models

    monkeypatch.setattr("jarvis.model_store._installed", lambda: ["llama3.2-vision:11b", "moondream:latest", "llava:13b"])
    monkeypatch.setattr("jarvis.ollama_health.supports_mllama", lambda: False)
    monkeypatch.setattr(
        "jarvis.model_store._load_raw",
        lambda: {
            "standard": {"vision": "llama3.2-vision:11b"},
            "uncensored": {},
        },
    )
    monkeypatch.setattr("jarvis.config.load_vision_quality", lambda: "custom")
    assert get_models()["vision"] == "llava:13b"


def test_supports_mllama_old_ollama(monkeypatch):
    import jarvis.ollama_health as oh
    from jarvis.ollama_health import supports_mllama

    oh._MLLAMA_SUPPORT = None
    monkeypatch.setattr(oh, "ollama_version", lambda: (0, 30, 7))
    assert supports_mllama(refresh=True) is False
    oh._MLLAMA_SUPPORT = None
    monkeypatch.setattr(oh, "ollama_version", lambda: (0, 24, 0))
    assert supports_mllama(refresh=True) is True
