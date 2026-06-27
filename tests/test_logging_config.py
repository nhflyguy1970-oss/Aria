"""Tests for centralized logging setup."""

from __future__ import annotations

import logging

import pytest


@pytest.fixture(autouse=True)
def _isolate_logging(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("JARVIS_LOG_LEVEL", "DEBUG")
    import jarvis.logging_config as lc

    monkeypatch.setattr(lc, "_CONFIGURED", False)
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)


def test_setup_logging_writes_to_data_logs(tmp_path, monkeypatch):
    import jarvis.logging_config as lc

    log_dir = tmp_path / "logs"
    monkeypatch.setenv("JARVIS_LOG_DIR", str(log_dir))
    lc.setup_logging(force=True)

    log = logging.getLogger("jarvis.test")
    log.info("hello from test")

    log_file = log_dir / "jarvis.log"
    assert log_file.is_file()
    assert "hello from test" in log_file.read_text(encoding="utf-8")


def test_setup_logging_idempotent(tmp_path, monkeypatch):
    import jarvis.logging_config as lc

    lc.setup_logging(force=True)
    count = len(logging.getLogger().handlers)
    lc.setup_logging()
    assert len(logging.getLogger().handlers) == count


def test_request_id_in_log_record(tmp_path, monkeypatch):
    import jarvis.logging_config as lc

    lc.setup_logging(force=True)
    lc.set_request_id("req-abc")
    record = logging.LogRecord(
        name="jarvis.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="with id",
        args=(),
        exc_info=None,
    )
    filt = lc.RequestIdFilter()
    assert filt.filter(record) is True
    assert record.request_id == "req-abc"  # type: ignore[attr-defined]
    lc.clear_request_id()
