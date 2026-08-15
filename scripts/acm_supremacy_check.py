#!/usr/bin/env python3
"""M4 supremacy CI gates — ACM sole cognitive SoT (INTEGRATION_TEST_PLAN M4-01..03)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _fail(msg: str) -> None:
    print(f" FAIL {msg}", file=sys.stderr)


def check_primary_default() -> bool:
    text = (ROOT / "aria_core/acm_bridge.py").read_text(encoding="utf-8")
    if '_env_bool("ARIA_ACM_PRIMARY", "1")' not in text:
        _fail('PRIMARY default must be _env_bool("ARIA_ACM_PRIMARY", "1") after M4')
        return False
    if '_env_bool("ARIA_ACM_LEGACY_READ_FALLBACK", "0")' not in text:
        _fail("LEGACY_READ_FALLBACK default must be off after M4")
        return False
    _ok("PRIMARY default on; legacy read fallback default off (source)")
    return True


def check_dualwrite_disabled() -> bool:
    sys.path.insert(0, str(ROOT))
    adapter = ROOT / "jarvis/modules/memory_adapter_store.py"
    if adapter.exists():
        _fail("DualWrite memory_adapter_store.py must stay deleted")
        return False
    memory_py = (ROOT / "jarvis/modules/memory.py").read_text(encoding="utf-8")
    if "jarvis.modules.memory_adapter_store" in memory_py or "wrap_memory_store(" in memory_py:
        _fail("MemoryStore factory must not import DualWrite wrapper")
        return False
    _ok("DualWrite adapter deleted; memory factory is direct")
    return True


def check_forbid_patterns() -> bool:
    bridge = (ROOT / "aria_core/acm_bridge.py").read_text(encoding="utf-8")
    if 'return _env_bool("ARIA_ACM_PRIMARY", "0")' in bridge:
        _fail("PRIMARY default still off — M4 requires default on")
        return False
    if "redirect_legacy_write_to_acm" not in bridge:
        _fail("Missing redirect_legacy_write_to_acm (M4 bypass closure)")
        return False
    cutover = (ROOT / "jarvis/platform_cutover.py").read_text(encoding="utf-8")
    if '"dual_write"' in cutover or "dual-read verification" in cutover:
        _fail("platform_cutover must not present dual_write as cognitive cutover")
        return False
    _ok("Forbid patterns / ACM authority markers present")
    return True


def main() -> int:
    print("aria-acm-supremacy (M4)")
    checks = (
        check_primary_default,
        check_dualwrite_disabled,
        check_forbid_patterns,
    )
    ok = True
    for fn in checks:
        try:
            ok = fn() and ok
        except Exception as exp:
            _fail(f"{fn.__name__}: {type(exp).__name__}: {exp}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
