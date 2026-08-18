"""Browser / computer use — durable, permissioned, observable browser control.

Drives ARIA's existing Playwright stack; adds session identity, structured
actions, impact-based permissions, navigation safety, secret redaction,
execution bounds and artifact retention.
"""

from jarvis.computer_use.actions import (
    ACTIONS,
    HIGH_IMPACT,
    HIGH_IMPACT_ACTIONS,
    INTERACT,
    INTERACT_ACTIONS,
    LIMITS,
    READ,
    READ_ACTIONS,
    ActionError,
    NavigationBlocked,
    check_url,
    impact_of,
    redact,
    redact_params,
    validate,
)
from jarvis.computer_use.engine import PlaywrightDriver, open_session, perform, run_steps
from jarvis.computer_use.evidence_bridge import capture_page_evidence
from jarvis.computer_use.permissions import (
    HIGH_IMPACT_ACTION,
    INTERACT_ACTION,
    READ_ACTION,
    BrowserPermissionDenied,
    agent_may,
    check_agent_action,
    gate_for,
)
from jarvis.computer_use.retention import prune_screenshots, usage
from jarvis.computer_use.sessions import SessionError, list_sessions, reap_expired, reset
from jarvis.computer_use.sessions import close as close_session
from jarvis.computer_use.sessions import get as get_session

__all__ = [
    "ACTIONS",
    "HIGH_IMPACT",
    "HIGH_IMPACT_ACTION",
    "HIGH_IMPACT_ACTIONS",
    "INTERACT",
    "INTERACT_ACTION",
    "INTERACT_ACTIONS",
    "LIMITS",
    "READ",
    "READ_ACTION",
    "READ_ACTIONS",
    "ActionError",
    "BrowserPermissionDenied",
    "NavigationBlocked",
    "PlaywrightDriver",
    "SessionError",
    "agent_may",
    "capture_page_evidence",
    "check_agent_action",
    "check_url",
    "close_session",
    "gate_for",
    "get_session",
    "impact_of",
    "list_sessions",
    "open_session",
    "perform",
    "prune_screenshots",
    "reap_expired",
    "redact",
    "redact_params",
    "reset",
    "run_steps",
    "usage",
    "validate",
]
