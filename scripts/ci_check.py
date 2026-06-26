#!/usr/bin/env python3
"""CI gates for ARIA during decompile recovery.

Skips syntax-broken modules (invalid decompiler output) and lints only
maintained paths until the tree is fully recovered.
"""

from __future__ import annotations

import argparse
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Paths known good after recovery work; expand as modules are repaired.
RUFF_PATHS: tuple[str, ...] = (
    "jarvis/async_util.py",
    "jarvis/gpu_routing.py",
    "jarvis/torch_device.py",
    "jarvis/env_loader.py",
    "jarvis/gpu.py",
    "jarvis/memgraph_docker.py",
    "jarvis/model_pull.py",
    "jarvis/daemon.py",
    "jarvis/extensibility",
    "jarvis/extensions/__init__.py",
    "jarvis/extensions/memory/extension.py",
    "jarvis/extensions/memory/handlers.py",
    "jarvis/extensions/memory/routes.py",
    "jarvis/extensions/git",
    "jarvis/extensions/journal/extension.py",
    "jarvis/extensions/journal/handlers.py",
    "jarvis/extensions/voice/extension.py",
    "jarvis/extensions/voice/handlers.py",
    "jarvis/extensions/security/extension.py",
    "jarvis/extensions/security/handlers.py",
    "jarvis/handlers/__init__.py",
    "jarvis/modules/vector_store.py",
    "tests/test_async_util.py",
    "tests/test_gpu_routing.py",
)

PYTEST_PATHS: tuple[str, ...] = (
    "tests/test_async_util.py",
    "tests/test_gpu_routing.py",
)


def _resolve(path: str) -> Path:
    return ROOT / path


def _compilable(path: Path) -> bool:
    if path.is_dir():
        return all(_compilable(p) for p in path.rglob("*.py"))
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except py_compile.PyCompileError:
        return False


def _expand_ruff_targets() -> list[Path]:
    targets: list[Path] = []
    for rel in RUFF_PATHS:
        path = _resolve(rel)
        if not path.exists():
            raise SystemExit(f"CI ruff path missing: {rel}")
        if path.is_dir():
            targets.extend(sorted(path.rglob("*.py")))
        else:
            targets.append(path)
    missing = [p for p in targets if not _compilable(p)]
    if missing:
        lines = "\n".join(f"  - {p.relative_to(ROOT)}" for p in missing)
        raise SystemExit(f"CI ruff target has syntax errors:\n{lines}")
    return targets


def run_ruff() -> int:
    targets = _expand_ruff_targets()
    cmd = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--config",
        str(ROOT / "ruff.toml"),
        *[str(p) for p in targets],
    ]
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


def run_pytest() -> int:
    for rel in PYTEST_PATHS:
        path = _resolve(rel)
        if not path.is_file() or not _compilable(path):
            raise SystemExit(f"CI pytest path not compilable: {rel}")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *PYTEST_PATHS,
        "-q",
        "--tb=short",
        "-m",
        "not network",
    ]
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="ARIA CI recovery gates")
    parser.add_argument("command", choices=("ruff", "pytest", "all"))
    args = parser.parse_args()
    if args.command == "ruff":
        return run_ruff()
    if args.command == "pytest":
        return run_pytest()
    code = run_ruff()
    if code != 0:
        return code
    return run_pytest()


if __name__ == "__main__":
    raise SystemExit(main())
