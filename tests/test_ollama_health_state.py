"""Ollama health_state: healthy / degraded / unavailable."""

from __future__ import annotations

import time
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


def test_soft_probe_skips_cold_model_without_generate():
    """Cold soft-probes orphan ~45s Ollama loads when the 5s client times out."""
    with patch.object(oh, "_list_via_http", return_value=(["qwen2.5:7b"], None)):
        with patch.object(oh, "_loaded_runner_names", return_value=[]):
            with patch.object(oh, "_soft_generate_probe") as probe:
                with patch.object(oh, "_probe_model_for_health", return_value="qwen2.5:7b"):
                    result = oh.refresh_inference_probe(force=False)
    probe.assert_not_called()
    assert result.get("skipped_cold") is True
    # API is up; skipping a cold generate is not a provider failure.
    assert "cold" in str(result.get("detail") or "").lower() or result.get("skipped_cold")


def test_soft_probe_runs_when_model_already_loaded():
    with patch.object(oh, "_list_via_http", return_value=(["qwen2.5:7b"], None)):
        with patch.object(oh, "_loaded_runner_names", return_value=["qwen2.5:7b"]):
            with patch.object(
                oh,
                "_soft_generate_probe",
                return_value={"ok": True, "detail": "generate ok", "model": "qwen2.5:7b", "elapsed_s": 0.1},
            ) as probe:
                with patch.object(oh, "_probe_model_for_health", return_value="qwen2.5:7b"):
                    result = oh.refresh_inference_probe(force=False)
    probe.assert_called_once()
    assert result["ok"] is True
    assert not result.get("skipped_cold")


def test_force_probe_may_cold_load():
    with patch.object(oh, "_loaded_runner_names", return_value=[]):
        with patch.object(
            oh,
            "_soft_generate_probe",
            return_value={"ok": True, "detail": "generate ok", "model": "qwen2.5:7b", "elapsed_s": 1.0},
        ) as probe:
            with patch.object(oh, "_probe_model_for_health", return_value="qwen2.5:7b"):
                result = oh.refresh_inference_probe(force=True)
    probe.assert_called_once()
    assert result["ok"] is True


def test_soft_probe_preserves_recent_live_success_when_cold():
    oh.note_inference_success("qwen2.5:7b")
    # Expire TTL so we enter the cold-skip path (not the early cache return).
    with oh._probe_lock:
        oh._probe_cache["at"] = time.time() - (oh._PROBE_TTL + 10)
    with patch.object(oh, "_loaded_runner_names", return_value=[]):
        with patch.object(oh, "_soft_generate_probe") as probe:
            with patch.object(oh, "_probe_model_for_health", return_value="qwen2.5:7b"):
                result = oh.refresh_inference_probe(force=False)
    probe.assert_not_called()
    assert result["ok"] is True
    assert result.get("skipped_cold") is True


def test_soft_generate_probe_includes_num_ctx(monkeypatch):
    """Probes must not omit num_ctx (daemon default 32768×parallel reloads chat)."""
    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"response":"ok"}'

    def fake_urlopen(req, timeout=0):
        import json

        captured["body"] = json.loads(req.data.decode())
        return _Resp()

    monkeypatch.setattr(oh.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("JARVIS_OLLAMA_NUM_CTX", "8192")
    out = oh._soft_generate_probe("http://127.0.0.1:11434", "qwen2.5:7b", timeout=2)
    assert out["ok"] is True
    assert captured["body"]["options"]["num_ctx"] == 8192
