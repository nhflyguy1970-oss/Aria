"""P3 engineering / CAD / print tests."""

from __future__ import annotations

import struct
from pathlib import Path


def test_cad_status():
    from jarvis.engineering.cad_deps import cad_status

    st = cad_status()
    assert "openscad" in st
    assert "build123d" in st


def test_verify_ascii_stl(tmp_path):
    from jarvis.engineering.cad_verify import verify_stl

    stl = tmp_path / "cube.stl"
    stl.write_text(
        "solid test\n"
        "facet normal 0 0 1\n"
        "  outer loop\n"
        "    vertex 0 0 0\n"
        "    vertex 10 0 0\n"
        "    vertex 0 10 0\n"
        "  endloop\n"
        "endfacet\n"
        "endsolid test\n",
        encoding="utf-8",
    )
    v = verify_stl(stl)
    assert v["ok"] is True
    assert v["triangles"] == 1


def test_verify_binary_stl(tmp_path):
    from jarvis.engineering.cad_verify import verify_stl

    stl = tmp_path / "b.stl"
    header = b"x" * 80
    tri_count = 1
    tri = b"\x00" * 12 + struct.pack("<9f", 0, 0, 0, 10, 0, 0, 0, 10, 0) + b"\x00\x00"
    stl.write_bytes(header + struct.pack("<I", tri_count) + tri)
    v = verify_stl(stl)
    assert v["ok"] is True
    assert v["triangles"] == 1


def test_cad_router_pick():
    from jarvis.engineering.cad_router import pick_backend

    assert pick_backend("make a hose adapter bracket", prefer="auto") in ("openscad", "build123d", "meshy")


def test_cad_store_register(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.engineering.cad_store.ENGINEERING_DIR", tmp_path)
    monkeypatch.setattr("jarvis.engineering.cad_store.INDEX_FILE", tmp_path / "models.json")
    from jarvis.engineering.cad_store import list_models, register_model

    register_model(prompt="test cube", backend="openscad", stl_path=str(tmp_path / "a.stl"))
    assert len(list_models()) >= 1


def test_openscad_render(tmp_path):
    import shutil

    if not shutil.which("openscad"):
        return
    from jarvis.engineering.openscad_runner import render_scad

    scad = tmp_path / "cube.scad"
    stl = tmp_path / "cube.stl"
    scad.write_text("cube(10);\n", encoding="utf-8")
    r = render_scad(scad, stl)
    assert r.get("ok") is True
    assert stl.is_file()


def test_p3_flags():
    from jarvis.p3_flags import p3_flags

    flags = p3_flags()
    assert "cad" in flags
    assert "printer" in flags
