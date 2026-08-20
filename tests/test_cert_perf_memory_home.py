"""Performance certification: Memory Home must not rescan the same text.

is_test_artifact is a pure function of its content, but Memory Home called it
11,731 times for ~1,100 entries — the same multi-kilobyte strings rescanned
about ten times each against a 22-branch case-insensitive pattern. That was
2.58s of the endpoint's 2.99s.
"""

from __future__ import annotations

import time

from jarvis import trust_memory


def test_the_answer_is_cached_not_recomputed():
    trust_memory._is_test_artifact_cached.cache_clear()
    text = "broken_calc.py failed again during the run"

    assert trust_memory.is_test_artifact(text) is True
    for _ in range(500):
        trust_memory.is_test_artifact(text)

    info = trust_memory._is_test_artifact_cached.cache_info()
    assert info.misses == 1, "the pattern was re-evaluated"
    assert info.hits >= 500


def test_caching_did_not_change_the_answers():
    trust_memory._is_test_artifact_cached.cache_clear()
    artifacts = [
        "broken_calc.py",
        "please buy milk today",
        "pytest journal scratch note",
        "ZXQ_PERSIST marker",
        "certification test entry",
    ]
    ordinary = [
        "The heron stands still in the shallows before dawn.",
        "Jeff prefers dark mode in the evening.",
        "",
        "   ",
        "A note about calculators in general",
    ]
    for text in artifacts:
        assert trust_memory.is_test_artifact(text) is True, text
    for text in ordinary:
        assert trust_memory.is_test_artifact(text) is False, text


def test_repeated_scanning_of_a_large_corpus_stays_fast():
    """The shape of the Memory Home workload: many entries, scanned repeatedly."""
    trust_memory._is_test_artifact_cached.cache_clear()
    corpus = [f"# Reference {i}\n" + ("lorem ipsum dolor sit amet " * 120) for i in range(300)]

    started = time.perf_counter()
    for _ in range(10):
        for text in corpus:
            trust_memory.is_test_artifact(text)
    elapsed = time.perf_counter() - started

    info = trust_memory._is_test_artifact_cached.cache_info()
    assert info.misses == len(corpus), "every pass re-evaluated the corpus"
    # 3000 lookups of cached results is trivial work; the uncached form took seconds.
    assert elapsed < 1.0, f"repeated scanning took {elapsed:.2f}s"


def test_the_cache_is_bounded():
    assert trust_memory._is_test_artifact_cached.cache_info().maxsize is not None
