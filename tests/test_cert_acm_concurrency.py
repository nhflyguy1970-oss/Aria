"""Live certification: reading ACM while it is being written must not crash.

Driving the authenticated UI produced 500s on Memory Home and the profile
questionnaire — "dictionary changed size during iteration", and the ACM read
diverter re-raising it as "ACM authoritative: list_entries failed". The store's
dicts are live, so a projection built while another thread remembered something
walked a mutating dict.
"""

from __future__ import annotations

import inspect
import re
import threading

from aria_core import acm_bridge


def _live_iterations(func) -> list[str]:
    """Iterations over the store's dicts that do not take a snapshot first."""
    src = inspect.getsource(func)
    return [
        line.strip()
        for line in src.splitlines()
        if re.search(r"for .* in engine\.store\.\w+\.values\(\)", line) and "list(" not in line
    ]


def test_projection_iterates_a_snapshot():
    assert not _live_iterations(acm_bridge.project_list_entries)


def test_every_store_walk_in_the_bridge_takes_a_snapshot():
    offenders = {}
    for name, obj in vars(acm_bridge).items():
        if not inspect.isfunction(obj):
            continue
        try:
            bad = _live_iterations(obj)
        except (OSError, TypeError):
            continue
        if bad:
            offenders[name] = bad
    assert not offenders, f"live dict iteration remains: {offenders}"


def test_iterating_a_snapshot_survives_concurrent_mutation():
    """The failure mode itself, in miniature."""
    store = {f"k{i}": i for i in range(500)}
    stop = threading.Event()
    errors = []

    def mutate():
        i = 500
        while not stop.is_set():
            store[f"k{i}"] = i
            store.pop(f"k{i - 400}", None)
            i += 1

    writer = threading.Thread(target=mutate, daemon=True)
    writer.start()
    try:
        for _ in range(200):
            try:
                sum(1 for _ in list(store.values()))
            except RuntimeError as exc:  # pragma: no cover - the bug being guarded
                errors.append(str(exc))
    finally:
        stop.set()
        writer.join(timeout=2)
    assert not errors, f"snapshot iteration still raced: {errors[:2]}"
