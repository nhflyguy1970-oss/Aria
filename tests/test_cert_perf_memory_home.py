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


def test_calendar_memory_dates_is_not_recomputed_every_visit(data_dir, monkeypatch):
    """Four ACM searches, each a full cognitive activation: 5.4s every time the
    Calendar room opened, for suggestions that only change when memory does."""
    from jarvis import calendar_services

    calls = {"n": 0}

    class FakeMemory:
        def search(self, query, limit=3):
            calls["n"] += 1
            return [{"content": f"{query} of Sam is in June"}]

    class FakeAssistant:
        memory = FakeMemory()

    calendar_services._MEMORY_DATES_CACHE.update({"at": 0.0, "value": None, "generation": None})
    monkeypatch.setattr(calendar_services, "_memory_generation", lambda _a: ("stable",))

    first = calendar_services.memory_dates(FakeAssistant())
    after_first = calls["n"]
    assert after_first > 0 and first["reminders"]

    for _ in range(5):
        again = calendar_services.memory_dates(FakeAssistant())
    assert calls["n"] == after_first, "the searches ran again"
    assert again["reminders"] == first["reminders"]


def test_calendar_memory_dates_refreshes_when_memory_changes(data_dir, monkeypatch):
    from jarvis import calendar_services

    calls = {"n": 0}
    generation = {"value": ("a",)}

    class FakeMemory:
        def search(self, query, limit=3):
            calls["n"] += 1
            return [{"content": f"{query} note"}]

    class FakeAssistant:
        memory = FakeMemory()

    calendar_services._MEMORY_DATES_CACHE.update({"at": 0.0, "value": None, "generation": None})
    monkeypatch.setattr(calendar_services, "_memory_generation", lambda _a: generation["value"])

    calendar_services.memory_dates(FakeAssistant())
    baseline = calls["n"]
    calendar_services.memory_dates(FakeAssistant())
    assert calls["n"] == baseline, "cache did not hold"

    generation["value"] = ("b",)  # memory changed
    calendar_services.memory_dates(FakeAssistant())
    assert calls["n"] > baseline, "a memory change did not invalidate the cache"


def test_startup_summary_is_not_rebuilt_on_every_request(data_dir, monkeypatch):
    """Assembling it collects the whole Mission Control picture — ~78
    subprocesses and a registry walk, 3.5s — and it ran on every request."""
    from jarvis import runtime_introspection

    builds = {"n": 0}

    def fake_build():
        builds["n"] += 1
        return {"ok": True, "summary": "built"}

    monkeypatch.setattr(runtime_introspection, "_build_startup_summary", fake_build)
    runtime_introspection._STARTUP_SUMMARY_CACHE.update({"at": 0.0, "value": None})

    first = runtime_introspection.format_startup_summary()
    for _ in range(6):
        again = runtime_introspection.format_startup_summary()

    assert builds["n"] == 1, f"rebuilt {builds['n']} times"
    assert again == first


def test_startup_summary_cache_expires(data_dir, monkeypatch):
    """A late-arriving component must not stay hidden."""
    import time

    from jarvis import runtime_introspection

    builds = {"n": 0}
    monkeypatch.setattr(
        runtime_introspection,
        "_build_startup_summary",
        lambda: (builds.__setitem__("n", builds["n"] + 1), {"ok": True})[1],
    )
    runtime_introspection._STARTUP_SUMMARY_CACHE.update({"at": 0.0, "value": None})
    runtime_introspection.format_startup_summary()
    assert builds["n"] == 1

    # Age the cache past its TTL.
    runtime_introspection._STARTUP_SUMMARY_CACHE["at"] = (
        time.time() - runtime_introspection._STARTUP_SUMMARY_TTL - 1
    )
    runtime_introspection.format_startup_summary()
    assert builds["n"] == 2, "the cache never expires"
