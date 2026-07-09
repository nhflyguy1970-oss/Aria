"""Tests for Aria workstation control plane (registry, lifecycle, operations)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from jarvis.behaviors import get_behavior, register_behaviors
from jarvis.handlers.registry import call_action, has_action
from jarvis.workstation.lifecycle import down, restart, status, up
from jarvis.workstation.operations import diagnose, format_report, recover_safe
from jarvis.workstation.registry import all_components, component, get_registry


class TestWorkstationRegistry(unittest.TestCase):
    def test_registry_has_core_components(self):
        reg = get_registry()
        for cid in ("ollama", "aria", "comfyui", "workstation", "searxng", "postgres"):
            self.assertIn(cid, reg)

    def test_all_components_sorted(self):
        items = all_components()
        self.assertGreater(len(items), 10)
        categories = {c.category for c in items}
        self.assertIn("inference", categories)
        self.assertIn("database", categories)

    def test_component_lookup(self):
        ollama = component("ollama")
        self.assertIsNotNone(ollama)
        assert ollama is not None
        self.assertEqual(ollama.label, "Ollama")
        self.assertTrue(ollama.required)


class TestWorkstationLifecycle(unittest.TestCase):
    @patch("jarvis.services._ollama_healthy", return_value=True)
    @patch("jarvis.services._jarvis_port_open", return_value=True)
    def test_status_ready_when_core_up(self, _port, _ollama):
        snap = status(force=True)
        self.assertTrue(snap.get("ready"))
        self.assertIn("components", snap)
        self.assertIn("summary", snap)

    @patch("jarvis.workstation.lifecycle.component")
    def test_up_unknown_component(self, mock_component):
        mock_component.return_value = None
        result = up("not-a-real-component")
        self.assertFalse(result.get("ok"))
        self.assertIn("Unknown component", result.get("error", ""))

    @patch("jarvis.workstation.lifecycle.component")
    def test_restart_managed_component(self, mock_component):
        comp = MagicMock()
        comp.managed = True
        comp.restart = MagicMock(return_value=True)
        mock_component.return_value = comp
        with patch("jarvis.workstation.lifecycle.status", return_value={"ready": True}):
            result = restart("comfyui")
        self.assertTrue(result.get("ok"))
        comp.restart.assert_called_once()

    @patch("jarvis.workstation.lifecycle.component")
    def test_down_skips_required(self, mock_component):
        comp = MagicMock()
        comp.managed = True
        comp.required = True
        comp.healthy = MagicMock(return_value=True)
        mock_component.return_value = comp
        with patch("jarvis.workstation.lifecycle.all_components", return_value=[comp]):
            with patch("jarvis.workstation.lifecycle.status", return_value={"ready": True}):
                result = down()
        self.assertTrue(result.get("ok"))


class TestWorkstationOperations(unittest.TestCase):
    @patch("jarvis.services._ollama_healthy", return_value=False)
    @patch("jarvis.services._jarvis_port_open", return_value=False)
    def test_diagnose_flags_required_down(self, _port, _ollama):
        report = diagnose(force=True)
        self.assertFalse(report.get("ok"))
        self.assertGreater(report.get("critical", 0), 0)
        issues = report.get("issues") or []
        self.assertTrue(any(i.get("component") == "ollama" for i in issues))

    def test_format_report_contains_heading(self):
        text = format_report(force=True)
        self.assertIn("Workstation Status", text)

    @patch("jarvis.workstation.operations.diagnose")
    @patch("jarvis.workstation.operations.up")
    def test_recover_bootstraps_when_no_auto_issues(self, mock_up, mock_diagnose):
        mock_diagnose.side_effect = [
            {
                "ok": False,
                "issues": [{"auto_recoverable": False, "component": "gpu", "action": "alert"}],
            },
            {"ok": True, "issues": []},
        ]
        mock_up.return_value = {"ok": True}
        result = recover_safe()
        self.assertTrue(result.get("ok"))
        mock_up.assert_called()


class TestWorkstationLifecycleCli(unittest.TestCase):
    def test_cli_parses_lifecycle_commands(self):
        from jarvis.workstation.cli import main

        with self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    @patch("jarvis.workstation.inventory.verify_inventory", return_value={"ready": True, "blockers": [], "warnings": [], "inventory": {"summary": {"ready": True, "total": 1, "healthy": 1}}})
    @patch("jarvis.workstation.inventory.format_inventory_text", return_value="## Inventory")
    def test_verify_uses_inventory(self, _fmt, mock_verify):
        from jarvis.workstation.cli import main

        self.assertEqual(main(["verify"]), 0)
        mock_verify.assert_called_once()


class TestOperationsBehavior(unittest.TestCase):
    def test_operations_behavior_registered(self):
        behavior = get_behavior("operations")
        from jarvis.behaviors.operations import OperationsBehavior

        self.assertIsInstance(behavior, OperationsBehavior)
        self.assertIn("workstation_status", behavior.action_names)

    def test_operations_actions_in_registry(self):
        register_behaviors()
        for action in (
            "workstation_status",
            "workstation_diagnose",
            "workstation_recover",
            "workstation_up",
            "workstation_restart",
        ):
            self.assertTrue(has_action(action))

    @patch("jarvis.workstation.operations.format_report", return_value="## Workstation Status\nOK")
    @patch("jarvis.workstation.lifecycle.status", return_value={"ready": True})
    def test_workstation_status_action(self, _status, _report):
        register_behaviors()
        result = call_action(MagicMock(), "workstation_status", {}, "status")
        self.assertTrue(result.get("ok"))
        self.assertIn("Workstation Status", result.get("message", ""))


if __name__ == "__main__":
    unittest.main()
