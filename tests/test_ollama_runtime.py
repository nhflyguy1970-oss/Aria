"""Tests for Ollama runtime helpers."""

from __future__ import annotations

from unittest.mock import patch


def test_probe_model_name_uses_general_model():
    from jarvis.ollama_runtime import probe_model_name

    with patch("jarvis.llm.general_model", return_value="qwen2.5:7b"):
        assert probe_model_name() == "qwen2.5:7b"


def test_probe_model_name_env_override():
    from jarvis.ollama_runtime import probe_model_name

    with patch.dict("os.environ", {"JARVIS_PROBE_OLLAMA_MODEL": "qwen3:1.7b"}, clear=False):
        assert probe_model_name() == "qwen3:1.7b"


def test_default_num_ctx_from_env():
    from jarvis.ollama_runtime import default_num_ctx

    with patch.dict("os.environ", {"JARVIS_OLLAMA_NUM_CTX": "4096"}, clear=False):
        assert default_num_ctx() == 4096


def test_run_inference_probe_success():
    from jarvis.ollama_runtime import run_inference_probe

    payload = {
        "response": "OK",
        "load_duration": 500_000_000,
        "prompt_eval_duration": 10_000_000,
        "eval_duration": 20_000_000,
        "eval_count": 2,
    }
    with patch("jarvis.ollama_runtime._http_generate", return_value=(payload, 0.5)):
        result = run_inference_probe("qwen2.5:7b")
    assert result["ok"] is True
    assert result["model"] == "qwen2.5:7b"
    assert result["tokens_per_sec"] > 0
