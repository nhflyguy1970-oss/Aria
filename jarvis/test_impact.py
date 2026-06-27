"""Predict which tests run after applying file changes."""

from __future__ import annotations

from pathlib import Path

from jarvis.coding_verify import _pytest_targets


def tests_for_files(py_files: list[Path], base: Path) -> list[str]:
    seen: set[str] = set()
    targets: list[str] = []
    for t in _pytest_targets(py_files, base):
        rel = str(t.relative_to(base)) if t.is_relative_to(base) else str(t)
        if rel not in seen and t.exists():
            seen.add(rel)
            targets.append(rel)
    return targets


def format_test_impact(py_files: list[Path], base: Path) -> str:
    targets = tests_for_files(py_files, base)
    if not targets:
        return ""
    lines = "\n".join(f"- `{t}`" for t in targets[:8])
    extra = f"\n… and {len(targets) - 8} more" if len(targets) > 8 else ""
    return f"**Tests that will run after apply:**\n{lines}{extra}"
