"""Phase 2 — Aria Core skeleton delegates without behavior change."""

from __future__ import annotations

from pathlib import Path

from aria_core.ownership import OWNERSHIP, all_module_names, module_ownership

REQUIRED_MODULES = {
    "identity",
    "memory",
    "knowledge",
    "learning",
    "reasoning",
    "planning",
    "reference",
    "runtime",
    "capabilities",
    "interfaces",
    "applications",
    "platform",
    "services",
    "operations",
    "infrastructure",
    "events",
}

OWNER_FIELDS = {
    "owner",
    "responsibilities",
    "public_api",
    "private_api",
    "dependencies",
    "consumers",
    "allowed_writers",
    "allowed_readers",
    "source_of_truth",
    "implementation",
    "future_owner",
}


def test_all_required_modules_registered():
    names = set(all_module_names())
    assert REQUIRED_MODULES <= names


def test_ownership_records_complete():
    for name in REQUIRED_MODULES:
        rec = module_ownership(name)
        assert OWNER_FIELDS <= set(rec.keys()), name
        assert rec["owner"].startswith("aria_core.")


def test_learning_governor_passthrough_via_core():
    from aria_core import learning

    assert learning.enabled() is True
    calls = []

    def apply():
        calls.append(1)
        return {"ok": True}

    out = learning.commit(learning.propose(kind="phase2", payload={}), apply)
    assert out == {"ok": True}
    assert calls == [1]


def test_memory_store_via_core_is_jarvis_facade():
    from aria_core import memory
    from jarvis.modules.memory import MemoryStore as JarvisStore

    store = memory.MemoryStore()
    assert type(store) is JarvisStore or store.__class__.__name__ == "MemoryStore"


def test_reference_search_via_core():
    from aria_core import reference

    result = reference.search_reference("Aria Core")
    assert isinstance(result, dict)
    assert "hits" in result or "ok" in result


def test_identity_and_interfaces_snapshots():
    from aria_core import identity, interfaces

    snap = identity.identity_snapshot()
    assert "uncensored" in snap
    desc = interfaces.describe_interfaces()
    assert "mission_control" in desc
    assert "chat_gui" in desc


def test_capabilities_match_contract_count():
    from aria_core import capabilities

    ids = capabilities.list_capability_ids()
    assert len(ids) >= 90
    assert "chat-assistant" in ids
    assert "aria-uncensored" in ids


def test_api_doc_exists():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs" / "aria_core" / "ARIA_CORE_API.md").is_file()
    assert (root / "docs" / "aria_core" / "PHASE2.md").is_file()


def test_ownership_dict_matches_module_count():
    assert len(OWNERSHIP) == len(REQUIRED_MODULES)
