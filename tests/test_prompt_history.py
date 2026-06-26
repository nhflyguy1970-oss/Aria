"""Tests for image prompt history."""

from jarvis.prompt_history import add_entry, delete_entry, list_entries, toggle_favorite


def test_prompt_history_roundtrip(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.prompt_history.HISTORY_FILE", data_dir / "prompt_history.json")
    e = add_entry("a cat in space", enhanced="detailed cat", image_path="/tmp/x.png")
    assert e["id"]
    items = list_entries()
    assert items[0]["prompt"] == "a cat in space"
    toggled = toggle_favorite(e["id"])
    assert toggled and toggled["favorite"] is True


def test_delete_entry(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.prompt_history.HISTORY_FILE", data_dir / "prompt_history.json")
    e = add_entry("delete me")
    assert delete_entry(e["id"]) is True
    assert list_entries() == []
    assert delete_entry("missing") is False

