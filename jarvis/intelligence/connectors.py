"""Unified external API connector framework — auth, retry, rate limit, cache."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("jarvis.intelligence.connectors")


@dataclass
class ConnectorConfig:
    name: str
    base_url: str = ""
    auth_type: str = "none"  # none | api_key | bearer | oauth_placeholder
    api_key: str = ""
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer "
    timeout_sec: float = 20.0
    max_retries: int = 2
    retry_backoff_sec: float = 0.4
    rate_limit_per_min: int = 60
    cache_ttl_sec: float = 0.0


@dataclass
class ConnectorResult:
    ok: bool
    status: int = 0
    data: Any = None
    error: str = ""
    cached: bool = False
    elapsed_ms: int = 0


class RateLimiter:
    def __init__(self, per_min: int) -> None:
        self.per_min = max(1, per_min)
        self._hits: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.time()
            self._hits = [t for t in self._hits if now - t < 60]
            if len(self._hits) >= self.per_min:
                sleep_for = 60 - (now - self._hits[0]) + 0.01
                time.sleep(max(0, sleep_for))
                now = time.time()
                self._hits = [t for t in self._hits if now - t < 60]
            self._hits.append(time.time())


class Connector:
    """Minimal REST connector with retries, rate limits, and optional GET cache."""

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self._limiter = RateLimiter(config.rate_limit_per_min)
        self._cache: dict[str, tuple[float, ConnectorResult]] = {}
        self._lock = threading.Lock()

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "AriaConnector/1.0"}
        if self.config.auth_type in ("api_key", "bearer") and self.config.api_key:
            headers[self.config.api_key_header] = f"{self.config.api_key_prefix}{self.config.api_key}".strip()
        if extra:
            headers.update(extra)
        return headers

    def _cache_key(self, method: str, url: str, body: bytes | None) -> str:
        h = hashlib.sha256()
        h.update(method.encode())
        h.update(url.encode())
        h.update(body or b"")
        return h.hexdigest()

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        headers: dict[str, str] | None = None,
        use_cache: bool = True,
    ) -> ConnectorResult:
        method = method.upper()
        url = path if path.startswith("http") else f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        body = None
        hdrs = self._headers(headers)
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            hdrs["Content-Type"] = "application/json"

        if use_cache and method == "GET" and self.config.cache_ttl_sec > 0:
            key = self._cache_key(method, url, body)
            with self._lock:
                hit = self._cache.get(key)
                if hit and time.time() - hit[0] < self.config.cache_ttl_sec:
                    cached = hit[1]
                    return ConnectorResult(
                        ok=cached.ok,
                        status=cached.status,
                        data=cached.data,
                        error=cached.error,
                        cached=True,
                        elapsed_ms=0,
                    )

        last_err = ""
        started = time.time()
        for attempt in range(self.config.max_retries + 1):
            try:
                self._limiter.acquire()
                req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
                with urllib.request.urlopen(req, timeout=self.config.timeout_sec) as resp:
                    raw = resp.read()
                    status = getattr(resp, "status", 200)
                    try:
                        data = json.loads(raw.decode("utf-8")) if raw else None
                    except Exception:
                        data = raw.decode("utf-8", errors="replace")
                    result = ConnectorResult(
                        ok=200 <= int(status) < 300,
                        status=int(status),
                        data=data,
                        elapsed_ms=int((time.time() - started) * 1000),
                    )
                    if use_cache and method == "GET" and self.config.cache_ttl_sec > 0 and result.ok:
                        key = self._cache_key(method, url, body)
                        with self._lock:
                            self._cache[key] = (time.time(), result)
                    return result
            except urllib.error.HTTPError as exc:
                last_err = f"HTTP {exc.code}: {exc.reason}"
                if exc.code in (429, 500, 502, 503, 504) and attempt < self.config.max_retries:
                    time.sleep(self.config.retry_backoff_sec * (attempt + 1))
                    continue
                return ConnectorResult(
                    ok=False,
                    status=int(exc.code),
                    error=last_err,
                    elapsed_ms=int((time.time() - started) * 1000),
                )
            except Exception as exc:
                last_err = str(exc)
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_backoff_sec * (attempt + 1))
                    continue
                return ConnectorResult(
                    ok=False,
                    error=last_err,
                    elapsed_ms=int((time.time() - started) * 1000),
                )
        return ConnectorResult(ok=False, error=last_err or "request failed")


_registry: dict[str, Connector] = {}


def register_connector(config: ConnectorConfig) -> Connector:
    conn = Connector(config)
    _registry[config.name] = conn
    return conn


def get_connector(name: str) -> Connector | None:
    return _registry.get(name)


def list_connectors() -> list[dict[str, Any]]:
    return [
        {
            "name": c.config.name,
            "base_url": c.config.base_url,
            "auth_type": c.config.auth_type,
            "rate_limit_per_min": c.config.rate_limit_per_min,
            "cache_ttl_sec": c.config.cache_ttl_sec,
        }
        for c in _registry.values()
    ]


def bootstrap_default_connectors() -> list[str]:
    """Register local + credentialed providers used by Integrations (External APIs runtime)."""
    names: list[str] = []
    register_connector(
        ConnectorConfig(
            name="aria_local",
            base_url="http://127.0.0.1:8765",
            auth_type="none",
            rate_limit_per_min=120,
            cache_ttl_sec=5,
            max_retries=1,
        )
    )
    names.append("aria_local")

    try:
        from jarvis.integrations_product.secrets_bus import get_secret

        gemini = get_secret("gemini_api_key")
        if gemini:
            register_connector(
                ConnectorConfig(
                    name="gemini",
                    base_url="https://generativelanguage.googleapis.com",
                    auth_type="api_key",
                    api_key=gemini,
                    api_key_header="x-goog-api-key",
                    api_key_prefix="",
                    rate_limit_per_min=30,
                    cache_ttl_sec=0,
                )
            )
            names.append("gemini")
        openai = get_secret("openai_api_key")
        if openai:
            register_connector(
                ConnectorConfig(
                    name="openai",
                    base_url="https://api.openai.com",
                    auth_type="bearer",
                    api_key=openai,
                    rate_limit_per_min=60,
                )
            )
            names.append("openai")
        openrouter = get_secret("openrouter_api_key")
        if openrouter:
            register_connector(
                ConnectorConfig(
                    name="openrouter",
                    base_url="https://openrouter.ai/api",
                    auth_type="bearer",
                    api_key=openrouter,
                    rate_limit_per_min=60,
                )
            )
            names.append("openrouter")
        meshy = get_secret("meshy_api_key")
        if meshy:
            register_connector(
                ConnectorConfig(
                    name="meshy",
                    base_url="https://api.meshy.ai",
                    auth_type="bearer",
                    api_key=meshy,
                    rate_limit_per_min=20,
                )
            )
            names.append("meshy")
        anthropic = get_secret("anthropic_api_key")
        if anthropic:
            register_connector(
                ConnectorConfig(
                    name="anthropic",
                    base_url="https://api.anthropic.com",
                    auth_type="api_key",
                    api_key=anthropic,
                    api_key_header="x-api-key",
                    api_key_prefix="",
                    rate_limit_per_min=30,
                )
            )
            names.append("anthropic")
    except Exception as exc:
        log.debug("credentialed connectors skipped: %s", exc)

    # Local optional services
    import os

    litellm = (os.getenv("JARVIS_LITELLM_URL") or "").rstrip("/")
    if litellm:
        register_connector(
            ConnectorConfig(
                name="litellm",
                base_url=litellm,
                auth_type="none",
                rate_limit_per_min=120,
                cache_ttl_sec=5,
            )
        )
        names.append("litellm")
    ollama = (os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
    register_connector(
        ConnectorConfig(
            name="ollama",
            base_url=ollama,
            auth_type="none",
            rate_limit_per_min=120,
            cache_ttl_sec=5,
        )
    )
    names.append("ollama")
    return names
