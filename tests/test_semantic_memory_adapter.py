import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestSemanticMemoryAdapter(unittest.TestCase):
    def test_wrap_disabled_without_env(self):
        from jarvis.modules.semantic_memory_adapter_store import (
            semantic_memory_adapter_enabled,
            wrap_semantic_memory_store,
        )

        legacy = object()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED", None)
            self.assertFalse(semantic_memory_adapter_enabled())
            self.assertIs(wrap_semantic_memory_store(legacy), legacy)

    def test_get_returns_legacy_vector(self):
        from jarvis.modules.semantic_memory_adapter_store import SemanticMemoryAdapter

        class Legacy:
            def get(self, memory_id: str) -> list[float]:
                return [1.0, 0.0]

            def search(self, *args, **kwargs):
                return []

        with patch.dict(os.environ, {"JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED": "1"}, clear=False):
            adapter = SemanticMemoryAdapter(Legacy())
            with patch.object(adapter, "_shadow_get"):
                self.assertEqual(adapter.get("abc"), [1.0, 0.0])

    def test_upsert_records_legacy_metric(self):
        from jarvis.modules.semantic_memory_adapter_store import SemanticMemoryAdapter

        class Legacy:
            def upsert(self, memory_id, vector, *, namespace="default", entry_type="fact", content=""):
                pass

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED": "1"}, clear=False),
            patch(
                "aiplatform.applications.semantic.state.semantic_memory_state_dir",
                return_value=Path(tmp),
            ),
        ):
            adapter = SemanticMemoryAdapter(Legacy(), application_id="aria")
            with patch.object(adapter, "_mirror_upsert"):
                with patch.object(adapter, "_record_legacy_write"):
                    adapter.upsert("id1", [1.0, 0.0], namespace="profile", content="hello")
            from aiplatform.applications.semantic.metrics import record_legacy_write

            record_legacy_write("aria", "profile")
            from aiplatform.applications.semantic.metrics import metrics_view

            state = metrics_view("aria")
            self.assertEqual(state.legacy_writes, 1)


if __name__ == "__main__":
    unittest.main()
