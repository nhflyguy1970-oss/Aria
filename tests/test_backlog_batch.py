"""Tests for backlog items shipped in batch (26, 33, 36, 37, 44, 48, 51, 84)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def test_voice_latency_profile():
    from jarvis.voice_latency import voice_latency_profile

    prof = voice_latency_profile()
    assert "tts_chunk_max_chars" in prof
    assert prof["tts_chunk_max_chars"] >= 40


def test_cloud_live_session_stub():
    from jarvis.cloud_live_voice import cloud_live_status, end_live_session, start_live_session

    with patch.dict("os.environ", {"JARVIS_CLOUD_LIVE_VOICE": "1", "OPENAI_API_KEY": "sk-test"}):
        from importlib import reload
        import jarvis.p4_flags as p4

        reload(p4)
        import jarvis.cloud_live_voice as clv

        reload(clv)
        st = clv.cloud_live_status()
        assert st.get("provider") == "openai_realtime"
        sess = clv.start_live_session()
        assert sess.get("ok") is True
        sid = sess["session_id"]
        assert clv.end_live_session(sid).get("ok") is True


def test_browser_download_safety():
    from jarvis.browser_agent import _check_download_safe

    ok, _ = _check_download_safe("report.pdf", allow_downloads=False)
    assert ok is False
    ok2, _ = _check_download_safe("setup.exe", allow_downloads=False)
    assert ok2 is False
    ok3, _ = _check_download_safe("notes.txt", allow_downloads=True)
    assert ok3 is True


def test_browser_vlm_uses_browser_task():
    import inspect

    from jarvis import browser_vlm

    src = inspect.getsource(browser_vlm.vlm_plan_click)
    assert 'task="browser"' in src


def test_vision_browser_model_env():
    import os

    from jarvis.llm import vision_model_for_task

    with patch.dict(os.environ, {"JARVIS_BROWSER_VLM_MODEL": "custom-vlm:7b"}, clear=False):
        assert vision_model_for_task("browser") == "custom-vlm:7b"


def test_kasa_set_color_signature():
    from jarvis.kasa_devices import control_device, set_color

    assert callable(set_color)
    assert "hue" in inspect_signature(control_device)


def inspect_signature(fn):
    import inspect

    return str(inspect.signature(fn))


def test_first_run_downloads_voice_structure():
    from jarvis.first_run_downloads import ensure_voice_assets

    with patch("jarvis.first_run_downloads.ensure_piper_voice", return_value=(True, "ok")):
        with patch("jarvis.first_run_downloads.warm_whisper_weights", return_value=(True, "ok")):
            with patch("jarvis.config.piper_ready", return_value=True):
                out = ensure_voice_assets()
    assert out.get("ok") is True
    assert "piper_voice" in out.get("pulled", [])


def test_device_router_passes_color_kwargs():
    import inspect

    from jarvis import device_router

    src = inspect.getsource(device_router.control_device)
    assert "hue=kwargs.get" in src
