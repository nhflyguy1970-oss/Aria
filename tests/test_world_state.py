"""Tests for world_state module."""

from __future__ import annotations

import json

import pytest


def test_world_state_enabled_default(monkeypatch):
    monkeypatch.delenv("JARVIS_WORLD_STATE", raising=False)
    monkeypatch.delenv("JARVIS_PRESET", raising=False)
    from jarvis.world_state import world_state_enabled

    assert world_state_enabled() is True


def test_world_state_preset_on(monkeypatch):
    monkeypatch.setenv("JARVIS_PRESET", "jarvis")
    from jarvis.world_state import jarvis_preset_enabled, world_state_enabled

    assert jarvis_preset_enabled()
    assert world_state_enabled()


def test_build_world_state_minimal(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_WORLD_STATE", "1")
    monkeypatch.setenv("JARVIS_HA_ENABLED", "0")
    (data_dir / "active_project.json").write_text(json.dumps({"slug": "jarvis"}), encoding="utf-8")
    from jarvis.world_state import build_world_state, world_state_summary

    state = build_world_state()
    assert "project" in state
    assert state["project"]["slug"] == "jarvis"
    md = world_state_summary(state)
    assert "World state" in md
    assert "jarvis" in md.lower()


def test_world_state_cache_ttl(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_WORLD_STATE_TTL", "60")
    from jarvis import world_state as ws

    ws._cache = None
    ws._cache_at = 0.0
    a = ws.refresh_world_state_cache()
    b = ws.refresh_world_state_cache()
    assert a["ts"] == b["ts"]
    c = ws.refresh_world_state_cache(force=True)
    assert c["ts"] != a["ts"] or c == a
