#!/usr/bin/env python3
"""M4 supremacy CI gates — ACM sole cognitive SoT (INTEGRATION_TEST_PLAN M4-01..03)."""

from __future__ import annotations

import os
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
    os.environ.pop("JARVIS_ALLOW_DUALWRITE_LEGACY", None)
    from jarvis.modules.memory_adapter_store import (
        memory_adapter_enabled,
        platform_data_authoritative,
        wrap_memory_store,
    )

    if memory_adapter_enabled():
        _fail("DualWrite memory_adapter_enabled must be False (M4b)")
        return False
    if platform_data_authoritative():
        _fail("platform_data_authoritative must be False when DualWrite retired")
        return False

    class _S:
        pass

    s = _S()
    if wrap_memory_store(s) is not s:
        _fail("wrap_memory_store must be identity when DualWrite disabled")
        return False
    _ok("DualWrite cognitive path disabled")
    return True


def check_forbid_patterns() -> bool:
    adapter = (ROOT / "jarvis/modules/memory_adapter_store.py").read_text(encoding="utf-8")
    if "M4b" not in adapter and "RETIRED" not in adapter:
        _fail("memory_adapter_store.py missing M4 retirement markers")
        return False
    bridge = (ROOT / "aria_core/acm_bridge.py").read_text(encoding="utf-8")
    if 'return _env_bool("ARIA_ACM_PRIMARY", "0")' in bridge:
        _fail("PRIMARY default still off — M4 requires default on")
        return False
    if "redirect_legacy_write_to_acm" not in bridge:
        _fail("Missing redirect_legacy_write_to_acm (M4 bypass closure)")
        return False
    _ok("Forbid patterns / retirement markers present")
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
