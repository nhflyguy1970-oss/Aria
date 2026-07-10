"""RuntimeClient — Aria consumes AI Platform Mission Control as single source of truth."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("jarvis.runtime_client")

_CLIENT: RuntimeClient | None = None


class RuntimeClientError(Exception):
    """Mission Control data required but unavailable."""


@dataclass
class RuntimeClient:
    """Discover, connect, and read live runtime state from Mission Control."""

    _connection_mode: str = "none"
    _last_heartbeat: float | None = None
    _last_api_call: float | None = None
    _last_latency_ms: float | None = None
    _last_error: str | None = None
    _last_path: str | None = None
    _cached_snapshot: dict[str, Any] | None = None
    _cached_at: float = 0.0
    _cache_ttl: float = 5.0
    _application_attached: bool = False
    _host_discovered: bool = False
    _warnings: list[str] = field(default_factory=list)

    def mission_control_base_url(self) -> str:
        host = os.getenv("MISSION_CONTROL_HOST", "127.0.0.1").strip()
        if host in ("0.0.0.0", "::", "::0"):
            host = "127.0.0.1"
        port = os.getenv("MISSION_CONTROL_PORT", "8780")
        return f"http://{host}:{port}"

    def platform_discovered(self) -> bool:
        try:
            import aiplatform  # noqa: F401

            return True
        except ImportError:
            return False

    def is_mission_control_reachable(self, *, timeout: float = 2.0) -> bool:
        url = f"{self.mission_control_base_url()}/api/health"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError, TimeoutError):
            return False

    def connect(self) -> dict[str, Any]:
        """Discover platform, attach application host, verify Mission Control."""
        self._warnings = []
        if not self.platform_discovered():
            self._connection_mode = "none"
            self._last_error = "AI Platform package not available"
            self._warnings.append(self._last_error)
            return self.connection_report()

        self._ensure_application_host()
        if self.is_mission_control_reachable():
            self._connection_mode = "http"
            self._last_error = None
            try:
                self.snapshot(force_refresh=True)
            except RuntimeClientError as exc:
                self._last_error = str(exc)
                self._warnings.append(self._last_error)
        elif self._in_process_available():
            self._connection_mode = "in_process"
            self._last_error = None
            try:
                self.snapshot(force_refresh=True)
            except RuntimeClientError as exc:
                self._last_error = str(exc)
                self._warnings.append(self._last_error)
        else:
            self._connection_mode = "none"
            self._last_error = "Mission Control API not reachable"
            self._warnings.append(self._last_error)

        return self.connection_report()

    def _ensure_application_host(self) -> None:
        from jarvis.application.host import attach_if_present

        self._application_attached = attach_if_present()
        try:
            from aiplatform.applications.host import discover_and_attach

            hosts = discover_and_attach()
            self._host_discovered = bool(hosts)
            aria = next((h for h in hosts if h.get("id") == "aria"), None)
            if aria:
                self._application_attached = bool(aria.get("attached"))
        except Exception as exc:
            self._warnings.append(f"ApplicationHost discovery: {exc}")
            logger.debug("ApplicationHost discovery failed: %s", exc)

    def _in_process_available(self) -> bool:
        try:
            from aiplatform.mission_control.aggregator import collect_mission_control  # noqa: F401

            return True
        except ImportError:
            return False

    def heartbeat(self) -> bool:
        ok = self.is_mission_control_reachable()
        if ok:
            self._last_heartbeat = time.time()
        return ok

    def snapshot(self, *, force_refresh: bool = False, required: bool = False) -> dict[str, Any]:
        """Full Mission Control snapshot."""
        now = time.time()
        if (
            not force_refresh
            and self._cached_snapshot
            and (now - self._cached_at) < self._cache_ttl
        ):
            return self._cached_snapshot

        started = time.perf_counter()
        payload: dict[str, Any] | None = None
        error: str | None = None

        if self._connection_mode == "http" or (
            self._connection_mode == "none" and self.is_mission_control_reachable()
        ):
            payload, error = self._fetch_http("/api/mission-control")
            if payload is not None:
                self._connection_mode = "http"

        if payload is None and self._in_process_available():
            payload, error = self._fetch_in_process()
            if payload is not None:
                self._connection_mode = "in_process"

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self._last_api_call = time.time()
        self._last_latency_ms = round(elapsed_ms, 1)
        self._last_path = "/api/mission-control"

        if payload is None:
            self._last_error = error or "Mission Control unavailable"
            self._cached_snapshot = None
            if required:
                raise RuntimeClientError(self._last_error)
            return {"ok": False, "error": self._last_error, "source": "none"}

        payload.setdefault("ok", True)
        payload["source"] = "mission_control"
        payload["connection_mode"] = self._connection_mode
        self._last_error = None
        self._last_heartbeat = time.time()
        self._cached_snapshot = payload
        self._cached_at = now
        return payload

    def tab(self, name: str, *, required: bool = False) -> dict[str, Any]:
        started = time.perf_counter()
        if self._connection_mode == "http" or self.is_mission_control_reachable():
            payload, error = self._fetch_http(f"/api/mission-control/{name.strip().lower()}")
            if payload is not None:
                self._connection_mode = "http"
                self._last_api_call = time.time()
                self._last_latency_ms = round((time.perf_counter() - started) * 1000.0, 1)
                self._last_path = f"/api/mission-control/{name}"
                payload.setdefault("source", "mission_control")
                return payload
            if required and error:
                raise RuntimeClientError(error)

        if self._in_process_available():
            from aiplatform.mission_control.aggregator import get_tab

            result = get_tab(name)
            self._connection_mode = "in_process"
            self._last_api_call = time.time()
            self._last_latency_ms = round((time.perf_counter() - started) * 1000.0, 1)
            self._last_path = f"/api/mission-control/{name}"
            if not result.get("ok") and required:
                raise RuntimeClientError(str(result.get("error") or "tab unavailable"))
            result["source"] = "mission_control"
            return result

        msg = "Mission Control tab unavailable"
        if required:
            raise RuntimeClientError(msg)
        return {"ok": False, "error": msg, "source": "none"}

    def _fetch_http(self, path: str) -> tuple[dict[str, Any] | None, str | None]:
        url = f"{self.mission_control_base_url()}{path}"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                return None, "invalid Mission Control response"
            return data, None
        except urllib.error.HTTPError as exc:
            return None, f"HTTP {exc.code} from Mission Control"
        except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
            return None, str(exc)

    def _fetch_in_process(self) -> tuple[dict[str, Any] | None, str | None]:
        try:
            from aiplatform.mission_control.aggregator import collect_mission_control

            return collect_mission_control(record_metrics=False), None
        except Exception as exc:
            return None, str(exc)

    def connection_report(self) -> dict[str, Any]:
        """Diagnostics for Runtime Connection page and startup self-test."""
        heartbeat_age: float | None = None
        if self._last_heartbeat:
            heartbeat_age = round(time.time() - self._last_heartbeat, 1)

        runtime_synced = bool(
            self._cached_snapshot and self._cached_snapshot.get("source") == "mission_control"
        )
        mc_reachable = self.is_mission_control_reachable()

        issues: list[str] = []
        if not self.platform_discovered():
            issues.append("AI Platform not discovered")
        if not mc_reachable and self._connection_mode != "in_process":
            issues.append("Mission Control API not reachable")
        if not self._application_attached:
            issues.append("Application not registered with platform")
        if not self._host_discovered:
            issues.append("ApplicationHost not connected")
        if not runtime_synced and not self._last_error:
            issues.append("Runtime not synced yet")
        if self._last_error:
            issues.append(self._last_error)
        issues.extend(w for w in self._warnings if w not in issues)

        return {
            "ok": len(issues) == 0,
            "platform_discovered": self.platform_discovered(),
            "mission_control_reachable": mc_reachable,
            "mission_control_url": self.mission_control_base_url(),
            "application_host_connected": self._host_discovered,
            "application_registered": self._application_attached,
            "runtime_synced": runtime_synced,
            "connection_mode": self._connection_mode,
            "heartbeat_age_seconds": heartbeat_age,
            "last_api_call": (
                datetime.fromtimestamp(self._last_api_call).isoformat(timespec="seconds")
                if self._last_api_call
                else None
            ),
            "last_api_path": self._last_path,
            "connection_latency_ms": self._last_latency_ms,
            "last_error": self._last_error,
            "issues": issues,
            "warnings": list(self._warnings),
        }


def get_runtime_client() -> RuntimeClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = RuntimeClient()
    return _CLIENT
