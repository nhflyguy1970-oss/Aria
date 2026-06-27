"""HTTP request logging middleware."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from jarvis.logging_config import clear_request_id, set_request_id

logger = logging.getLogger("jarvis.http")

_SKIP_PATHS = frozenset({"/api/ping", "/api/live", "/api/health/lite"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        rid = (
            request.headers.get("x-request-id")
            or request.headers.get("x-jarvis-request-id")
            or uuid.uuid4().hex[:12]
        )
        set_request_id(rid)
        path = request.url.path
        skip = path in _SKIP_PATHS or path.startswith("/static/")
        start = time.perf_counter()
        try:
            response = await call_next(request)
            if not skip and path.startswith("/api/"):
                ms = (time.perf_counter() - start) * 1000
                logger.info(
                    "%s %s -> %s (%.0fms)",
                    request.method,
                    path,
                    response.status_code,
                    ms,
                )
            response.headers.setdefault("X-Request-Id", rid)
            return response
        except Exception:
            if not skip:
                ms = (time.perf_counter() - start) * 1000
                logger.exception(
                    "%s %s failed after %.0fms",
                    request.method,
                    path,
                    ms,
                )
            raise
        finally:
            clear_request_id()
