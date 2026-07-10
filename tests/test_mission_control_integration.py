"""Live Mission Control integration — requires sibling AI-Platform install."""

from __future__ import annotations

import importlib.util
import os

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("aiplatform") is None,
    reason="aiplatform not installed (run scripts/ci-local.sh for full integration)",
)


def test_collect_mission_control_live():
    from jarvis.mission_control import collect_mission_control

    data = collect_mission_control(record_metrics=False)
    assert data.get("ok") is True
    assert data.get("owner") == "aiplatform"


def test_collect_dashboard_live():
    from jarvis.runtime_introspection import collect_dashboard

    if os.getenv("MISSION_CONTROL_SKIP_LIVE") == "1":
        pytest.skip("live MC skipped")
    data = collect_dashboard()
    assert data.get("ok") is True
    assert "overview" in data
