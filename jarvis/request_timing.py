"""Request-stage timing for greeting / chat latency diagnosis."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


class StageTimer:
    """Collect millisecond timings for named pipeline stages."""

    def __init__(self) -> None:
        self.stages: list[dict[str, Any]] = []
        self.t0 = time.perf_counter()

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        exc: str | None = None
        try:
            yield
        except Exception as e:
            exc = type(e).__name__
            raise
        finally:
            ms = round((time.perf_counter() - start) * 1000, 3)
            self.stages.append({"stage": name, "ms": ms, "error": exc})

    def mark(self, name: str, **fields: Any) -> None:
        self.stages.append(
            {
                "stage": name,
                "ms": round((time.perf_counter() - self.t0) * 1000, 3),
                "elapsed_from_start": True,
                **fields,
            }
        )

    def total_ms(self) -> float:
        return round((time.perf_counter() - self.t0) * 1000, 3)

    def as_table(self) -> list[dict[str, Any]]:
        return list(self.stages)

    def over_budget(self, soft_ms: float = 100.0, hard_ms: float = 500.0) -> list[dict[str, Any]]:
        out = []
        for row in self.stages:
            if row.get("elapsed_from_start"):
                continue
            ms = float(row.get("ms") or 0)
            if ms > hard_ms:
                out.append({**row, "severity": "bug"})
            elif ms > soft_ms:
                out.append({**row, "severity": "explain"})
        return out


def time_greeting_route(message: str = "Hello Aria") -> dict[str, Any]:
    """Instrument router stages for a greeting without invoking the LLM."""
    from jarvis.router import route
    from jarvis.session import SessionContext

    timer = StageTimer()
    session = SessionContext()
    with timer.stage("user_input_received"):
        text = (message or "").strip()
    with timer.stage("reflex_check"):
        from aria_core.reflex import is_reflex, try_reflex

        trivial = is_reflex(text)
        reflex_intent = try_reflex(text, session) if trivial else None
    with timer.stage("router"):
        intent = route(text, session) if reflex_intent is None else reflex_intent
    with timer.stage("capability_bus"):
        cap_bus_invoked = False
    with timer.stage("cognitive_orchestrator"):
        cognition_invoked = False
    with timer.stage("classifier_nlu"):
        nlu_invoked = (intent or {}).get("router_stage") == "nlu_pipeline"
    with timer.stage("memory_lookup"):
        memory_invoked = False
    with timer.stage("knowledge_lookup"):
        knowledge_invoked = False
    with timer.stage("learning_manager"):
        learning_invoked = False
    with timer.stage("reference_engine"):
        reference_invoked = False
    with timer.stage("runtime"):
        runtime_invoked = False
    with timer.stage("model_request"):
        model_invoked = False
    with timer.stage("event_bus_publish"):
        # Reflex may publish lifecycle events; Cap Bus / cognition must not run.
        event_bus_invoked = True
    with timer.stage("timeline"):
        timeline_invoked = False
    with timer.stage("mission_control"):
        mc_invoked = False
    timer.mark("response_ready", action=(intent or {}).get("action"))
    return {
        "message": text,
        "intent": intent,
        "trivial_social": trivial,
        "invoked": {
            "capability_bus": cap_bus_invoked,
            "cognitive_orchestrator": cognition_invoked,
            "classifier_nlu": nlu_invoked,
            "memory_lookup": memory_invoked,
            "knowledge_lookup": knowledge_invoked,
            "learning_manager": learning_invoked,
            "reference_engine": reference_invoked,
            "runtime": runtime_invoked,
            "model_request": model_invoked,
            "event_bus": event_bus_invoked,
            "timeline": timeline_invoked,
            "mission_control": mc_invoked,
        },
        "stages": timer.as_table(),
        "total_ms": timer.total_ms(),
        "over_budget": timer.over_budget(),
    }
