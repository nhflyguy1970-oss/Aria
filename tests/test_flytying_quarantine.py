"""Blackfly's quarantine must hold across every ARIA retrieval path.

Blackfly proved that some records in its raw scrape describe a fly their
source page never contained. The records stay in the scrape on purpose -- it
is the authoritative record of what was fetched -- so ARIA is the layer that
has to refuse to serve them. These tests pin that refusal to every path a user
can reach a recipe through, and pin the two things that must NOT happen:
valid records disappearing, and an unreadable manifest silently becoming an
empty one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

JEEP = "f3a70c1f187d83d82cce23ea5ff371636c900aeed35495ec0ad7b1477016b0df"
GOOD = "aaaa1111bbbb2222cccc3333dddd4444eeee5555ffff6666aaaa7777bbbb8888"
AMBIG = "1111aaaa2222bbbb3333cccc4444dddd5555eeee6666ffff7777aaaa8888bbbb"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _records() -> list[dict]:
    return [
        {
            "fly_name": "Renegade #14",
            "type": "terrestrial",
            "hook": "14",
            "content_sha256": JEEP,
            "content_hash": JEEP,
            "materials": ["Hook", "Thread (Color Matches Hook)"],
            "steps": ["Attach the hook to a pair of pliers", "Wrap the thread"],
            "quality_score": 95,
            "source_url": "https://www.caranddriver.com/reviews/a15105641/jeep-renegade",
        },
        {
            "fly_name": "Adams CDC",
            "type": "dry",
            "hook": "16",
            "content_sha256": GOOD,
            "content_hash": GOOD,
            "materials": ["cdc", "grizzly hackle"],
            "steps": ["Start the thread", "Tie in the cdc"],
            "quality_score": 90,
            "source_url": "https://midcurrent.com/videos/how-to-tie-an-adams/",
        },
        {
            "fly_name": "Frenchie nymph",
            "type": "nymph",
            "hook": "14",
            "content_sha256": AMBIG,
            "content_hash": AMBIG,
            "materials": ["pheasant tail", "copper wire"],
            "steps": ["Start the thread", "Wrap the wire"],
            "quality_score": 85,
            "source_url": "https://midcurrent.com/2013/02/17/video-how-to-tie-the-frenchie-nymph/",
        },
    ]


@pytest.fixture
def library(tmp_path, monkeypatch):
    """A three-record library where exactly the Jeep record is quarantined."""
    from jarvis.flytying import config as fcfg
    from jarvis.flytying import index as idx
    from jarvis.flytying import quarantine as fq

    dataset = tmp_path / "dataset.jsonl"
    _write_jsonl(dataset, _records())
    manifest = tmp_path / "quarantined_records.json"
    manifest.write_text(
        json.dumps({"version": 1, "records": [
            {"content_sha256": JEEP, "fly_name": "Renegade #14"}]}),
        encoding="utf-8",
    )

    monkeypatch.setattr(fcfg, "recipe_source_path", lambda: dataset)
    monkeypatch.setattr(fcfg, "blackfly_data_available", lambda: True)
    monkeypatch.setattr(idx, "recipe_source_path", lambda: dataset)
    monkeypatch.setattr(idx, "blackfly_data_available", lambda: True)
    monkeypatch.setattr(fq, "manifest_path", lambda: manifest)
    fq.reset_cache()
    idx.invalidate()
    monkeypatch.setattr(idx, "_CACHE", {
        "mtime": 0, "path": "", "recipes": [], "by_id": {}, "by_name": {},
        "browse_sorted": [], "browse_rows": [], "quarantined": 0, "raw_count": 0,
    })
    yield {"dataset": dataset, "manifest": manifest, "tmp": tmp_path}
    fq.reset_cache()


# --- the manifest itself ------------------------------------------------

def test_manifest_is_read_and_reports_ok(library):
    from jarvis.flytying import quarantine as fq

    state = fq.quarantine_state()
    assert state["status"] == fq.STATUS_OK
    assert state["ids"] == {JEEP}


def test_a_missing_manifest_quarantines_nothing(tmp_path, monkeypatch):
    """Blackfly quarantine simply may not be in use on this machine."""
    from jarvis.flytying import quarantine as fq

    monkeypatch.setattr(fq, "manifest_path", lambda: tmp_path / "nope.json")
    fq.reset_cache()
    state = fq.quarantine_state()
    assert state["status"] == fq.STATUS_ABSENT
    assert state["ids"] == frozenset()
    fq.reset_cache()


def test_an_empty_manifest_quarantines_nothing(tmp_path, monkeypatch):
    from jarvis.flytying import quarantine as fq

    m = tmp_path / "q.json"
    m.write_text(json.dumps({"version": 1, "records": []}), encoding="utf-8")
    monkeypatch.setattr(fq, "manifest_path", lambda: m)
    fq.reset_cache()
    assert fq.quarantine_state()["status"] == fq.STATUS_OK
    assert fq.quarantine_state()["ids"] == frozenset()
    fq.reset_cache()


def test_an_unreadable_manifest_is_never_treated_as_empty(tmp_path, monkeypatch):
    """Failing open here would serve exactly the records this layer excludes."""
    from jarvis.flytying import quarantine as fq

    m = tmp_path / "q.json"
    m.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(fq, "manifest_path", lambda: m)
    fq.reset_cache()
    state = fq.quarantine_state()
    assert state["status"] == fq.STATUS_ERROR
    fq.reset_cache()


def test_an_unreadable_manifest_withholds_the_library(library, monkeypatch):
    """No verdict means no serving -- not serving everything."""
    from jarvis.flytying import index as idx
    from jarvis.flytying import quarantine as fq

    assert len(idx.recipes()) == 2
    library["manifest"].write_text("{ broken", encoding="utf-8")
    fq.reset_cache()
    idx.invalidate()
    assert idx.recipes() == []
    assert idx.find_recipe("Adams CDC") is None
    fq.reset_cache()


def test_a_corrupt_manifest_falls_back_to_the_last_good_set(library):
    """A transient read failure must not drop the quarantine."""
    from jarvis.flytying import quarantine as fq

    assert fq.quarantine_state()["ids"] == {JEEP}
    library["manifest"].write_text("{ broken", encoding="utf-8")
    state = fq.quarantine_state()
    assert state["status"] == fq.STATUS_OK
    assert state["ids"] == {JEEP}
    fq.reset_cache()


# --- every retrieval path ------------------------------------------------

def test_keyword_search_excludes_quarantined(library):
    from jarvis.flytying import index as idx

    rows, mode, total = idx.search("Renegade", limit=20)
    assert mode == "keyword"
    assert [r["name"] for r in rows] == []
    assert total == 0


def test_browse_excludes_quarantined(library):
    from jarvis.flytying import index as idx

    rows, mode, total = idx.search(None, limit=50)
    assert mode == "browse"
    names = {r["name"] for r in rows}
    assert "Renegade #14" not in names
    assert names == {"Adams CDC", "Frenchie nymph"}
    assert total == 2


def test_direct_lookup_by_name_excludes_quarantined(library):
    from jarvis.flytying import index as idx

    assert idx.find_recipe("Renegade #14") is None


def test_direct_lookup_by_id_excludes_quarantined(library):
    """The content hash is the id ARIA exposes; it must not resolve either."""
    from jarvis.flytying import index as idx

    assert idx.find_recipe(JEEP) is None


def test_similar_recipes_never_returns_quarantined(library):
    from jarvis.flytying import index as idx

    similar = idx.similar_recipes("Adams CDC", limit=10)
    assert "Renegade #14" not in {r["name"] for r in similar}


def test_recipes_listing_excludes_quarantined(library):
    from jarvis.flytying import index as idx

    assert {r["fly_name"] for r in idx.recipes()} == {"Adams CDC", "Frenchie nymph"}


def test_suggest_from_materials_excludes_quarantined(library):
    from jarvis.flytying import bridge

    rows = bridge.suggest_from_materials(["Hook", "Thread"], limit=10)
    assert "Renegade #14" not in {r.get("name") for r in rows}


def test_qa_retrieval_context_excludes_quarantined(library, monkeypatch):
    """chat_turn builds its LLM context from bridge.search_recipes."""
    from jarvis.flytying import chat

    context, hits = chat._blackfly_rag_context("renegade dry fly", limit=5)
    assert "caranddriver" not in context
    assert "Renegade #14" not in {h.get("name") for h in hits}


def test_library_health_counts_only_servable_records(library):
    from jarvis.flytying.library_health import library_health

    health = library_health()
    assert health.get("total") == 2


# --- what must survive ---------------------------------------------------

def test_a_valid_record_is_still_retrievable(library):
    from jarvis.flytying import index as idx

    assert idx.find_recipe("Adams CDC") is not None
    rows, _mode, total = idx.search("Adams", limit=10)
    assert total == 1
    assert rows[0]["name"] == "Adams CDC"


def test_an_ambiguous_record_is_still_retrievable(library):
    """Unverified is not invalid -- Blackfly preserved these deliberately."""
    from jarvis.flytying import index as idx

    assert idx.find_recipe("Frenchie nymph") is not None


def test_releasing_a_record_restores_it_without_touching_the_dataset(library):
    """The manifest is the only thing that decides, and it is reversible."""
    from jarvis.flytying import index as idx
    from jarvis.flytying import quarantine as fq

    before = library["dataset"].read_bytes()
    assert idx.find_recipe("Renegade #14") is None
    library["manifest"].write_text(
        json.dumps({"version": 1, "records": []}), encoding="utf-8")
    fq.reset_cache()
    idx.invalidate()
    assert idx.find_recipe("Renegade #14") is not None
    assert library["dataset"].read_bytes() == before
    fq.reset_cache()


def test_the_raw_dataset_is_never_written(library):
    from jarvis.flytying import index as idx

    before = library["dataset"].read_bytes()
    idx.recipes()
    idx.search("Renegade", limit=5)
    idx.find_recipe("Renegade #14")
    assert library["dataset"].read_bytes() == before


# --- identity handling ---------------------------------------------------

def test_a_record_without_a_hash_is_never_filtered(library):
    """No id means no verdict; it must not be silently dropped."""
    from jarvis.flytying import quarantine as fq

    assert fq.is_quarantined({"fly_name": "Nameless"}, {JEEP}) is False


def test_content_hash_alone_still_matches(library):
    """Blackfly writes both fields; ARIA's own id falls back to content_hash."""
    from jarvis.flytying import quarantine as fq

    assert fq.is_quarantined({"content_hash": JEEP}, {JEEP}) is True


def test_an_unrelated_record_sharing_a_name_is_not_filtered(library):
    """Filtering is by hash, so a same-named valid record must survive."""
    from jarvis.flytying import index as idx

    rows = _records() + [{
        "fly_name": "Renegade #14",
        "type": "dry",
        "content_sha256": "9" * 64,
        "content_hash": "9" * 64,
        "materials": ["peacock herl", "brown hackle"],
        "steps": ["Start the thread", "Wind the hackle"],
        "quality_score": 88,
        "source_url": "https://midcurrent.com/2017/06/25/how-to-tie-the-renegade/",
    }]
    _write_jsonl(library["dataset"], rows)
    idx.invalidate()
    found = idx.find_recipe("Renegade #14")
    assert found is not None
    assert found["content_sha256"] == "9" * 64
    assert "midcurrent" in found["source_url"]


# --- stale persisted state ----------------------------------------------

def test_the_manifest_is_part_of_the_index_cache_key(library):
    """Quarantining must take effect without waiting for a dataset touch."""
    from jarvis.flytying import index as idx

    assert idx.find_recipe("Frenchie nymph") is not None
    library["manifest"].write_text(
        json.dumps({"version": 1, "records": [
            {"content_sha256": JEEP}, {"content_sha256": AMBIG}]}),
        encoding="utf-8",
    )
    from jarvis.flytying import quarantine as fq

    fq.reset_cache()
    assert idx.find_recipe("Frenchie nymph") is None
    fq.reset_cache()


def test_a_stale_document_index_does_not_survive_a_deletion(tmp_path, monkeypatch):
    """Withdrawing a document has to withdraw it from search too.

    index_needs_rebuild compared mtimes only, and deleting a file leaves every
    surviving mtime alone -- so a removed document went on being retrievable
    out of the stale index.
    """
    from jarvis import documents_rag as dr

    docs = tmp_path / "documents"
    docs.mkdir()
    (docs / "keep.md").write_text("# Keep\nA real pattern.\n", encoding="utf-8")
    (docs / "drop.md").write_text("# Drop\nA fabricated pattern.\n", encoding="utf-8")
    index_file = tmp_path / "documents_index.json"
    index_file.write_text(json.dumps([
        {"source": "keep.md", "title": "Keep", "text": "A real pattern.", "embedding": []},
        {"source": "drop.md", "title": "Drop", "text": "A fabricated pattern.", "embedding": []},
    ]), encoding="utf-8")

    monkeypatch.setattr(dr, "DOCUMENTS_DIR", docs)
    monkeypatch.setattr(dr, "INDEX_FILE", index_file)
    monkeypatch.setattr(dr, "_INDEX_MEM", {"mtime": None, "chunks": None})
    # Make the index look newer than every document, as it would be in practice.
    import os
    import time

    future = time.time() + 60
    os.utime(index_file, (future, future))
    assert dr.index_needs_rebuild() is False

    (docs / "drop.md").unlink()
    assert dr.index_needs_rebuild() is True
