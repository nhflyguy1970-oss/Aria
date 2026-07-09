"""Tests for workstation lifecycle phase."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.application.standalone.workstation_impl.phase import (
    WorkstationPhase,
    current_phase,
    is_transitional,
    set_phase,
)


class TestWorkstationPhase(unittest.TestCase):
    def test_transitional_phases(self):
        with patch(
            "jarvis.application.standalone.workstation_impl.phase._PHASE_FILE",
            Path(tempfile.mkdtemp()) / "phase.json",
        ):
            set_phase(WorkstationPhase.STARTING)
            self.assertTrue(is_transitional())
            set_phase(WorkstationPhase.READY)
            self.assertFalse(is_transitional())
            self.assertEqual(current_phase(), WorkstationPhase.READY)


if __name__ == "__main__":
    unittest.main()
