"""aria_coder helper coverage."""

from __future__ import annotations

from jarvis.aria_coder import normalize_self_fix_task, write_file_bridge


def test_normalize_self_fix_task():
    out = normalize_self_fix_task("fix aria and apply: tighten router")
    assert isinstance(out, str)


def test_write_file_bridge(tmp_path):
    out = write_file_bridge("new.py", "x = 1\n", tmp_path, backup=False)
    assert out["ok"] is True
    assert (tmp_path / "new.py").read_text(encoding="utf-8") == "x = 1\n"


def test_smoke_targets_include_coding_suite():
    from jarvis.aria_coder import SMOKE_TEST_TARGETS

    joined = " ".join(SMOKE_TEST_TARGETS)
    assert "test_coding.py" in joined
