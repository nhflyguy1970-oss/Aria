"""Unified-diff helpers for proposal / coding UI."""

from __future__ import annotations

import difflib


def make_diff(original: str = "", updated: str = "") -> str:
    lines = difflib.unified_diff(
        (original or "").splitlines(),
        (updated or "").splitlines(),
        fromfile="original",
        tofile="proposed",
        lineterm="",
    )
    return "\n".join(lines)


def show_diff(original: str = "", updated: str = "") -> None:
    diff = difflib.unified_diff(
        (original or "").splitlines(),
        (updated or "").splitlines(),
        fromfile="original",
        tofile="proposed",
        lineterm="",
    )
    print("\n--- DIFF ---\n")
    for line in diff:
        print(line)
    print()
