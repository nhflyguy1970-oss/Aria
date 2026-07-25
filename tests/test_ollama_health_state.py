"""Ollama health_state: healthy / degraded / unavailable."""

from __future__ import annotations

from unittest.mock import patch

import jarvis.ollama_health as oh


def setup_function():
    with oh._probe_lock:
        oh._probe_cache.update({
            "at": 0.0,
            "ok": None,
            "detail": "",
            "model": "",
            "elapsed_s": None,
        })


def test_unavailable_when_tags_fail():
    with patch.object(oh, "_list_via_http", return_value=([], "connection refused")):
        with patch.object(oh, "_list_via_cli", return_value=[]):
            result = oh.check_ollama(soft_probe=True)
    assert result["running"] is False
    assert result["health_state"] == "unavailable"


def test_degraded_when_generate_probe_fails():
    with patch.object(oh, "_list_via_http", return_value=(["qwen2.5:7b"], None)):
        with patch.object(
            oh,
            "_soft_generate_probe",
            return_value={"ok": False, "detail": "timed out", "model": "qwen2.5:7b", "elapsed_s": 5.0},
        ):
            result = oh.check_ollama(soft_probe=True, force_probe=True)
    assert result["running"] is True
    assert result["health_state"] == "degraded"
    assert "timed out" in (result.get("error") or "")


def test_healthy_when_generate_probe_ok():
    with patch.object(oh, "_list_via_http", return_value=(["qwen2.5:7b"], None)):
        with patch.object(
            oh,
            "_soft_generate_probe",
            return_value={"ok": True, "detail": "generate ok", "model": "qwen2.5:7b", "elapsed_s": 0.2},
        ):
            result = oh.check_ollama(soft_probe=True, force_probe=True)
    assert result["health_state"] == "healthy"


def test_soft_probe_false_uses_cache_without_generate():
    oh.note_inference_failure("wedged", model="qwen2.5:7b")
    with patch.object(oh, "_list_via_http", return_value=(["qwen2.5:7b"], None)):
        with patch.object(oh, "_soft_generate_probe") as probe:
            result = oh.check_ollama(soft_probe=False)
    probe.assert_not_called()
    assert result["health_state"] == "degraded"
    assert result["probe"]["cached"] is True


def test_note_inference_success_marks_healthy_on_lite_check():
    oh.note_inference_success("qwen2.5:7b")
    with patch.object(oh, "_list_via_http", return_value=(["qwen2.5:7b"], None)):
        result = oh.check_ollama(soft_probe=False)
    assert result["health_state"] == "healthy"
