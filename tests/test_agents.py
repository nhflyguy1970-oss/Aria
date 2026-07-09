"""Tests for agent coordinator."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from jarvis.agents.coordinator import AgentCoordinator, suggest_agents
from jarvis.behaviors import register_behaviors
from jarvis.handlers.registry import has_action


class TestAgentCoordinator(unittest.TestCase):
    def test_suggest_agents_research_and_code(self):
        roles = suggest_agents("research vector stores and implement indexing")
        self.assertIn("research", roles)
        self.assertIn("coding", roles)

    def test_suggest_defaults_when_ambiguous(self):
        roles = suggest_agents("hello there")
        self.assertTrue(roles)

    @patch("jarvis.handlers.registry.has_action", return_value=True)
    @patch("jarvis.handlers.registry.call_action")
    def test_run_chain_executes_steps(self, mock_call, _has):
        mock_call.return_value = {"ok": True, "message": "step done"}
        coord = AgentCoordinator(MagicMock())
        result = coord.run_chain("research LiteLLM", roles=["research", "operations"])
        self.assertEqual(len(result.get("steps") or []), 2)
        self.assertTrue(result.get("ok"))

    def test_agent_actions_registered(self):
        register_behaviors()
        self.assertTrue(has_action("agent_chain"))
        self.assertTrue(has_action("agent_suggest"))


if __name__ == "__main__":
    unittest.main()
