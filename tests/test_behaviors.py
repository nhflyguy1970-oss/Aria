"""Tests for extracted application behaviors."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from jarvis.behaviors import discover_behaviors, register_behaviors
from jarvis.handlers.registry import call_action, has_action


class TestGitBehavior(unittest.TestCase):
    def test_git_behavior_registered(self):
        register_behaviors()
        self.assertTrue(has_action("git_status"))
        self.assertTrue(has_action("git_diff"))

    def test_discover_git_behavior(self):
        behaviors = discover_behaviors()
        git = next(item for item in behaviors if item.behavior_id == "git")
        self.assertEqual(git.name, "Git")
        self.assertEqual(git.category, "Coding")
        self.assertEqual(git.action_names, ["git_status", "git_diff"])

    @patch("jarvis.git_util.status", return_value="clean")
    def test_git_status_via_registry(self, _mock_status):
        register_behaviors()
        assistant = MagicMock()
        result = call_action(assistant, "git_status", {}, "status")
        self.assertIn("clean", result.get("message", ""))


if __name__ == "__main__":
    unittest.main()
