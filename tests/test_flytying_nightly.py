"""Fly Tying nightly — Pattern of the Day + scheduled gate."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import patch


def test_pattern_of_the_day_deterministic(tmp_path, monkeypatch):
    from jarvis.flytying import nightly

    db = tmp_path / "lib.jsonl"
    rows = [
        {"fly_name": "Alpha", "type": "dry", "materials": ["a"], "id": "1"},
        {"fly_name": "Beta", "type": "nymph", "materials": ["b"], "id": "2"},
        {"fly_name": "Gamma", "type": "streamer", "materials": ["c"], "id": "3"},
    ]
    db.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    with patch("jarvis.flytying.config.recipe_source_path", return_value=db):
        a = nightly.pattern_of_the_day(day="2026-01-01")
        b = nightly.pattern_of_the_day(day="2026-01-01")
        c = nightly.pattern_of_the_day(day="2026-01-02")
    assert a["ok"] is True
    assert a["name"] == b["name"]
    assert a["name"] in ("Alpha", "Beta", "Gamma")
    assert c["ok"] is True


def test_run_scheduled_skips_outside_window():
    from jarvis.flytying import nightly

    with patch.object(nightly, "nightly_enabled", return_value=True):
        with patch.object(nightly, "nightly_hour", return_value=3):
            out = nightly.run_scheduled(datetime(2026, 7, 28, 15, 0))
    assert out.get("skipped") is True


def test_nightly_status_shape():
    from jarvis.flytying.nightly import nightly_status

    st = nightly_status()
    assert "enabled" in st
    assert "hour" in st
