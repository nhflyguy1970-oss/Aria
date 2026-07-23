"""Aria dual-import identity — acm.* and aria_acm.acm.* must share classes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = ROOT / "aria_acm" / "VERSION.json"


def test_aria_acm_pin_is_045() -> None:
    data = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
    assert data["source_version"] == "0.45.1"
    assert data["aria_acm_local_version"] == "aria-acm-v0.45.1-1"


def test_dual_import_class_identity() -> None:
    """Regression: ConversationDebugPolicy/CognitiveEngine must be identical objects."""
    from aria_acm.acm.api.engine import CognitiveEngine as CE_A
    from aria_acm.acm.authority.debug_capture import ConversationDebugPolicy as P_A
    from acm.api.engine import CognitiveEngine as CE_B
    from acm.authority.debug_capture import ConversationDebugPolicy as P_B

    assert CE_A is CE_B
    assert P_A is P_B
