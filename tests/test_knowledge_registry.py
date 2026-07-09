"""Tests for knowledge registry and unified search."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.knowledge.registry import (
    KnowledgeSource,
    discover_all_sources,
    format_registry_markdown,
    sync_registry,
)
from jarvis.knowledge.search import format_unified_results, unified_search


class TestKnowledgeRegistry(unittest.TestCase):
    def test_knowledge_source_roundtrip(self):
        src = KnowledgeSource(
            id="test-1",
            type="markdown",
            label="Test",
            location="/tmp/test",
            retrieval_available=True,
        )
        restored = KnowledgeSource.from_dict(src.to_dict())
        self.assertEqual(restored.id, "test-1")
        self.assertTrue(restored.retrieval_available)

    def test_discover_includes_core_sources(self):
        sources = discover_all_sources()
        types = {s.type for s in sources}
        self.assertIn("document_library", types)
        self.assertIn("code_index", types)

    def test_sync_persists_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg_file = Path(tmp) / "registry.json"
            with patch("jarvis.knowledge.registry.REGISTRY_FILE", reg_file):
                with patch("jarvis.knowledge.registry.REGISTRY_DIR", Path(tmp)):
                    result = sync_registry()
                    self.assertTrue(result.get("ok"))
                    self.assertTrue(reg_file.is_file())
                    data = json.loads(reg_file.read_text())
                    self.assertIn("sources", data)

    def test_registry_markdown(self):
        text = format_registry_markdown(refresh=True)
        self.assertIn("Knowledge Registry", text)


class TestUnifiedSearch(unittest.TestCase):
    @patch("jarvis.knowledge.search._search_documents", return_value=[{
        "source_type": "document_library",
        "source_label": "Document Library",
        "title": "LiteLLM Guide",
        "excerpt": "LiteLLM routing",
        "location": "guide.pdf",
        "strategy": "semantic",
        "score": 0.9,
    }])
    @patch("jarvis.knowledge.search._search_code", return_value=[])
    @patch("jarvis.knowledge.search._search_memory", return_value=[])
    @patch("jarvis.knowledge.search._search_journal", return_value=[])
    @patch("jarvis.knowledge.search._search_project_docs", return_value=[])
    @patch("jarvis.knowledge.search._search_learned", return_value=[])
    @patch("jarvis.knowledge.search.list_sources", return_value=[
        KnowledgeSource(
            id="d1",
            type="document_library",
            label="Docs",
            location="/data/documents",
            retrieval_available=True,
        )
    ])
    def test_unified_search_merges_hits(self, *_mocks):
        result = unified_search("LiteLLM")
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("hit_count"), 1)
        text = format_unified_results(result)
        self.assertIn("LiteLLM", text)

    def test_unified_search_requires_query(self):
        result = unified_search("")
        self.assertFalse(result.get("ok"))

    @patch("jarvis.behaviors.get_behavior")
    def test_knowledge_actions_registered(self, _mock):
        from jarvis.behaviors import register_behaviors
        from jarvis.handlers.registry import has_action

        register_behaviors()
        self.assertTrue(has_action("unified_search"))
        self.assertTrue(has_action("knowledge_registry"))
        self.assertTrue(has_action("knowledge_sync"))


if __name__ == "__main__":
    unittest.main()
