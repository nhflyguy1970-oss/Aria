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
    @patch("jarvis.search_product.pipeline.run_search")
    def test_unified_search_merges_hits(self, mock_run):
        mock_run.return_value = {
            "ok": True,
            "query": "LiteLLM",
            "corpora": ["documents"],
            "searched": ["documents"],
            "results": [
                {
                    "id": "1",
                    "source": "documents",
                    "source_label": "Document Library",
                    "title": "LiteLLM Guide",
                    "summary": "LiteLLM routing",
                    "preview": "LiteLLM routing",
                    "location": "guide.pdf",
                    "score": 0.9,
                    "confidence": 0.85,
                    "strategy": "semantic",
                    "open": {"view": "documents"},
                    "metadata": {},
                    "highlights": [],
                    "icon": "documents",
                }
            ],
            "latency_ms": 1.0,
            "intent": {"primary": "documents"},
        }
        result = unified_search("LiteLLM")
        self.assertTrue(result["ok"])
        self.assertEqual(result["pipeline"], "shared_search_pipeline")
        self.assertEqual(len(result["hits"]), 1)
        self.assertIn("LiteLLM", result["hits"][0]["title"])
        self.assertTrue(result["results"])
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
