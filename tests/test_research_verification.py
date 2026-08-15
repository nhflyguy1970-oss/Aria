"""Unit tests for research verification authority tiers and filtering."""

from __future__ import annotations

from jarvis.research_verification import (
    classify_source_tier,
    filter_results_for_query,
    postcheck_research_answer,
)


def test_tier1_official_hosts():
    assert classify_source_tier("https://ubuntu.com/download") == 1
    assert classify_source_tier("https://nodejs.org/en/download") == 1
    assert classify_source_tier("https://docs.nvidia.com/cuda/") == 1


def test_tier4_weak_hosts():
    assert classify_source_tier("https://www.justanswer.com/ford/abc") == 4
    assert classify_source_tier("https://www.quora.com/what-is-torque") == 4


def test_consequential_filters_out_weak_only():
    results = [
        {"title": "Forum", "url": "https://www.justanswer.com/x", "snippet": "torque 129 Nm"},
        {"title": "Reddit", "url": "https://reddit.com/r/MechanicAdvice", "snippet": "95 ft-lbs"},
    ]
    filtered, meta = filter_results_for_query("torque caliper", results, consequential=True)
    assert filtered == []
    assert "no_usable" in meta.get("reason", "")


def test_current_prefers_official():
    results = [
        {"title": "Blog", "url": "https://random-blog.example/node", "snippet": "Node 18"},
        {"title": "Official", "url": "https://nodejs.org/en/about/previous-releases", "snippet": "Node 22 LTS"},
    ]
    filtered, meta = filter_results_for_query("latest Node LTS", results, current=True)
    assert any("nodejs.org" in str(r.get("url")) for r in filtered)
    assert meta.get("filtered") is True


def test_postcheck_refuses_weak_current_claim():
    results = [
        {"title": "Weak", "url": "https://www.justanswer.com/x", "snippet": "PM is Alice"},
    ]
    out = postcheck_research_answer(
        "Who is the current Prime Minister of the United Kingdom?",
        "The current Prime Minister is Alice [1].",
        results,
        consequential=False,
        current=True,
    )
    assert out is not None
    assert (
        "weak" in out.lower()
        or "could not" in out.lower()
        or "cannot" in out.lower()
        or "no reliable" in out.lower()
        or "not invent" in out.lower()
    )
