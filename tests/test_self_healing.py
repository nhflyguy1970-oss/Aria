"""Tests for expanded self-healing operations."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from jarvis.workstation.operations import _issue_action, diagnose, recover_safe


class TestSelfHealing(unittest.TestCase):
    def test_ollama_uses_start_not_restart(self):
        self.assertEqual(_issue_action("ollama"), "start")

    def test_litellm_uses_restart(self):
        self.assertEqual(_issue_action("litellm"), "restart")

    @patch("jarvis.workstation.operations.registry_snapshot")
    def test_diagnose_ok_when_healthy(self, mock_snap):
        mock_snap.return_value = {
            "components": [{"id": "ollama", "label": "Ollama", "required": True, "running": True}],
            "resources": {},
            "environment": {"disk_free_gb": 100},
        }
        report = diagnose(force=True)
        self.assertTrue(report.get("ok"))

    @patch("jarvis.workstation.operations.up")
    @patch("jarvis.workstation.operations.diagnose")
    def test_recover_no_issues(self, mock_diag, mock_up):
        mock_diag.return_value = {"ok": True, "issues": []}
        result = recover_safe()
        self.assertTrue(result.get("ok"))
        mock_up.assert_not_called()


if __name__ == "__main__":
    unittest.main()
