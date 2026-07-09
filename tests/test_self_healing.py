"""Tests for expanded self-healing operations."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from jarvis.application.standalone.workstation_impl.operations import (
    _issue_action,
    diagnose,
    recover_safe,
)


class TestSelfHealing(unittest.TestCase):
    def test_ollama_uses_start_not_restart(self):
        self.assertEqual(_issue_action("ollama"), "start")

    def test_litellm_uses_restart(self):
        self.assertEqual(_issue_action("litellm"), "restart")

    @patch("jarvis.application.standalone.workstation_impl.operations.registry_snapshot")
    def test_diagnose_ok_when_healthy(self, mock_snap):
        mock_snap.return_value = {
            "components": [{"id": "ollama", "label": "Ollama", "required": True, "running": True}],
            "resources": {},
            "environment": {"disk_free_gb": 100},
        }
        report = diagnose(force=True)
        self.assertTrue(report.get("ok"))

    @patch("jarvis.application.standalone.workstation_impl.operations.registry_snapshot")
    def test_diagnose_optional_managed_when_enabled(self, mock_snap):
        mock_snap.return_value = {
            "components": [
                {
                    "id": "postgres",
                    "label": "PostgreSQL",
                    "required": False,
                    "managed": True,
                    "autostart": False,
                    "running": False,
                }
            ],
            "resources": {},
            "environment": {},
        }
        with patch.dict("os.environ", {"JARVIS_AUTO_RECOVER_OPTIONAL": "1"}, clear=False):
            report = diagnose(force=True)
        postgres = [i for i in report.get("issues") or [] if i.get("component") == "postgres"]
        self.assertEqual(len(postgres), 1)
        self.assertTrue(postgres[0].get("auto_recoverable"))

    @patch("jarvis.server_restart.request_restart")
    def test_recover_aria_requests_restart(self, mock_restart):
        mock_restart.return_value = {"ok": True, "message": "restarting"}
        from jarvis.application.standalone.workstation_impl.operations import _recover_aria

        result = _recover_aria()
        self.assertTrue(result.get("ok"))
        mock_restart.assert_called_once()

    @patch("jarvis.application.standalone.workstation_impl.operations.registry_snapshot")
    def test_diagnose_aria_offline_is_recoverable(self, mock_snap):
        mock_snap.return_value = {
            "components": [
                {
                    "id": "aria",
                    "label": "Aria",
                    "required": True,
                    "running": False,
                    "managed": False,
                }
            ],
            "resources": {},
            "environment": {},
        }
        report = diagnose(force=True)
        aria_issues = [i for i in report.get("issues") or [] if i.get("component") == "aria"]
        self.assertEqual(len(aria_issues), 1)
        self.assertTrue(aria_issues[0].get("auto_recoverable"))
        self.assertEqual(aria_issues[0].get("action"), "restart_aria")

    @patch("jarvis.application.standalone.workstation_impl.operations.up")
    @patch("jarvis.application.standalone.workstation_impl.operations.diagnose")
    def test_recover_no_issues(self, mock_diag, mock_up):
        mock_diag.return_value = {"ok": True, "issues": []}
        result = recover_safe()
        self.assertTrue(result.get("ok"))
        mock_up.assert_not_called()


if __name__ == "__main__":
    unittest.main()
