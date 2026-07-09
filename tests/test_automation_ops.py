"""Tests for automation and prometheus metrics."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from jarvis.automation.ops import run_maintenance
from jarvis.observability.prometheus import collect_metrics, prometheus_text


class TestAutomationOps(unittest.TestCase):
    @patch("jarvis.knowledge.registry.sync_registry", return_value={"ok": True, "source_count": 3})
    @patch("jarvis.workstation.operations.diagnose", return_value={"ok": True, "critical": 0, "warnings": 0})
    def test_run_maintenance(self, _diag, _sync):
        result = run_maintenance(smoke_tests=False)
        self.assertTrue(result.get("ok"))
        self.assertGreaterEqual(len(result.get("results") or []), 2)


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
