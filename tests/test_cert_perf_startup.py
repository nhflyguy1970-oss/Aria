"""Performance certification: boot must not wait on a dashboard.

Establishing the platform connection costs ~0.1s. The Mission Control snapshot
behind it is a full dashboard aggregation — it shells out to the GitHub CLI for
CI status and rebuilds the ACM dashboard — and it was pulled twice on the boot
path: 5.4s in connect() and again in the startup self-test. `import main` took
10.55s of a 17s startup. Neither the warm-up nor the self-test gates anything,
so both now run in the background; nothing is skipped.
"""

from __future__ import annotations

import inspect
import time

from jarvis import platform_runtime
from jarvis.runtime_client import RuntimeClient


def test_connect_does_not_block_on_a_snapshot():
    src = inspect.getsource(RuntimeClient.connect)
    assert "self.snapshot(force_refresh=True)" not in src, "boot waits on the dashboard again"
    assert "_warm_snapshot_async()" in src


def test_the_warm_up_still_happens_just_off_the_boot_path():
    src = inspect.getsource(RuntimeClient._warm_snapshot_async)
    assert "threading.Thread" in src
    assert "daemon=True" in src
    assert "self.snapshot(force_refresh=True)" in src, "the snapshot is no longer warmed at all"


def test_the_startup_self_test_still_runs():
    src = inspect.getsource(platform_runtime.bootstrap_runtime_connection)
    assert "validate_runtime_startup()" in src, "the self-test was dropped, not deferred"
    assert "threading.Thread" in src and "daemon=True" in src


def test_the_self_test_waits_for_the_first_sync_before_judging():
    """Otherwise it reports 'not synced yet' on every boot."""
    src = inspect.getsource(platform_runtime.bootstrap_runtime_connection)
    assert "runtime_synced" in src


def test_a_failing_self_test_cannot_kill_the_process():
    src = inspect.getsource(platform_runtime.bootstrap_runtime_connection)
    assert "except Exception" in src


def test_connect_returns_promptly(monkeypatch):
    """The whole point: connect() must not carry a multi-second aggregation."""
    client = RuntimeClient()
    monkeypatch.setattr(client, "platform_discovered", lambda: True)
    monkeypatch.setattr(client, "_ensure_application_host", lambda: None)
    monkeypatch.setattr(client, "is_mission_control_reachable", lambda: True)

    slow_calls = []

    def slow_snapshot(*a, **kw):
        slow_calls.append(time.time())
        time.sleep(2.0)
        return {}

    monkeypatch.setattr(client, "snapshot", slow_snapshot)

    started = time.perf_counter()
    client.connect()
    elapsed = time.perf_counter() - started

    assert elapsed < 0.5, f"connect() blocked for {elapsed:.2f}s"
