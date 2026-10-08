"""The ARIA workload benchmark's scorers — deterministic and fair, no model needed."""

from __future__ import annotations

import pytest

from jarvis.inference import quality_benchmark as qb

TASKS = {t.id: t for suite in qb.SUITES.values() for t in suite}


@pytest.mark.parametrize(
    "task,output,expected",
    [
        ("r1", "The answer is 14.", True),
        ("r1", "<think>maybe 13</think>14", True),
        ("r1", "15", False),
        ("r5", "Sunday.", True),
        ("r5", "10 days from Thursday is still Thursday.", False),
        ("r7", "ACK", True),
        ("r7", "ACK!", False),
        ("r8", "Trout are fish. They like cold water.", True),
        ("r8", "- a\n- b", False),
        ("r9", "53, 59, 61", True),
        ("r9", "51, 53, 59", False),
        ("r10", '{"name": "caddis", "count": 3}', True),
        ("r10", '{"name": "caddis", "count": "3"}', False),
        ("j2", '{"action": "continuity_recall"}', True),
        ("j2", '{"action": "chat"}', False),
        ("m3", "We log catches by lake, not by river.", True),
        ("m3", "By river.", False),
        ("m5", "There is no record of a price.", True),
        ("m5", "We decided $4.99.", False),
        ("m6", "We picked Python.", False),
        ("e1", "INSUFFICIENT", True),
        ("e1", "SUPPORTED", False),
        ("e1", "SUPPORTED or INSUFFICIENT", False),
        ("v3", "TROUT 42", True),
    ],
)
def test_scorers(task, output, expected):
    assert TASKS[task].score(output) is expected


def test_tool_scorer_requires_the_right_call():
    t = TASKS["t2"]
    assert t.score_tool([{"name": "route", "arguments": {"action": "continuity_recall"}}])
    assert not t.score_tool([{"name": "route", "arguments": {"action": "chat"}}])
    assert not t.score_tool([])


def test_coding_runs_hidden_tests_in_isolation():
    good = "```python\ndef average(xs):\n    return sum(xs) / len(xs) if xs else 0.0\n```"
    bad = "```python\ndef average(xs):\n    return sum(xs) // len(xs)\n```"
    assert TASKS["c6"].score(good)
    assert not TASKS["c6"].score(bad)
    assert not TASKS["c5"].score("while True: pass")  # times out, scored as a failure


def test_summary_reports_accuracy_and_latency():
    rows = [
        {"model": "m", "category": "reasoning", "passed": True, "wall_ms": 100},
        {"model": "m", "category": "reasoning", "passed": False, "wall_ms": 300},
        {"model": "m", "category": "routing", "passed": False, "error": "unsupported"},
    ]
    s = qb.summarise(rows)["m"]["categories"]
    assert s["reasoning"]["accuracy"] == 0.5 and s["reasoning"]["p50_ms"] == 300
    assert s["routing"]["errors"] == 1


def test_vision_images_are_generated(tmp_path):
    paths = qb.make_vision_images(tmp_path)
    assert set(paths) == {"red_circle", "three_squares", "text", "green_triangle"}
