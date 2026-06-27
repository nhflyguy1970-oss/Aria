"""Tests for Memgraph Docker autostart."""

from unittest.mock import patch

from jarvis.memgraph_docker import (
    ensure_memgraph,
    memgraph_bolt_healthy,
    should_autostart_memgraph,
)


def test_should_autostart_default_off(monkeypatch):
    monkeypatch.delenv("JARVIS_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("JARVIS_MEMGRAPH_AUTOSTART", raising=False)
    monkeypatch.setattr("jarvis.memgraph_docker.shutil.which", lambda _: "/usr/bin/docker")
    assert should_autostart_memgraph() is False


def test_should_autostart_on_when_graph_backend_memgraph(monkeypatch):
    monkeypatch.setenv("JARVIS_GRAPH_BACKEND", "memgraph")
    monkeypatch.delenv("JARVIS_MEMGRAPH_AUTOSTART", raising=False)
    monkeypatch.setattr("jarvis.memgraph_docker.docker_available", lambda: True)
    assert should_autostart_memgraph() is True


def test_should_autostart_respects_explicit_off(monkeypatch):
    monkeypatch.setenv("JARVIS_GRAPH_BACKEND", "memgraph")
    monkeypatch.setenv("JARVIS_MEMGRAPH_AUTOSTART", "0")
    monkeypatch.setattr("jarvis.memgraph_docker.docker_available", lambda: True)
    assert should_autostart_memgraph() is False


def test_ensure_skips_when_autostart_off(monkeypatch):
    monkeypatch.setenv("JARVIS_MEMGRAPH_AUTOSTART", "0")
    with patch("jarvis.memgraph_docker.memgraph_bolt_healthy", return_value=False), patch(
        "jarvis.memgraph_docker.container_running", return_value=False
    ), patch("jarvis.memgraph_docker.subprocess.run") as run:
        assert ensure_memgraph() is False
        run.assert_not_called()


def test_ensure_starts_existing_container(monkeypatch):
    monkeypatch.setenv("JARVIS_GRAPH_BACKEND", "memgraph")
    monkeypatch.delenv("JARVIS_MEMGRAPH_AUTOSTART", raising=False)
    with patch("jarvis.memgraph_docker.should_autostart_memgraph", return_value=True), patch(
        "jarvis.memgraph_docker.memgraph_bolt_healthy", return_value=False
    ), patch("jarvis.memgraph_docker.container_running", return_value=False), patch(
        "jarvis.memgraph_docker.container_exists", return_value=True
    ), patch(
        "jarvis.memgraph_docker.subprocess.run"
    ) as run:
        assert ensure_memgraph() is True
        run.assert_called_once()
        assert run.call_args.args[0][:2] == ["docker", "start"]


def test_ensure_creates_container_with_restart_policy(monkeypatch):
    monkeypatch.setenv("JARVIS_GRAPH_BACKEND", "memgraph")
    with patch("jarvis.memgraph_docker.should_autostart_memgraph", return_value=True), patch(
        "jarvis.memgraph_docker.memgraph_bolt_healthy", return_value=False
    ), patch("jarvis.memgraph_docker.container_running", return_value=False), patch(
        "jarvis.memgraph_docker.container_exists", return_value=False
    ), patch(
        "jarvis.memgraph_docker.subprocess.run"
    ) as run:
        assert ensure_memgraph() is True
        args = run.call_args.args[0]
        assert args[:2] == ["docker", "run"]
        assert "--restart=unless-stopped" in args


def test_memgraph_bolt_healthy_socket(monkeypatch):
    class FakeSock:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch("jarvis.memgraph_docker.socket.create_connection", return_value=FakeSock()):
        assert memgraph_bolt_healthy() is True
