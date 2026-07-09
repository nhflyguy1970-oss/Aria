import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestCapabilityAdapter(unittest.TestCase):
    def test_disabled_without_env(self):
        from jarvis.modules.capability_adapter import (
            capability_invoke,
            tool_capability_enabled,
        )

        def legacy_call(assistant, action, params, message):
            return {"ok": True, "action": action}

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED", None)
            self.assertFalse(tool_capability_enabled())
            result = capability_invoke(
                legacy_call,
                MagicMock(),
                "test_action",
                {},
                "hello",
            )
            self.assertEqual(result["action"], "test_action")

    def test_invoke_records_metrics(self):
        from jarvis.modules.capability_adapter import capability_invoke

        def legacy_call(assistant, action, params, message):
            return {"ok": True}

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED": "1"}, clear=False),
            patch(
                "aiplatform.applications.tool_capability.state.tool_capability_state_dir",
                return_value=Path(tmp),
            ),
            patch("jarvis.modules.capability_adapter.sync_capabilities", return_value=0),
            patch("jarvis.handlers.registry.get_spec", return_value=None),
        ):
            result = capability_invoke(
                legacy_call,
                MagicMock(),
                "git_status",
                {},
                "status",
            )
            self.assertTrue(result["ok"])
            from aiplatform.applications.tool_capability.metrics import metrics_view

            state = metrics_view("aria")
            self.assertEqual(state.invocation_count, 1)


if __name__ == "__main__":
    unittest.main()
