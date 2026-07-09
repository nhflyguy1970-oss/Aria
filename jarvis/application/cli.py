"""Standalone Aria CLI — install, start, stop, doctor, acceptance."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """Aria application lifecycle (standalone mode)."""
    from jarvis.application.standalone.workstation_impl.cli import main as standalone_main

    return standalone_main(argv)


if __name__ == "__main__":
    sys.exit(main())
