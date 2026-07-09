"""Tests for tool executor framework."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from jarvis.behaviors import register_behaviors
from jarvis.handlers.registry import has_action
from jarvis.tools.executor import execute_tool, select_tool, tool_status
from jarvis.tools.registry import get_tool, list_tools


class TestToolRegistry(unittest.TestCase):
    def test_builtin_tools_registered(self):
        tools = list_tools()
        ids = {t.id for t in tools}
        self.assertIn("aria_engineering", ids)
        self.assertIn("cursor", ids)
        self.assertIn("claude_code", ids)

    def test_tool_status_shape(self):
        status = tool_status()
        self.assertIn("tools", status)
        self.assertGreater(status.get("total", 0), 0)

    def test_select_tool_prefers_engineering_for_fix(self):
        tool = select_tool("fix the bug in auth module")
        self.assertIsNotNone(tool)
        assert tool is not None
        self.assertEqual(tool.id, "aria_engineering")

    def test_execute_unknown_tool(self):
        result = execute_tool("not-a-tool", {}, memory_sink=False)
        self.assertFalse(result.get("ok"))

    def test_execute_aria_engineering_delegates(self):
        mock_result = {"ok": True, "message": "engineering done"}
        with patch("jarvis.assistant_instance.get_assistant") as ga:
            ga.return_value.process.return_value = mock_result
            result = execute_tool("aria_engineering", {"task": "fix auth"}, memory_sink=False)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("tool"), "aria_engineering")

    @patch("jarvis.tools.registry._run_cli")
    def test_execute_cli_tool(self, mock_run):
        mock_run.return_value = {"ok": True, "stdout": "done", "returncode": 0}
        tool = get_tool("claude_code")
        if tool and tool.run:
            with patch.object(tool, "available", return_value=True):
                with patch.object(tool, "health", return_value=True):
                    result = execute_tool("claude_code", {"task": "hello"}, memory_sink=False)
        else:
            result = {"ok": False}
        if get_tool("claude_code") and get_tool("claude_code").available():
            self.assertTrue(result.get("ok") or result.get("error"))


class TestToolsBehavior(unittest.TestCase):
    def test_tools_actions_registered(self):
        register_behaviors()
        for action in ("tool_list", "tool_execute", "tool_select", "tool_status", "tool_runs", "tool_run_status"):
            self.assertTrue(has_action(action))


if __name__ == "__main__":
    unittest.main()
