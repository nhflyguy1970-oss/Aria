"""Live certification: a page load must not rewrite the database.

/api/cheatsheets listed from the legacy vault while add() was diverted to ACM.
The reader therefore always saw nothing, the route reseeded every default on
every request, and each page load wrote the whole set again — 11 memory writes
per view, forever, while the page still showed nothing.
"""

from __future__ import annotations

from jarvis import cheatsheets


class FakeStore:
    """Reads and writes go to the same place, as any store must."""

    def __init__(self):
        self.entries: list[dict] = []
        self.writes = 0

    def list_entries(self, entry_type=None, *, namespace=None, **kw):
        return [e for e in self.entries if not namespace or e.get("namespace") == namespace]

    def add(self, entry_type, content, tags=None, *, namespace=None):
        self.writes += 1
        entry = {
            "id": f"m{len(self.entries)}",
            "type": entry_type,
            "content": content,
            "tags": list(tags or []),
            "namespace": namespace,
            "timestamp": f"2026-01-01T00:00:{len(self.entries):02d}",
        }
        self.entries.append(entry)
        return entry

    @property
    def _data(self):  # the projection the old code read
        return {"entries": []}


def test_seeding_happens_once_not_on_every_view(data_dir):
    store = FakeStore()
    cheatsheets.seed_cheatsheets(store)
    after_first = store.writes
    assert after_first > 0, "nothing was seeded"

    assert cheatsheets.list_cheatsheets(store), "the reader cannot see what was written"

    cheatsheets.seed_cheatsheets(store)
    assert store.writes == after_first, "reseeded work that already existed"


def test_the_reader_uses_the_same_store_the_writer_used(data_dir):
    store = FakeStore()
    cheatsheets.seed_cheatsheets(store)
    listed = cheatsheets.list_cheatsheets(store)
    assert listed
    assert cheatsheets.find_by_key(store, listed[0]["key"]) is not None


def test_duplicates_already_in_memory_collapse_to_one_per_key(data_dir):
    """Existing databases carry the copies the old behaviour left behind."""
    store = FakeStore()
    for _ in range(5):
        store.add(
            "note",
            "# Audio\ncontent",
            tags=[cheatsheets.TAG_CHEATSHEET, cheatsheets.key_tag("audio")],
            namespace=cheatsheets.CHEATSHEET_NAMESPACE,
        )

    listed = cheatsheets.list_cheatsheets(store)
    assert [c["key"] for c in listed] == ["audio"]
    # The most recent copy wins.
    assert listed[0]["id"] == "m4"


def test_a_store_without_list_entries_still_works(data_dir):
    """Older stores expose only the raw projection."""

    class LegacyStore:
        _data = {
            "entries": [
                {
                    "id": "x",
                    "content": "# Audio\nc",
                    "tags": [cheatsheets.TAG_CHEATSHEET, cheatsheets.key_tag("audio")],
                    "namespace": cheatsheets.CHEATSHEET_NAMESPACE,
                    "timestamp": "2026-01-01",
                }
            ]
        }

    assert [c["key"] for c in cheatsheets.list_cheatsheets(LegacyStore())] == ["audio"]
