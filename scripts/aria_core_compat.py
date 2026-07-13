#!/usr/bin/env python3
"""Aria Core behavioral compatibility harness (Phase 1).

Validates:
1. Behavioral contract completeness vs inventory rules
2. Learning Governor passthrough parity
3. Critical unit tests for standard + uncensored profiles
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "aria_core" / "BEHAVIORAL_CONTRACT.json"
INVENTORY = ROOT / "docs" / "aria_core" / "CAPABILITY_INVENTORY.md"

REQUIRED_FIELDS = (
    "id",
    "layer",
    "name",
    "user_visible_behavior",
    "expected_inputs",
    "expected_outputs",
    "external_apis",
    "cli_behavior",
    "gui_behavior",
    "runtime_behavior",
    "failure_behavior",
    "recovery_behavior",
    "existing_regression_tests",
    "smoke_coverage",
    "owner",
    "jeff_would_notice",
    "protected",
)

# Critical automated checks safe on CI runners (no GPU/Docker required).
CRITICAL_PYTEST = (
    "tests/test_learning_governor.py",
    "tests/test_aria_core_contract.py",
    "tests/test_nlu_routing.py",
    "tests/test_routing_regression.py",
    "tests/test_uncensored_auth.py",
    "tests/test_platform_cutover.py",
    "tests/test_memory_adapter.py",
    "tests/test_workstation.py",
    "tests/test_mission_control.py",
)


def _load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def check_contract() -> list[str]:
    errors: list[str] = []
    if not CONTRACT.is_file():
        return [f"missing contract: {CONTRACT}"]
    if not INVENTORY.is_file():
        errors.append(f"missing inventory: {INVENTORY}")
    data = _load_contract()
    caps = data.get("capabilities") or []
    if len(caps) < 90:
        errors.append(f"contract too small: {len(caps)} capabilities")
    ids: set[str] = set()
    for cap in caps:
        cid = cap.get("id")
        if not cid:
            errors.append("capability missing id")
            continue
        if cid in ids:
            errors.append(f"duplicate id: {cid}")
        ids.add(cid)
        for field in REQUIRED_FIELDS:
            if field not in cap:
                errors.append(f"{cid}: missing field {field}")
        if cap.get("protected") and not (
            cap.get("existing_regression_tests") or cap.get("smoke_coverage")
        ):
            errors.append(f"{cid}: protected capability lacks tests/smoke")
        # Inventory must mention protected ids
        if INVENTORY.is_file() and cap.get("protected"):
            text = INVENTORY.read_text(encoding="utf-8")
            if f"`{cid}`" not in text:
                errors.append(f"{cid}: missing from inventory markdown")
    profiles = data.get("profiles") or []
    if "standard" not in profiles or "uncensored" not in profiles:
        errors.append("contract profiles must include standard and uncensored")
    return errors


def check_governor_passthrough() -> list[str]:
    errors: list[str] = []
    sys.path.insert(0, str(ROOT))
    os.environ.pop("ARIA_LEARNING_GOVERNOR", None)
    from jarvis.learning_governor import commit, enabled, propose

    if not enabled():
        errors.append("governor should default enabled")
    marker = {"n": 0}

    def apply():
        marker["n"] += 1
        return {"ok": True, "n": marker["n"]}

    out = commit(propose(kind="harness", payload={"x": 1}), apply)
    if out != {"ok": True, "n": 1} or marker["n"] != 1:
        errors.append("passthrough commit did not apply exactly once")

    os.environ["ARIA_LEARNING_GOVERNOR"] = "0"
    from importlib import reload

    import jarvis.learning_governor as lg

    reload(lg)
    if lg.enabled():
        errors.append("ARIA_LEARNING_GOVERNOR=0 should disable")
    out2 = lg.commit(lg.propose(kind="harness"), apply)
    if out2["n"] != 2:
        errors.append("disabled governor should still apply writer")
    os.environ.pop("ARIA_LEARNING_GOVERNOR", None)
    reload(lg)
    return errors


def run_pytest(profile: str) -> int:
    env = os.environ.copy()
    env["JARVIS_NLU_SKIP_BENCHMARK"] = "1"
    if profile == "uncensored":
        env["JARVIS_UNCENSORED"] = "1"
    else:
        env.pop("JARVIS_UNCENSORED", None)
    paths = [str(ROOT / p) for p in CRITICAL_PYTEST if (ROOT / p).exists()]
    if not paths:
        print("No pytest paths found", file=sys.stderr)
        return 1
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=line", *paths]
    print(f"== pytest profile={profile} ==")
    return subprocess.run(cmd, cwd=ROOT, env=env, check=False).returncode


def main() -> int:
    errors = check_contract() + check_governor_passthrough()
    if errors:
        print("CONTRACT/GOVERNOR FAILURES:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"Contract OK ({_load_contract()['capability_count']} capabilities)")
    print("Governor passthrough OK")
    rc = 0
    for profile in ("standard", "uncensored"):
        code = run_pytest(profile)
        if code != 0:
            rc = code
            print(f"FAIL profile={profile}")
        else:
            print(f"PASS profile={profile}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
