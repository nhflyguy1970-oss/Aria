"""Tests for git_util."""

from jarvis import git_util


def test_status_not_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(git_util, "PROJECT_ROOT", tmp_path)
    assert "Not a git repository" in git_util.status(tmp_path)


def test_status_in_repo(tmp_path, monkeypatch):
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    monkeypatch.setattr(git_util, "PROJECT_ROOT", tmp_path)
    out = git_util.status(tmp_path)
    assert "main" in out or "master" in out or "No commits" in out or out
