"""The router: requirements in, an explainable model choice out.

Two phases, deliberately separate. Hard filtering removes anything that would
make the result invalid, and its verdicts are final — no score can buy a model
back in. Only what survives is ranked, and the ranking is a plain weighted sum
that can be read off the decision.
"""

from __future__ import annotations

import logging
from typing import Any

from jarvis.model_routing import capabilities as caps
from jarvis.model_routing import health, profiles
from jarvis.model_routing.decision import (
    NONE_AVAILABLE,
    PREFERRED,
    SCORED,
    Candidate,
    RoutingDecision,
)
from jarvis.model_routing.profiles import ModelProfile
from jarvis.model_routing.request import BALANCED, FAST, QUALITY, RoutingRequest, validate

log = logging.getLogger("jarvis.model_routing.router")

# Scoring weights. Explicit so a decision can be explained rather than trusted.
WEIGHTS = {
    "preferred_model": 5.0,
    "preferred_provider": 0.5,
    "task_specialisation": 2.0,
    "preferred_capabilities": 1.5,
    "context_fit": 1.0,
    "latency_match": 1.0,
    "quality": 1.0,
    "health": 1.0,
    "priority": 0.5,
    # A model whose weights do not fit in free accelerator memory will either
    # fail to load or crawl on CPU. That is a strong preference, not a hard
    # requirement: offloading is legitimate, and an unknown reading must not
    # rule anything out.
    "memory_fit": 1.5,
}

# Which strength matters for which task.
_TASK_STRENGTH = {
    "coding": "coding_strength",
    "reasoning": "reasoning_strength",
    "research": "research_strength",
    "general": "general_strength",
}

# Role names ARIA already uses, mapped to the task they represent.
ROLE_TASKS = {
    "coding": "coding",
    "coder": "coding",
    "review": "coding",
    "reasoning": "reasoning",
    "planning": "reasoning",
    "reflection": "reasoning",
    "web_research": "research",
    "document": "research",
    "conversation": "general",
    "general": "general",
    "fast_chat": "general",
    "summarization": "general",
    "vision": "general",
    "browser_vision": "general",
    "tool_calling": "general",
}


def _task_for(request: RoutingRequest) -> str:
    if request.task_type and request.task_type != "general":
        return request.task_type
    return ROLE_TASKS.get(request.role, request.task_type or "general")


def _reject(profile: ModelProfile, reason: str) -> Candidate:
    return Candidate(
        model_id=profile.model_id,
        provider=profile.provider,
        accepted=False,
        rejection_reason=reason,
        capability_evidence=dict(profile.capability_evidence),
    )


def _hard_filter(profile: ModelProfile, request: RoutingRequest) -> str:
    """Return a rejection reason, or "" if the model may be considered.

    Everything here makes a result invalid rather than merely worse, which is
    why none of it is expressed as a score.
    """
    if not profile.enabled:
        return "model is disabled"
    if profile.model_id in request.excluded_models or profile.key in request.excluded_models:
        return "model is explicitly excluded by the request"
    if request.role and request.role in profile.prohibited_roles:
        return f"model is prohibited for role {request.role!r}"
    if request.preferred_provider and profile.provider != request.preferred_provider:
        return f"provider {profile.provider!r} is not the required {request.preferred_provider!r}"
    if request.local_only and not profile.is_local():
        return "request is local-only and this model is not local"

    for capability in request.hard_capabilities():
        state = profile.supports(capability)
        if not caps.satisfies(state, capability):
            # UNKNOWN is a rejection for safety-critical capabilities: claiming
            # support ARIA cannot verify is exactly what this must not do.
            return (
                f"requires {capability} but model reports {state} "
                f"({profile.evidence_for(capability)})"
            )

    needed = request.total_context_needed()
    if needed and profile.context_window and profile.context_window < needed:
        return (
            f"context window {profile.context_window} is below the required {needed} "
            f"(prompt {request.min_context_tokens} + reserve {request.output_reserve_tokens})"
        )
    if needed and not profile.context_window:
        return "context requirement given but the model's context window is unknown"

    if health.is_avoided(profile.model_id):
        return health.avoidance_reason(profile.model_id)
    return ""


def _score(
    profile: ModelProfile, request: RoutingRequest, task: str, free_bytes: int = -1
) -> tuple[float, dict]:
    breakdown: dict[str, float] = {}

    if request.preferred_model and profile.model_id == request.preferred_model:
        breakdown["preferred_model"] = WEIGHTS["preferred_model"]
    if request.preferred_provider and profile.provider == request.preferred_provider:
        breakdown["preferred_provider"] = WEIGHTS["preferred_provider"]

    strength_field = _TASK_STRENGTH.get(task, "general_strength")
    breakdown["task_specialisation"] = (
        getattr(profile, strength_field, 0.5) * WEIGHTS["task_specialisation"]
    )

    if request.preferred_capabilities:
        met = sum(1 for c in request.preferred_capabilities if profile.satisfies(c))
        breakdown["preferred_capabilities"] = (met / len(request.preferred_capabilities)) * WEIGHTS[
            "preferred_capabilities"
        ]

    needed = request.total_context_needed()
    if profile.context_window:
        if needed:
            # Enough headroom scores well; enormous excess is not extra credit.
            ratio = min(profile.context_window / max(needed, 1), 4.0) / 4.0
        else:
            ratio = min(profile.context_window / 131072, 1.0)
        breakdown["context_fit"] = ratio * WEIGHTS["context_fit"]

    latency_fit = {
        FAST: {profiles.FAST: 1.0, profiles.MEDIUM: 0.4, profiles.SLOW: 0.0},
        BALANCED: {profiles.FAST: 0.6, profiles.MEDIUM: 1.0, profiles.SLOW: 0.5},
        QUALITY: {profiles.FAST: 0.2, profiles.MEDIUM: 0.6, profiles.SLOW: 1.0},
    }[request.latency_preference]
    breakdown["latency_match"] = latency_fit[profile.latency_class] * WEIGHTS["latency_match"]

    quality = 1.0 if profile.supports(caps.HIGH_QUALITY) == caps.SUPPORTED else 0.5
    if request.latency_preference == FAST:
        quality *= 0.5
    breakdown["quality"] = quality * WEIGHTS["quality"]

    entry = health.get(profile.model_id)
    if entry is None:
        breakdown["health"] = 0.75 * WEIGHTS["health"]  # unproven, not penalised
    else:
        breakdown["health"] = (1.0 - entry.failure_rate()) * WEIGHTS["health"]

    breakdown["priority"] = min(max(profile.priority, -5), 5) / 5.0 * WEIGHTS["priority"]

    fits = profiles.fits_in_memory(profile, free_bytes)
    if fits is not None:
        breakdown["memory_fit"] = (1.0 if fits else 0.0) * WEIGHTS["memory_fit"]

    return round(sum(breakdown.values()), 6), breakdown


def route(
    request: RoutingRequest, *, candidates: list[ModelProfile] | None = None
) -> RoutingDecision:
    """Choose a model, and explain the choice."""
    validate(request)
    task = _task_for(request)
    pool = candidates if candidates is not None else profiles.all_profiles()

    decision = RoutingDecision(
        request=request.to_dict(),
        preferred_model=request.preferred_model,
        preferred_model_status="not_requested" if not request.preferred_model else "unknown",
    )

    # Read free memory once so every candidate is judged against the same state.
    free_bytes = profiles.available_vram_bytes()
    evaluated: list[tuple[float, ModelProfile, dict]] = []
    for profile in sorted(pool, key=lambda p: p.model_id):
        reason = _hard_filter(profile, request)
        if reason:
            decision.candidates.append(_reject(profile, reason))
            if request.preferred_model and profile.model_id == request.preferred_model:
                decision.preferred_model_status = f"rejected: {reason}"
            continue
        score, breakdown = _score(profile, request, task, free_bytes)
        evaluated.append((score, profile, breakdown))
        decision.candidates.append(
            Candidate(
                model_id=profile.model_id,
                provider=profile.provider,
                score=score,
                accepted=True,
                score_breakdown=breakdown,
                capability_evidence={
                    c: profile.evidence_for(c) for c in request.hard_capabilities()
                },
            )
        )

    if not evaluated:
        decision.selection_method = NONE_AVAILABLE
        decision.reason = (
            f"no model satisfies the requirements "
            f"({', '.join(request.hard_capabilities()) or 'no hard capabilities'}); "
            f"{len(decision.candidates)} candidate(s) rejected"
        )
        if request.preferred_model and decision.preferred_model_status == "unknown":
            decision.preferred_model_status = "not_registered"
        return decision

    # Deterministic: score first, then model_id, so equal scores never shuffle.
    evaluated.sort(key=lambda item: (-item[0], item[1].model_id))
    score, chosen, _ = evaluated[0]

    decision.selected_model = chosen.model_id
    decision.provider = chosen.provider
    decision.score = score
    decision.capability_evidence = {c: chosen.evidence_for(c) for c in request.hard_capabilities()}

    if request.preferred_model and chosen.model_id == request.preferred_model:
        decision.selection_method = PREFERRED
        decision.preferred_model_used = True
        decision.preferred_model_status = "used"
        decision.reason = f"preferred model {chosen.model_id} satisfies every requirement"
    else:
        decision.selection_method = SCORED
        if request.preferred_model and decision.preferred_model_status == "unknown":
            decision.preferred_model_status = "not_registered"
        decision.reason = (
            f"{chosen.model_id} scored highest ({score:.3f}) for task {task!r} "
            f"among {len(evaluated)} compatible model(s)"
        )
        if request.preferred_model:
            # The status was recorded but never said out loud: a caller who
            # asked for a specific model was handed a different one with no
            # mention that its request could not be honoured.
            decision.reason += (
                f"; requested {request.preferred_model!r} was not used "
                f"({decision.preferred_model_status})"
            )
    return decision


def explain(request: RoutingRequest) -> dict[str, Any]:
    """Route without invoking anything: the decision and its reasoning."""
    return route(request).to_dict()
