"""Consistency: journal notes appear on calendar; missing job assets not Complete."""

from __future__ import annotations


def test_journal_notes_federate_to_calendar():
    from jarvis.calendar_schedule import _journal_items

    class FakeJ:
        def daily_get(self, day, enrich=False):
            return {
                "bullets": [
                    {
                        "id": "n1",
                        "type": "note",
                        "content": "Hello note",
                        "status": "open",
                        "time": None,
                        "children": [],
                    }
                ]
            }

    items = _journal_items(FakeJ(), "2026-07-31")
    assert any(i.get("kind") == "note" and i.get("title") == "Hello note" for i in items)


def test_jobs_center_marks_missing_assets():
    from jarvis.jobs_center import _sanitize_job

    out = _sanitize_job(
        {
            "id": "j1",
            "kind": "generate_image",
            "done": True,
            "message": "Complete",
            "error": "",
            "result": {
                "ok": True,
                "image_name": "gone.png",
                "image_path": "/tmp/definitely_missing_gone.png",
            },
        },
        queue="media",
    )
    assert out.get("result_ok") is False
    assert out.get("asset_missing") is True
