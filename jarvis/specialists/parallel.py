"""Parallel read-only specialist helper (experimental)."""

from __future__ import annotations

from typing import Any

# Execution lives in engine.run_team(parallel_readers=True).
# This module documents the contract.


def can_parallelize(team: list[str]) -> dict[str, Any]:
    from jarvis.specialists.catalog import get_specialist

    readers = []
    blocked = []
    for sid in team:
        meta = get_specialist(sid)
        if meta and meta.get("read_only"):
            readers.append(sid)
        else:
            blocked.append(sid)
    return {
        "ok": True,
        "readers": readers,
        "writers_serial": blocked,
        "note": "Only read-only specialists may run in parallel. Writers stay serial.",
    }
