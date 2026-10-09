"""Supervision uses real installed Codex command/exec without model requests."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_phase5_coding_agents import _register, agents, repo  # noqa: F401

from jarvis.coding_agents import contract, discovery, oci, runs, runtime

# Shared fixtures are intentionally also the test parameter names.
# ruff: noqa: F811


@pytest.fixture
def native(agents, monkeypatch, tmp_path):
    binary = Path.home() / ".nvm/versions/node/v24.15.0/bin/codex"
    if not shutil.which("docker") or not binary.exists():
        pytest.skip("deployment-critical native OCI prerequisite absent")
    image = oci.image_id("ollama/ollama:latest")
    execution = {"state": "verified", "backend": "oci", "image": image}
    monkeypatch.setattr(runtime, "compatibility", lambda *a: execution)
    discovery.set_discovery_for_tests(
        {
            "codex": discovery.AgentStatus(
                agent="codex",
                label="Codex",
                installed=True,
                path=str(binary),
                version="codex-cli 0.161.0",
                auth={"state": "logged_in", "billing": "chatgpt_subscription", "paid_api": False},
                modes=["workspace_write", "read_only"],
                execution=execution,
            )
        }
    )
    state = tmp_path / "native-state"
    state.mkdir()
    real_create = oci.create

    def fixture_create(**kw):
        request = dict(kw["request"])
        request["command"] = [
            "/bin/sh",
            "-c",
            "echo ready > ready.txt; setsid sleep 120 & sleep 120",
        ]
        kw["request"] = request
        kw["bindings"] = [(str(state), str(Path.home() / ".codex"))]
        return real_create(**kw)

    monkeypatch.setattr(oci, "create", fixture_create)


def test_supervisor_cancels_real_native_tree_and_keeps_receipt(native, repo):
    proj = _register(repo)
    plan = runs.create_plan(
        agent="codex", project=proj["slug"], mode="workspace_write", task="fixture command"
    )
    run = runs.start(
        plan["id"], token=runs.approval_token(plan["id"]), via="isolated test", background=True
    )
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        current = runs.get_run(run["id"])
        if current.get("workspace") and Path(current["workspace"], "ready.txt").exists():
            break
        time.sleep(0.1)
    else:
        pytest.fail(str(current))
    cid = current["receipt"]["container_id"]
    runs.cancel(run["id"])
    deadline = time.monotonic() + 10
    while (
        time.monotonic() < deadline and runs.get_run(run["id"])["status"] not in contract.TERMINAL
    ):
        time.sleep(0.1)
    final = runs.get_run(run["id"])
    assert final["status"] == contract.CANCELLED and final["result"]["error_class"] == "cancelled"
    assert Path(final["receipt"]["output_logs"]["stdout"]).is_file()
    assert subprocess.run([*oci.DOCKER, "inspect", cid], capture_output=True).returncode != 0


def test_supervisor_timeout_kills_native_container(native, repo, monkeypatch):
    real_popen = runs.subprocess.Popen
    armed = {"value": False}

    def popen(argv, **kw):
        process = real_popen(argv, **kw)
        if argv[: len(oci.DOCKER)] == oci.DOCKER and "start" in argv:
            armed["value"] = True
        return process

    monkeypatch.setattr(runs.subprocess, "Popen", popen)
    monkeypatch.setattr(
        runs,
        "time",
        SimpleNamespace(
            time=lambda: time.time() + (1000 if armed["value"] else 0), sleep=time.sleep
        ),
    )
    proj = _register(repo)
    plan = runs.create_plan(
        agent="codex",
        project=proj["slug"],
        mode="workspace_write",
        task="fixture command",
        timeout_s=30,
    )
    run = runs.start(
        plan["id"], token=runs.approval_token(plan["id"]), via="isolated test", background=False
    )
    assert run["status"] == contract.TIMEOUT and run["result"]["error_class"] == "timeout"
    assert (
        subprocess.run(
            [*oci.DOCKER, "inspect", run["receipt"]["container_id"]], capture_output=True
        ).returncode
        != 0
    )


def test_restart_removes_only_recorded_dead_owner_container(native, repo):
    # No old Python supervisor remains: model the persisted restart state.
    from jarvis.coding_agents import workspace

    proj = _register(repo)
    ws = workspace.prepare(proj["path"], "restart_native")
    out = Path(ws["workspace"]).parent / "restart-output"
    out.mkdir()
    from jarvis.coding_agents import transport

    broker = transport.Broker("codex", out.parent / "restart-control-network.jsonl")
    cid = oci.create(
        run_id="restart_native",
        image=oci.image_id("ollama/ollama:latest"),
        ws=ws["workspace"],
        out_dir=str(out),
        request={
            "agent": "codex",
            "binary": str(Path.home() / ".nvm/versions/node/v24.15.0/bin/codex"),
            "cwd": ws["workspace"],
            "out_dir": str(out),
        },
        installations=runs._install_dirs(
            str(Path.home() / ".nvm/versions/node/v24.15.0/bin/codex")
        ),
        bindings=[],
        socket_path=broker.path,
        read_only=False,
    )
    proc = subprocess.Popen(
        [*oci.DOCKER, "start", "--attach", cid], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not Path(ws["workspace"], "ready.txt").exists():
            time.sleep(0.1)
        assert Path(ws["workspace"], "ready.txt").exists()
        with runs._conn() as conn:
            conn.execute(
                "INSERT INTO runs (id,status,owner_pid,receipt) VALUES (?,?,?,?)",
                (
                    "restart_native",
                    runs.RUNNING,
                    99999999,
                    json.dumps({"container_id": cid, "sandbox": oci.SCHEME}),
                ),
            )
        assert runs.recover_interrupted() == ["restart_native"]
        assert runs.get_run("restart_native")["status"] == contract.INTERRUPTED
        assert runs.recover_interrupted() == []
        proc.communicate(timeout=10)
    finally:
        oci.remove(cid, "restart_native")
        broker.close()
        if proc.poll() is None:
            proc.kill()
            proc.communicate(timeout=10)
