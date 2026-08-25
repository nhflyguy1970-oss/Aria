"""Exclusion layer over the Blackfly raw scrape.

Blackfly's audit proved that some records in `dataset.jsonl` describe a fly
their source page never contained -- a Jeep review read as "Renegade #14", an
IGN walkthrough as a hopper pattern. The raw scrape is the authoritative
record of what was fetched, so those records are deliberately *not* deleted
from it. Blackfly instead records the verdict in a manifest, and every derived
view is expected to honour it:

    dataset.jsonl  (raw, never filtered)
        -> quarantine filter          <- this module
            -> ARIA's index, counts, documents
                -> what a user can retrieve

Blackfly owns the manifest and ships `blackfly_quarantine` to read it, so that
helper is used when it can be imported and the file is read directly only when
it cannot (the data can be mounted without the code). Nothing here re-derives
Blackfly's verdict -- this module only applies it.

Failure behaviour is deliberately asymmetric:

    no manifest at all   -> quarantine is not in use, serve everything
    manifest unreadable  -> reuse the last good set, or report `error` so the
                            caller can refuse to serve rather than serve
                            records that may be fabricated

Serving a fabricated recipe is the failure this whole layer exists to prevent,
so an unreadable manifest must never silently become an empty one.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Iterable

log = logging.getLogger("jarvis.flytying.quarantine")

STATUS_OK = "ok"
STATUS_ABSENT = "absent"
STATUS_ERROR = "error"

MANIFEST_RELPATH = ("config", "quarantined_records.json")

_LOCK = threading.Lock()
_CACHE: dict[str, Any] = {
    "key": None,        # (path, mtime_ns, size) the ids were read from
    "ids": frozenset(),
    "status": STATUS_ABSENT,
    "path": "",
}


def manifest_path() -> Path:
    """Where Blackfly keeps the verdict, asked of Blackfly when possible."""
    try:
        from jarvis.flytying.config import ensure_blackfly_on_path

        ensure_blackfly_on_path()
        import blackfly_quarantine  # type: ignore

        return Path(blackfly_quarantine.manifest_path())
    except Exception:
        pass
    try:
        from jarvis.flytying.config import flytying_root

        return flytying_root().joinpath(*MANIFEST_RELPATH)
    except Exception:
        return Path(*MANIFEST_RELPATH)


def _read_ids(path: Path) -> frozenset[str]:
    """Parse the manifest. Raises if it exists but cannot be understood."""
    try:
        from jarvis.flytying.config import ensure_blackfly_on_path

        ensure_blackfly_on_path()
        import blackfly_quarantine  # type: ignore

        return frozenset(blackfly_quarantine.quarantined_ids(str(path)))
    except ImportError:
        pass
    # Blackfly's data without Blackfly's code: the manifest is plain JSON.
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"quarantine manifest is not an object: {path}")
    out = set()
    for row in data.get("records") or []:
        if isinstance(row, dict):
            rid = str(row.get("content_sha256") or "").strip()
            if rid:
                out.add(rid)
    return frozenset(out)


def quarantine_state(*, refresh: bool = True) -> dict[str, Any]:
    """{'ids', 'status', 'path', 'count'} -- cached against the file's mtime.

    The id set is read once per manifest change, not once per query: 43 ids is
    a set membership test, and re-reading the file for every search would put
    a disk hit on the hot path for no benefit.
    """
    path = manifest_path()
    try:
        st = path.stat()
        key = (str(path), st.st_mtime_ns, st.st_size)
    except OSError:
        key = None

    with _LOCK:
        if not refresh and _CACHE["key"] is not None:
            return _snapshot()
        if key is None:
            # No manifest: Blackfly quarantine is not in use here.
            _CACHE.update(key=None, ids=frozenset(), status=STATUS_ABSENT,
                          path=str(path))
            return _snapshot()
        if _CACHE["key"] == key and _CACHE["status"] == STATUS_OK:
            return _snapshot()
        try:
            ids = _read_ids(path)
        except Exception as exc:
            # The file is there, so the verdict exists and we simply cannot
            # read it. Keep the last good set if we have one; otherwise say so
            # loudly and let the caller refuse to serve.
            if _CACHE["status"] == STATUS_OK and _CACHE["ids"]:
                log.error(
                    "fly-tying quarantine manifest unreadable (%s: %s) -- "
                    "reusing the last good set of %d ids",
                    type(exc).__name__, exc, len(_CACHE["ids"]),
                )
                return _snapshot()
            log.error(
                "fly-tying quarantine manifest unreadable and no previous set "
                "is known (%s: %s) -- the recipe library will not be served",
                type(exc).__name__, exc,
            )
            _CACHE.update(key=None, ids=frozenset(), status=STATUS_ERROR,
                          path=str(path))
            return _snapshot()
        _CACHE.update(key=key, ids=ids, status=STATUS_OK, path=str(path))
        return _snapshot()


def _snapshot() -> dict[str, Any]:
    return {
        "ids": _CACHE["ids"],
        "status": _CACHE["status"],
        "path": _CACHE["path"],
        "count": len(_CACHE["ids"]),
    }


def reset_cache() -> None:
    with _LOCK:
        _CACHE.update(key=None, ids=frozenset(), status=STATUS_ABSENT, path="")


def quarantined_ids() -> frozenset[str]:
    return quarantine_state()["ids"]


def record_id(recipe: dict[str, Any]) -> str:
    """The id the manifest keys on.

    Blackfly writes `content_sha256` and `content_hash` identically on every
    record, and ARIA's own `_recipe_id` falls back to `content_hash`, so these
    agree on what identifies a record.
    """
    return str(
        recipe.get("content_sha256") or recipe.get("content_hash") or ""
    ).strip()


def is_quarantined(recipe: dict[str, Any], ids: Iterable[str] | None = None) -> bool:
    known = quarantined_ids() if ids is None else ids
    rid = record_id(recipe)
    return bool(rid) and rid in known


def filter_records(
    rows: Iterable[dict[str, Any]], ids: Iterable[str] | None = None
) -> tuple[list[dict[str, Any]], int]:
    """(kept, dropped_count), order preserved."""
    known = quarantined_ids() if ids is None else ids
    if not known:
        rows = list(rows)
        return rows, 0
    kept: list[dict[str, Any]] = []
    dropped = 0
    for row in rows:
        if is_quarantined(row, known):
            dropped += 1
        else:
            kept.append(row)
    return kept, dropped
