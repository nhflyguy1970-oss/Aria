"""Fly Tying in-memory index tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_index_search_finds_name(tmp_path, monkeypatch):
    from jarvis.flytying import index as idx

    db = tmp_path / "scraped.jsonl"
    _write_jsonl(
        db,
        [
            {
                "fly_name": "Blue Wing Olive",
                "type": "dry",
                "hook": "14",
                "materials": ["cdc", "olive dubbing"],
                "steps": ["Start thread", "Dub body"],
                "quality_score": 80,
                "recipe_id": "bwo-1",
            },
            {
                "fly_name": "Woolly Bugger",
                "type": "streamer",
                "hook": "8",
                "materials": ["marabou", "chenille"],
                "steps": ["Tie in marabou"],
                "quality_score": 70,
                "recipe_id": "wb-1",
            },
        ],
    )
    monkeypatch.setattr(
        idx,
        "_CACHE",
        {"mtime": 0, "path": "", "recipes": [], "by_id": {}, "by_name": {}, "browse_sorted": [], "browse_rows": []},
    )
    with patch("jarvis.flytying.index.blackfly_data_available", return_value=True):
        with patch("jarvis.flytying.index.recipe_source_path", return_value=db):
            hits, mode, total = idx.search("olive", limit=10)
    assert mode in ("keyword", "browse")
    assert total >= 1
    assert any("Blue Wing" in str(h.get("name") or "") for h in hits)


def test_index_empty_when_unavailable():
    from jarvis.flytying import index as idx

    with patch("jarvis.flytying.index.blackfly_data_available", return_value=False):
        hits, mode, total = idx.search("anything", limit=5)
    assert hits == []
    assert mode == "unavailable"
    assert total == 0
