"""Tests for partial backlog completions."""

from __future__ import annotations

import json
from pathlib import Path


def test_image_extensions_exported():
    from jarvis.vision_media import IMAGE_EXTENSIONS

    assert ".png" in IMAGE_EXTENSIONS
    assert ".jpg" in IMAGE_EXTENSIONS


def test_room_aliases_resolve():
    from jarvis import room_aliases

    monkeypatch = None
    aliases = {"lab": ["office lights", "desk lamp"]}
    path = room_aliases.ALIASES_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"aliases": aliases}), encoding="utf-8")
    assert room_aliases.resolve_targets("lab") == ["office lights", "desk lamp"]
    assert room_aliases.resolve_targets("desk lamp") == ["desk lamp"]


def test_router_training_export(tmp_path, monkeypatch):
    out = tmp_path / "router_training.jsonl"
    monkeypatch.setattr("jarvis.router_training.OUT", out)
    from jarvis.router_training import export_training_jsonl

    path = export_training_jsonl()
    assert path == out
    assert path.is_file()


def test_health_integrations_extended(monkeypatch):
    from jarvis.gui import server

    monkeypatch.setattr(server, "detect_gpu", lambda: {"vendor": "cpu"})
    monkeypatch.setattr(server, "detect_devices", lambda: {})
    monkeypatch.setattr(
        "jarvis.services.get_status",
        lambda force=False: {"ready": True, "services": [], "ollama": {}},
    )
    monkeypatch.setattr(
        server.assistant,
        "get_status",
        lambda: {},
    )
    payload = server._build_health_payload()
    integrations = payload.get("integrations") or {}
    for key in ("cad", "printer", "browser_agent", "kasa", "face_auth"):
        assert key in integrations
