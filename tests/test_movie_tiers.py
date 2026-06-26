"""Tests for movie tier helpers."""

from jarvis.movie_tiers import (
    memory_citations_from_context,
    profile_banner,
    task_nudge_check,
    trust_health,
    validate_ics_url,
)


def test_trust_health_shape():
    h = trust_health()
    assert "disk_free_gb" in h
    assert h["test_filter"] == "active"


def test_profile_banner_offline():
    b = profile_banner("offline")
    assert b["show"] is True
    assert b["web_search_off"] is True


def test_task_nudge_before_hour():
    r = task_nudge_check(hour=6, threshold=1)
    assert r["nudge"] is False


def test_validate_ics_empty():
    r = validate_ics_url("")
    assert r["ok"] is False


def test_memory_citations_parse():
    ctx = "- **fact** (2026-01-01): User prefers brief answers"
    cites = memory_citations_from_context(ctx)
    assert len(cites) == 1
    assert cites[0]["type"] == "fact"
