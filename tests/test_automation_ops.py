"""Tests for automation and prometheus metrics."""

from __future__ import annotations

import os
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from jarvis.assistant_instance import clear_assistant
from jarvis.automation.ops import run_maintenance
from jarvis.observability.prometheus import collect_metrics, prometheus_text

_MAINTENANCE_ENV = {
    "JARVIS_MAINTENANCE_SMOKE_TESTS": "0",
    "JARVIS_AUTO_INGEST": "0",
}

_STEP_PATCHES = {
    "jarvis.automation.ops._step_knowledge_sync": {
        "job": "knowledge_sync",
        "ok": True,
        "detail": 3,
    },
    "jarvis.automation.ops._step_git_sync": {
        "job": "git_sync",
        "ok": True,
        "repos": 0,
    },
    "jarvis.automation.ops._step_memory_consolidate": {
        "job": "memory_consolidate",
        "ok": True,
        "promoted": 0,
    },
    "jarvis.automation.ops._step_workstation": [
        {
            "job": "workstation_diagnose",
            "ok": True,
            "critical": 0,
            "warnings": 0,
        }
    ],
}


def _failed_jobs(results: list[dict]) -> list[dict]:
    return [entry for entry in results if entry.get("ok") is not True]


class TestAutomationOps(unittest.TestCase):
    def setUp(self) -> None:
        clear_assistant()
        self._stack = ExitStack()
        self.addCleanup(self._stack.close)
        self._stack.enter_context(patch.dict(os.environ, _MAINTENANCE_ENV, clear=False))
        self._stack.enter_context(patch("jarvis.automation.ops._persist_run"))
        for target, payload in _STEP_PATCHES.items():
            self._stack.enter_context(patch(target, return_value=payload))
        self._stack.enter_context(
            patch("jarvis.automation.ops._step_knowledge_ingest", return_value=None)
        )

    def test_run_maintenance(self) -> None:
        result = run_maintenance(smoke_tests=False)
        self.assertTrue(
            result.get("ok"),
            f"unexpected maintenance failures: {_failed_jobs(result.get('results') or [])}",
        )
        self.assertGreaterEqual(len(result.get("results") or []), 2)
        jobs = {entry["job"] for entry in result.get("results") or []}
        self.assertIn("knowledge_sync", jobs)
        self.assertIn("workstation_diagnose", jobs)
        self.assertNotIn("smoke_tests", jobs)

    def test_run_maintenance_honors_smoke_env_only_when_enabled(self) -> None:
        with patch.dict(os.environ, {"JARVIS_MAINTENANCE_SMOKE_TESTS": "1"}, clear=False):
            with patch(
                "jarvis.automation.ops._run_smoke_tests",
                return_value={"job": "smoke_tests", "ok": True, "returncode": 0},
            ) as smoke:
                result = run_maintenance(smoke_tests=False)
        self.assertTrue(result.get("ok"))
        smoke.assert_called_once()
        jobs = {entry["job"] for entry in result.get("results") or []}
        self.assertIn("smoke_tests", jobs)

    def test_run_maintenance_propagates_step_failure(self) -> None:
        with patch(
            "jarvis.automation.ops._step_git_sync",
            return_value={"job": "git_sync", "ok": False, "repos": 0},
        ):
            result = run_maintenance(smoke_tests=False)
        self.assertFalse(result.get("ok"))
        self.assertEqual(
            _failed_jobs(result.get("results") or []),
            [{"job": "git_sync", "ok": False, "repos": 0}],
        )


class TestPrometheusMetrics(unittest.TestCase):
    def test_prometheus_text_format(self):
        text = prometheus_text()
        self.assertIn("jarvis_uptime_seconds", text)
        self.assertIn("# TYPE", text)

    def test_collect_metrics_numeric(self):
        metrics = collect_metrics()
        for value in metrics.values():
            self.assertIsInstance(value, float)


if __name__ == "__main__":
    unittest.main()
