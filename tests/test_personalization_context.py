"""Tests for personalization and unified context."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from jarvis.personalization.store import (
    preferred_model,
    preferred_tool,
    record_model_use,
    record_tool_use,
    snapshot,
)


class TestPersonalization(unittest.TestCase):
    def test_record_and_prefer_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefs_file = Path(tmp) / "preferences.json"
            with patch("jarvis.personalization.store.PREFS_FILE", prefs_file):
                record_model_use("general", "qwen2.5:7b")
                record_model_use("general", "qwen2.5:7b")
                record_model_use("general", "llama3.1:8b")
                self.assertEqual(preferred_model("general"), "qwen2.5:7b")

    def test_record_tool_preference(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefs_file = Path(tmp) / "preferences.json"
            with patch("jarvis.personalization.store.PREFS_FILE", prefs_file):
                record_tool_use("claude_code", success=True)
                record_tool_use("claude_code", success=True)
                record_tool_use("continue", success=True)
                self.assertEqual(preferred_tool(), "claude_code")

    def test_snapshot_shape(self):
        snap = snapshot()
        self.assertIn("preferences", snap)


class TestUnifiedContext(unittest.TestCase):
    def test_append_context_extras(self):
        from jarvis.context.builder import append_context_extras

        parts: list[str] = []
        meta: dict = {}
        assistant = MagicMock()
        assistant.memory.search.return_value = [{"content": "tool ran ok"}]
        with patch("jarvis.context.builder._append_workspace") as ws:
            ws.side_effect = lambda p, m: p.append("workstation line")
            append_context_extras(parts, assistant, "hello", meta)
        self.assertIn("workstation line", parts[0])


if __name__ == "__main__":
    unittest.main()
