"""Tests for workstation acceptance scoring."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.workstation.acceptance import (
    AcceptanceItem,
    AcceptanceStatus,
    _classify,
    format_acceptance_markdown,
    run_acceptance,
)


def _item(**kwargs) -> AcceptanceItem:
    defaults = dict(
        id="test",
        label="Test",
        category="test",
        status="",
        installed=True,
        configured=True,
        running=True,
        healthy=True,
        verified=True,
        used_by_aria=True,
        integration_ok=True,
    )
    defaults.update(kwargs)
    return AcceptanceItem(**defaults)


def test_classify_ready():
    assert _classify(_item()) == AcceptanceStatus.READY.value


def test_classify_not_installed():
    assert _classify(_item(installed=False, healthy=False)) == AcceptanceStatus.NOT_INSTALLED.value


def test_classify_needs_config_when_unverified():
    assert (
        _classify(_item(integration_ok=False, used_by_aria=True))
        == AcceptanceStatus.NEEDS_CONFIGURATION.value
    )


@patch("jarvis.workstation.acceptance._CATALOG", [])
def test_run_acceptance_empty_catalog():
    report = run_acceptance(persist=False)
    assert report["score"]["overall"] == 100.0
    assert report["items"] == []


@patch("jarvis.workstation.integration_probes.run_probe")
@patch("jarvis.workstation.acceptance._probe_aria_api")
@patch("jarvis.workstation.acceptance._probe_registry")
def test_run_acceptance_marks_aria_ready(mock_registry, mock_aria, mock_run_probe):
    mock_run_probe.return_value = {"ok": True, "detail": "ok"}
    mock_registry.return_value = {
        "installed": True,
        "running": True,
        "healthy": True,
        "configured": True,
        "verified": True,
        "version": "0.31",
    }
    mock_aria.return_value = {
        "installed": True,
        "running": True,
        "healthy": True,
        "configured": True,
        "verified": True,
        "version": "127.0.0.1:8765",
    }
    tiny_catalog = [
        ("ollama", "Ollama", "ai_runtime", True, True, True, [], lambda: mock_registry.return_value),
        ("aria", "Aria", "interfaces", True, True, True, [], mock_aria),
    ]
    with patch("jarvis.workstation.acceptance._CATALOG", tiny_catalog):
        report = run_acceptance(persist=False)
    assert report["summary"]["ready"] == 2
    assert "Workstation Acceptance Report" in format_acceptance_markdown(report)
