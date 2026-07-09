"""Tests for workstation inventory and install profiles."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from jarvis.workstation.inventory import (
    InventoryRecord,
    collect_inventory,
    verify_inventory,
)
from jarvis.workstation.optimize import apply_optimization
from jarvis.workstation.profiles import PROFILES, resolve_profile


class TestInstallProfiles(unittest.TestCase):
    def test_profiles_defined(self):
        for name in ("minimal", "developer", "full", "gpu", "headless"):
            self.assertIn(name, PROFILES)

    def test_resolve_profile(self):
        profile, rest = resolve_profile(["--minimal", "--skip-ollama"])
        self.assertEqual(profile.name, "minimal")
        self.assertEqual(rest, ["--skip-ollama"])


class TestInventory(unittest.TestCase):
    def test_collect_inventory_shape(self):
        with patch("jarvis.workstation.inventory._registry_records", return_value=[]):
            with patch(
                "jarvis.workstation.inventory._venv_record",
                return_value=InventoryRecord(
                    id="aria_venv",
                    label="venv",
                    category="development",
                    installed=True,
                    healthy=True,
                    running=True,
                ),
            ):
                inv = collect_inventory(persist=False)
        self.assertIn("items", inv)
        self.assertIn("summary", inv)
        self.assertTrue(inv["summary"]["ready"])

    def test_verify_flags_missing_venv(self):
        with patch(
            "jarvis.workstation.inventory.collect_inventory",
            return_value={
                "summary": {"ready": False},
                "items": [
                    {
                        "id": "aria_venv",
                        "label": "venv",
                        "installed": False,
                        "healthy": False,
                        "install_hint": "./workstation install",
                    }
                ],
            },
        ):
            result = verify_inventory()
        self.assertFalse(result["ready"])
        self.assertTrue(result["blockers"])


class TestOptimize(unittest.TestCase):
    def test_optimize_dry_run(self):
        with patch(
            "jarvis.workstation.optimize.collect_hardware",
            return_value={
                "ram_gb": 8,
                "recommended_placement": {"llm_inference": "nvidia", "image_generation": "amd"},
                "bottlenecks": [],
            },
        ):
            result = apply_optimization(dry_run=True)
        self.assertTrue(result.get("ok"))
        self.assertIn("JARVIS_GPU_PREFER", result.get("changes") or {})


if __name__ == "__main__":
    unittest.main()
