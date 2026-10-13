"""Tests for workstation lifecycle phase."""

from __future__ import annotations

import os
import subprocess
import sys
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
from jarvis.config import PROJECT_ROOT


def _resolve_phase_file(*, data_dir: str | None) -> Path:
    """Resolve _PHASE_FILE in a fresh interpreter under a given JARVIS_DATA_DIR.

    A subprocess is used deliberately: _PHASE_FILE is bound at import time, so
    resolution can only be observed on a clean import, and reloading the module
    in-process would leak the changed path into the rest of the session.
    """
    env = dict(os.environ)
    if data_dir is None:
        env.pop("JARVIS_DATA_DIR", None)
    else:
        env["JARVIS_DATA_DIR"] = data_dir
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from jarvis.application.standalone.workstation_impl.phase import _PHASE_FILE;"
            "print(_PHASE_FILE)",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    return Path(result.stdout.strip())


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


class TestWorkstationPhaseStorageLocation(unittest.TestCase):
    """workstation_phase.json must follow JARVIS_DATA_DIR, not the repo root."""

    def test_isolated_data_dir_confines_phase_file(self):
        with tempfile.TemporaryDirectory() as scratch:
            resolved = _resolve_phase_file(data_dir=scratch)
            self.assertEqual(
                resolved,
                Path(scratch) / "automation" / "workstation_phase.json",
            )
            self.assertIn(Path(scratch), resolved.parents)
            self.assertNotIn(PROJECT_ROOT / "data", resolved.parents)

    def test_production_default_location_is_unchanged(self):
        resolved = _resolve_phase_file(data_dir=None)
        self.assertEqual(
            resolved,
            PROJECT_ROOT / "data" / "automation" / "workstation_phase.json",
        )

    def test_explicit_production_data_dir_resolves_to_same_path(self):
        """systemd sets JARVIS_DATA_DIR=<repo>/data; that must not shift the path."""
        production = str(PROJECT_ROOT / "data")
        self.assertEqual(
            _resolve_phase_file(data_dir=production),
            _resolve_phase_file(data_dir=None),
        )


if __name__ == "__main__":
    unittest.main()
