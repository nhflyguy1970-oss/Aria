"""Tests for action_confidence module."""

from __future__ import annotations

import pytest


def test_confidence_insufficient_samples(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_CONFIDENCE_MIN_SAMPLES", "5")
    from jarvis import action_confidence as ac

    ac._loaded = False
    ac._stats = {}
    assert ac.confidence_for("ha_control") == 0.5
    assert ac.confidence_tier("ha_control") == "medium"


def test_confidence_after_outcomes(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_CONFIDENCE_MIN_SAMPLES", "3")
    from jarvis import action_confidence as ac

    ac._loaded = False
    ac._stats = {}
    ac.STORE_FILE = data_dir / "action_confidence.json"
    for _ in range(4):
        ac.record_outcome("ha_control", ok=True)
    ac.record_outcome("ha_control", ok=False)
    c = ac.confidence_for("ha_control")
    assert 0.7 <= c <= 0.9
    assert ac.confidence_tier("ha_control") == "high"


def test_autonomy_decision_low(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_CONFIDENCE_MIN_SAMPLES", "3")
    monkeypatch.setenv("JARVIS_CONFIDENCE_LOW", "0.45")
    from jarvis import action_confidence as ac

    ac._loaded = False
    ac._stats = {"workflow_run": {"success": 0, "failure": 5}}
    ac.STORE_FILE = data_dir / "action_confidence.json"
    d = ac.autonomy_decision("workflow_run")
    assert d["needs_confirm"] is True
    assert d["tier"] == "low"
