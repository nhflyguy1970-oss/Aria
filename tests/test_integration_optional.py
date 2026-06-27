"""Optional integration tests — skip when Playwright, OpenSCAD, or CAD stack missing."""

from __future__ import annotations

import shutil

import pytest


def test_openscad_integration_if_installed(tmp_path):
    if not shutil.which("openscad"):
        pytest.skip("OpenSCAD not installed")
    from jarvis.engineering.openscad_runner import render_scad

    scad = tmp_path / "t.scad"
    stl = tmp_path / "t.stl"
    scad.write_text("cube(5);\n", encoding="utf-8")
    r = render_scad(scad, stl)
    assert r.get("ok") is True
    assert stl.is_file()


def test_playwright_browser_if_installed():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        pytest.skip("playwright not installed")
    from jarvis.p2_flags import browser_agent_enabled

    if not browser_agent_enabled():
        pytest.skip("JARVIS_BROWSER_AGENT=0")


def test_cad_teaching_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "jarvis.engineering.cad_teaching.PATTERNS_FILE",
        tmp_path / "cad_patterns.json",
    )
    from jarvis.engineering.cad_teaching import list_patterns, parse_teach_cad, record_pattern

    p = parse_teach_cad("teach cad: hose adapters use 25.4mm threads")
    assert p and "25.4" in p["text"]
    record_pattern(p["text"], kind=p["kind"])
    assert len(list_patterns()) == 1


def test_stl_dimensions_ascii(tmp_path):
    from jarvis.engineering.cad_verify import stl_dimensions

    stl = tmp_path / "cube.stl"
    stl.write_text(
        "solid t\nfacet normal 0 0 1\n outer loop\n"
        "  vertex 0 0 0\n  vertex 10 0 0\n  vertex 0 10 0\n"
        " endloop\nendfacet\nendsolid t\n",
        encoding="utf-8",
    )
    d = stl_dimensions(stl)
    assert d["ok"] is True
    assert d["dimensions_mm"]["x"] == 10.0
