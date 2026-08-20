"""Every shipped script must parse.

A stray brace left by an edit made view_router.js fail to parse, which broke
navigation across the whole authenticated UI — the page still loaded, so only
driving it revealed the damage.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

STATIC = Path("jarvis/gui/static")


def _scripts() -> list[Path]:
    return sorted(STATIC.rglob("*.js"))


def test_there_are_scripts_to_check():
    assert len(_scripts()) > 100


@pytest.mark.skipif(
    subprocess.run(["which", "node"], capture_output=True).returncode != 0,
    reason="node is not available to parse the scripts",
)
def test_every_static_script_parses():
    broken = []
    for path in _scripts():
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode != 0:
            first = (result.stderr or "").strip().splitlines()
            broken.append(f"{path.name}: {first[0] if first else 'parse error'}")
    assert not broken, "scripts that do not parse: " + "; ".join(broken)
