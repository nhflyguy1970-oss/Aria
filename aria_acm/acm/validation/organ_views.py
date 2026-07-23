"""Organ-scoped observability views (B27) over the singular ValidationHarness.

Does not split the harness. Projects stable per-organ report slices for hosts.
Full privacy redaction remains B29.
"""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

SCHEMA = "acm.organ_view.v1"

# Harness snapshot keys primarily owned by each organ view.
_HARNESS_KEYS: dict[str, tuple[str, ...]] = {
    "identity": ("identity", "identity_touches"),
    "experience": ("experience", "experience_events"),
    "concept": ("concept", "concept_events"),
    "association": ("association", "association_events", "association_changes"),
    "remembering": ("remembering", "remembering_events", "activations", "reconsolidations"),
    "reflection": ("reflection", "reflection_events"),
    "learning": ("learning", "learning_events"),
    "attention": ("attention", "attention_events"),
    "forgetting": ("forgetting", "forgetting_events", "accessibility_events"),
    "prediction": ("prediction", "prediction_events"),
    "simulation": ("simulation", "simulation_events"),
    "reconciliation": ("reconciliation", "reconciliation_events"),
    "confidence": ("confidence", "confidence_deltas", "confidence_events"),
    "sleep": ("sleep", "sleep_events"),
    "working": ("working_transitions",),
    "lifecycle": ("lifecycle",),
}


def _organ_callable(engine: CognitiveEngine, name: str) -> Callable[[], dict[str, Any]] | None:
    mapping = {
        "identity": lambda: engine.identity.observables(),
        "experience": lambda: engine.experiences.observables(),
        "concept": lambda: engine.concepts.observables(),
        "association": lambda: engine.associations.observables(),
        "remembering": lambda: engine.remembering.observables(),
        "reflection": lambda: engine.reflection.observables(),
        "learning": lambda: engine.learning.observables(),
        "attention": lambda: engine.attention.observables(),
        "forgetting": lambda: engine.forgetting.observables(),
        "prediction": lambda: engine.prediction.observables(),
        "simulation": lambda: engine.simulation.observables(),
        "reconciliation": lambda: engine.reconciliation.observables(),
        "confidence": lambda: engine.confidence.observables(),
        "sleep": lambda: engine.offline.observables(),
        "analogy": lambda: engine.analogy.observables(),
        "recombination": lambda: engine.recombination.observables(),
    }
    return mapping.get(name)


def available_organ_views() -> tuple[str, ...]:
    return tuple(sorted(set(_HARNESS_KEYS) | {
        "analogy",
        "recombination",
    }))


def organ_view(engine: CognitiveEngine, organ: str) -> dict[str, Any]:
    """Return a versioned per-organ observability slice."""
    name = (organ or "").strip().lower()
    snap = engine.validation.snapshot()
    harness_slice: dict[str, Any] = {}
    for key in _HARNESS_KEYS.get(name, ()):
        if key in snap:
            harness_slice[key] = snap[key]
    organ_obs: dict[str, Any] = {}
    getter = _organ_callable(engine, name)
    if getter is not None:
        try:
            organ_obs = getter() or {}
        except Exception as exc:  # noqa: BLE001 — view must not crash hosts
            organ_obs = {"error": type(exc).__name__}
    return {
        "schema": SCHEMA,
        "organ": name,
        "empty": not harness_slice and not organ_obs,
        "harness": harness_slice,
        "observables": organ_obs,
        "redaction": "none",  # B29 will apply policy here
        "note": "Privacy redaction deferred to B29; views are structural only.",
    }


def organ_views(engine: CognitiveEngine, organs: list[str] | None = None) -> dict[str, Any]:
    names = list(organs) if organs else list(available_organ_views())
    return {
        "schema": "acm.organ_views.v1",
        "organs": {name: organ_view(engine, name) for name in names},
    }
