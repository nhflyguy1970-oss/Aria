"""Prompt history delete/restore (undo) round-trip."""

from __future__ import annotations

import pathlib


def test_delete_returns_entry_and_restore_reinserts(tmp_path: pathlib.Path, monkeypatch):
    from jarvis import prompt_history as ph

    monkeypatch.setattr(ph, "HISTORY_FILE", tmp_path / "ph.json")
    monkeypatch.setattr(ph, "DATA_DIR", tmp_path)

    first = ph.add_entry("test prompt one")
    second = ph.add_entry("test prompt two")

    removed = ph.delete_entry(first["id"])
    assert removed is not None and removed["id"] == first["id"]
    assert [e["id"] for e in ph.list_entries()] == [second["id"]]

    restored = ph.restore_entry(removed)
    assert restored is not None
    assert [e["id"] for e in ph.list_entries()] == [second["id"], first["id"]]

    # Idempotent restore, safe failure modes
    assert ph.restore_entry(removed)["id"] == first["id"]
    assert len(ph.list_entries()) == 2
    assert ph.delete_entry("missing") is None
    assert ph.restore_entry({}) is None


def test_gallery_undo_ui_is_wired():
    root = pathlib.Path(__file__).resolve().parents[1]
    js = (root / "jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert "/api/prompts/restore" in js
    assert "Prompt deleted." in js
    assert 'confirm("Delete this prompt' not in js
    routes = (root / "jarvis/gui/extra_routes.py").read_text(encoding="utf-8")
    assert '@app.post("/api/prompts/restore")' in routes
