"""Live certification: confinement inside a root is useless if the root can be
the system. Any existing directory was accepted as a coding workspace — /etc,
the home directory, a non-repo with no way to undo anything.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from jarvis.dev_agent import workspace


def _repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    return path


def test_system_directories_are_refused(tmp_path):
    for bad in ("/etc", "/", "/usr", "/var"):
        if not Path(bad).is_dir():
            continue
        with pytest.raises(workspace.WorkspaceError, match="system directory"):
            workspace.open_workspace(bad)


def test_the_home_directory_itself_is_refused(tmp_path):
    with pytest.raises(workspace.WorkspaceError, match="too broad"):
        workspace.open_workspace(str(Path.home()))


def test_a_non_repository_is_refused_because_nothing_could_be_undone(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(workspace.WorkspaceError, match="not a git repository"):
        workspace.open_workspace(str(plain))


def test_a_real_project_repository_is_accepted(tmp_path):
    ws = workspace.open_workspace(str(_repo(tmp_path / "project")))
    assert ws.root == (tmp_path / "project").resolve()


def test_an_allowlist_narrows_it_further(tmp_path, monkeypatch):
    inside = _repo(tmp_path / "allowed" / "project")
    outside = _repo(tmp_path / "elsewhere" / "project")
    monkeypatch.setenv(workspace.ALLOWED_ROOTS_ENV, str(tmp_path / "allowed"))

    assert workspace.open_workspace(str(inside)).root == inside.resolve()
    with pytest.raises(workspace.WorkspaceError, match=workspace.ALLOWED_ROOTS_ENV):
        workspace.open_workspace(str(outside))


def test_multiple_allowed_roots_are_honoured(tmp_path, monkeypatch):
    a = _repo(tmp_path / "a" / "proj")
    b = _repo(tmp_path / "b" / "proj")
    monkeypatch.setenv(
        workspace.ALLOWED_ROOTS_ENV, os.pathsep.join([str(tmp_path / "a"), str(tmp_path / "b")])
    )
    assert workspace.open_workspace(str(a))
    assert workspace.open_workspace(str(b))


def test_path_confinement_inside_the_root_still_applies(tmp_path):
    ws = workspace.open_workspace(str(_repo(tmp_path / "project")))
    with pytest.raises(workspace.PathEscape):
        ws.resolve("../outside.txt")
    with pytest.raises(workspace.PathEscape):
        ws.resolve("/etc/passwd")


def test_the_interpreter_is_not_a_way_around_the_command_policy(tmp_path):
    """`python -c` runs arbitrary code, and `python -m pip install` walks past
    the pip ban — the allowlist denied the binaries but handed over the
    interpreter that can call them."""
    from jarvis.dev_agent import commands

    for argv in (
        ["python", "-c", "import os; os.system('rm -rf /')"],
        ["python3", "-c", "print(1)"],
        ["python", "-m", "pip", "install", "requests"],
        ["python3", "-m", "http.server"],
        ["python", "-i"],
        ["python"],
    ):
        with pytest.raises(commands.CommandDenied):
            commands.classify(argv)


def test_legitimate_python_use_still_works(tmp_path):
    from jarvis.dev_agent import commands

    assert commands.classify(["python", "-m", "pytest", "-q"]) == commands.DEVELOPMENT
    assert commands.classify(["python", "-m", "unittest"]) == commands.DEVELOPMENT
    assert commands.classify(["python", "scripts/build.py"]) == commands.DEVELOPMENT
    assert commands.classify(["pytest", "-q"]) == commands.DEVELOPMENT
