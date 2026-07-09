import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestAutomationEventAdapter(unittest.TestCase):
    def test_disabled_without_env(self):
        from jarvis.modules.automation_event_adapter import (
            automation_planner_call,
            automation_event_enabled,
        )

        def legacy_call(duration: str, label: str | None = None) -> dict:
            return {"id": "t1"}

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JARVIS_PLATFORM_AUTOMATION_EVENT_ATTACHED", None)
            self.assertFalse(automation_event_enabled())
            result = automation_planner_call("timer", legacy_call, "5m", "tea")
            self.assertEqual(result["id"], "t1")

    def test_planner_records_metrics(self):
        from jarvis.modules.automation_event_adapter import automation_planner_call

        def legacy_call(duration: str, label: str | None = None) -> dict:
            return {"id": "t2"}

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(
                os.environ,
                {"JARVIS_PLATFORM_AUTOMATION_EVENT_ATTACHED": "1"},
                clear=False,
            ),
            patch(
                "aiplatform.applications.automation_event.state.automation_event_state_dir",
                return_value=Path(tmp),
            ),
            patch("jarvis.modules.automation_event_adapter.sync_automations", return_value=6),
            patch(
                "aiplatform.applications.automation_event.bridge.shadow_verify_trigger",
            ),
        ):
            automation_planner_call("timer", legacy_call, "10m")
            from aiplatform.applications.automation_event.metrics import metrics_view

            state = metrics_view("aria")
            self.assertEqual(state.planner_events, 1)
            self.assertEqual(state.trigger_executions, 1)


if __name__ == "__main__":
    unittest.main()
