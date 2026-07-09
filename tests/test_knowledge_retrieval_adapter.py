import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestKnowledgeRetrievalAdapter(unittest.TestCase):
    def test_disabled_without_env(self):
        from jarvis.modules.knowledge_retrieval_adapter import (
            knowledge_retrieval_enabled,
            knowledge_search,
        )

        def legacy_search(query: str, limit: int = 5) -> list[dict]:
            return [{"source": "doc.md", "text": "hello"}]

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED", None)
            self.assertFalse(knowledge_retrieval_enabled())
            hits = knowledge_search("aria:project_docs", legacy_search, "test")
            self.assertEqual(len(hits), 1)

    def test_search_returns_legacy_results(self):
        from jarvis.modules.knowledge_retrieval_adapter import knowledge_search

        def legacy_search(query: str, limit: int = 5) -> list[dict]:
            return [{"source": "readme.md", "text": query}]

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED": "1"}, clear=False),
            patch(
                "aiplatform.applications.knowledge_retrieval.state.knowledge_retrieval_state_dir",
                return_value=Path(tmp),
            ),
            patch(
                "aiplatform.applications.knowledge_retrieval.bridge.shadow_verify_retrieval",
            ),
        ):
            hits = knowledge_search("aria:project_docs", legacy_search, "readme", limit=3)
            self.assertEqual(hits[0]["source"], "readme.md")

    def test_index_build_returns_legacy_chunks(self):
        from jarvis.modules.knowledge_retrieval_adapter import knowledge_index_build

        def legacy_build() -> list[dict]:
            return [{"source": "a.md", "text": "chunk", "embedding": [1.0, 0.0]}]

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED": "1"}, clear=False),
            patch(
                "aiplatform.applications.knowledge_retrieval.state.knowledge_retrieval_state_dir",
                return_value=Path(tmp),
            ),
            patch(
                "aiplatform.applications.knowledge_retrieval.bridge.mirror_index_chunks",
            ),
        ):
            chunks = knowledge_index_build("aria:project_docs", legacy_build)
            self.assertEqual(len(chunks), 1)


if __name__ == "__main__":
    unittest.main()
