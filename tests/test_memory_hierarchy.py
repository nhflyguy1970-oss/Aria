"""Tests for memory hierarchy."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from jarvis.memory.hierarchy import (
    MemoryLayer,
    consolidate,
    hierarchical_search,
    infer_layer,
    should_promote,
    should_prune,
    tag_layer,
)


class TestMemoryHierarchy(unittest.TestCase):
    def test_infer_layer_from_namespace(self):
        entry = {"type": "note", "namespace": "project:jarvis", "tags": []}
        self.assertEqual(infer_layer(entry), MemoryLayer.PROJECT.value)

    def test_infer_preference_long_term(self):
        entry = {"type": "preference", "namespace": "default", "tags": []}
        self.assertEqual(infer_layer(entry), MemoryLayer.LONG_TERM.value)

    def test_tag_layer(self):
        tagged = tag_layer({"id": "1", "tags": []}, MemoryLayer.SEMANTIC)
        self.assertIn("layer:semantic", tagged["tags"])

    def test_should_promote_conversation(self):
        entry = {
            "type": "note",
            "namespace": "project:test",
            "access_count": 4,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tags": ["layer:conversation"],
        }
        self.assertEqual(should_promote(entry), MemoryLayer.PROJECT.value)

    def test_should_prune_old_auto(self):
        old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        entry = {
            "type": "auto",
            "namespace": "default",
            "access_count": 0,
            "timestamp": old,
            "tags": ["layer:conversation"],
        }
        self.assertTrue(should_prune(entry))

    def test_hierarchical_search_ranks(self):
        memory = MagicMock()
        memory.search.return_value = [
            {"id": "a", "type": "auto", "namespace": "default", "access_count": 1, "timestamp": datetime.now(timezone.utc).isoformat(), "tags": [], "score": 0.5},
            {"id": "b", "type": "preference", "namespace": "profile", "access_count": 5, "timestamp": datetime.now(timezone.utc).isoformat(), "tags": [], "score": 0.4},
        ]
        hits = hierarchical_search(memory, "test", limit=2)
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0]["id"], "b")

    def test_consolidate_dry_run(self):
        memory = MagicMock()
        memory.list_entries.return_value = [
            {
                "id": "1",
                "type": "note",
                "namespace": "project:x",
                "access_count": 5,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tags": ["layer:conversation"],
            }
        ]
        result = consolidate(memory, dry_run=True)
        self.assertTrue(result.get("ok"))


if __name__ == "__main__":
    unittest.main()
