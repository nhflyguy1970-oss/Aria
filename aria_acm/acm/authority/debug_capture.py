"""Conversation-safe debugging capture (B10).

Traces classify → route → reconstruct without contaminating autobiographical
memory or influencing subsequent activation. Opt-in; production default OFF.
Composes B07 read-only, B09 diagnostic safety, B27 organ views.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from time import time
from typing import Any, TYPE_CHECKING

from acm.authority.diagnostic_policy import apply_diagnostic_policy
from acm.authority.mode import read_only

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

SCHEMA = "acm.debug.capture.v1"


@dataclass(frozen=True)
class ConversationDebugPolicy:
    """Host opt-in for conversation-safe debug capture (disabled by default)."""

    enabled: bool = False
    max_captures: int = 64
    include_organ_view: str = ""  # optional organ name for B27 slice


DEFAULT_CONVERSATION_DEBUG_POLICY = ConversationDebugPolicy()


def policy_for_engine_debug(engine: CognitiveEngine) -> ConversationDebugPolicy:
    policy = getattr(engine, "conversation_debug_policy", None)
    if policy is not None and hasattr(policy, "enabled") and hasattr(policy, "max_captures"):
        # Accept duck-typed policies (Aria nested import class identity).
        if isinstance(policy, ConversationDebugPolicy):
            return policy
        return ConversationDebugPolicy(
            enabled=bool(getattr(policy, "enabled", False)),
            max_captures=int(getattr(policy, "max_captures", 64)),
            include_organ_view=str(getattr(policy, "include_organ_view", "") or ""),
        )
    return DEFAULT_CONVERSATION_DEBUG_POLICY


def with_debug_enabled(
    policy: ConversationDebugPolicy, *, enabled: bool
) -> ConversationDebugPolicy:
    return replace(policy, enabled=enabled)


@dataclass
class DebugCaptureBuffer:
    """Side-channel capture ring — never written into Experiences/Concepts."""

    max_captures: int = 64
    items: list[dict[str, Any]] = field(default_factory=list)

    def append(self, item: dict[str, Any]) -> None:
        self.items.append(item)
        overflow = len(self.items) - self.max_captures
        if overflow > 0:
            del self.items[:overflow]

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return list(self.items[-limit:])

    def clear(self) -> None:
        self.items.clear()


def capture_cognitive_debug(
    engine: CognitiveEngine,
    cue: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Capture a live cognitive trace without store contamination.

    When policy.enabled is False (default), returns status=disabled unless
    ``force=True`` (tests / explicit operator override).
    """
    policy = policy_for_engine_debug(engine)
    if not policy.enabled and not force:
        return {
            "schema": SCHEMA,
            "status": "disabled",
            "enabled": False,
            "invents_experiences": False,
            "store_unchanged": True,
            "safety_note": "Conversation debug capture is opt-in.",
        }

    text = (cue or "").strip()
    if not text:
        return {
            "schema": SCHEMA,
            "status": "empty",
            "enabled": True,
            "invents_experiences": False,
            "store_unchanged": True,
        }

    exp_before = len(engine.store.experiences)
    concept_before = len(engine.store.concepts)
    assoc_before = len(engine.store.associations)
    fp_before = engine.store_fingerprint()
    t0 = time()

    classification = engine.classify_request(text)
    routing = engine.route_request(text)

    with read_only():
        # inspect applies B09; remains under read_only for the full path
        reconstruction = engine.inspect(text)

    organ_slice: dict[str, Any] | None = None
    if policy.include_organ_view:
        organ_slice = engine.organ_view(policy.include_organ_view)

    fp_after = engine.store_fingerprint()
    store_unchanged = fp_after == fp_before
    no_new_memory = (
        len(engine.store.experiences) == exp_before
        and len(engine.store.concepts) == concept_before
        and len(engine.store.associations) == assoc_before
    )

    payload = {
        "schema": SCHEMA,
        "status": "captured",
        "enabled": True,
        "cue": text,
        "captured_at": time(),
        "latency_ms": round((time() - t0) * 1000.0, 3),
        "classification": classification,
        "routing": routing,
        "reconstruction": {
            "intent": reconstruction.get("intent"),
            "status": reconstruction.get("status"),
            "memory": reconstruction.get("memory"),
            "confidence": reconstruction.get("confidence"),
            "ambiguous": reconstruction.get("ambiguous"),
            "uncertainty": reconstruction.get("uncertainty"),
            "terminated_at": (reconstruction.get("diagnostics") or {}).get(
                "terminated_at"
            ),
            "execution_mode": (reconstruction.get("diagnostics") or {}).get(
                "execution_mode"
            ),
            "safety_policy_applied": reconstruction.get("safety_policy_applied"),
        },
        "organ_view": organ_slice,
        "fingerprint": fp_after,
        "store_unchanged": store_unchanged and no_new_memory,
        "invents_experiences": False,
        "exposes_internals": False,
    }
    # Final safety pass (B09) on the capture envelope itself
    safe = apply_diagnostic_policy(payload, engine=engine, cue=text)
    buf = getattr(engine, "_debug_captures", None)
    if isinstance(buf, DebugCaptureBuffer):
        buf.max_captures = policy.max_captures
        buf.append(safe)
    return safe


def capture_replay_equivalent(
    engine: CognitiveEngine,
    cue: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Capture twice; verify answer/fingerprint equivalence (no store drift)."""
    a = capture_cognitive_debug(engine, cue, force=force)
    if a.get("status") != "captured":
        return a
    b = capture_cognitive_debug(engine, cue, force=force)
    equiv = (
        a.get("reconstruction", {}).get("memory")
        == b.get("reconstruction", {}).get("memory")
        and a.get("fingerprint") == b.get("fingerprint")
        and a.get("store_unchanged") is True
        and b.get("store_unchanged") is True
    )
    return {
        "schema": "acm.debug.replay.v1",
        "status": "ok" if equiv else "drift",
        "equivalent": equiv,
        "first": a,
        "second": b,
        "invents_experiences": False,
    }
