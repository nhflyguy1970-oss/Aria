"""Centralized logging setup for ARIA."""

from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_DIR = PROJECT_ROOT / "data" / "logs"

_request_id: ContextVar[str] = ContextVar("request_id", default="")
_CONFIGURED = False

# Keep chat/API logs readable; bump via JARVIS_LOG_LEVEL=DEBUG when needed.
_QUIET_LOGGERS = ("httpcore", "httpx", "urllib3", "uvicorn.access", "onnxruntime")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get() or "-"  # type: ignore[attr-defined]
        return True


def set_request_id(request_id: str) -> None:
    _request_id.set((request_id or "").strip())


def clear_request_id() -> None:
    _request_id.set("")


def get_request_id() -> str:
    return _request_id.get() or ""


def log_dir() -> Path:
    return Path(os.getenv("JARVIS_LOG_DIR", str(DEFAULT_LOG_DIR)))


def log_file_path() -> Path:
    explicit = os.getenv("JARVIS_LOG_FILE", "").strip()
    if explicit:
        return Path(explicit)
    return log_dir() / "jarvis.log"


def rotate_log_file(path: Path, *, max_bytes: int | None = None, backup_count: int | None = None) -> None:
    max_bytes = max_bytes if max_bytes is not None else int(os.getenv("JARVIS_LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    backup_count = backup_count if backup_count is not None else int(os.getenv("JARVIS_LOG_BACKUP_COUNT", "3"))
    if max_bytes <= 0 or backup_count <= 0 or not path.is_file():
        return
    try:
        if path.stat().st_size < max_bytes:
            return
    except OSError:
        return
    for i in range(backup_count - 1, 0, -1):
        src = path.with_name(f"{path.name}.{i}")
        dst = path.with_name(f"{path.name}.{i + 1}")
        if src.exists():
            try:
                src.replace(dst)
            except OSError:
                pass
    try:
        path.replace(path.with_name(f"{path.name}.1"))
    except OSError:
        pass


def open_rotating_log(path: Path):
    """Open an append log for subprocess output after size-based rotation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rotate_log_file(path)
    return open(path, "a", encoding="utf-8")


def setup_logging(*, force: bool = False) -> None:
    """Configure root logging once per process (file + stderr, with rotation)."""
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    level_name = os.getenv("JARVIS_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    log_path = log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = "%(asctime)s %(levelname)s [%(name)s] [%(request_id)s] %(message)s"
    formatter = logging.Formatter(fmt)
    req_filter = RequestIdFilter()

    root = logging.getLogger()
    root.setLevel(level)

    if force:
        for handler in list(root.handlers):
            root.removeHandler(handler)

    log_file = str(log_path.resolve())
    has_file = any(
        isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == log_file
        for h in root.handlers
    )
    if not has_file:
        fh = RotatingFileHandler(
            log_file,
            maxBytes=int(os.getenv("JARVIS_LOG_MAX_BYTES", str(5 * 1024 * 1024))),
            backupCount=int(os.getenv("JARVIS_LOG_BACKUP_COUNT", "3")),
            encoding="utf-8",
        )
        fh.setFormatter(formatter)
        fh.addFilter(req_filter)
        root.addHandler(fh)

    has_stderr = any(
        isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stderr
        for h in root.handlers
    )
    if not has_stderr:
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(level)
        sh.setFormatter(formatter)
        sh.addFilter(req_filter)
        root.addHandler(sh)

    quiet_level = logging.WARNING if level <= logging.INFO else level
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(quiet_level)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, ensuring setup ran at least once."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)
