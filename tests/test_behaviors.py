"""Tests for extracted application behaviors."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from jarvis.behaviors import discover_behaviors, get_behavior, register_behaviors
from jarvis.behaviors.conversation import ConversationEngine, ConversationBehavior
from jarvis.handlers.registry import call_action, has_action


class TestEngineeringBehavior(unittest.TestCase):
    def test_git_actions_registered(self):
        register_behaviors()
        self.assertTrue(has_action("git_status"))
        self.assertTrue(has_action("git_diff"))
        self.assertTrue(has_action("coding_read"))

    def test_discover_engineering_behavior(self):
        behavior = get_behavior("engineering")
        from jarvis.behaviors.engineering import EngineeringBehavior

        self.assertIsInstance(behavior, EngineeringBehavior)
        self.assertIn("git_status", behavior.action_names)
        self.assertIn("coding_read", behavior.action_names)

    @patch("jarvis.git_util.status", return_value="clean")
    def test_git_status_via_registry(self, _mock_status):
        register_behaviors()
        assistant = MagicMock()
        result = call_action(assistant, "git_status", {}, "status")
        self.assertIn("clean", result.get("message", ""))


class TestKnowledgeBehavior(unittest.TestCase):
    def test_discover_knowledge_behavior(self):
        behavior = get_behavior("knowledge")
        from jarvis.behaviors.knowledge import KnowledgeBehavior

        self.assertIsInstance(behavior, KnowledgeBehavior)
        self.assertIn("web_search", behavior.action_names)
        self.assertIn("document_search", behavior.action_names)

    def test_knowledge_registers_actions(self):
        register_behaviors()
        for action in ("web_search", "learn_about", "document_info", "ingest_document"):
            self.assertTrue(has_action(action))

    def test_prepare_context_default(self):
        from jarvis.behaviors.knowledge import KnowledgeBehavior

        behavior = KnowledgeBehavior()
        parts, citations = behavior.prepare_context(MagicMock(), "hello")
        self.assertIsInstance(parts, list)
        self.assertIsInstance(citations, list)


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


class TestPlanningBehavior(unittest.TestCase):
    def test_discover_planning_behavior(self):
        behavior = get_behavior("planning")
        from jarvis.behaviors.planning import PlanningBehavior

        self.assertIsInstance(behavior, PlanningBehavior)
        self.assertEqual(behavior.stability, "stable")
        self.assertEqual(behavior.owner, "application")
        self.assertIn("planner_set_timer", behavior.action_names)

    def test_planning_registers_actions(self):
        register_behaviors()
        for action in (
            "planner_add_task",
            "planner_set_timer",
            "planner_today",
            "journal_schedule",
            "journal_log",
            "journal_today",
            "journal_open_tasks",
        ):
            self.assertTrue(has_action(action))

    @patch("jarvis.feature_flags.planner_enabled", return_value=True)
    def test_add_task_via_registry(self, _enabled):
        register_behaviors()
        with patch("jarvis.planner_store.add_task", return_value={"text": "buy milk"}):
            result = call_action(MagicMock(), "planner_add_task", {"text": "buy milk"}, "add task")
        self.assertIn("buy milk", result.get("message", ""))


class TestMemoryBehavior(unittest.TestCase):
    def test_discover_memory_behavior(self):
        behavior = get_behavior("memory")
        from jarvis.behaviors.memory import MemoryBehavior

        self.assertIsInstance(behavior, MemoryBehavior)
        self.assertEqual(behavior.stability, "stable")
        self.assertEqual(behavior.owner, "application")
        self.assertEqual(behavior.version, "1.0.0")
        self.assertIn("remember", behavior.action_names)
        self.assertIn("memory_search", behavior.action_names)

    def test_memory_registers_actions(self):
        register_behaviors()
        for action in ("remember", "recall", "memory_search", "project_checkpoint"):
            self.assertTrue(has_action(action))

    def test_prepare_context_default(self):
        from jarvis.behaviors.memory import MemoryBehavior

        behavior = MemoryBehavior()
        parts, citations = behavior.prepare_context(MagicMock(), "hello")
        self.assertIsInstance(parts, list)
        self.assertIsInstance(citations, list)


if __name__ == "__main__":
    unittest.main()
