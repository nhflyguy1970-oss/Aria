"""14-phase whole-system audit engine for ARIA / CLI."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from jarvis.audit_paths import (
    audit_locations,
    audit_path_env,
    audit_path_string,
    configured_gpu_preference,
    install_command,
    jarvis_root,
    nvidia_ai_hybrid_configured,
    prepare_gui_sudo_env,
    read_env_file_var,
    resolve_script,
    resolve_venv_python,
)
from jarvis.config import DATA_DIR

Item = dict[str, str]
PhaseResult = dict[str, Any]

# Jarvis install scripts — referenced in warn/fail fix lines when something needs installing.
_INSTALL_SCRIPTS: dict[str, str] = {
    "audit_deps": "scripts/install-system-audit-deps.sh",
    "dependencies": "scripts/install-dependencies.sh",
    "ollama": "scripts/install-ollama-latest.sh",
    "rocm_pytorch": "scripts/install-rocm-pytorch.sh",
    "cuda_pytorch": "scripts/install-cuda-pytorch.sh",
    "nvidia_gpu": "scripts/enable-nvidia-gpu.sh",
    "docker": "scripts/install-docker.sh",
    "audit_sudoers": "scripts/install-audit-sudoers.sh",
    "lsp": "scripts/install-lsp-servers.sh",
    "verify": "scripts/verify-setup.sh",
    "harden": "scripts/harden-security.sh",
    "comfyui": "scripts/install-comfyui-deps.sh",
    "dev_tools": "scripts/install-dev-tools.sh",
    "rust": "scripts/install-rust.sh",
}


def _fix_script(key: str, *, note: str = "") -> str:
    rel = _INSTALL_SCRIPTS.get(key, key)
    if rel.startswith(("curl ", "sudo apt", "http")):
        cmd = rel
    else:
        cmd = install_command(rel)
    if note:
        return f"{cmd}  # {note}"
    return cmd


def _audit_path() -> str:
    return audit_path_string()


def _audit_env() -> dict[str, str]:
    return audit_path_env()


def install_script_path(key: str) -> Path | None:
    rel = _INSTALL_SCRIPTS.get(key)
    if not rel or rel.startswith(("curl ", "sudo apt", "http")):
        return None
    path = resolve_script(rel)
    return path if path.is_file() else None


def _install_argv(script: Path, env: dict[str, str]) -> list[str]:
    """Run install script; wrap sudo with -A when zenity askpass is available."""
    script_q = shlex.quote(str(script))
    gui_env = prepare_gui_sudo_env(env)
    if gui_env:
        askpass_q = shlex.quote(gui_env["SUDO_ASKPASS"])
        inner = (
            f"export SUDO_ASKPASS={askpass_q}; "
            f"export DISPLAY={shlex.quote(gui_env.get('DISPLAY', ''))}; "
            f"sudo() {{ command sudo -A \"$@\"; }}; "
            f"exec bash {script_q}"
        )
        return ["bash", "-c", inner]
    return ["bash", str(script)]


def run_install_script(key: str) -> dict[str, Any]:
    """Run a whitelisted Jarvis install script (from ARIA System tab)."""
    script = install_script_path(key)
    if not script:
        return {"ok": False, "error": f"Unknown or missing install script: {key}"}
    env = _audit_env()
    gui = prepare_gui_sudo_env(env)
    if gui:
        env = gui
    root = jarvis_root()
    try:
        proc = subprocess.run(
            _install_argv(script, env),
            capture_output=True,
            text=True,
            timeout=900,
            cwd=str(root),
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Install timed out after 15 minutes"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    out = (proc.stdout or "")[-6000:]
    err = (proc.stderr or "")[-3000:]
    ok = proc.returncode == 0
    error = ""
    if not ok:
        combined = f"{err}\n{out}".lower()
        if "password is required" in combined or "askpass" in combined:
            error = (
                "Install needs sudo. A password dialog should appear — if it did not, run in a terminal: "
                f"bash {script}"
            )
        elif err.strip():
            error = err.strip().splitlines()[-1][:240]
        else:
            error = f"Script exited with code {proc.returncode}"
    return {
        "ok": ok,
        "install_key": key,
        "script": str(script),
        "exit_code": proc.returncode,
        "stdout": out,
        "stderr": err,
        "error": error,
        "needs_gui_sudo": not ok and "password" in f"{err}{out}".lower(),
        "message": "Install finished" if ok else error or "Install failed — see output",
    }


def _dev_install_fix(tool: str) -> str:
    if tool in ("git",):
        return _fix_script("dependencies", note=f"installs {tool}")
    if tool in ("gcc", "cmake", "make", "node", "npm", "java"):
        return _fix_script("dev_tools", note=f"installs {tool}")
    if tool in ("cargo", "rustc"):
        return _fix_script("rust", note=f"installs {tool} via rustup")
    return _fix_script("dev_tools")


@dataclass
class Collector:
    phases: dict[str, PhaseResult] = field(default_factory=dict)

    def _phase(self, pid: str, title: str) -> PhaseResult:
        if pid not in self.phases:
            self.phases[pid] = {
                "id": pid,
                "title": title,
                "pass": [],
                "warn": [],
                "fail": [],
            }
        return self.phases[pid]

    def pass_(self, pid: str, title: str, message: str, *, scope: str = "system") -> None:
        self._phase(pid, title)["pass"].append({"message": message, "scope": scope})

    def warn(self, pid: str, title: str, message: str, fix: str = "", *, install_key: str = "", scope: str = "system") -> None:
        item: Item = {"message": message, "scope": scope}
        if install_key:
            item["install_key"] = install_key
            item["fix"] = _fix_script(install_key, note=fix)
        elif fix:
            item["fix"] = fix
        self._phase(pid, title)["warn"].append(item)

    def fail(self, pid: str, title: str, message: str, fix: str = "", *, install_key: str = "", scope: str = "system") -> None:
        item: Item = {"message": message, "scope": scope}
        if install_key:
            item["install_key"] = install_key
            item["fix"] = _fix_script(install_key, note=fix)
        elif fix:
            item["fix"] = fix
        self._phase(pid, title)["fail"].append(item)

    def flatten(self) -> tuple[list[Item], list[Item], list[Item]]:
        passed: list[Item] = []
        warned: list[Item] = []
        failed: list[Item] = []
        for phase in self.phases.values():
            passed.extend(phase["pass"])
            warned.extend(phase["warn"])
            failed.extend(phase["fail"])
        return passed, warned, failed

    @staticmethod
    def _scope_count(items: list[Item], scope: str) -> int:
        return sum(1 for i in items if i.get("scope", "system") == scope)

    def to_report(self, *, sudo_smart: bool = False) -> dict[str, Any]:
        passed, warned, failed = self.flatten()
        total = len(passed) + len(warned) + len(failed)

        sys_fail = self._scope_count(failed, "system")
        sys_warn = self._scope_count(warned, "system")
        jrv_fail = self._scope_count(failed, "jarvis")
        jrv_warn = self._scope_count(warned, "jarvis")

        if sys_fail:
            result = "fail"
        elif sys_warn:
            result = "warning"
        else:
            result = "pass"
        if jrv_fail:
            jarvis_result = "fail"
        elif jrv_warn:
            jarvis_result = "warning"
        else:
            jarvis_result = "pass"

        phase_list = list(self.phases.values())
        return {
            "ok": True,
            "result": result,
            "jarvis_result": jarvis_result,
            "hostname": socket.gethostname(),
            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
            "sudo_smart": sudo_smart,
            "locations": audit_locations(),
            "summary": {
                "pass": len(passed),
                "warn": len(warned),
                "fail": len(failed),
                "total": total,
                "phases": len(phase_list),
                "system": {
                    "pass": self._scope_count(passed, "system"),
                    "warn": sys_warn,
                    "fail": sys_fail,
                },
                "jarvis": {
                    "pass": self._scope_count(passed, "jarvis"),
                    "warn": jrv_warn,
                    "fail": jrv_fail,
                },
            },
            "phases": phase_list,
            "pass": passed,
            "warn": warned,
            "fail": failed,
        }


def _run(cmd: list[str], *, timeout: int = 30, text: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, capture_output=True, text=text, timeout=timeout, check=False, env=_audit_env()
    )


_SUDO_TIMEOUT_RC = 124
_SMARTCTL_TIMEOUT = 10
_SMARTCTL_EXTERNAL_TIMEOUT = 8


def _completed_on_timeout(
    exc: subprocess.TimeoutExpired,
    cmd: list[str],
    *,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    stdout = exc.stdout or ""
    stderr = exc.stderr or ""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if not stderr.strip():
        stderr = f"Command timed out after {timeout}s"
    return subprocess.CompletedProcess(
        args=cmd, returncode=_SUDO_TIMEOUT_RC, stdout=stdout, stderr=stderr
    )


def _run_sudo(cmd: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        if os.geteuid() == 0:
            return _run(cmd, timeout=timeout)
        probe = _run(["sudo", "-n", *cmd], timeout=timeout)
        if probe.returncode == 0 or (probe.stdout or "").strip():
            return probe
        return probe
    except subprocess.TimeoutExpired as exc:
        return _completed_on_timeout(exc, cmd, timeout=timeout)


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _pytorch_install_key() -> str:
    """ROCm wheels for AMD-only AI; CUDA wheels when NVIDIA handles Jarvis AI."""
    if _have("nvidia-smi") and configured_gpu_preference() in ("nvidia", "both", "auto"):
        return "cuda_pytorch"
    return "rocm_pytorch"


def _dual_gpu() -> bool:
    has_amd = "amdgpu" in _read("/proc/modules") or _have("rocm-smi")
    return _have("nvidia-smi") and has_amd


def _tool_cmd(name: str) -> str | None:
    """Resolve dev tool binary — PATH, then common install locations."""
    found = shutil.which(name, path=_audit_path())
    if found:
        return found
    home = Path.home()
    for candidate in (
        home / ".cargo" / "bin" / name,
        home / ".local" / "bin" / name,
        Path("/usr/local/bin") / name,
    ):
        try:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
        except OSError:
            continue
    rustup = home / ".rustup" / "toolchains"
    if rustup.is_dir():
        for tc in sorted(rustup.iterdir(), reverse=True):
            candidate = tc / "bin" / name
            try:
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    return str(candidate)
            except OSError:
                continue
    return None


def _have(cmd: str) -> bool:
    return _tool_cmd(cmd) is not None


def _smartctl_json(dev: str, *args: str, timeout: int = _SMARTCTL_TIMEOUT) -> tuple[dict[str, Any], str | None]:
    """Run smartctl and return (json, error). error is timeout|standby|parse or None."""
    proc = _run_sudo(
        ["smartctl", "-j", "-n", "standby", "-T", "permissive", *args, dev],
        timeout=timeout,
    )
    if proc.returncode == _SUDO_TIMEOUT_RC:
        return {}, "timeout"
    try:
        data: dict[str, Any] = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {}, "parse"
    smartctl = data.get("smartctl") or {}
    exit_status = smartctl.get("exit_status")
    msgs = smartctl.get("messages") or []
    if exit_status == 2 and any("standby" in str(m.get("string", "")).lower() for m in msgs):
        return data, "standby"
    return data, None


@dataclass(frozen=True)
class BlockDevice:
    path: str
    name: str
    transport: str
    removable: bool
    rotational: bool | None

    @property
    def is_external(self) -> bool:
        return self.transport == "usb" or self.removable

    @property
    def smart_timeout(self) -> int:
        return _SMARTCTL_EXTERNAL_TIMEOUT if self.is_external else _SMARTCTL_TIMEOUT


def _parse_lsblk_flag(raw: str) -> bool | None:
    raw = raw.strip()
    if raw == "1":
        return True
    if raw == "0":
        return False
    return None


def _block_devices() -> list[BlockDevice]:
    proc = _run(
        ["lsblk", "-d", "-n", "-o", "NAME,TYPE,RM,ROTA,TRAN,HOTPLUG"],
        timeout=10,
    )
    devs: list[BlockDevice] = []
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[1] != "disk":
            continue
        name = parts[0]
        if name.startswith(("loop", "zram")):
            continue
        removable = _parse_lsblk_flag(parts[2]) if len(parts) > 2 else False
        rotational = _parse_lsblk_flag(parts[3]) if len(parts) > 3 else None
        transport = parts[4].lower() if len(parts) > 4 and parts[4] != "-" else ""
        hotplug = _parse_lsblk_flag(parts[5]) if len(parts) > 5 else False
        if hotplug and not transport:
            transport = "usb"
        devs.append(
            BlockDevice(
                path=f"/dev/{name}",
                name=name,
                transport=transport,
                removable=bool(removable),
                rotational=rotational,
            )
        )
    return devs


def _diagnose_unit(unit: str) -> tuple[str, str]:
    journal = _run(["journalctl", "-u", unit, "-n", "20", "--no-pager"], timeout=15).stdout or ""
    wd_proc = _run(["systemctl", "show", unit, "-p", "WorkingDirectory", "--value"], timeout=5)
    wd = (wd_proc.stdout or "").strip()
    if "CHDIR" in journal or "No such file or directory" in journal:
        if wd and not Path(wd).is_dir():
            return (
                f"{unit}: folder missing — {wd} (drive not mounted or project moved)",
                f"sudo systemctl disable --now {unit} && sudo systemctl reset-failed {unit}",
            )
    if unit == "mongod.service":
        docker_m = _run(["docker", "ps", "--format", "{{.Names}}"], timeout=10).stdout or ""
        names = [n for n in docker_m.splitlines() if "mongo" in n.lower()]
        if names:
            return (
                f"mongod.service failed — MongoDB runs in Docker ({', '.join(names)}); system unit redundant",
                "sudo systemctl disable --now mongod && sudo systemctl reset-failed mongod",
            )
    last = ""
    for line in reversed(journal.splitlines()):
        if re.search(r"error|fail|exited|denied|fatal", line, re.I):
            last = line.strip()[:160]
            break
    if last:
        return f"{unit} failed — {last}", f"journalctl -u {unit} -n 40 --no-pager; sudo systemctl restart {unit}"
    return f"{unit} failed", f"systemctl status {unit}; journalctl -u {unit} -n 30 --no-pager"


def _sensor_temps() -> list[tuple[str, float]]:
    """Return (label, celsius) from sensors -j — temperature inputs only."""
    proc = _run(["sensors", "-j"], timeout=15)
    if proc.returncode != 0 or not (proc.stdout or "").strip():
        return []
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    out: list[tuple[str, float]] = []

    def is_temp_key(key: str) -> bool:
        low = key.lower()
        if "fan" in low or "rpm" in low or low.startswith("in") or "power" in low or "curr" in low:
            return False
        return (
            low.endswith("_input") and any(t in low for t in ("temp", "tctl", "tdie", "tskt"))
            or low in ("temp1", "temp2", "composite", "edge", "junction", "package")
        )

    def walk(node: Any, prefix: str) -> None:
        if not isinstance(node, dict):
            return
        for key, val in node.items():
            if key in ("adapter", "limits", "min", "max", "crit", "high", "low"):
                continue
            path = f"{prefix}.{key}" if prefix else key
            if "fan" in path.lower():
                continue
            if isinstance(val, (int, float)) and is_temp_key(key):
                temp = float(val)
                if -50 <= temp <= 150:
                    out.append((path, temp))
            elif isinstance(val, dict):
                walk(val, path)

    walk(data, "")
    return out


def _zombie_count() -> int:
    proc = _run(["ps", "-eo", "stat"], timeout=10)
    if proc.returncode != 0:
        return 0
    return sum(1 for line in (proc.stdout or "").splitlines()[1:] if "Z" in line.split()[0])


def _service_state(unit: str) -> str:
    return (_run(["systemctl", "is-active", unit], timeout=5).stdout or "").strip()


# ---------------------------------------------------------------------------
# Phases (14 — whole computer + Jarvis stack)
# ---------------------------------------------------------------------------

P1 = ("p1_os", "Phase 1 — Operating System")
P2 = ("p2_packages", "Phase 2 — Package Manager")
P3 = ("p3_storage", "Phase 3 — Storage & Filesystems")
P4 = ("p4_memory", "Phase 4 — Memory & Swap")
P5 = ("p5_hardware", "Phase 5 — Hardware & Sensors")
P6 = ("p6_gpu", "Phase 6 — GPU & Graphics")
P7 = ("p7_services", "Phase 7 — Services & Desktop")
P8 = ("p8_containers", "Phase 8 — Containers & Data")
P9 = ("p9_dev", "Phase 9 — Development Tools")
P10 = ("p10_integrity", "Phase 10 — System Integrity")
P11 = ("p11_perf", "Phase 11 — Performance")
P12 = ("p12_security", "Phase 12 — Security")
P13 = ("p13_network", "Phase 13 — Network")
P14 = ("p14_jarvis", "Phase 14 — Jarvis & AI Runtime")


def phase_os(c: Collector) -> None:
    pid, title = P1
    rel = _run(["lsb_release", "-ds"], timeout=5).stdout.strip().strip('"')
    if rel:
        c.pass_(pid, title, f"OS: {rel}")
    else:
        c.warn(pid, title, "Could not detect distro version", "lsb_release -a")
    kernel = _run(["uname", "-r"], timeout=5).stdout.strip()
    c.pass_(pid, title, f"Kernel: {kernel}")
    uptime = _run(["uptime", "-p"], timeout=5).stdout.strip() or "unknown"
    c.pass_(pid, title, f"Uptime: {uptime}")
    boot_ts = _run(["who", "-b"], timeout=5).stdout.strip()
    if boot_ts:
        c.pass_(pid, title, f"Last boot: {boot_ts.replace('system boot ', '')}")
    else:
        boot_line = _run(
            ["journalctl", "--list-boots", "-n", "1", "--no-pager"], timeout=10
        ).stdout.strip()
        if boot_line:
            c.pass_(pid, title, f"Last boot: {boot_line.split()[-2] if len(boot_line.split()) > 2 else boot_line}")
    start = _run(
        ["systemd-analyze", "time"], timeout=10
    ).stdout.strip().replace("\n", " · ")
    if start:
        c.pass_(pid, title, f"Boot time: {start}")
    else:
        c.warn(pid, title, "Boot time unavailable", "systemd-analyze time")
    cpuinfo = _read("/proc/cpuinfo")
    model = ""
    for line in cpuinfo.splitlines():
        if line.lower().startswith("model name"):
            model = line.split(":", 1)[-1].strip()
            break
    if not model and _have("lscpu"):
        lscpu = _run(["lscpu"], timeout=5).stdout or ""
        model = next((l.split(":", 1)[1].strip() for l in lscpu.splitlines() if "Model name" in l), "")
    ncpu = os.cpu_count() or 0
    if model:
        c.pass_(pid, title, f"CPU: {model} ({ncpu} logical CPUs)")
    elif ncpu:
        c.pass_(pid, title, f"CPU: {ncpu} logical CPUs")
    if _have("timedatectl"):
        tz = _run(["timedatectl", "show", "-p", "Timezone", "--value"], timeout=5).stdout.strip()
        ntp = _run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], timeout=5).stdout.strip()
        if tz:
            c.pass_(pid, title, f"Timezone: {tz}")
        if ntp == "yes":
            c.pass_(pid, title, "Clock: NTP synchronized")
        elif ntp == "no":
            c.warn(pid, title, "Clock: NTP not synchronized", "timedatectl set-ntp true")
    zombies = _zombie_count()
    if zombies > 5:
        c.warn(pid, title, f"Zombie processes: {zombies}", "ps aux | awk '$8 ~ /Z/'; reboot if persistent")
    else:
        c.pass_(pid, title, f"Zombie processes: {zombies}")
    maxfiles = _run(["bash", "-c", "ulimit -n"], timeout=5).stdout.strip()
    if maxfiles:
        c.pass_(pid, title, f"Open files limit (soft): {maxfiles}")


def phase_packages(c: Collector) -> None:
    pid, title = P2
    broken = _run(["dpkg", "--audit"], timeout=30).stdout.strip()
    if broken:
        c.fail(pid, title, "Broken packages detected", install_key="dependencies")
    else:
        c.pass_(pid, title, "No broken packages")
    held = _run(["apt-mark", "showhold"], timeout=15).stdout.strip()
    if held:
        count = len([l for l in held.splitlines() if l.strip()])
        c.pass_(pid, title, f"Held packages: {count}")
    else:
        c.pass_(pid, title, "No held packages")
    orphans = ""
    if _have("deborphan"):
        orphans = _run(["deborphan"], timeout=30).stdout.strip()
    if orphans:
        n_orphan = len(orphans.splitlines())
        c.warn(
            pid,
            title,
            f"Orphan packages: {n_orphan} (optional — libs nothing depends on)",
            fix=(
                "deborphan -a   # full list; review then remove: "
                "sudo apt remove --purge $(deborphan)"
            ),
        )
    elif not _have("deborphan"):
        c.pass_(pid, title, "Orphan check skipped (deborphan not installed)")
    else:
        c.pass_(pid, title, "No orphan packages")
    apt_check = _run_sudo(["apt-get", "check"], timeout=60)
    if apt_check.returncode == 0:
        c.pass_(pid, title, "Package integrity: apt-get check OK")
    elif os.geteuid() != 0 and "password" in (apt_check.stderr or "").lower():
        c.warn(pid, title, "apt-get check needs sudo", _fix_script("audit_sudoers"))
    else:
        c.warn(pid, title, "apt-get check reported issues",
               _fix_script("dependencies", note="then: sudo apt-get check"))
    upgrades = _run(
        ["bash", "-c", "apt list --upgradable 2>/dev/null | tail -n +2 | wc -l"],
        timeout=60,
    ).stdout.strip()
    try:
        n_up = int(upgrades or "0")
    except ValueError:
        n_up = 0
    if n_up > 50:
        c.warn(pid, title, f"Pending upgrades: {n_up}", "sudo apt update && sudo apt upgrade")
    elif n_up > 0:
        c.pass_(pid, title, f"Pending upgrades: {n_up} (optional)")
    else:
        c.pass_(pid, title, "No pending upgrades")


def phase_storage(c: Collector, *, sudo_smart: bool) -> None:
    pid, title = P3
    if not _have("smartctl"):
        c.warn(pid, title, "smartctl not installed", install_key="audit_deps")
    else:
        smart_ok = 0
        disks = _block_devices()
        for devinfo in disks:
            dev = devinfo.path
            timeout = devinfo.smart_timeout
            data, err = _smartctl_json(dev, "-H", timeout=timeout)
            if err == "timeout":
                hint = (
                    " (USB/external — may sleep or respond slowly)"
                    if devinfo.is_external
                    else ""
                )
                c.warn(
                    pid,
                    title,
                    f"SMART {dev}: timed out after {timeout}s{hint}",
                    f"sudo smartctl -a {dev}",
                )
                continue
            if err == "standby":
                c.warn(
                    pid,
                    title,
                    f"SMART {dev}: in standby — SMART skipped",
                    f"sudo smartctl -a {dev}",
                )
                continue
            msgs = data.get("smartctl", {}).get("messages", [])
            if any("Permission denied" in m.get("string", "") for m in msgs):
                continue
            health = data.get("smart_status", {}).get("passed")
            name = data.get("model_name") or data.get("device", {}).get("name") or dev
            detail, detail_err = _smartctl_json(dev, "-A", timeout=timeout)
            if detail_err == "timeout":
                c.warn(
                    pid,
                    title,
                    f"SMART attributes {dev}: timed out after {timeout}s",
                    f"sudo smartctl -a {dev}",
                )
                detail = {}
            elif detail_err == "standby":
                detail = {}
            attrs = {a.get("name"): a for a in detail.get("ata_smart_attributes", {}).get("table", [])}
            nvme = detail.get("nvme_smart_health_information_log", {})
            temp = nvme.get("temperature") or detail.get("temperature", {}).get("current")
            poh = nvme.get("power_on_hours") or attrs.get("Power_On_Hours", {}).get("raw", {}).get("value")
            wear = nvme.get("percentage_used")
            reallocated = attrs.get("Reallocated_Sector_Ct", {}).get("raw", {}).get("value")
            crc = attrs.get("UDMA_CRC_Error_Count", {}).get("raw", {}).get("value")
            if health is True:
                c.pass_(pid, title, f"SMART {dev} ({name}): PASSED")
                smart_ok += 1
            elif health is False:
                c.fail(pid, title, f"SMART {dev}: FAILED — drive may be failing",
                       f"sudo smartctl -a {dev}  # backup data immediately")
                smart_ok += 1
            else:
                c.warn(pid, title, f"SMART {dev}: status unknown", f"sudo smartctl -a {dev}")
                smart_ok += 1
            if temp is not None:
                t = int(temp) if isinstance(temp, (int, float)) else temp
                if isinstance(t, int) and t >= 80:
                    c.warn(pid, title, f"{dev} temperature: {t}°C", "check cooling and airflow")
                elif isinstance(t, int):
                    c.pass_(pid, title, f"{dev} temperature: {t}°C")
            if poh is not None:
                c.pass_(pid, title, f"{dev} power-on hours: {poh}")
            if wear is not None:
                if int(wear) >= 90:
                    c.warn(pid, title, f"{dev} NVMe wear: {wear}%", "plan drive replacement")
                else:
                    c.pass_(pid, title, f"{dev} NVMe wear: {wear}%")
            if reallocated is not None and int(reallocated) > 0:
                c.warn(pid, title, f"{dev} reallocated sectors: {reallocated}",
                       f"sudo smartctl -a {dev}  # monitor closely")
            if crc is not None and int(crc) > 0:
                c.warn(pid, title, f"{dev} CRC errors: {crc}", "check SATA/NVMe cable and port")
        if not sudo_smart and smart_ok == 0 and disks:
            c.warn(pid, title, f"SMART skipped on {len(disks)} drive(s) — needs sudo",
               install_key="audit_sudoers")
    df = _run(["df", "-hP"], timeout=15).stdout or ""
    warn_disk = fail_disk = False
    for line in df.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        pct_s, mp, avail = parts[4].rstrip("%"), parts[5], parts[3]
        if mp in ("/dev", "/run", "/proc"):
            continue
        if parts[0] in ("tmpfs", "devtmpfs"):
            continue
        try:
            pct = int(pct_s)
        except ValueError:
            continue
        if pct >= 95:
            c.fail(pid, title, f"{mp} at {pct}% ({avail} free)",
                   f"du -xh {mp} --max-depth=1 | sort -hr | head -20")
            fail_disk = True
        elif pct >= 85:
            c.warn(pid, title, f"{mp} at {pct}% ({avail} free)",
                   f"du -xh {mp} --max-depth=1 | sort -hr | head -20")
            warn_disk = True
    if not warn_disk and not fail_disk:
        c.pass_(pid, title, "Disk usage below 85% on all filesystems")
    warn_inode = fail_inode = False
    for line in (_run(["df", "-iP"], timeout=15).stdout or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        mp = parts[5]
        if mp in ("/dev", "/run", "/proc") or parts[0] in ("tmpfs", "devtmpfs"):
            continue
        try:
            iused = int(parts[4].rstrip("%"))
        except ValueError:
            continue
        if iused >= 95:
            c.fail(pid, title, f"Inodes {iused}% used on {mp}", f"sudo find {mp} -xdev -type f | wc -l")
            fail_inode = True
        elif iused >= 85:
            c.warn(pid, title, f"Inodes {iused}% used on {mp}", f"find large dirs: du -xh {mp} --max-depth=2 | sort -hr | head")
            warn_inode = True
    if not warn_inode and not fail_inode:
        c.pass_(pid, title, "Inode usage below 85% on all filesystems")
    lsblk = _run(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE", "-e", "7"], timeout=10).stdout or ""
    disks = [l.strip() for l in lsblk.splitlines()[1:] if l.strip() and "disk" in l]
    if disks:
        c.pass_(pid, title, f"Block devices: {len(disks)} disk(s)")
        for line in disks[:6]:
            c.pass_(pid, title, f"  {line[:90]}")
    mounts = _run(["findmnt", "-rn", "-o", "TARGET,FSTYPE,OPTIONS"], timeout=10).stdout or ""
    ro_critical = False
    for line in mounts.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        target, opts = parts[0], parts[2]
        if target.startswith("/sys") or target == "/proc":
            continue
        if re.search(r"(^|,)ro(,|$)", opts) and (
            target == "/" or target.startswith("/home") or target.startswith("/media")
        ):
            c.fail(pid, title, f"Read-only mount: {target}",
                   f"sudo mount -o remount,rw {target}")
            ro_critical = True
    if not ro_critical:
        c.pass_(pid, title, "Critical mount points are read-write")
    if _have("systemctl"):
        fsck_timer = _run(["systemctl", "is-enabled", "fstrim.timer"], timeout=5).stdout.strip()
        if fsck_timer == "enabled":
            c.pass_(pid, title, "fstrim.timer enabled (SSD maintenance)")
        else:
            c.pass_(pid, title, "Filesystem health: no ro mounts detected")


def phase_memory(c: Collector) -> None:
    pid, title = P4
    mem = {}
    for line in _read("/proc/meminfo").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            mem[k.strip()] = v.strip()
    total_kb = int(mem.get("MemTotal", "0 kB").split()[0] or 0)
    avail_kb = int(mem.get("MemAvailable", "0 kB").split()[0] or 0)
    if total_kb:
        used_pct = 100 - (avail_kb * 100 // total_kb)
        c.pass_(pid, title, f"RAM: {used_pct}% used ({avail_kb // 1024 // 1024}G avail / {total_kb // 1024 // 1024}G)")
        if used_pct >= 98:
            c.fail(pid, title, f"RAM critical: {used_pct}%", "ps aux --sort=-%mem | head -15")
        elif used_pct >= 90:
            c.warn(pid, title, f"RAM high: {used_pct}%", "ps aux --sort=-%mem | head -15")
    swap_lines = _run(["swapon", "--show"], timeout=5).stdout or ""
    if swap_lines.count("\n") <= 0:
        c.warn(pid, title, "No swap configured",
               "sudo fallocate -l 16G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile")
    else:
        c.pass_(pid, title, f"Swap: {swap_lines.count(chr(10))} device(s) active")
    if "zram" in (_read("/proc/swaps") + swap_lines):
        c.pass_(pid, title, "zram swap active")
    else:
        c.pass_(pid, title, "zram: not in use (optional)")
    huge = mem.get("HugePages_Total", "0")
    c.pass_(pid, title, f"Huge pages total: {huge.split()[0]}")
    oom = _run(["journalctl", "-k", "-b", "--no-pager", "-g", "Out of memory"], timeout=15).stdout or ""
    oom_count = len([l for l in oom.splitlines() if l.strip() and not l.startswith("--")])
    if oom_count:
        c.fail(pid, title, f"OOM events this boot: {oom_count}",
               "dmesg | grep -i oom; reduce memory pressure or add swap")
    else:
        c.pass_(pid, title, "No OOM events this boot")


def phase_gpu(c: Collector) -> None:
    pid, title = P6
    amdgpu = "amdgpu" in _read("/proc/modules")
    if amdgpu:
        c.pass_(pid, title, "amdgpu kernel module loaded")
    elif _have("rocm-smi"):
        c.pass_(pid, title, "AMD GPU via ROCm (amdgpu may be built-in)")
    else:
        c.warn(pid, title, "amdgpu module not listed", _fix_script("verify", note="GPU driver check"))
    if _have("glxinfo"):
        gl = _run(["glxinfo", "-B"], timeout=10).stdout or ""
        renderer = next((l.split(":", 1)[1].strip() for l in gl.splitlines() if "OpenGL renderer" in l), "")
        if renderer:
            c.pass_(pid, title, f"OpenGL: {renderer[:80]}")
        else:
            c.warn(pid, title, "OpenGL renderer not detected", "glxinfo -B")
    elif _have("glxgears"):
        c.pass_(pid, title, "OpenGL tools present (glxgears)")
    else:
        c.warn(pid, title, "OpenGL not tested", _fix_script("audit_deps", note="installs mesa-utils"))
    if _have("vulkaninfo"):
        vk = _run(["vulkaninfo", "--summary"], timeout=15).stdout or ""
        if "GPU" in vk or "deviceName" in vk:
            c.pass_(pid, title, "Vulkan: available")
        else:
            c.warn(pid, title, "Vulkan: no devices reported", "vulkaninfo --summary")
    else:
        c.warn(pid, title, "Vulkan not tested", _fix_script("audit_deps", note="installs vulkan-tools"))
    if _have("clinfo"):
        cl = _run(["clinfo"], timeout=15).stdout or ""
        n = len(re.findall(r"Platform Name|Device Name", cl))
        c.pass_(pid, title, f"OpenCL: {n} platform/device entries") if n else c.warn(
            pid, title, "OpenCL: no platforms", _fix_script("audit_deps", note="installs clinfo"))
    elif _have("rocm-smi"):
        c.pass_(pid, title, "OpenCL/ROCm: rocm-smi available")
    try:
        from jarvis.gpu import detect_gpu, free_vram_mb
        gpu = detect_gpu()
        name = gpu.get("name") or "GPU"
        vram = gpu.get("vram_mb")
        free = free_vram_mb()
        c.pass_(pid, title, f"GPU: {name}")
        if vram:
            c.pass_(pid, title, f"VRAM: {free or '?'}MB free / {vram}MB total")
        temp_out = _run(["sensors"], timeout=10).stdout or ""
        for line in temp_out.splitlines():
            if "edge" in line.lower() or "junction" in line.lower():
                m = re.search(r"\+(\d+)", line)
                if m:
                    t = int(m.group(1))
                    if t >= 85:
                        c.warn(pid, title, f"GPU temperature: {t}°C", "check fans and workload")
                    else:
                        c.pass_(pid, title, f"GPU temperature: {t}°C")
                    break
    except Exception as exc:
        c.warn(pid, title, f"GPU detection: {exc}", _fix_script("verify"))
    if _have("nvidia-smi"):
        nv = _run(["nvidia-smi", "--query-gpu=name,temperature.gpu,memory.free,memory.total",
                   "--format=csv,noheader"], timeout=10).stdout.strip()
        if nv:
            c.pass_(pid, title, f"NVIDIA (AI): {nv}")
    if _dual_gpu():
        if nvidia_ai_hybrid_configured():
            c.pass_(pid, title, "Hybrid GPU: AMD display/desktop, Jarvis AI on NVIDIA")
        elif configured_gpu_preference() == "amd":
            c.warn(pid, title, "Dual GPU but JARVIS_GPU_PREFER=amd — AI will use AMD ROCm",
                   install_key="nvidia_gpu", fix="route Jarvis AI to NVIDIA")
        else:
            c.warn(pid, title, "Dual GPU — set NVIDIA-for-AI preset (HIP_VISIBLE_DEVICES=-1)",
                   install_key="nvidia_gpu", fix="AMD display + NVIDIA for Jarvis AI")


def phase_hardware(c: Collector) -> None:
    pid, title = P5
    if _have("sensors"):
        temps = _sensor_temps()
        if not temps:
            text = _run(["sensors"], timeout=10).stdout or ""
            for line in text.splitlines():
                m = re.search(r"^([^:]+):\s+\+(\d+)", line)
                if m:
                    temps.append((m.group(1).strip(), float(m.group(2))))
        if temps:
            hot = crit = 0
            for label, temp in sorted(temps, key=lambda x: -x[1])[:12]:
                short = label.split(".")[-1].replace("_input", "")
                if temp >= 90:
                    c.fail(pid, title, f"Critical temperature {temp:.0f}°C — {short}", "check fans, dust, thermal paste")
                    crit += 1
                elif temp >= 80:
                    c.warn(pid, title, f"High temperature {temp:.0f}°C — {short}", "sensors; reduce load or improve cooling")
                    hot += 1
                else:
                    c.pass_(pid, title, f"Temperature {temp:.0f}°C — {short}")
            if not hot and not crit and temps:
                c.pass_(pid, title, f"All {len(temps)} temperature sensor(s) below 80°C")
        else:
            c.warn(pid, title, "lm-sensors: no temperature readings", install_key="audit_deps", fix="install lm-sensors")
    else:
        c.warn(pid, title, "lm-sensors not installed", install_key="audit_deps", fix="installs lm-sensors")
    lspci = _run(["lspci"], timeout=10).stdout or ""
    if lspci:
        bridges = [l for l in lspci.splitlines() if re.search(r"VGA|Display|3D", l, re.I)]
        for line in bridges[:4]:
            c.pass_(pid, title, f"PCI: {line.split(': ', 1)[-1][:85]}")
    if _have("upower"):
        bat = _run(["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"], timeout=5).stdout or ""
        if "percentage" in bat.lower():
            pct = re.search(r"percentage:\s*(\d+)", bat)
            state = re.search(r"state:\s*(\S+)", bat)
            c.pass_(pid, title, f"Battery: {pct.group(1) if pct else '?'}% ({state.group(1) if state else 'unknown'})")
        else:
            c.pass_(pid, title, "Battery: desktop / no battery reported")
    usb = len([l for l in (_run(["lsusb"], timeout=10).stdout or "").splitlines() if l.strip()])
    if usb:
        c.pass_(pid, title, f"USB devices: {usb}")
    entropy = _read("/proc/sys/kernel/random/entropy_avail").strip()
    if entropy.isdigit():
        e = int(entropy)
        if e < 500:
            c.warn(pid, title, f"Low entropy: {e}", "check rng-tools / haveged if crypto hangs")
        else:
            c.pass_(pid, title, f"Entropy pool: {e}")


def phase_services(c: Collector) -> None:
    pid, title = P7
    for label, unit in (
        ("NetworkManager", "NetworkManager.service"),
        ("systemd-resolved", "systemd-resolved.service"),
        ("D-Bus", "dbus.service"),
        ("display-manager", "display-manager.service"),
    ):
        st = _service_state(unit)
        if st == "active":
            c.pass_(pid, title, f"{label}: active")
        elif st in ("inactive", "failed"):
            c.warn(pid, title, f"{label}: {st}", f"systemctl status {unit}")
        else:
            c.pass_(pid, title, f"{label}: {st or 'not installed'}")
    pw = _run(["systemctl", "--user", "is-active", "pipewire"], timeout=5).stdout.strip()
    if pw == "active":
        c.pass_(pid, title, "PipeWire (user): active")
    elif pw:
        c.warn(pid, title, f"PipeWire (user): {pw}", "systemctl --user start pipewire pipewire-pulse")
    else:
        pulse = _service_state("pulseaudio.service")
        if pulse == "active":
            c.pass_(pid, title, "PulseAudio: active")
        else:
            c.pass_(pid, title, "Audio stack: not detected (optional)")
    if _have("bluetoothctl"):
        bt = _run(["bluetoothctl", "show"], timeout=8).stdout or ""
        if "Powered: yes" in bt:
            c.pass_(pid, title, "Bluetooth: powered on")
        elif "Powered: no" in bt:
            c.pass_(pid, title, "Bluetooth: adapter present (off)")
        else:
            c.pass_(pid, title, "Bluetooth: checked")
    cups = _service_state("cups.service")
    if cups == "active":
        c.pass_(pid, title, "CUPS printing: active")
    else:
        c.pass_(pid, title, f"Printing (CUPS): {cups or 'not installed'}")
    session = os.environ.get("XDG_SESSION_TYPE") or read_env_file_var("XDG_SESSION_TYPE")
    if session:
        c.pass_(pid, title, f"Session type: {session}")
    timers = _run(["systemctl", "list-timers", "--no-pager", "--no-legend"], timeout=10).stdout or ""
    n_timers = len([l for l in timers.splitlines() if l.strip()])
    c.pass_(pid, title, f"systemd timers: {n_timers} active")


def phase_containers(c: Collector) -> None:
    pid, title = P8
    if _have("docker") and _run(["docker", "info"], timeout=15).returncode == 0:
        n = len((_run(["docker", "ps", "-q"], timeout=10).stdout or "").splitlines())
        c.pass_(pid, title, f"Docker running — {n} container(s)", scope="jarvis")
        names = (_run(["docker", "ps", "--format", "{{.Names}}"], timeout=10).stdout or "").strip()
        if names:
            sample = ", ".join(names.splitlines()[:8])
            if len(names.splitlines()) > 8:
                sample += f" (+{len(names.splitlines()) - 8} more)"
            c.pass_(pid, title, f"Containers: {sample}", scope="jarvis")
    else:
        c.warn(pid, title, "Docker not running", install_key="docker", scope="jarvis")
    mongo_ok = False
    if _have("mongosh"):
        p = _run(["mongosh", "--quiet", "--eval", "db.runCommand({ping:1}).ok"], timeout=10)
        mongo_ok = "1" in (p.stdout or "")
    if mongo_ok:
        c.pass_(pid, title, "MongoDB: responding to ping", scope="jarvis")
    else:
        c.warn(pid, title, "MongoDB not reachable",
               _fix_script("docker", note="or start existing Docker mongo stack"), scope="jarvis")
    if _have("ollama"):
        ver = _run(["ollama", "--version"], timeout=5).stdout.strip()
        c.pass_(pid, title, f"Ollama: {ver or 'installed'}", scope="jarvis")
        try:
            import urllib.request
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as resp:
                tags = json.loads(resp.read().decode())
            models = tags.get("models") or []
            c.pass_(pid, title, f"Ollama API — {len(models)} model(s)", scope="jarvis")
        except Exception:
            c.warn(pid, title, "Ollama API not reachable on :11434",
                   "systemctl --user start ollama  # or: ollama serve", scope="jarvis")
    else:
        c.warn(pid, title, "Ollama not installed", install_key="ollama", scope="jarvis")


def phase_dev(c: Collector) -> None:
    pid, title = P9
    tools = {
        "git": ["git", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "cargo": ["cargo", "--version"],
        "rustc": ["rustc", "--version"],
        "gcc": ["gcc", "--version"],
        "cmake": ["cmake", "--version"],
        "make": ["make", "--version"],
        "java": ["java", "-version"],
    }
    for name, cmd in tools.items():
        tool = _tool_cmd(cmd[0])
        if not tool:
            if name in ("cargo", "rustc"):
                c.warn(pid, title, f"{name}: not installed", f"install {name} via rustup",
                       install_key="rust")
            else:
                key = "dependencies" if name == "git" else "dev_tools"
                c.warn(pid, title, f"{name}: not installed", f"installs {name}", install_key=key)
            continue
        out = _run([tool, *cmd[1:]], timeout=10)
        line = (out.stdout or out.stderr or "").splitlines()[0][:100] if (out.stdout or out.stderr) else name
        c.pass_(pid, title, f"{name}: {line}")
    cuda_paths = list(Path("/usr/local").glob("cuda*/version.json")) + list(Path("/opt/rocm").glob("**/version"))
    if Path("/usr/local/cuda").exists() or _have("nvcc"):
        nvcc = _run(["nvcc", "--version"], timeout=10).stdout.splitlines()
        c.pass_(pid, title, f"CUDA: {(nvcc[-1] if nvcc else 'present')[:80]}")
    elif _have("nvidia-smi"):
        c.pass_(pid, title, "NVIDIA driver present (CUDA toolkit optional for Jarvis AI)")
    elif Path("/opt/rocm").exists() or _have("rocm-smi"):
        c.pass_(pid, title, "ROCm: /opt/rocm present (AMD display/compute)")
    elif _dual_gpu():
        c.pass_(pid, title, "Dual GPU: AMD + NVIDIA drivers detected")
    else:
        key = _pytorch_install_key()
        c.warn(pid, title, "CUDA/OpenCL: drivers not detected", install_key=key, fix="install GPU stack")


def _integrity_fix(label: str, sample: str) -> str:
    """Actionable next steps for kernel integrity warnings (not just log browsing)."""
    low = sample.lower()
    fixes = {
        "disk errors": (
            "Backup data now; check cables/port; run: sudo smartctl -a /dev/nvme0n1; "
            "sudo fsck -n /dev/<partition>  # after unmount"
        ),
        "GPU hangs": (
            "Update GPU drivers; check thermals (sensors); if NVIDIA: dmesg | grep -i NVRM; "
            "if AMD: journalctl -k -b -g amdgpu | tail -20"
        ),
        "kernel panics": (
            "Serious — note what you were doing; update kernel/drivers; "
            "check RAM (memtest); journalctl -k -b -g panic | tail -30"
        ),
        "ext4 errors": (
            "Backup; boot live USB or single-user; sudo fsck -f /dev/<root-partition>"
        ),
        "nvme errors": (
            "Backup immediately; sudo smartctl -a /dev/nvme0n1; plan drive replacement if SMART fails"
        ),
        "SATA errors": (
            "Reseat SATA/power cable; try another port; sudo smartctl -a /dev/sdX"
        ),
        "memory errors": (
            "Hardware RAM issue likely — run memtest; reseat RAM sticks; check EDAC logs"
        ),
    }
    base = fixes.get(label, "Inspect: journalctl -k -b --no-pager | less")
    if "xid" in low or "nvrm" in low:
        return "NVIDIA driver reset — update drivers or reduce GPU load; " + base
    if "amdgpu" in low:
        return "AMD GPU reset — check temps and amdgpu driver; " + base
    return base


def phase_integrity(c: Collector) -> None:
    pid, title = P10
    patterns = [
        ("disk errors", r"I/O error|Buffer I/O error|blk_update_request"),
        ("GPU hangs", r"amdgpu.*reset|GPU hang|NVRM.*Xid"),
        ("kernel panics", r"Kernel panic|BUG:|Oops:"),
        ("ext4 errors", r"ext4.*error|EXT4-fs error"),
        ("nvme errors", r"nvme.*failed|nvme.*error"),
        ("SATA errors", r"ATA.*error|SATA.*error"),
        ("memory errors", r"EDAC|Machine check|hardware error"),
    ]
    found_any = False
    for label, pat in patterns:
        proc = _run(
            ["journalctl", "-k", "-b", "--no-pager", "-g", pat.split("|")[0].split()[0]],
            timeout=20,
        )
        lines = [l for l in (proc.stdout or "").splitlines() if l.strip() and not l.startswith("--")]
        hits = [l for l in lines if re.search(pat, l, re.I)]
        if hits:
            found_any = True
            sample = hits[-1].strip()[:140]
            c.warn(pid, title, f"{label}: {len(hits)} hit(s) — {sample}",
                   _integrity_fix(label, sample))
        else:
            c.pass_(pid, title, f"No {label} this boot")
    failed = _run(["systemctl", "--failed", "--no-legend", "--no-pager"], timeout=10).stdout or ""
    units: list[str] = []
    for ln in failed.splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[1].endswith(".service"):
            units.append(parts[1])
    for unit in units:
        msg, fix = _diagnose_unit(unit)
        if "mongod" in unit and _have("mongosh"):
            p = _run(["mongosh", "--quiet", "--eval", "db.runCommand({ping:1}).ok"], timeout=10)
            if "1" in (p.stdout or ""):
                c.warn(pid, title, msg, fix)
                continue
        c.fail(pid, title, msg, fix)
    if not units:
        c.pass_(pid, title, "No failed systemd units")


def phase_perf(c: Collector) -> None:
    pid, title = P11
    load = _read("/proc/loadavg").split()
    ncpu = os.cpu_count() or 1
    if load:
        c.pass_(pid, title, f"Load: {load[0]} / {load[1]} / {load[2]} ({ncpu} CPUs)")
        try:
            if float(load[0]) > ncpu * 2:
                c.warn(pid, title, "High CPU load", "ps aux --sort=-%cpu | head -15")
        except ValueError:
            pass
    mem_avail = _read("/proc/meminfo")
    c.pass_(pid, title, "Memory pressure: see Phase 4")
    if _have("iostat"):
        io = _run(["iostat", "-x", "1", "2"], timeout=15).stdout or ""
        if io:
            c.pass_(pid, title, "I/O stats collected (iostat)")
    else:
        c.pass_(pid, title, "I/O: iostat not installed (optional)")
    top_cpu = _run(["bash", "-c", "ps aux --sort=-%cpu | head -4 | tail -3"], timeout=10).stdout or ""
    if top_cpu.strip():
        for line in top_cpu.strip().splitlines()[:3]:
            parts = line.split(None, 10)
            if len(parts) >= 11:
                c.pass_(pid, title, f"Top CPU: {parts[10][:50]} ({parts[2]}%)")
    top_ram = _run(["bash", "-c", "ps aux --sort=-%mem | head -4 | tail -3"], timeout=10).stdout or ""
    if top_ram.strip():
        for line in top_ram.strip().splitlines()[:3]:
            parts = line.split(None, 10)
            if len(parts) >= 11:
                c.pass_(pid, title, f"Top RAM: {parts[10][:50]} ({parts[3]}%)")
    trim = _run(["systemctl", "is-enabled", "fstrim.timer"], timeout=5).stdout.strip()
    if trim == "enabled":
        c.pass_(pid, title, "SSD TRIM: fstrim.timer enabled")
    else:
        c.warn(pid, title, "SSD TRIM timer not enabled", "sudo systemctl enable --now fstrim.timer")
    sched = _read("/sys/block/sda/queue/scheduler") or _read("/sys/block/nvme0n1/queue/scheduler")
    if sched:
        active = re.search(r"\[(\w+)\]", sched)
        c.pass_(pid, title, f"I/O scheduler: {active.group(1) if active else sched.strip()}")


def phase_security(c: Collector) -> None:
    pid, title = P12
    ufw = _run(["ufw", "status"], timeout=10).stdout or ""
    if "active" in ufw.lower():
        c.pass_(pid, title, "Firewall: ufw active")
    else:
        c.warn(pid, title, "Firewall: ufw not active",
               "sudo ufw enable  # or ensure router does not port-forward services")
    if _have("mokutil"):
        sb = _run(["mokutil", "--sb-state"], timeout=5).stdout.strip()
        c.pass_(pid, title, f"Secure Boot: {sb or 'unknown'}")
    else:
        c.pass_(pid, title, "Secure Boot: mokutil not installed")
    if _have("aa-status"):
        aa = _run(["aa-status", "--enabled"], timeout=10)
        c.pass_(pid, title, "AppArmor: enabled" if aa.returncode == 0 else "AppArmor: disabled or partial")
    else:
        c.pass_(pid, title, "AppArmor: not checked")
    failed_logins = _run(
        ["journalctl", "-b", "--no-pager", "-g", "Failed password|authentication failure"],
        timeout=15,
    ).stdout or ""
    n_fail = len([l for l in failed_logins.splitlines() if l.strip() and not l.startswith("--")])
    if n_fail > 10:
        c.warn(pid, title, f"Failed login attempts this boot: {n_fail}", "journalctl -b -g 'Failed password'")
    else:
        c.pass_(pid, title, f"Failed logins this boot: {n_fail}")
    listeners = _run(["ss", "-tln"], timeout=10).stdout or ""
    public = [l for l in listeners.splitlines() if re.search(r"0\.0\.0\.0:|^\s*LISTEN.*\*:", l)]
    sensitive = [l for l in public if re.search(r":22 |:8765 |:11434 |:27017 ", l)]
    if sensitive:
        for line in sensitive[:5]:
            c.warn(pid, title, f"Open port: {line.strip()[-30:]}",
                   _fix_script("harden"))
    else:
        c.pass_(pid, title, "No sensitive ports on 0.0.0.0")
    ssh = _run(["systemctl", "is-active", "ssh"], timeout=5).stdout.strip()
    if ssh == "active":
        c.pass_(pid, title, "SSH service: active")
    elif ssh == "inactive":
        c.pass_(pid, title, "SSH service: inactive")
    else:
        c.pass_(pid, title, f"SSH: {ssh or 'not installed'}")


def phase_network(c: Collector) -> None:
    pid, title = P13
    iface = _run(["bash", "-c", "ip route show default | awk '{print $5}' | head -1"], timeout=5).stdout.strip()
    gw = _run(["bash", "-c", "ip route show default | awk '{print $3}' | head -1"], timeout=5).stdout.strip()
    if iface:
        state = _run(["cat", f"/sys/class/net/{iface}/operstate"], timeout=5).stdout.strip()
        c.pass_(pid, title, f"Default route: {iface} ({state}, gateway {gw or 'none'})")
        if gw and _run(["ping", "-c", "1", "-W", "2", gw], timeout=5).returncode == 0:
            c.pass_(pid, title, f"Gateway {gw} reachable")
    else:
        c.fail(pid, title, "No default route", "ip route; sudo systemctl restart NetworkManager")
    links = _run(["ip", "-br", "link"], timeout=10).stdout or ""
    for line in links.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) >= 2 and parts[0] != "lo":
            c.pass_(pid, title, f"Interface {parts[0]}: {parts[1]}")
    if _have("resolvectl"):
        dns = _run(["resolvectl", "status"], timeout=10).stdout or ""
        servers = re.findall(r"DNS Servers?:\s*([0-9a-f.:]+)", dns)
        if servers:
            c.pass_(pid, title, f"DNS servers: {', '.join(servers[:3])}")
    if _have("nmcli"):
        wifi = _run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"], timeout=10).stdout or ""
        active = [l for l in wifi.splitlines() if l.startswith("yes:")]
        if active:
            c.pass_(pid, title, f"WiFi: {active[0].replace('yes:', '')[:60]}")
    if _run(["getent", "hosts", "one.one.one.one"], timeout=5).returncode == 0:
        c.pass_(pid, title, "DNS resolution: OK")
    else:
        c.fail(pid, title, "DNS resolution failed", "resolvectl status")
    if _run(["ping", "-c", "1", "-W", "3", "1.1.1.1"], timeout=8).returncode == 0:
        c.pass_(pid, title, "Internet connectivity: OK")
    else:
        c.warn(pid, title, "Internet check failed", "ping -c 3 1.1.1.1")
    if _run(["ip", "link", "show", "docker0"], timeout=5).returncode == 0:
        c.pass_(pid, title, "Docker bridge: docker0 present")
    else:
        c.pass_(pid, title, "Docker bridge: not present (optional)")
    c.pass_(pid, title, f"Hostname: {socket.gethostname()}")


def phase_jarvis(c: Collector) -> None:
    pid, title = P14
    py = _run(["python3", "--version"], timeout=5).stdout.strip()
    if py:
        c.pass_(pid, title, f"System Python: {py}", scope="jarvis")
    venv = resolve_venv_python()
    if venv:
        c.pass_(pid, title, f"Jarvis venv: {(_run([str(venv), '--version'], timeout=5).stdout or '').strip()} ({venv})", scope="jarvis")
        pip = venv.parent / "pip"
        if pip.is_file():
            outdated = _run([str(pip), "list", "--outdated"], timeout=60).stdout or ""
            n = max(0, len(outdated.splitlines()) - 2)
            c.pass_(pid, title, f"pip: {n} optional upgrade(s)", scope="jarvis")
        jenv = _audit_env()
        root = str(jarvis_root())
        jenv["PYTHONPATH"] = root if not jenv.get("PYTHONPATH") else f"{root}{os.pathsep}{jenv['PYTHONPATH']}"
        try:
            subprocess.run(
                [str(venv), "-c", "import jarvis"],
                capture_output=True,
                timeout=10,
                check=True,
                env=jenv,
            )
            c.pass_(pid, title, "Jarvis package importable", scope="jarvis")
        except Exception:
            c.fail(pid, title, "Jarvis import failed", install_key="dependencies", scope="jarvis")
        try:
            proc = subprocess.run(
                [str(venv), "-c", "import torch; print(torch.__version__); print(torch.cuda.is_available())"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
                env=jenv,
            )
            lines = (proc.stdout or "").strip().splitlines()
            ver = lines[0] if lines else "?"
            cuda_ok = len(lines) > 1 and lines[1].strip().lower() == "true"
            build = "ROCm" if "+rocm" in ver or "hip" in ver.lower() else "CUDA" if "+cu" in ver else "CPU"
            c.pass_(pid, title, f"PyTorch {ver} ({build}, device: {cuda_ok})", scope="jarvis")
            if _dual_gpu() and nvidia_ai_hybrid_configured():
                if "+cu" in ver and cuda_ok:
                    c.pass_(pid, title, "PyTorch CUDA — correct for NVIDIA AI / AMD display", scope="jarvis")
                elif "+rocm" in ver:
                    c.warn(pid, title, "PyTorch ROCm build — wrong for NVIDIA AI preset",
                           install_key="cuda_pytorch", fix="install CUDA PyTorch", scope="jarvis")
                elif not cuda_ok:
                    c.warn(pid, title, "PyTorch CUDA not available",
                           install_key="cuda_pytorch", fix="reinstall CUDA PyTorch", scope="jarvis")
        except Exception as exc:
            key = _pytorch_install_key()
            c.warn(pid, title, f"PyTorch — {exc}", install_key=key, fix="install PyTorch in venv", scope="jarvis")
    else:
        c.warn(pid, title, "Jarvis venv missing", install_key="dependencies", scope="jarvis")
    try:
        from jarvis.gpu_routing import routing_status
        routing = routing_status()
        c.pass_(pid, title,
                f"GPU routing: torch={routing.get('resolved_torch_device')} whisper={routing.get('resolved_whisper_device')}",
                scope="jarvis")
    except Exception:
        pass
    ollama_models = _run(["ollama", "list"], timeout=15).stdout or ""
    model_lines = [l for l in ollama_models.splitlines() if l.strip() and not l.lower().startswith("name")]
    if model_lines:
        c.pass_(pid, title, f"Ollama models loaded: {len(model_lines)}", scope="jarvis")
    data_dirs = [DATA_DIR / "knowledge", DATA_DIR / "documents", jarvis_root() / "data"]
    for d in data_dirs:
        if d.is_dir():
            c.pass_(pid, title, f"Jarvis data path: {d}", scope="jarvis")
            break
    try:
        from jarvis.gpu import detect_gpu, free_vram_mb
        gpu = detect_gpu()
        free = free_vram_mb()
        c.pass_(pid, title, f"AI VRAM: {free}MB free / {gpu.get('vram_mb', '?')}MB total", scope="jarvis")
    except Exception:
        c.warn(pid, title, "VRAM — could not query", _fix_script("verify"), scope="jarvis")


def run_engine(
    *,
    sudo_smart: bool = False,
    progress: Callable[[int, int, str, str], None] | None = None,
) -> dict[str, Any]:
    """Run all audit phases. Optional progress(phase_num, total, phase_id, title)."""
    c = Collector()
    steps: list[tuple[tuple[str, str], Callable[[], None]]] = [
        (P1, lambda: phase_os(c)),
        (P2, lambda: phase_packages(c)),
        (P3, lambda: phase_storage(c, sudo_smart=sudo_smart)),
        (P4, lambda: phase_memory(c)),
        (P5, lambda: phase_hardware(c)),
        (P6, lambda: phase_gpu(c)),
        (P7, lambda: phase_services(c)),
        (P8, lambda: phase_containers(c)),
        (P9, lambda: phase_dev(c)),
        (P10, lambda: phase_integrity(c)),
        (P11, lambda: phase_perf(c)),
        (P12, lambda: phase_security(c)),
        (P13, lambda: phase_network(c)),
        (P14, lambda: phase_jarvis(c)),
    ]
    total = len(steps)
    for i, ((pid, title), run) in enumerate(steps, 1):
        if progress:
            progress(i, total, pid, title)
        run()
    if progress:
        progress(total + 1, total, "done", "Finalizing report")
    return c.to_report(sudo_smart=sudo_smart)


def main() -> None:
    import sys
    sudo_smart = os.geteuid() == 0 or _run(["sudo", "-n", "true"], timeout=5).returncode == 0
    report = run_engine(sudo_smart=sudo_smart)
    print(json.dumps(report, indent=2))
    sys.exit(1 if report["result"] == "fail" else 0)


if __name__ == "__main__":
    main()
