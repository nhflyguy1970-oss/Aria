import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestWorkflowOrchestrationAdapter(unittest.TestCase):
    def test_disabled_without_env(self):
        from jarvis.modules.workflow_orchestration_adapter import (
            workflow_enqueue,
            workflow_orchestration_enabled,
        )

        def legacy_submit(label: str) -> str:
            return "job-123"

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JARVIS_PLATFORM_WORKFLOW_ORCHESTRATION_ATTACHED", None)
            self.assertFalse(workflow_orchestration_enabled())
            job_id = workflow_enqueue("coding", "task", legacy_submit, "task")
            self.assertEqual(job_id, "job-123")

    def test_enqueue_records_metrics(self):
        from jarvis.modules.workflow_orchestration_adapter import workflow_enqueue

        def legacy_submit(label: str) -> str:
            return "job-456"

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(
                os.environ,
                {"JARVIS_PLATFORM_WORKFLOW_ORCHESTRATION_ATTACHED": "1"},
                clear=False,
            ),
            patch(
                "aiplatform.applications.workflow_orchestration.state.workflow_orchestration_state_dir",
                return_value=Path(tmp),
            ),
            patch("jarvis.modules.workflow_orchestration_adapter.sync_workflows", return_value=0),
            patch("jarvis.modules.workflow_orchestration_adapter._queue_depth", return_value=1),
        ):
            job_id = workflow_enqueue("background", "learn_about", legacy_submit, "learn")
            self.assertEqual(job_id, "job-456")
            from aiplatform.applications.workflow_orchestration.metrics import metrics_view

            state = metrics_view("aria")
            self.assertEqual(state.workflow_executions, 1)
            self.assertEqual(state.background_jobs, 1)


if __name__ == "__main__":
    unittest.main()
