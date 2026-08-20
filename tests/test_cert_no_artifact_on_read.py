"""Opening the certification page must not leave anything behind.

Production Integrity treats DATA_DIR/certification as development residue and
deducts for it. Reading the certification home page used to create that
directory and write a legacy_probes.json into it, so a production install that
had never certified anything still failed its own integrity check — and the
index counted itself as a probe, recording its own previous size, so the file
grew by one generation on every read.
"""

from __future__ import annotations

import json

import pytest

from jarvis.certification_product import store


@pytest.fixture
def cert_root(tmp_path, monkeypatch):
    root = tmp_path / "certification"
    monkeypatch.setattr(store, "CERT_ROOT", root)
    monkeypatch.setattr(store, "RUNS_DIR", root / "runs")
    monkeypatch.setattr(store, "INDEX_FILE", root / "index.json")
    monkeypatch.setattr(store, "LATEST_FILE", root / "latest_run.json")
    return root


def test_ingest_creates_nothing_when_never_certified(cert_root):
    assert not cert_root.exists()
    result = store.ingest_legacy_probes()
    assert result["ok"] is True
    assert result["probes"] == []
    assert not cert_root.exists(), "reading conjured a certification directory"


def test_listing_runs_creates_nothing(cert_root):
    assert store.list_runs() == []
    assert not cert_root.exists(), "listing runs conjured a certification directory"


def test_invalidate_creates_nothing(cert_root):
    store.invalidate_unverified_ready_runs()
    assert not cert_root.exists()


def test_index_does_not_count_itself(cert_root):
    cert_root.mkdir(parents=True)
    (cert_root / "legacy_probes.json").write_text(
        json.dumps({"probes": [{"name": "legacy_probes.json", "bytes": 46}]}), encoding="utf-8"
    )
    result = store.ingest_legacy_probes()
    assert result["probes"] == [], "the index listed itself as a probe"


def test_real_probes_are_still_indexed(cert_root):
    cert_root.mkdir(parents=True)
    (cert_root / "smoke_probe.json").write_text('{"x": 1}', encoding="utf-8")
    result = store.ingest_legacy_probes()
    assert [p["name"] for p in result["probes"]] == ["smoke_probe.json"]
    written = json.loads((cert_root / "legacy_probes.json").read_text(encoding="utf-8"))
    assert [p["name"] for p in written["probes"]] == ["smoke_probe.json"]


def test_repeated_reads_do_not_grow_the_index(cert_root):
    cert_root.mkdir(parents=True)
    (cert_root / "smoke_probe.json").write_text('{"x": 1}', encoding="utf-8")
    store.ingest_legacy_probes()
    first = (cert_root / "legacy_probes.json").read_text(encoding="utf-8")
    for _ in range(3):
        store.ingest_legacy_probes()
    after = json.loads((cert_root / "legacy_probes.json").read_text(encoding="utf-8"))
    assert [p["name"] for p in after["probes"]] == ["smoke_probe.json"]
    assert len(after["probes"]) == len(json.loads(first)["probes"])
