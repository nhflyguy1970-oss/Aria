"""Tests for interrupt_policy module."""

from __future__ import annotations

import pytest


def test_should_interrupt_focus_mode(monkeypatch):
    from jarvis import interrupt_policy as ip

    monkeypatch.setattr(
        "jarvis.config._load_chat_settings",
        lambda: {"scene_state": {"active_preset": "focus mode"}},
    )
    ip._focus_mode = False
    assert ip.should_interrupt(tier="useful") is False
    assert ip.should_interrupt(tier="urgent") is True


def test_should_interrupt_voice_active():
    from jarvis import interrupt_policy as ip

    ip._voice_state = "speaking"
    ip._focus_mode = False
    assert ip.should_interrupt(tier="useful") is False
    ip._voice_state = "idle"


def test_evaluate_interrupt_suppressed(monkeypatch):
    from jarvis import interrupt_policy as ip

    ip._focus_mode = True
    monkeypatch.setattr(ip, "_notify", lambda *a, **k: None)
    out = ip.evaluate_interrupt("test", title="T", body="B", tier="useful")
    assert out["fired"] is False
    ip._focus_mode = False


def test_evaluate_interrupt_fires(monkeypatch):
    from jarvis import interrupt_policy as ip

    ip._focus_mode = False
    ip._voice_state = "idle"
    calls = []
    monkeypatch.setattr(ip, "_notify", lambda t, b: calls.append((t, b)))
    out = ip.evaluate_interrupt("job_complete", title="ARIA", body="Done", tier="useful")
    assert out["fired"] is True
    assert calls
