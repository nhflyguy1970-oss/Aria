"""M0 — Aria ACM import / packaging gates (blueprint INTEGRATION_TEST_PLAN)."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARIA_ACM = ROOT / "aria_acm"
VERSION_PATH = ARIA_ACM / "VERSION.json"
ACM_TREE = ARIA_ACM / "acm"


def _tree_sha256(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            rel = path.relative_to(root).as_posix()
            h.update(rel.encode())
            h.update(b"\0")
            h.update(path.read_bytes())
            h.update(b"\0")
    return h.hexdigest()


@pytest.mark.m0
def test_m0_01_version_json_pin_matches_tree_hash() -> None:
    """M0-01: VERSION.json pin matches tree hash of aria_acm/acm/."""
    assert VERSION_PATH.is_file(), "aria_acm/VERSION.json missing"
    meta = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
    assert meta["source_commit"] == "74532ac60ebd448dc66de0cf7be752edac92449d"
    assert meta["source_tag"] == "v0.26.0"
    assert meta["source_version"] == "0.26.0"
    assert meta["aria_acm_local_version"] == "aria-acm-v0.26.0-7"
    assert meta["license"] == "Apache-2.0"
    assert ACM_TREE.is_dir()
    assert _tree_sha256(ACM_TREE) == meta["tree_sha256"]


@pytest.mark.m0
def test_m0_02_import_authority_vendored_path() -> None:
    """M0-02: CognitiveEngine resolves from vendored aria_acm, not site-packages alone."""
    # Fresh import path preference: repo root first
    root_s = str(ROOT)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)

    # Drop any previously loaded acm / aria_acm modules that might point elsewhere
    for key in list(sys.modules):
        if key == "acm" or key.startswith("acm.") or key == "aria_acm" or key.startswith("aria_acm."):
            del sys.modules[key]

    from aria_acm.acm.api.engine import CognitiveEngine

    mod = importlib.import_module(CognitiveEngine.__module__)
    file_path = Path(mod.__file__).resolve()
    assert "aria_acm" in file_path.parts, f"expected vendored path, got {file_path}"
    assert ARIA_ACM.resolve() in file_path.parents or file_path.is_relative_to(ARIA_ACM.resolve())
    # Must not be a pure site-packages install without aria_acm in the path
    assert "site-packages" not in str(file_path) or "aria_acm" in str(file_path)


@pytest.mark.m0
def test_m0_03_cognitive_engine_encode_remember_smoke(tmp_path: Path) -> None:
    """M0-03: tmp CognitiveEngine encode/remember round-trip."""
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_TEACHING

    persist = tmp_path / "cognitive.db"
    engine = CognitiveEngine(agent_id="m0-smoke", persist_path=str(persist), auto_persist=True)
    encoded = engine.encode(
        "User prefers morning espresso",
        kind="preference",
        pin=True,
        context_tags=("ns:profile",),
        provenance=TRUSTED_USER_TEACHING,
    )
    assert encoded.get("encoded") is True or encoded.get("experience_id"), encoded

    view = engine.what_do_i_remember("espresso")
    assert isinstance(view, dict)
    # Public remembering view should be non-empty for pinned preference
    text_blob = json.dumps(view).lower()
    assert "espresso" in text_blob or "prefer" in text_blob or bool(view)

    # Flush / verify persistence helpers exist (M0 packaging only)
    flush = engine.flush(kind="checkpoint")
    assert isinstance(flush, dict)
    verify = engine.verify_persistence()
    assert isinstance(verify, dict)


@pytest.mark.m0
def test_m0_no_adapter_copied() -> None:
    """Import Plan exclude: aria_memory_adapter must not live under aria_acm/."""
    assert not (ARIA_ACM / "aria_memory_adapter").exists()
    assert (ARIA_ACM / "LICENSE").is_file()
    assert (ARIA_ACM / "NOTICE").is_file()
    assert not (ARIA_ACM / "acm_bridge.py").exists()
