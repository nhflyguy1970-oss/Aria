"""Capability → role → policy → model routing — single authoritative selection layer.

Stage 1: intent/action (router.py, NLU)
Stage 2: capability (this module)
Stage 3: role → model_policy → selected model

Non-LLM capabilities (memory/ACM, Mission Control, speech, embeddings) return model=None.
"""

from __future__ import annotations

from typing import Any

from jarvis.model_store import canonical_role, model_for

# Capabilities that never use a chat LLM in Aria.
NON_LLM_CAPABILITIES = frozenset(
    {
        "memory",
        "episodic_recall",
        "episodic_teaching",
        "mission_control",
        "runtime",
        "speech",
        "stt",
        "tts",
        "greeting",
        "reference",
        "embeddings",
        "image_generation",
    }
)

# Capability → model_store role (None = non-LLM / ACM / Mission Control).
CAPABILITY_TO_ROLE: dict[str, str | None] = {
    "conversation": "conversation",
    "reasoning": "reasoning",
    "planning": "planning",
    "coding": "coding",
    "code_review": "review",
    "debugging": "coding",
    "memory": None,
    "episodic_recall": None,
    "episodic_teaching": None,
    "mission_control": None,
    "runtime": None,
    "vision": "vision",
    "ocr": "vision",
    "speech": None,
    "stt": None,
    "tts": None,
    "tool_calling": "tool_calling",
    "routing": "router",
    "intent_classification": "router",
    "summarization": "summarization",
    "document_analysis": "document",
    "web_research": "web_research",
    "creative_writing": "conversation",
    "math": "reasoning",
    "scientific_reasoning": "reasoning",
    "reflection": "reflection",
    "learning": "learning",
    "workflow_orchestration": "planning",
    "agent_coordination": "planning",
    "image_generation": None,
    "embeddings": None,
    "greeting": None,
    "reference": None,
    "knowledge": "conversation",
    "search": "web_research",
}

ACTION_TO_CAPABILITY: dict[str, str] = {
    "chat": "conversation",
    "coding_chat": "coding",
    "coding_fix": "debugging",
    "coding_generate": "coding",
    "coding_review": "code_review",
    "coding_diagnose": "debugging",
    "coding_patch": "coding",
    "coding_multi_edit": "coding",
    "web_search": "web_research",
    "journal_reflect": "reflection",
    "planner_plan": "planning",
    "document_analyze": "document_analysis",
    "memory_about_user": "memory",
    "remember": "memory",
    "memory_search": "memory",
    "memory_correct": "memory",
    "memory_forget": "memory",
    "recall": "memory",
}


def capability_for_action(action: str) -> str:
    key = (action or "chat").strip().lower()
    return ACTION_TO_CAPABILITY.get(key, "conversation")


def capability_for_action_and_message(action: str, message: str = "") -> str:
    """Finer capability resolution (e.g. episodic recall vs generic memory)."""
    action_key = (action or "chat").strip().lower()
    text = (message or "").strip()
    try:
        from jarvis.nlu.episodic_patterns import is_episodic_memory_query, is_episodic_teaching, is_past_event_memory_question

        if action_key in ("memory_about_user", "remember", "recall", "memory_search"):
            if is_episodic_teaching(text):
                return "episodic_teaching"
            if is_episodic_memory_query(text) or is_past_event_memory_question(text):
                return "episodic_recall"
    except Exception:
        pass
    if action_key.startswith("runtime_") or action_key == "status_summary":
        return "mission_control"
    return capability_for_action(action_key)


def role_for_capability(capability: str) -> str | None:
    key = (capability or "conversation").strip().lower()
    if key in NON_LLM_CAPABILITIES:
        return None
    return CAPABILITY_TO_ROLE.get(key, "conversation")


def configured_model_for_role(role: str) -> str:
    """Registry configured model (no policy overlay)."""
    return model_for(canonical_role(role))


def select_model_via_policy(
    role: str,
    *,
    configured_hint: str = "",
    user_model_override: str = "",
    context_tokens: int = 0,
) -> tuple[str | None, dict[str, Any]]:
    """Role → policy → model. Returns (model, policy_metadata)."""
    from jarvis.model_policy import PolicyContext, select_model_for_role

    selection = select_model_for_role(
        role,
        context=PolicyContext.from_env(
            user_model_override=user_model_override,
            context_tokens=context_tokens,
        ),
        configured_override=(configured_hint or user_model_override or None),
    )
    meta = selection.to_dict()
    return selection.selected_model, meta


def apply_gateway_model(model: str, role: str, *, context_tokens: int = 0) -> str:
    """Policy-selected model for a role (benchmark/hardware/personalization applied)."""
    selected, _meta = select_model_via_policy(
        role,
        configured_hint=model,
        context_tokens=context_tokens,
    )
    return str(selected or model)


def resolve_model_for_capability(capability: str) -> str | None:
    role = role_for_capability(capability)
    if role is None:
        return None
    selected, _ = select_model_via_policy(role)
    return selected


def resolve_conversation_model(
    message: str,
    params: dict | None = None,
    *,
    session_chat_model: str = "",
    voice: bool = False,
    action: str = "chat",
) -> tuple[str, str]:
    """Brain-routed conversational model and registry role."""
    from jarvis.brain_routing import select_chat_model

    params = params or {}
    brain_model = select_chat_model(
        message,
        params,
        action=action,
        voice=voice,
        session_chat_model=session_chat_model,
    )
    role = "reasoning"
    mode = (params.get("thinking_mode") or "").strip().lower()
    if mode == "fast" or voice:
        role = "fast_chat"
    elif mode != "deep" and not _needs_reasoning_role(message, action=action):
        role = "conversation"
    model = apply_gateway_model(brain_model, role)
    _record_capability_trace(action, message, role, model)
    return model, role


def _needs_reasoning_role(message: str, *, action: str) -> bool:
    from jarvis.brain_routing import needs_deep_thinking

    return needs_deep_thinking(message, action=action)


def resolve_model_for_action(
    action: str,
    message: str = "",
    params: dict | None = None,
    *,
    session_chat_model: str = "",
    voice: bool = False,
) -> tuple[str | None, str, str]:
    """Return (model, role, capability) for an action that may need an LLM."""
    capability = capability_for_action_and_message(action, message)
    role = role_for_capability(capability)
    if role is None:
        _record_non_llm_trace(action, message, capability)
        return None, "memory" if capability.startswith("episodic") or capability == "memory" else "", capability

    params = params or {}
    explicit = (params.get("model") or session_chat_model or "").strip()
    if explicit:
        model = apply_gateway_model(explicit, role)
        _record_capability_trace(action, message, role, model, capability=capability)
        return model, role, capability

    if capability in (
        "conversation",
        "reasoning",
        "knowledge",
        "creative_writing",
        "math",
        "scientific_reasoning",
    ):
        model, conv_role = resolve_conversation_model(
            message,
            params,
            session_chat_model=session_chat_model,
            voice=voice,
            action=action,
        )
        return model, conv_role, capability

    model = apply_gateway_model(configured_model_for_role(role), role)
    _record_capability_trace(action, message, role, model, capability=capability)
    return model, role, capability


def _record_capability_trace(
    action: str,
    message: str,
    role: str,
    model: str | None,
    *,
    capability: str | None = None,
) -> None:
    try:
        from jarvis.routing_trace import record_capability, record_intent

        cap = capability or capability_for_action_and_message(action, message)
        record_capability(capability=cap, role=role)
        record_intent(intent=cap, action=action)
    except Exception:
        pass


def _record_non_llm_trace(action: str, message: str, capability: str) -> None:
    try:
        from jarvis.routing_trace import record_capability, record_handler, record_intent

        record_intent(intent=capability, action=action)
        record_capability(capability=capability, role="memory")
        if capability == "mission_control" or action.startswith("runtime_"):
            record_handler(handler="RuntimeClient", provider="mission_control")
        else:
            record_handler(handler="MemoryEngine", provider="acm")
    except Exception:
        pass


def routing_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for capability in sorted(set(CAPABILITY_TO_ROLE) | NON_LLM_CAPABILITIES):
        role = role_for_capability(capability)
        model = resolve_model_for_capability(capability) if role else None
        rows.append(
            {
                "capability": capability,
                "role": role or "(non-llm)",
                "model": model,
                "llm": role is not None,
            }
        )
    return rows
