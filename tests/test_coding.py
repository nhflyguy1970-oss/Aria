"""Tests for coding filesystem helpers and secret blocklist."""

from __future__ import annotations

from pathlib import Path


def test_search_skips_secret_files(tmp_path: Path):
    from jarvis import fs

    (tmp_path / "main.py").write_text("def hello(): pass\n", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=hello in env file\n", encoding="utf-8")
    (tmp_path / "credentials.json").write_text('{"token": "hello"}\n', encoding="utf-8")

    hits = fs.search_files("hello", tmp_path)
    paths = {p for p, _, _ in hits}
    assert any("main.py" in p for p in paths)
    assert not any(".env" in p for p in paths)
    assert not any("credentials.json" in p for p in paths)


def test_find_skips_secret_files(tmp_path: Path):
    from jarvis import fs

    (tmp_path / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "my_secrets.json").write_text("", encoding="utf-8")

    found = fs.find_files("app", tmp_path)
    assert any("app.py" in p for p in found)
    assert not any("secrets" in p for p in found)


def test_coding_engine_load_file(tmp_path: Path):
    from jarvis.modules.coding import CodingEngine

    proj = tmp_path / "myproj"
    proj.mkdir()
    (proj / "foo.py").write_text("x = 1\n", encoding="utf-8")
    engine = CodingEngine()
    engine.project_root = proj.resolve()
    result = engine.load_file("foo.py")
    assert result == "OK"
    assert engine.loaded_files[-1]["content"].strip() == "x = 1"
