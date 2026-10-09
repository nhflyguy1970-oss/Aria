"""Trusted controller for disposable OCI agent processes; no host socket inside."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

SCHEME = "aria-oci-external-v1"
LABEL = "aria.phase6.run"
DOCKER = ["docker", "--host", "unix:///var/run/docker.sock"]


def docker(*args, timeout=30):
    return subprocess.run(
        [*DOCKER, *args], capture_output=True, text=True, timeout=timeout, check=True
    )


def image_id(image: str) -> str:
    value = docker("image", "inspect", "--format", "{{.Id}}", image).stdout.strip()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise RuntimeError("local immutable OCI image is unavailable")
    return value


def create(
    *,
    run_id: str,
    image: str,
    ws: str,
    out_dir: str,
    request: dict,
    installations: list[str],
    bindings: list[tuple[str, str]],
    socket_path: str,
    read_only: bool,
) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("invalid run identity")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise ValueError("OCI image must be pinned by local immutable ID")
    if not Path(ws).is_dir() or not Path(out_dir).is_dir():
        raise ValueError("missing authorized workspace/output directory")
    code = Path(__file__).resolve().parent
    req = Path(out_dir) / "request.json"
    req.write_text(json.dumps(request))
    req.chmod(0o600)
    args = [
        "create",
        "--pull",
        "never",
        "--label",
        f"{LABEL}={run_id}",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges=true",
        "--security-opt",
        "apparmor=docker-default",
        "--pids-limit",
        "512",
        "--memory",
        "6g",
        "--memory-swap",
        "6g",
        "--cpus",
        "4",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--workdir",
        ws,
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=512m",
        "--tmpfs",
        "/run:rw,nosuid,nodev,size=16m",
    ]

    def mount(source, target, readonly=False):
        if any(c in str(source) + str(target) for c in (",", "\n", "\0")):
            raise ValueError("invalid mount path")
        args.extend(
            ["--mount", f"type=bind,src={source},dst={target}" + (",readonly" if readonly else "")]
        )

    for path in ("/usr", "/lib", "/lib64", *installations):
        if Path(path).exists():
            mount(path, path, True)
    mount(code, code, True)
    mount(ws, ws, read_only)
    if (Path(ws) / ".git").is_dir():
        mount(Path(ws) / ".git", Path(ws) / ".git", True)
    mount(out_dir, out_dir)
    for source, target in bindings:
        mount(source, target)
    mount(socket_path, "/run/aria-subscription.sock", True)
    for key, value in {
        "HOME": str(Path.home()),
        "PATH": ":".join([str(Path(p) / "bin") for p in installations] + ["/usr/bin", "/bin"]),
        "NO_COLOR": "1",
        "JARVIS_CLOUD_INFERENCE": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "DISABLE_TELEMETRY": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    }.items():
        args.extend(["--env", f"{key}={value}"])
    args += ["--entrypoint", "/usr/bin/python3", image, str(code / "rpc_worker.py"), str(req)]
    cid = docker(*args).stdout.strip()
    try:
        detail = json.loads(docker("inspect", cid).stdout)[0]
        host = detail["HostConfig"]
        if (
            host["NetworkMode"] != "none"
            or not host["ReadonlyRootfs"]
            or host["Privileged"]
            or "ALL" not in host["CapDrop"]
            or host["Memory"] != 6 * 1024**3
            or host["PidsLimit"] != 512
            or host["NanoCpus"] != 4 * 10**9
            or "no-new-privileges=true" not in host["SecurityOpt"]
            or host.get("CapAdd")
            or host.get("PidMode")
            or host.get("IpcMode") == "host"
            or "apparmor=docker-default" not in host["SecurityOpt"]
            or detail["Config"]["User"] != f"{os.getuid()}:{os.getgid()}"
            or any("unconfined" in x for x in host["SecurityOpt"])
        ):
            raise RuntimeError("OCI daemon did not establish the required isolation")
        return cid
    except Exception:
        remove(cid, run_id)
        raise


def remove(cid: str, run_id: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", cid):
        raise ValueError("invalid container identity")
    try:
        detail = json.loads(docker("inspect", cid).stdout)[0]
    except subprocess.CalledProcessError as exc:
        if any(
            message in (exc.stderr or "").lower()
            for message in ("no such object:", "no such container:")
        ) and cid in (exc.stderr or ""):
            return  # previously removed, e.g. cancellation before a restart
        raise
    if (detail.get("Config", {}).get("Labels") or {}).get(LABEL) != run_id:
        raise RuntimeError("refusing to remove a container owned by another task")
    docker("rm", "--force", cid)
