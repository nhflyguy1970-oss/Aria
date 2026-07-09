"""Tests for tool runner."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.tools.runner import ToolRun, build_command, list_runs, run_status, save_run


class TestToolRunner(unittest.TestCase):
    def test_build_command_claude(self):
        with patch("shutil.which", return_value="/usr/bin/claude"):
            built = build_command("claude_code", {"task": "fix tests"})
        self.assertIsNotNone(built)
        args, _cwd = built  # type: ignore[misc]
        self.assertIn("claude", args[0])
        self.assertIn("fix tests", args)

    def test_save_and_list_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp)
            with patch("jarvis.tools.runner.RUNS_DIR", runs_dir):
                run = ToolRun(id="run1", tool_id="claude_code", task="hello")
                save_run(run)
                runs = list_runs()
                self.assertEqual(len(runs), 1)

    def test_run_status_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("jarvis.tools.runner.RUNS_DIR", Path(tmp)):
                result = run_status("missing")
                self.assertFalse(result.get("ok"))


if __name__ == "__main__":
    unittest.main()
