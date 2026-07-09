"""Data behavior tests."""

from __future__ import annotations

import csv
from unittest.mock import MagicMock

import pytest

from jarvis.behaviors.data.engine import DataActionEngine
from jarvis.handlers.registry import call_action, has_action


@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "sales.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["region", "amount"])
        writer.writerow(["east", "10"])
        writer.writerow(["west", "20"])
    return str(path)


def test_data_actions_registered():
    from jarvis.behaviors import register_behaviors

    register_behaviors()
    assert has_action("data_load")
    assert has_action("data_summary")


def test_data_load_via_registry(sample_csv):
    from jarvis.behaviors import register_behaviors

    register_behaviors()
    assistant = MagicMock()
    assistant.data.load_dataset.return_value = "Loaded 2 rows."
    assistant.data.describe_stats.return_value = "2 rows, 2 columns"
    assistant.session = MagicMock()
    assistant.session.resolve_data.return_value = sample_csv
    result = call_action(assistant, "data_load", {"path": sample_csv}, "load data")
    assert result.get("ok") is True
    assert "sales.csv" in result.get("message", "")


def test_data_summary_requires_dataset():
    ctx = MagicMock()
    ctx.data.dataset = None
    ctx.session.last_data_path = ""
    result = DataActionEngine.data_summary(ctx, {}, "summarize")
    assert result.get("ok") is False
