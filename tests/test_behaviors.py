"""Tests for extracted application behaviors."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from jarvis.behaviors import discover_behaviors, get_behavior, register_behaviors
from jarvis.behaviors.conversation import ConversationEngine, ConversationBehavior
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


class TestConversationBehavior(unittest.TestCase):
    def test_discover_conversation_behavior(self):
        behavior = get_behavior("conversation")
        self.assertIsInstance(behavior, ConversationBehavior)
        self.assertEqual(
            behavior.dependencies,
            ["memory", "retrieval", "capability_registry", "workflow_manager"],
        )

    def test_conversation_registers_chat_action(self):
        register_behaviors()
        self.assertTrue(has_action("chat"))

    def test_messages_for_llm_prefix(self):
        engine = ConversationEngine(MagicMock())
        msgs = [{"role": "user", "content": "hello"}]
        out = engine.messages_for_llm(msgs, "Context block")
        self.assertIn("Context block", out[-1]["content"])
        self.assertIn("hello", out[-1]["content"])

    def test_validate_dependencies_soft(self):
        behavior = ConversationBehavior()
        with patch.dict(os.environ, {}, clear=True):
            warnings = behavior.validate()
        self.assertEqual(len(warnings), 4)

    def test_lifecycle_health(self):
        behavior = ConversationBehavior()
        health = behavior.health()
        self.assertEqual(health["behavior_id"], "conversation")
        self.assertIn("dependencies", health)


if __name__ == "__main__":
    unittest.main()
