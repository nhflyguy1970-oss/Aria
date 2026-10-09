"""Real native Codex command/exec probes under the externally enforced boundary.

No model requests or credentials. Fixtures and evidence are disposable; the
probe commands deliberately ignore instructions and use ordinary subprocesses.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest

from jarvis.coding_agents import oci, runtime, transport


@pytest.fixture
def boundary(tmp_path):
    binary = Path.home() / ".nvm/versions/node/v24.15.0/bin/codex"
    if not shutil.which("docker") or not binary.is_file():
        pytest.skip("deployment-critical OCI/native CLI prerequisite absent")
    ws = tmp_path / "workspace"
    ws.mkdir()
    out = tmp_path / "output"
    out.mkdir(mode=0o700)
    state = tmp_path / "private-state"
    state.mkdir(mode=0o700)
    outside = tmp_path / "outside.txt"
    outside.write_text("KEEP\n")
    broker = transport.Broker("codex", tmp_path / "control/network.jsonl")
    installed = str(binary.parents[1])
    containers = []

    def create(command, *, read_only=False):
        cid = oci.create(
            run_id="cert_fixture",
            image=oci.image_id("ollama/ollama:latest"),
            ws=str(ws),
            out_dir=str(out),
            installations=[installed],
            bindings=[(str(state), str(Path.home() / ".codex"))],
            socket_path=broker.path,
            read_only=read_only,
            request={
                "agent": "codex",
                "binary": str(binary),
                "cwd": str(ws),
                "out_dir": str(out),
                "command": command,
            },
        )
        containers.append(cid)
        return cid

    def run(code, *, read_only=False):
        cid = create(["/usr/bin/python3", "-c", code], read_only=read_only)
        result = subprocess.run(
            [*oci.DOCKER, "start", "--attach", cid], capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stdout + result.stderr
        event = next(
            json.loads(line)
            for line in result.stdout.splitlines()
            if "certification.command" in line
        )
        assert event["result"]["exitCode"] == 0, event
        return json.loads(event["result"]["stdout"])

    yield type(
        "Boundary",
        (),
        {
            "ws": ws,
            "out": out,
            "outside": outside,
            "create": staticmethod(create),
            "run": staticmethod(run),
            "broker": broker,
        },
    )
    for cid in containers:
        oci.remove(cid, "cert_fixture")
    broker.close()
    assert outside.read_text() == "KEEP\n"


@pytest.mark.parametrize("operation", ["read", "write", "unlink", "rename", "symlink", "hardlink"])
def test_real_codex_rejects_outside_operations(boundary, operation):
    outside = str(boundary.outside)
    code = f"""
import os,json,pathlib
p={outside!r}; local='escape.txt'
try:
 if {operation!r}=='read': pathlib.Path(p).read_text()
 elif {operation!r}=='write': pathlib.Path(p).write_text('BROKEN')
 elif {operation!r}=='unlink': os.unlink(p)
 elif {operation!r}=='rename': os.rename('source.txt',p)
 elif {operation!r}=='symlink': os.symlink(p,local); pathlib.Path(local).write_text('BROKEN')
 elif {operation!r}=='hardlink': os.link(p,local)
 outcome='escaped'
except OSError as e: outcome=type(e).__name__
print(json.dumps({{'outcome':outcome}}))
"""
    (boundary.ws / "source.txt").write_text("SAFE")
    assert boundary.run(code)["outcome"] != "escaped"


def test_readonly_workspace_enforced_for_real_native_process(boundary):
    code = "import pathlib,json\ntry:\n pathlib.Path('edit.txt').write_text('bad'); result='escaped'\nexcept OSError as e: result=type(e).__name__\nprint(json.dumps({'result':result}))"
    assert boundary.run(code, read_only=True)["result"] != "escaped"
    assert not (boundary.ws / "edit.txt").exists()


def test_host_process_credentials_projects_and_sockets_absent(boundary):
    paths = [
        "/media/jeff/AI/jarvis",
        "/media/jeff/C/fly_tying_reference",
        "/media/jeff/C/fly_fishing_project",
        "/home/jeff/.ssh",
        "/home/jeff/.bash_history",
        "/home/jeff/.claude.json",
        "/var/run/docker.sock",
        "/run/user/1000/bus",
        f"/proc/{os.getpid()}/root",
    ]
    result = boundary.run(
        f"import pathlib,json\nprint(json.dumps({{p:pathlib.Path(p).exists() for p in {paths!r}}}))"
    )
    assert not any(result.values()), result


def test_no_privilege_or_network_escape(boundary):
    code = """
import pathlib,subprocess,socket,json
status=pathlib.Path('/proc/self/status').read_text()
r={key:next(l.split(':',1)[1].strip() for l in status.splitlines() if l.startswith(key+':')) for key in ('CapEff','NoNewPrivs','Seccomp')}
r['mount_exit']=subprocess.run(['/usr/bin/mount','-t','tmpfs','tmpfs','/tmp'],capture_output=True).returncode
r['unshare_exit']=subprocess.run(['/usr/bin/unshare','--mount','/usr/bin/true'],capture_output=True).returncode
for name,addr in [('host_loopback',('127.0.0.1',5432)),('external',('1.1.1.1',443)),('docker_gateway',('172.17.0.1',2375))]:
 s=socket.socket();s.settimeout(.5)
 try:s.connect(addr);r[name]='escaped'
 except OSError as e:r[name]=type(e).__name__
 s.close()
print(json.dumps(r))
"""
    result = boundary.run(code)
    assert (
        int(result["CapEff"], 16) == 0 and result["NoNewPrivs"] == "1" and result["Seccomp"] == "2"
    )
    assert result["mount_exit"] != 0 and result["unshare_exit"] != 0
    assert all(result[k] != "escaped" for k in ("host_loopback", "external", "docker_gateway"))


def test_remove_kills_detached_native_command_tree(boundary):
    cid = boundary.create(
        ["/bin/sh", "-c", 'setsid sh -c "echo ready > detached.txt; sleep 120" & sleep 120']
    )
    proc = subprocess.Popen(
        [*oci.DOCKER, "start", "--attach", cid], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not (boundary.ws / "detached.txt").exists():
            time.sleep(0.1)
        assert (boundary.ws / "detached.txt").exists()
        details = json.loads(oci.docker("inspect", cid).stdout)[0]
        pid = details["State"]["Pid"]
        subprocess.run([*oci.DOCKER, "kill", cid], check=True, capture_output=True)
        proc.communicate(timeout=10)
        assert not Path(f"/proc/{pid}").exists()
        assert json.loads(oci.docker("inspect", cid).stdout)[0]["State"]["Running"] is False
    finally:
        if proc.poll() is None:
            subprocess.run([*oci.DOCKER, "kill", cid], capture_output=True)
            proc.communicate(timeout=10)


@pytest.mark.parametrize(
    "connect_request",
    [
        b"GET https://chatgpt.com HTTP/1.1\r\n\r\n",
        b"CONNECT localhost:443 HTTP/1.1\r\n\r\n",
        b"CONNECT 127.0.0.1:443 HTTP/1.1\r\n\r\n",
        b"CONNECT chatgpt.com:80 HTTP/1.1\r\n\r\n",
        b"CONNECT chatgpt.com.attacker.com:443 HTTP/1.1\r\n\r\n",
        b"CONNECT api.openai.com:443 HTTP/1.1\r\n\r\n",
    ],
)
def test_connect_broker_blocks_unapproved_authority_with_durable_evidence(
    tmp_path, connect_request
):
    log = tmp_path / "network.jsonl"
    broker = transport.Broker("codex", log)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(broker.path)
            client.sendall(connect_request)
            assert client.recv(1024).startswith(b"HTTP/1.1 403")
    finally:
        broker.close()
    record = json.loads(log.read_text())
    assert record["decision"] == "deny" and "headers" not in record


def test_broker_rejects_private_dns_before_connect(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(ValueError, match="non-public"):
        transport.public_addresses("chatgpt.com")


def test_certificate_missing_stale_or_fake_backend_never_qualifies(tmp_path, monkeypatch):
    binary = tmp_path / "binary"
    binary.write_text("fake")
    monkeypatch.setattr(runtime, "FILE", tmp_path / "certificates.json")
    assert runtime.compatibility("codex", str(binary), "1")["state"] == "disabled"
    runtime.FILE.write_text(
        json.dumps({"codex": {"state": "verified", "version": "1", "backend": "offline_fixture"}})
    )
    assert runtime.compatibility("codex", str(binary), "1")["state"] == "disabled"


@pytest.mark.parametrize("host,allowed", [("chatgpt.com", True), ("attacker.example", False)])
def test_tls_sni_is_checked_independently_of_connect_authority(host, allowed):
    name = host.encode()
    extension = (
        len(name + bytes(3)).to_bytes(2, "big") + b"\x00" + len(name).to_bytes(2, "big") + name
    )
    extensions = b"\x00\x00" + len(extension).to_bytes(2, "big") + extension
    body = (
        b"\x03\x03"
        + bytes(32)
        + b"\x00"
        + b"\x00\x02\x13\x01"
        + b"\x01\x00"
        + len(extensions).to_bytes(2, "big")
        + extensions
    )
    hello = b"\x01" + len(body).to_bytes(3, "big") + body
    wire = b"\x16\x03\x01" + len(hello).to_bytes(2, "big") + hello
    left, right = socket.socketpair()
    try:
        left.sendall(wire)
        if allowed:
            assert transport.client_hello(right, "chatgpt.com") == wire
        else:
            with pytest.raises(ValueError, match="SNI"):
                transport.client_hello(right, "chatgpt.com")
    finally:
        left.close()
        right.close()


def test_isolated_watchdog_survives_host_client_disconnection(boundary):
    real_create = oci.create
    # A shortened, trusted certification request exercises the same PID-1
    # watchdog used with the approved run timeout; no model is contacted.
    state = boundary.out.parent / "watchdog-state"
    state.mkdir()
    binary = str(Path.home() / ".nvm/versions/node/v24.15.0/bin/codex")
    cid = real_create(
        run_id="cert_watchdog",
        image=oci.image_id("ollama/ollama:latest"),
        ws=str(boundary.ws),
        out_dir=str(boundary.out),
        installations=[str(Path(binary).parents[1])],
        bindings=[(str(state), str(Path.home() / ".codex"))],
        socket_path=boundary.broker.path,
        read_only=False,
        request={
            "agent": "codex",
            "binary": binary,
            "cwd": str(boundary.ws),
            "out_dir": str(boundary.out),
            "command": ["/bin/sh", "-c", "setsid sleep 120 & sleep 120"],
            "timeout_s": 2,
        },
    )
    try:
        oci.docker("start", cid)  # no attached host process or supervising loop
        time.sleep(3)
        detail = json.loads(oci.docker("inspect", cid).stdout)[0]
        assert not detail["State"]["Running"] and detail["State"]["ExitCode"] == 124
    finally:
        oci.remove(cid, "cert_watchdog")
