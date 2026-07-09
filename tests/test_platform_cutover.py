"""Tests for platform migration cutover."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.platform_cutover import (
    current_mode,
    rollback_to_legacy,
    status,
    verify_readiness,
)


class TestPlatformCutover(unittest.TestCase):
    def test_default_mode_dual_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            cutover_file = Path(tmp) / "cutover.json"
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                self.assertEqual(current_mode(), "dual_write")

    def test_rollback_restores_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            cutover_file = Path(tmp) / "cutover.json"
            legacy = Path(tmp) / "legacy"
            legacy.mkdir()
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                with patch.dict("os.environ", {"JARVIS_LEGACY_DATA_DIR": str(legacy)}, clear=False):
                    result = rollback_to_legacy()
                    self.assertTrue(result.get("ok"))
                    self.assertEqual(current_mode(), "dual_write")

    def test_status_shape(self):
        snap = status()
        self.assertIn("mode", snap)
        self.assertIn("verification", snap)

    def test_verify_readiness_has_ready_flag(self):
        with patch.dict("os.environ", {"JARVIS_PLATFORM_ATTACHED": "1"}, clear=False):
            result = verify_readiness()
            self.assertIn("ready", result)


if __name__ == "__main__":
    unittest.main()
