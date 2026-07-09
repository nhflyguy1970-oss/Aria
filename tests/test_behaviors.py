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
        for action in ("branch_create", "branch_switch", "branch_list", "branch_delete"):
            self.assertTrue(has_action(action))

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


class TestAudioBehavior(unittest.TestCase):
    def test_discover_audio_behavior(self):
        behavior = get_behavior("audio")
        from jarvis.behaviors.audio import AudioBehavior

        self.assertIsInstance(behavior, AudioBehavior)
        self.assertIn("transcribe", behavior.action_names)
        self.assertIn("generate_song", behavior.action_names)

    def test_audio_registers_actions(self):
        register_behaviors()
        for action in ("transcribe", "generate_audio", "speak", "diarize_audio"):
            self.assertTrue(has_action(action))


class TestMediaBehavior(unittest.TestCase):
    def test_discover_media_behavior(self):
        behavior = get_behavior("media")
        from jarvis.behaviors.media import MediaBehavior

        self.assertIsInstance(behavior, MediaBehavior)
        self.assertIn("generate_image", behavior.action_names)
        self.assertIn("enhance_prompt", behavior.action_names)

    def test_media_registers_actions(self):
        from jarvis.handlers.registry import get_queue

        register_behaviors()
        self.assertTrue(has_action("enhance_prompt"))
        self.assertEqual(get_queue("generate_image"), "media")


class TestVisionBehavior(unittest.TestCase):
    def test_discover_vision_behavior(self):
        behavior = get_behavior("vision")
        from jarvis.behaviors.vision import VisionBehavior

        self.assertIsInstance(behavior, VisionBehavior)
        self.assertIn("describe_image", behavior.action_names)
        self.assertIn("compare_images", behavior.action_names)

    def test_vision_registers_actions(self):
        register_behaviors()
        for action in (
            "describe_image",
            "analyze_image",
            "ocr_image",
            "compare_images",
            "analyze_video_frame",
        ):
            self.assertTrue(has_action(action))


class TestDataBehavior(unittest.TestCase):
    def test_discover_data_behavior(self):
        behavior = get_behavior("data")
        from jarvis.behaviors.data import DataBehavior

        self.assertIsInstance(behavior, DataBehavior)
        self.assertIn("data_load", behavior.action_names)
        self.assertIn("data_chart", behavior.action_names)

    def test_data_registers_actions(self):
        register_behaviors()
        for action in (
            "data_load",
            "data_query",
            "data_summary",
            "data_chart",
            "data_sql",
        ):
            self.assertTrue(has_action(action))


class TestSmartHomeBehavior(unittest.TestCase):
    def test_discover_smarthome_behavior(self):
        behavior = get_behavior("smarthome")
        from jarvis.behaviors.smarthome import SmartHomeBehavior

        self.assertIsInstance(behavior, SmartHomeBehavior)
        self.assertIn("ha_status", behavior.action_names)
        self.assertIn("ha_control", behavior.action_names)

    def test_smarthome_registers_actions(self):
        register_behaviors()
        for action in ("ha_status", "ha_control", "ha_scene", "ha_query", "ha_set_token"):
            self.assertTrue(has_action(action))


class TestBriefingBehavior(unittest.TestCase):
    def test_discover_briefing_behavior(self):
        behavior = get_behavior("briefing")
        from jarvis.behaviors.briefing import BriefingBehavior

        self.assertIsInstance(behavior, BriefingBehavior)
        self.assertIn("morning_briefing", behavior.action_names)
        self.assertIn("briefing_news_detail", behavior.action_names)

    def test_briefing_registers_actions(self):
        register_behaviors()
        for action in ("morning_briefing", "briefing_news_detail"):
            self.assertTrue(has_action(action))


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
