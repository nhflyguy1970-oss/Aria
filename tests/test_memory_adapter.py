import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestMemoryAdapterStore(unittest.TestCase):
    def test_wrap_disabled_without_env(self):
        from jarvis.modules.memory_adapter_store import memory_adapter_enabled, wrap_memory_store

        legacy = object()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JARVIS_PLATFORM_MEMORY_ATTACHED", None)
            self.assertFalse(memory_adapter_enabled())
            self.assertIs(wrap_memory_store(legacy), legacy)

    def test_dual_write_records_legacy_metric(self):
        from jarvis.modules.memory_adapter_store import DualWriteMemoryAdapter

        class Legacy:
            def add(self, entry_type, content, tags=None, *, namespace=None):
                return {
                    "id": "abc123",
                    "type": entry_type,
                    "content": content,
                    "namespace": namespace or "default",
                    "tags": tags or [],
                }

            def get(self, entry_id):
                return {"id": entry_id, "content": "hello", "namespace": "default", "type": "fact"}

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"JARVIS_PLATFORM_MEMORY_ATTACHED": "1"}, clear=False),
            patch(
                "aiplatform.applications.memory.state.memory_adapter_state_dir",
                return_value=Path(tmp),
            ),
            patch("aiplatform.applications.memory.bridge.mirror_add"),
        ):
            adapter = DualWriteMemoryAdapter(Legacy())
            entry = adapter.add("fact", "hello", namespace="profile")
            self.assertEqual(entry["content"], "hello")
            from aiplatform.applications.memory.metrics import metrics_view

            state = metrics_view("aria")
            self.assertEqual(state.legacy_writes, 1)


if __name__ == "__main__":
    unittest.main()
