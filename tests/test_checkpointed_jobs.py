"""Tests for checkpointed jobs."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.jobs.checkpointed import CheckpointedJob, job_status, list_jobs, save_job


class TestCheckpointedJobs(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "jobs"
            with patch("jarvis.jobs.checkpointed.JOBS_DIR", jobs_dir):
                job = CheckpointedJob(id="abc123", kind="agent_chain", goal="test goal")
                save_job(job)
                loaded = list_jobs()
                self.assertEqual(len(loaded), 1)
                self.assertEqual(loaded[0].goal, "test goal")

    def test_job_status_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("jarvis.jobs.checkpointed.JOBS_DIR", Path(tmp)):
                result = job_status("missing")
                self.assertFalse(result.get("ok"))


if __name__ == "__main__":
    unittest.main()
