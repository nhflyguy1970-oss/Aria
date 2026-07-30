"""Request latency traces — stage timing, context inventory, provider/stream metrics."""

from __future__ import annotations

import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

_active: ContextVar[LatencyTrace | None] = ContextVar("aria_latency_trace", default=None)
_LOCK = threading.RLock()
_BY_ID: dict[str, LatencyTrace] = {}
_BY_REQUEST: dict[str, str] = {}
_LIVE: dict[str, LatencyTrace] = {}
_MAX_LIVE = 64
_MAX_RECENT = 200
_RECENT: list[str] = []


def _now() -> float:
    return time.perf_counter()


def _wall() -> float:
    return time.time()


def new_trace_id() -> str:
    return f"lt-{uuid.uuid4().hex[:12]}"


@dataclass
class StageSpan:
    name: str
    start: float
    end: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed_ms(self) -> float | None:
        if self.end is None:
            return round((_now() - self.start) * 1000, 2)
        return round((self.end - self.start) * 1000, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "elapsed_ms": self.elapsed_ms,
            "running": self.end is None,
            **({k: v for k, v in self.meta.items() if v is not None}),
        }


@dataclass
class LatencyTrace:
    trace_id: str
    request_id: str = ""
    conversation_id: str = ""
    provider_request_id: str = ""
    prompt: str = ""
    action: str = ""
    started_at: float = field(default_factory=_wall)
    t0: float = field(default_factory=_now)
    stages: list[StageSpan] = field(default_factory=list)
    open_stages: dict[str, StageSpan] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    provider: dict[str, Any] = field(default_factory=dict)
    stream: dict[str, Any] = field(default_factory=dict)
    model: dict[str, Any] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict)
    budgets: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    completed: bool = False
    ok: bool | None = None
    current_stage: str = ""

    def start_stage(self, name: str, **meta: Any) -> None:
        span = StageSpan(name=name, start=_now(), meta=dict(meta))
        self.open_stages[name] = span
        self.current_stage = name

    def end_stage(self, name: str, **meta: Any) -> float | None:
        span = self.open_stages.pop(name, None)
        if span is None:
            # Allow one-shot note without start.
            span = StageSpan(name=name, start=_now(), meta={})
            span.end = span.start
        else:
            span.end = _now()
        span.meta.update({k: v for k, v in meta.items() if v is not None})
        self.stages.append(span)
        if self.current_stage == name:
            self.current_stage = next(iter(self.open_stages), "")
        return span.elapsed_ms

    def note_stage(self, name: str, elapsed_ms: float, **meta: Any) -> None:
        now = _now()
        start = now - max(0.0, float(elapsed_ms)) / 1000.0
        span = StageSpan(name=name, start=start, end=now, meta=dict(meta))
        self.stages.append(span)

    def set_context_inventory(self, inventory: dict[str, Any] | None) -> None:
        inv = dict(inventory or {})
        sources = {}
        for name, info in (inv.get("sources") or {}).items():
            chars = int(info.get("characters") or 0)
            sources[name] = {
                "enabled": bool(info.get("required") or info.get("injected")),
                "why": "required" if info.get("required") else "skipped",
                "characters": chars,
                "tokens_est": max(0, chars // 4),
                "latency_ms": info.get("elapsed_ms"),
                "injected": bool(info.get("injected")),
                "cache": info.get("cache"),
            }
        self.context = {
            "lightweight": inv.get("lightweight"),
            "prefix_characters": inv.get("prefix_characters"),
            "prefix_tokens_est": max(0, int(inv.get("prefix_characters") or 0) // 4),
            "sources": sources,
            "message": inv.get("message"),
        }

    def note_provider(self, **fields: Any) -> None:
        self.provider.update({k: v for k, v in fields.items() if v is not None})

    def note_stream(self, **fields: Any) -> None:
        self.stream.update({k: v for k, v in fields.items() if v is not None})

    def note_model(self, **fields: Any) -> None:
        self.model.update({k: v for k, v in fields.items() if v is not None})

    def note_cache(self, name: str, *, hit: bool, saved_ms: float | None = None) -> None:
        entry = self.cache.setdefault(name, {"hits": 0, "misses": 0, "saved_ms": 0.0})
        if hit:
            entry["hits"] += 1
            if saved_ms:
                entry["saved_ms"] = round(float(entry["saved_ms"]) + float(saved_ms), 2)
        else:
            entry["misses"] += 1

    def elapsed_ms(self) -> float:
        return round((_now() - self.t0) * 1000, 2)

    def slowest_stage(self) -> dict[str, Any] | None:
        done = [s for s in self.stages if s.elapsed_ms is not None]
        if not done:
            return None
        best = max(done, key=lambda s: s.elapsed_ms or 0)
        return best.to_dict()

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "conversation_id": self.conversation_id,
            "provider_request_id": self.provider_request_id,
            "prompt": (self.prompt or "")[:160],
            "action": self.action,
            "started_at": self.started_at,
            "elapsed_ms": self.elapsed_ms(),
            "completed": self.completed,
            "ok": self.ok,
            "current_stage": self.current_stage,
            "stages": [s.to_dict() for s in self.stages],
            "open_stages": [s.to_dict() for s in self.open_stages.values()],
            "context": self.context,
            "provider": self.provider,
            "stream": self.stream,
            "model": self.model,
            "cache": self.cache,
            "budgets": self.budgets,
            "errors": self.errors,
            "slowest": self.slowest_stage(),
            "waterfall": self.waterfall(),
            "developer_overlay": self.developer_overlay(),
        }

    def developer_overlay(self) -> list[str]:
        lines = [f"Trace {self.trace_id}"]
        if self.request_id:
            lines.append(f"Request {self.request_id}")
        for s in self.stages:
            ms = s.elapsed_ms
            label = s.name.replace("_", " ").title()
            if ms is None:
                lines.append(f"{label:20} …")
            elif s.meta.get("skipped"):
                lines.append(f"{label:20} skipped")
            else:
                lines.append(f"{label:20} {ms:.0f} ms")
        ft = self.stream.get("first_token_ms")
        if ft is not None:
            lines.append(f"{'First Token':20} {float(ft):.0f} ms")
        lines.append(f"{'Elapsed':20} {self.elapsed_ms():.0f} ms")
        return lines

    def waterfall(self) -> list[dict[str, Any]]:
        rows = []
        for s in self.stages:
            rows.append(
                {
                    "stage": s.name,
                    "elapsed_ms": s.elapsed_ms,
                    "start_offset_ms": round((s.start - self.t0) * 1000, 2),
                    **s.meta,
                }
            )
        return rows


def begin_trace(
    *,
    request_id: str = "",
    conversation_id: str = "",
    provider_request_id: str = "",
    prompt: str = "",
    trace_id: str | None = None,
) -> LatencyTrace:
    tid = (trace_id or "").strip() or new_trace_id()
    tr = LatencyTrace(
        trace_id=tid,
        request_id=(request_id or "").strip(),
        conversation_id=(conversation_id or "").strip(),
        provider_request_id=(provider_request_id or "").strip() or (request_id or "").strip(),
        prompt=(prompt or "")[:200],
    )
    _active.set(tr)
    with _LOCK:
        _BY_ID[tid] = tr
        if tr.request_id:
            _BY_REQUEST[tr.request_id] = tid
        if tr.provider_request_id and tr.provider_request_id != tr.request_id:
            _BY_REQUEST[tr.provider_request_id] = tid
        _LIVE[tid] = tr
        _RECENT.append(tid)
        while len(_RECENT) > _MAX_RECENT:
            old = _RECENT.pop(0)
            if old not in _LIVE:
                _BY_ID.pop(old, None)
        while len(_LIVE) > _MAX_LIVE:
            # Drop oldest completed live entries preferentially.
            for k in list(_LIVE.keys()):
                if _LIVE[k].completed:
                    _LIVE.pop(k, None)
                    break
            else:
                _LIVE.pop(next(iter(_LIVE)), None)
                break
    return tr


def bind_active(trace_id: str = "", request_id: str = "") -> LatencyTrace | None:
    """Re-bind ContextVar in the current thread (e.g. stream worker)."""
    tr = None
    if trace_id:
        tr = get_trace(trace_id)
    if tr is None and request_id:
        tr = get_by_request_id(request_id)
    if tr is not None:
        _active.set(tr)
    return tr


def get_by_request_id(request_id: str) -> LatencyTrace | None:
    rid = (request_id or "").strip()
    if not rid:
        return None
    with _LOCK:
        tid = _BY_REQUEST.get(rid)
        return _BY_ID.get(tid) if tid else None


def active_trace() -> LatencyTrace | None:
    return _active.get()


def current_trace_id() -> str:
    tr = _active.get()
    return tr.trace_id if tr else ""


def get_trace(trace_id: str) -> LatencyTrace | None:
    with _LOCK:
        return _BY_ID.get(trace_id)


def note_stage(name: str, elapsed_ms: float | None = None, **meta: Any) -> None:
    tr = _active.get()
    if tr is None:
        return
    if elapsed_ms is None:
        tr.start_stage(name, **meta)
    else:
        tr.note_stage(name, float(elapsed_ms), **meta)


def end_stage(name: str, **meta: Any) -> None:
    tr = _active.get()
    if tr is None:
        return
    tr.end_stage(name, **meta)


def complete_trace(*, ok: bool | None = None, error: str = "", action: str = "") -> LatencyTrace | None:
    tr = _active.get()
    if tr is None:
        return None
    for name in list(tr.open_stages.keys()):
        tr.end_stage(name)
    if action:
        tr.action = action
    if error:
        tr.errors.append(error[:300])
    tr.ok = ok
    tr.completed = True
    tr.current_stage = ""
    # Budgets evaluated at completion.
    try:
        from jarvis.latency_observability.budgets import evaluate_budgets

        tr.budgets = evaluate_budgets(tr)
    except Exception:
        tr.budgets = []
    with _LOCK:
        _LIVE.pop(tr.trace_id, None)
    try:
        from jarvis.latency_observability.store import append_trace

        append_trace(tr)
    except Exception:
        pass
    return tr


def live_traces() -> list[dict[str, Any]]:
    with _LOCK:
        rows = [t.to_dict() for t in _LIVE.values()]
    rows.sort(key=lambda r: r.get("started_at") or 0, reverse=True)
    return rows


def recent_trace_ids(*, limit: int = 40) -> list[str]:
    with _LOCK:
        return list(reversed(_RECENT[-limit:]))
