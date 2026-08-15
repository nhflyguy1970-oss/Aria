"""Coding propose must not fall through to chat for Jeff-speak."""

from __future__ import annotations

from jarvis.router import route
from jarvis.session import SessionContext


def _action(message: str) -> str:
    return str(route(message, SessionContext()).get("action") or "")


def test_propose_improvement_with_path_routes_coding():
    assert (
        _action(
            "In Coding, propose a one-line docstring improvement for "
            "jarvis/__init__.py without changing behavior."
        )
        == "coding_propose"
    )


def test_propose_improvement_alone_routes_coding():
    assert _action("propose an improvement to jarvis/fs.py") == "coding_propose"


def test_propose_docstring_not_stolen_by_gpu_filename():
    assert _action("can you propose a docstring for jarvis/gpu.py") == "coding_propose"


def test_propose_fix_still_routes():
    assert _action("propose a fix for jarvis/__init__.py") == "coding_propose"


def test_undo_last_coding_apply_routes():
    assert _action("Undo the last coding apply.") == "undo_apply"


def test_undo_that_still_routes():
    assert _action("undo that") == "undo_apply"
