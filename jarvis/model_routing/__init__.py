"""ARIA model routing — capability-based selection with explainable fallback.

Sits above the model infrastructure ARIA already has: model_store holds the
configured role→model registry, model_policy applies hardware and preference
policy, and jarvis.llm performs the actual call. This layer adds what none of
them do — capabilities established from provider evidence, hard requirements
that cannot be scored away, and fallback that is bounded, classified and
recorded rather than silent.
"""

from jarvis.model_routing.capabilities import (
    CAPABILITIES,
    CODING,
    EMBEDDING,
    EXTRACTION,
    FAST_RESPONSE,
    GENERAL_CHAT,
    HIGH_QUALITY,
    LOCAL_ONLY,
    LONG_CONTEXT,
    REASONING,
    RESEARCH,
    SAFETY_CRITICAL,
    STRUCTURED_OUTPUT,
    SUMMARIZATION,
    SUPPORT_STATES,
    SUPPORTED,
    TOOL_USE,
    UNKNOWN,
    UNSUPPORTED,
    VISION,
    satisfies,
)
from jarvis.model_routing.decision import FALLBACK as FALLBACK_METHOD
from jarvis.model_routing.decision import (
    NONE_AVAILABLE,
    POLICY_VERSION,
    PREFERRED,
    SCORED,
    Candidate,
    RoutingDecision,
)
from jarvis.model_routing.execute import (
    CANCELLED,
    DENIED,
    FAILED,
    STATUSES,
    SUCCESS,
    UNROUTABLE,
    PolicyDenied,
    RoutingCancelled,
    execute,
)
from jarvis.model_routing.failures import (
    FALLBACK_ELIGIBLE,
    NEVER_FALLBACK,
    classify,
    may_fallback,
)
from jarvis.model_routing.health import (
    clear as clear_health,
)
from jarvis.model_routing.health import (
    is_avoided,
    record_failure,
    record_success,
    snapshot,
)
from jarvis.model_routing.profiles import (
    ModelProfile,
    all_profiles,
    discover,
    get_profile,
    register_profile,
    set_override,
)
from jarvis.model_routing.request import RoutingRequest, validate
from jarvis.model_routing.router import ROLE_TASKS, WEIGHTS, explain, route
from jarvis.model_routing.store import counters, history

__all__ = [
    "CANCELLED",
    "CAPABILITIES",
    "CODING",
    "Candidate",
    "DENIED",
    "EMBEDDING",
    "EXTRACTION",
    "FAILED",
    "FALLBACK_ELIGIBLE",
    "FALLBACK_METHOD",
    "FAST_RESPONSE",
    "GENERAL_CHAT",
    "HIGH_QUALITY",
    "LOCAL_ONLY",
    "LONG_CONTEXT",
    "ModelProfile",
    "NEVER_FALLBACK",
    "NONE_AVAILABLE",
    "POLICY_VERSION",
    "PREFERRED",
    "PolicyDenied",
    "REASONING",
    "RESEARCH",
    "ROLE_TASKS",
    "RoutingCancelled",
    "RoutingDecision",
    "RoutingRequest",
    "SAFETY_CRITICAL",
    "SCORED",
    "STATUSES",
    "STRUCTURED_OUTPUT",
    "SUCCESS",
    "SUMMARIZATION",
    "SUPPORTED",
    "SUPPORT_STATES",
    "TOOL_USE",
    "UNKNOWN",
    "UNROUTABLE",
    "UNSUPPORTED",
    "VISION",
    "WEIGHTS",
    "all_profiles",
    "classify",
    "clear_health",
    "counters",
    "discover",
    "execute",
    "explain",
    "get_profile",
    "history",
    "is_avoided",
    "may_fallback",
    "record_failure",
    "record_success",
    "register_profile",
    "route",
    "satisfies",
    "set_override",
    "snapshot",
    "validate",
]
