"""Cognitive execution mode — normal recall vs read-only diagnostics (B07).

NORMAL preserves biologically inspired update-on-retrieval.
READ_ONLY inspects cognition without living-memory mutation.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from enum import Enum
from typing import Iterator


class ExecutionMode(str, Enum):
    NORMAL = "normal"
    READ_ONLY = "read_only"


_MODE: ContextVar[ExecutionMode] = ContextVar(
    "acm_execution_mode", default=ExecutionMode.NORMAL
)


def current_execution_mode() -> ExecutionMode:
    return _MODE.get()


def is_read_only() -> bool:
    return _MODE.get() is ExecutionMode.READ_ONLY


@contextmanager
def execution_mode(mode: ExecutionMode) -> Iterator[ExecutionMode]:
    """Temporarily set the execution mode for the current context."""
    token = _MODE.set(mode)
    try:
        yield mode
    finally:
        _MODE.reset(token)


@contextmanager
def read_only() -> Iterator[ExecutionMode]:
    """Diagnostic context: reconstruct without store / buffer / adaptation writes."""
    with execution_mode(ExecutionMode.READ_ONLY) as mode:
        yield mode
