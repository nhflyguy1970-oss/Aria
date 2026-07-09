"""Tests for daily workflow."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from jarvis.workflows.daily import anything_broken, dispatch, repos_need_attention


class TestDailyWorkflow(unittest.TestCase):
    @patch("jarvis.workstation.operations.diagnose")
    @patch("jarvis.workstation.operations.format_report")
    def test_anything_broken(self, mock_report, mock_diag):
        mock_diag.return_value = {"ok": False, "issues": []}
        mock_report.return_value = "issues found"
        result = anything_broken()
        self.assertFalse(result.get("ok"))
        self.assertIn("issues", result.get("message", ""))

    @patch("jarvis.knowledge.git_sync.list_repo_states")
    def test_repos_clean(self, mock_states):
        mock_states.return_value = []
        result = repos_need_attention()
        self.assertTrue(result.get("ok"))

    def test_dispatch_unknown(self):
        assistant = MagicMock()
        result = dispatch("not_a_real_intent", assistant)
        self.assertFalse(result.get("ok"))


if __name__ == "__main__":
    unittest.main()
