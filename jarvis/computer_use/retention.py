"""Browser artifact retention.

Earlier milestones showed the browser leaves two growing footprints under
DATA_DIR: a Playwright profile (thousands of cache files) and a screenshot
directory that grows one file per navigation, with nothing pruning either.

The profile is the browser's own working state and is left alone. Screenshots
are ARIA's artifacts, so they get a bounded retention policy: keep the newest N
and anything under the age floor, prune the rest. Pruning is opt-in per call and
never touches anything outside the screenshot directory.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.computer_use.retention")

MAX_SCREENSHOTS = 200
MIN_AGE_S = 3600.0  # never prune something a running task may still reference


def screenshot_dir() -> Path:
    from jarvis.browser_product.screenshots import SHOT_DIR

    return Path(SHOT_DIR)


def usage() -> dict[str, Any]:
    """Inspect the artifact footprint without changing anything."""
    shots = screenshot_dir()
    files = sorted(shots.glob("*.png"), key=lambda p: p.stat().st_mtime) if shots.is_dir() else []
    total = sum(f.stat().st_size for f in files)

    profile_files = 0
    profile_bytes = 0
    try:
        from jarvis.browser_product.session import profile_dir

        root = Path(profile_dir())
        if root.is_dir():
            for p in root.rglob("*"):
                if p.is_file():
                    profile_files += 1
                    profile_bytes += p.stat().st_size
    except Exception:  # noqa: BLE001 - inspection must never fail a task
        pass

    return {
        "screenshot_dir": str(shots),
        "screenshots": len(files),
        "screenshot_bytes": total,
        "screenshot_limit": MAX_SCREENSHOTS,
        "over_limit": max(0, len(files) - MAX_SCREENSHOTS),
        "profile_files": profile_files,
        "profile_bytes": profile_bytes,
    }


def prune_screenshots(
    *, keep: int = MAX_SCREENSHOTS, min_age_s: float = MIN_AGE_S
) -> dict[str, Any]:
    """Bound screenshot growth. Only ever deletes *.png inside the screenshot dir."""
    shots = screenshot_dir()
    if not shots.is_dir():
        return {"pruned": 0, "kept": 0, "bytes_freed": 0}
    files = sorted(shots.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    now = time.time()
    pruned = 0
    freed = 0
    for path in files[keep:]:
        try:
            if now - path.stat().st_mtime < min_age_s:
                continue  # too recent to be safely reclaimed
            size = path.stat().st_size
            # Guard: never step outside the screenshot directory.
            if path.parent.resolve() != shots.resolve():
                continue
            path.unlink()
            pruned += 1
            freed += size
        except OSError:
            continue
    return {"pruned": pruned, "kept": min(len(files), keep), "bytes_freed": freed}
