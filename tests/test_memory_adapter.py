"""Memory store tests — no ollama dependency."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

_STORE_PATH = Path(__file__).resolve().parents[1] / "jarvis" / "modules" / "memory_adapter_store.py"
_spec = importlib.util.spec_from_file_location("memory_adapter_store", _STORE_PATH)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

DualWriteMemoryAdapter = _mod.DualWriteMemoryAdapter
platform_data_authoritative = _mod.platform_data_authoritative
wrap_memory_store = _mod.wrap_memory_store


class _FakeLegacy:
    def __init__(self) -> None:
        self._entries = [{"id": "1", "content": "hello", "type": "fact", "namespace": "default"}]

    def get(self, entry_id: str):
        return next((e for e in self._entries if e["id"] == entry_id), None)

    def list_entries(self, namespace=None):
        if namespace:
            return [e for e in self._entries if e.get("namespace") == namespace]
        return list(self._entries)

    def search(self, query, limit=10, *, namespace=None):
        return self.list_entries(namespace)[:limit]

    def add(self, entry_type, content, tags=None, *, namespace=None):
        entry = {"id": "2", "content": content, "type": entry_type, "namespace": namespace or "default"}
        self._entries.append(entry)
        return entry


class TestMemoryAdapter(unittest.TestCase):
    def test_wrap_disabled_returns_legacy(self):
        legacy = _FakeLegacy()
        with patch.object(_mod, "memory_adapter_enabled", return_value=False):
            wrapped = wrap_memory_store(legacy)
        self.assertIs(wrapped, legacy)

    def test_dual_write_delegates_get(self):
        legacy = _FakeLegacy()
        adapter = DualWriteMemoryAdapter(legacy)
        with patch.object(_mod, "platform_data_authoritative", return_value=False):
            self.assertEqual(adapter.get("1"), legacy.get("1"))

    def test_platform_authoritative_env(self):
        with patch.dict("os.environ", {"JARVIS_PLATFORM_DATA_AUTHORITATIVE": "1"}):
            self.assertTrue(platform_data_authoritative())


if __name__ == "__main__":
    unittest.main()
