"""Conversation behavior — isolated chat engine extracted from JarvisAssistant."""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jarvis import llm
from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.config import is_uncensored
from jarvis.handlers.registry import register_action
from jarvis.ollama_health import check_ollama
from jarvis.response import err as _err
from jarvis.response import ok as _ok
from jarvis.response import stream_done as _stream_done

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant

_CONVERSATION_DEPENDENCIES = [
    "memory",
    "retrieval",
    "capability_registry",
    "workflow_manager",
]

_USER_SAFE_BACKEND = (
    "I couldn't complete that reply just now. Please try again in a moment — "
    "if it keeps failing, check that the local model service is running."
)

# Owner-facing text per failure category (jarvis.inference.boundary.classify_failure).
# Says what went wrong and what helps, without backend text or model internals.
_CATEGORY_MESSAGES = {
    "out_of_memory": (
        "I couldn't load the chat model: the graphics card doesn't have enough free memory "
        "right now (an image job or another model may be holding it). Try again in a moment, "
        "or free GPU memory first."
    ),
    "model_load_failed": "The chat model failed to start. Please try again in a moment.",
    "model_missing": (
        "The configured chat model isn't installed. Choose an installed model in "
        "Settings → Models, or download it."
    ),
    "connection_refused": (
        "I couldn't reach the local model service — it may be restarting. "
        "Try again in a few seconds."
    ),
    "service_unavailable": "The local model service returned an error. Please try again in a moment.",
    "timeout": (
        "The model took too long to answer. Please try again; if it keeps happening, "
        "the system may be busy with another job."
    ),
    "context_overflow": (
        "This conversation is longer than the model can read at once. "
        "Start a new chat or shorten the message."
    ),
    "invalid_response": "The model's reply came back unreadable. Please try again.",
    "stream_interrupted": (
        "The reply was cut off partway through, so the partial answer above is incomplete "
        "and wasn't saved. Please try again."
    ),
}

logger = logging.getLogger("jarvis.conversation")


def _log_chat_failure(stage: str, exc: BaseException, *, request_id: str, model: str, usage: dict) -> str:
    """One structured line per failed chat; returns the category. Never logs message content."""
    from jarvis.inference.boundary import classify_failure

    category = classify_failure(exc)
    receipt = usage.get("receipt") if isinstance(usage.get("receipt"), dict) else {}
    attempts = receipt.get("attempts") or []
    logger.warning(
        "chat failed request_id=%s stage=%s category=%s model=%s attempts=%s fallback=%s "
        "receipt=%s error=%s",
        request_id or "-",
        stage,
        category,
        model or "-",
        len(attempts),
        bool(receipt.get("fallback_used")),
        receipt.get("id") or "-",
        f"{type(exc).__name__}: {str(exc)[:300]}",
    )
    return category


def _sanitize_user_error(exc: BaseException | str) -> str:
    """Never surface backend/model implementation details to end users."""
    text = str(exc or "").strip()
    lower = text.lower()
    if (
        "returned empty" in lower
        or "ollama" in lower
        or re.search(r"\bmodel\s*[`']?[\w.:-]+", text, re.I)
        or "connection refused" in lower
        or "status code" in lower
        or "traceback" in lower
    ):
        return _USER_SAFE_BACKEND
    if len(text) > 240:
        return _USER_SAFE_BACKEND
    return text or _USER_SAFE_BACKEND


def _record_backend_failure(detail: str) -> None:
    """Keep failure diagnostics off the user path (Conversation Trace / events)."""
    try:
        from aria_core.event_bus import safe_publish

        safe_publish(
            "InferenceBackendFailure",
            source="jarvis.conversation",
            detail=(detail or "")[:240],
            user_visible=False,
        )
    except Exception:
        pass


class ConversationEngine:
    """Conversation context assembly, LLM dispatch, and persistence."""

    def __init__(self, assistant: JarvisAssistant) -> None:
        self._a = assistant

    @staticmethod
    def memory_citation(entry: dict) -> dict:
        from jarvis.behaviors.memory.engine import MemoryEngine

        return MemoryEngine.memory_citation(entry)

    def build_context_prefix(
        self,
        message: str,
        *,
        skip_unified_extras: bool = False,
    ) -> tuple[str, list[str], list[dict]]:
        import time as _time

        from jarvis.context.policy import (
            cached_language_hint,
            context_needs,
            local_clock_line,
            record_inventory,
        )
        from jarvis.router import is_general_knowledge_question, is_meta_self_question
        from jarvis.runtime_routing import is_runtime_routing_question

        parts: list[str] = []
        warnings: list[str] = []
        citations: list[dict] = []
        inventory: dict[str, Any] = {"message": (message or "")[:120], "sources": {}}

        needs = context_needs(message)
        runtime_self = is_runtime_routing_question(message)
        general = is_general_knowledge_question(message, self._a.session)
        skip_project_context = (
            needs.lightweight
            or general
            or is_meta_self_question(message)
            or runtime_self
        )

        def _note(source: str, t0: float, chunks: list[str] | str, *, used: bool) -> None:
            text = chunks if isinstance(chunks, str) else "\n".join(chunks or [])
            inventory["sources"][source] = {
                "elapsed_ms": round((_time.perf_counter() - t0) * 1000, 1),
                "characters": len(text or ""),
                "required": used,
                "injected": bool(text and used),
            }

        if needs.local_clock:
            t0 = _time.perf_counter()
            line = local_clock_line()
            parts.append(line)
            _note("local_clock", t0, line, used=True)

        if needs.memory:
            from jarvis.behaviors.memory import get_memory_behavior

            memory_behavior = get_memory_behavior()
            if memory_behavior is not None:
                t0 = _time.perf_counter()
                try:
                    mem_parts, mem_citations = memory_behavior.prepare_context(
                        self._a,
                        message,
                        general=general,
                        skip_project_context=skip_project_context,
                    )
                except Exception as exc:  # noqa: BLE001 - answer without memory, and say so
                    logger.warning("memory retrieval failed; answering without it: %s: %s",
                                   type(exc).__name__, str(exc)[:200])
                    mem_parts = [
                        "Long-term memory: UNAVAILABLE — retrieval failed this turn. "
                        "Do not claim to remember or not remember anything specific."
                    ]
                    mem_citations = []
                    warnings.append("Memory was unavailable for this reply.")
                parts.extend(mem_parts)
                citations.extend(mem_citations)
                _note("memory", t0, mem_parts, used=True)
            else:
                inventory["sources"]["memory"] = {
                    "elapsed_ms": 0,
                    "characters": 0,
                    "required": False,
                    "injected": False,
                }
        else:
            inventory["sources"]["memory"] = {
                "elapsed_ms": 0,
                "characters": 0,
                "required": False,
                "injected": False,
            }

        if needs.continuity:
            t0 = _time.perf_counter()
            try:
                from jarvis import continuity

                branches = getattr(self._a, "branches", None)
                found = continuity.retrieve(message, branch=getattr(branches, "active_id", None))
                block = found.to_prompt()
                parts.append(block)
                if found.status in (continuity.HITS, continuity.PARTIAL):
                    citations.extend(found.citations())
                inventory["continuity_status"] = found.status
                _note("continuity", t0, block, used=True)
            except Exception as exc:  # noqa: BLE001 - say so; never imply "no record"
                parts.append(
                    "Conversation history: UNAVAILABLE — the history search failed "
                    f"({type(exc).__name__}). Do not claim there is no record."
                )
                inventory["continuity_status"] = "UNAVAILABLE"
                _note("continuity", t0, "", used=True)

        if needs.planning_tasks or needs.weather:
            from jarvis.behaviors.planning import get_planning_behavior

            planning_behavior = get_planning_behavior()
            if planning_behavior is not None:
                t0 = _time.perf_counter()
                plan_parts, _plan_citations = planning_behavior.prepare_context(
                    self._a,
                    message,
                    skip_project_context=skip_project_context or not needs.planning_tasks,
                    include_weather=needs.weather,
                    include_tasks=needs.planning_tasks,
                )
                parts.extend(plan_parts)
                _note("planning", t0, plan_parts, used=True)
            else:
                inventory["sources"]["planning"] = {
                    "elapsed_ms": 0,
                    "characters": 0,
                    "required": False,
                    "injected": False,
                }
        else:
            inventory["sources"]["planning"] = {
                "elapsed_ms": 0,
                "characters": 0,
                "required": False,
                "injected": False,
            }

        if needs.knowledge_topics or needs.documents or needs.web_search:
            from jarvis.behaviors.knowledge import get_knowledge_behavior

            knowledge_behavior = get_knowledge_behavior()
            if knowledge_behavior is not None:
                t0 = _time.perf_counter()
                know_parts, know_citations = knowledge_behavior.prepare_context(
                    self._a,
                    message,
                    general=general,
                    skip_project_context=skip_project_context,
                    include_topics=needs.knowledge_topics,
                    include_documents=needs.documents,
                    include_web=needs.web_search and not needs.lightweight,
                )
                parts.extend(know_parts)
                citations.extend(know_citations)
                know_warnings = getattr(knowledge_behavior, "_last_warnings", [])
                warnings.extend(know_warnings)
                _note("knowledge", t0, know_parts, used=True)
            else:
                inventory["sources"]["knowledge"] = {
                    "elapsed_ms": 0,
                    "characters": 0,
                    "required": False,
                    "injected": False,
                }
        else:
            inventory["sources"]["knowledge"] = {
                "elapsed_ms": 0,
                "characters": 0,
                "required": False,
                "injected": False,
            }

        if needs.relationships:
            t0 = _time.perf_counter()
            try:
                from jarvis.relationship_memory import relationship_context_for_chat

                conn_ctx = relationship_context_for_chat(message, limit=6)
                if conn_ctx:
                    parts.append(conn_ctx)
                _note("relationships", t0, conn_ctx or "", used=True)
            except Exception:
                _note("relationships", t0, "", used=True)
        else:
            inventory["sources"]["relationships"] = {
                "elapsed_ms": 0,
                "characters": 0,
                "required": False,
                "injected": False,
            }

        if getattr(needs, "health", False):
            t0 = _time.perf_counter()
            try:
                from jarvis.health_product.context import health_context_for_chat

                health_ctx = health_context_for_chat(message, limit=8)
                if health_ctx:
                    parts.append(health_ctx)
                _note("health", t0, health_ctx or "", used=True)
            except Exception:
                _note("health", t0, "", used=True)
        else:
            inventory["sources"]["health"] = {
                "elapsed_ms": 0,
                "characters": 0,
                "required": False,
                "injected": False,
            }

        t0 = _time.perf_counter()
        lang_hint = cached_language_hint(message)
        if lang_hint:
            parts.append(lang_hint)
        _note("language", t0, lang_hint or "", used=True)

        from jarvis.resource_router import chat_busy_hint

        if needs.lightweight:
            inventory["sources"]["busy_hint"] = {
                "elapsed_ms": 0,
                "characters": 0,
                "required": False,
                "injected": False,
            }
        else:
            t0 = _time.perf_counter()
            busy_hint = chat_busy_hint()
            if busy_hint:
                parts.append(busy_hint)
            _note("busy_hint", t0, busy_hint or "", used=bool(busy_hint))

        if not skip_project_context and not skip_unified_extras and needs.project_extras:
            t0 = _time.perf_counter()
            try:
                from jarvis.context.builder import append_context_extras

                meta: dict = {}
                before = len(parts)
                append_context_extras(parts, self._a, message, meta)
                added = parts[before:]
                _note("project_extras", t0, added, used=True)
            except Exception:
                _note("project_extras", t0, "", used=True)
        else:
            inventory["sources"]["project_extras"] = {
                "elapsed_ms": 0,
                "characters": 0,
                "required": False,
                "injected": False,
            }

        prefix = "\n\n".join(parts)
        inventory["prefix_characters"] = len(prefix)
        inventory["lightweight"] = needs.lightweight
        record_inventory(inventory)
        try:
            from jarvis.latency_observability.trace import active_trace

            tr = active_trace()
            if tr is not None:
                tr.set_context_inventory(inventory)
                total_ctx = sum(
                    float((info or {}).get("elapsed_ms") or 0)
                    for info in (inventory.get("sources") or {}).values()
                )
                tr.note_stage("context_assembly", total_ctx, sources=len(inventory.get("sources") or {}))
        except Exception:
            pass
        return prefix, warnings, citations

    def messages_for_llm(self, messages: list[dict], context_prefix: str, *, selected_model: str = "") -> list[dict]:
        if not context_prefix or not messages or messages[-1].get("role") != "user":
            return messages
        from jarvis.inference.boundary import is_cloud_model
        if is_cloud_model(selected_model):
            # Retrieved context is not the current turn: enforce its disclosure class.
            return [{"role": "system", "content": context_prefix}, *messages]
        out = list(messages)
        raw = out[-1]["content"]
        out[-1] = {"role": "user", "content": f"{context_prefix}\n\nUser: {raw}"}
        return out

    def prepare_user_message(self, message: str, params: dict) -> str:
        user_message = message
        file_path = params.get("file_path", "")
        if file_path:
            snippet = self._read_upload_snippet(file_path)
            name = Path(file_path).name
            if snippet:
                user_message = f"Attached file `{name}`:\n```\n{snippet}\n```\n\n{message}"
        return user_message

    def _read_upload_snippet(self, path: str, limit: int = 12000) -> str:
        try:
            file_path = Path(path)
            if not file_path.is_file():
                return ""
            text = file_path.read_text(encoding="utf-8", errors="replace")
            if len(text) > limit:
                return text[:limit] + "\n… (truncated)"
            return text
        except OSError:
            return ""

    def ask_instruction_sentence(self, topic: str, n_words: int) -> str:
        from jarvis.capability_routing import resolve_model_for_capability

        model = resolve_model_for_capability("summarization") or llm.conversation_model()
        msgs = [
            {
                "role": "system",
                "content": "Reply with exactly one sentence. No numbering, quotes, or extra lines.",
            },
            {
                "role": "user",
                "content": f"Write exactly {n_words} words about {topic}. Output only that sentence.",
            },
        ]
        answer, _ = llm.ask_with_usage(model, msgs, temperature=0, role="summarization")
        return answer.strip()

    def try_strict_instructions(self, message: str) -> str | None:
        from jarvis.instruction_follow import try_execute_strict_instructions

        return try_execute_strict_instructions(
            message,
            lambda topic, n, _orig: self.ask_instruction_sentence(topic, n),
        )

    def auto_remember(self, user_msg: str, assistant_msg: str) -> None:
        from jarvis.behaviors.memory import get_memory_behavior

        behavior = get_memory_behavior()
        if behavior is not None:
            behavior.auto_remember(self._a, user_msg, assistant_msg)

    def _learn_preferences(self, model: str) -> None:
        try:
            from jarvis.personalization.learner import learn_from_active_project, learn_from_chat

            learn_from_chat(model=model, role="general")
            learn_from_active_project()
        except Exception:
            pass

    def _apply_answer_integrity_gates(
        self,
        user_message: str,
        answer: str,
        *,
        memory_citations: list | None = None,
        context_warnings: list | None = None,
    ) -> str:
        """Memory honesty + consequential-spec verification before owner-facing text."""
        text = answer or ""
        try:
            from jarvis.orchestration_policy import (
                answer_has_actionable_destructive_command,
                destructive_system_refusal,
                is_destructive_system_request,
                memory_honesty_refusal,
                should_apply_memory_honesty,
                strip_or_refuse_unverified_specs,
            )

            if is_destructive_system_request(user_message) or (
                answer_has_actionable_destructive_command(text)
                and re.search(
                    r"\b(?:wipe|erase|destroy|rm\s+-rf|root\s+filesystem|boot\s+drive)\b",
                    user_message or "",
                    re.I,
                )
            ):
                return destructive_system_refusal(user_message)

            had_memory = bool(memory_citations)
            if should_apply_memory_honesty(
                user_message, text, had_memory_hits=had_memory
            ):
                return memory_honesty_refusal(user_message)

            # Web/knowledge citations in context_warnings or answer Sources block count.
            verified = bool(
                re.search(r"\*\*sources\*\*|^\s*\[\d+\]\s+\S+", text, re.I | re.M)
                or any("web" in str(w).lower() for w in (context_warnings or []))
            )
            refused = strip_or_refuse_unverified_specs(
                user_message, text, verified=verified
            )
            if refused:
                return refused

            # Current-information must not silently use stale model knowledge.
            from jarvis.orchestration_policy import research_required

            if research_required(user_message) and not verified:
                if re.search(
                    r"\b(?:latest|current|currently|newest|does\s+.+\s+exist|version\s+\d)",
                    user_message or "",
                    re.I,
                ):
                    return (
                        "I can't verify the current value from retrieved evidence right now, "
                        "so I won't substitute a possibly stale model estimate. "
                        "Ask me to search the web, or provide an official source URL."
                    )
        except Exception:
            pass
        return text

    def _requested_model(self, params: dict) -> str:
        return str(getattr(self._a.session, "chat_model", "") or params.get("model") or "").strip()

    def _model_override_selected(self, params: dict) -> bool:
        from jarvis.inference.boundary import is_cloud_model

        return bool(getattr(self._a.session, "chat_model", "") or is_cloud_model(self._requested_model(params)))

    def _needs_local_runtime(self, params: dict) -> bool:
        """Only a request that will run locally depends on Ollama being up."""
        from jarvis.inference.boundary import needs_local_runtime

        requested = self._requested_model(params)
        if self._model_override_selected(params):
            from jarvis.inference.boundary import is_cloud_model
            if is_cloud_model(requested):
                return False  # Authorization errors must not become local-health errors.
        return needs_local_runtime(requested)

    def _inference_error(self, params: dict, exc: BaseException) -> str:
        from jarvis.inference import boundary
        requested = self._requested_model(params)
        if self._model_override_selected(params) and boundary.is_cloud_model(requested):
            if isinstance(exc, boundary.StreamInterrupted):
                return str(exc)
            provider = boundary.provider_of(requested)
            label = {"google": "Gemini", "openai": "OpenAI", "anthropic": "Anthropic"}.get(provider, provider)
            reason = "could not complete this request"
            if isinstance(exc, boundary.CloudNotPermitted):
                reason = "is not authorized under the current provider, privacy or spending settings"
            elif isinstance(exc, boundary.ProviderUnavailable):
                reason = "is unavailable; check its credentials, quota and selected model"
            return f"Selected {label} provider {reason}. No local fallback was used."
        from jarvis.gpu_scheduler import GpuUnavailable, WorkloadCutoff

        cause: BaseException | None = exc
        while cause is not None:  # GPU admission reasons are owner-facing, not backend detail
            if isinstance(cause, WorkloadCutoff):
                return f"I stopped that reply to protect the system: {cause.reason}. Try again once it cools."
            if isinstance(cause, GpuUnavailable):
                return f"That reply couldn't start yet: {cause.reason}."
            cause = cause.__cause__ or cause.__context__
        message = _CATEGORY_MESSAGES.get(boundary.classify_failure(exc))
        return message or _sanitize_user_error(exc)

    def execute(self, params: dict, message: str) -> dict:
        from jarvis.branding import assistant_name

        # Tags-only: soft generate probes compete with real chat for VRAM/time.
        # A permitted cloud target does not depend on local Ollama health.
        ollama = (
            check_ollama(soft_probe=False) if self._needs_local_runtime(params) else {"running": True}
        )
        if not ollama["running"]:
            return _err(
                "Ollama is still starting. Wait a few seconds and try again — "
                f"{assistant_name()} starts it automatically.",
                module=None,
            )

        user_message = self.prepare_user_message(message, params)
        if params.get("routing_explain"):
            from jarvis.routing_explain import explain_routing

            text = str(params.get("explain_text") or explain_routing(message))
            return _ok(text, module=None, type="routing_explain")
        fixed = str(params.get("policy_fixed_reply") or "").strip()
        if fixed:
            self._a.conversation.add_user(user_message)
            self._a.conversation.add_assistant(fixed)
            self._a.branches.persist(session=self._a.session)
            return _ok(fixed, module=None, type="policy_refusal")
        piped = self.try_strict_instructions(user_message)
        if piped:
            self._a.conversation.add_user(user_message)
            self._a.conversation.add_assistant(piped)
            self._a.branches.persist(session=self._a.session)
            return _ok(piped, module=None, type="instruction_follow")

        context_prefix, context_warnings, memory_citations = self.build_context_prefix(user_message)
        retrieval_hint = ""
        if memory_citations:
            from jarvis.learning_notice import memory_retrieval_hint, set_retrieval_hint

            retrieval_hint = memory_retrieval_hint(memory_citations)
            if retrieval_hint:
                set_retrieval_hint(retrieval_hint)
        from jarvis.instruction_follow import (
            is_strict_instruction_prompt,
            strict_instruction_context_prefix,
        )

        if is_strict_instruction_prompt(user_message):
            hint = strict_instruction_context_prefix()
            context_prefix = f"{hint}\n\n{context_prefix}" if context_prefix else hint
        self._a.conversation.add_user(user_message)
        from jarvis.capability_routing import resolve_conversation_model

        model, chat_role = resolve_conversation_model(
            user_message,
            params,
            session_chat_model=(self._a.session.chat_model or "").strip(),
            action="chat",
        )
        usage: dict = {}
        from jarvis.chat_lanes import lane_for

        lane = lane_for(model, explicit=self._model_override_selected(params), role=chat_role)
        try:
            msgs = self.messages_for_llm(self._a.conversation.messages, context_prefix, selected_model=model)
            t0 = time.perf_counter()
            answer = ""
            if lane is not None:
                try:
                    with lane.scope():
                        answer, usage = llm.ask_with_usage(lane.model, lane.fit(msgs), role=chat_role, **lane.kwargs)
                    model = lane.model
                    answer = f"{answer.rstrip()}\n\n{lane.note}" if answer.strip() else answer
                except Exception as exc:  # noqa: BLE001 — helper unavailable: wait for the RTX as before
                    logger.info("RX 7600 chat lane unavailable (%s); using %s", exc, model)
                    answer = ""
            if not answer.strip():
                answer, usage = llm.ask_with_usage(
                    model, msgs, role=chat_role, explicit_model=self._model_override_selected(params)
                )
            inference_ms = int((time.perf_counter() - t0) * 1000)
        except Exception as exc:
            self._a.conversation.pop_last_user()
            _record_backend_failure(str(exc))
            category = _log_chat_failure("provider", exc, request_id="", model=model, usage=usage)
            return _err(self._inference_error(params, exc), module=None, error_category=category)
        if not answer.strip():
            self._a.conversation.pop_last_user()
            detail = f"Model `{model}` returned empty"
            _record_backend_failure(detail)
            return _err(_sanitize_user_error(detail), module=None)
        answer = self._apply_answer_integrity_gates(
            user_message,
            answer,
            memory_citations=memory_citations,
            context_warnings=context_warnings,
        )
        self._a.conversation.add_assistant(answer)
        self.auto_remember(message, answer)
        self._learn_preferences(model)
        self._a.branches.persist(session=self._a.session)
        display = answer
        if retrieval_hint:
            from jarvis.learning_notice import append_retrieval_to_message

            display = append_retrieval_to_message(answer, retrieval_hint)
        extra: dict = {
            "inference_ms": inference_ms,
            **usage,
            "model": usage.get("execution_model") or model,
            "requested_model": model,
        }
        if context_warnings:
            extra["warnings"] = context_warnings
        if memory_citations:
            extra["memory_citations"] = memory_citations
        return _ok(display, module=None, **extra)

    def execute_stream(
        self,
        message: str,
        params: dict,
        *,
        request_id: str = "",
    ) -> Iterator[dict]:
        from jarvis.branding import assistant_name

        # Emit immediately so SSE heartbeats can flow while we validate the provider.
        yield {"type": "status", "message": "Checking provider…"}
        # Tags-only reachability — never soft-probe generate on the chat hot path.
        # A generate probe (up to ~5s) serializes behind / contends with the real
        # first token and is a systemic FIRST_PROGRESS_TIMEOUT contributor.
        ollama = (
            check_ollama(soft_probe=False) if self._needs_local_runtime(params) else {"running": True}
        )
        if not ollama["running"]:
            yield {
                "type": "done",
                "ok": False,
                "message": (
                    f"**Ollama is still starting.** {assistant_name()} is bringing it online — "
                    "try again in a few seconds.\n\n"
                    "Ask **what can you do?** anytime for an instant answer."
                ),
            }
            return

        user_message = self.prepare_user_message(message, params)
        if params.get("routing_explain"):
            from jarvis.routing_explain import explain_routing

            text = str(params.get("explain_text") or explain_routing(message))
            yield _stream_done(_ok(text, module=None, type="routing_explain"))
            return
        fixed = str(params.get("policy_fixed_reply") or "").strip()
        if fixed:
            self._a.conversation.add_user(user_message)
            self._a.conversation.add_assistant(fixed)
            self._a.branches.persist(session=self._a.session)
            yield _stream_done(_ok(fixed, module=None, type="policy_refusal"))
            return
        piped = self.try_strict_instructions(user_message)
        if piped:
            self._a.conversation.add_user(user_message)
            self._a.conversation.add_assistant(piped)
            self._a.branches.persist(session=self._a.session)
            yield _stream_done(_ok(piped, module=None, type="instruction_follow"))
            return

        yield {"type": "status", "message": "Gathering context…"}
        _ctx_t0 = time.perf_counter()
        context_prefix, context_warnings, stream_citations = self.build_context_prefix(user_message)
        try:
            from jarvis.latency_observability.trace import active_trace

            tr = active_trace()
            if tr is not None and not any(s.name == "context_assembly" for s in tr.stages):
                tr.note_stage(
                    "context_assembly",
                    round((time.perf_counter() - _ctx_t0) * 1000, 2),
                )
        except Exception:
            pass
        from jarvis.instruction_follow import (
            is_strict_instruction_prompt,
            strict_instruction_context_prefix,
        )

        if is_strict_instruction_prompt(user_message):
            hint = strict_instruction_context_prefix()
            context_prefix = f"{hint}\n\n{context_prefix}" if context_prefix else hint
        pending = self._a.conversation.messages + [{"role": "user", "content": user_message}]
        _pb_t0 = time.perf_counter()
        msgs = self.messages_for_llm(pending, context_prefix, selected_model=self._requested_model(params))
        try:
            from jarvis.latency_observability.trace import active_trace

            tr = active_trace()
            if tr is not None:
                tr.note_stage(
                    "prompt_build",
                    round((time.perf_counter() - _pb_t0) * 1000, 2),
                    messages=len(msgs),
                    prompt_chars=sum(len(m.get("content") or "") for m in msgs),
                )
        except Exception:
            pass
        from jarvis.chat_cancel import finish as finish_cancel
        from jarvis.chat_cancel import is_cancelled

        from jarvis.capability_routing import resolve_conversation_model

        chat_model, chat_role = resolve_conversation_model(
            user_message,
            params,
            session_chat_model=(self._a.session.chat_model or "").strip(),
            action="chat",
        )
        yield {"type": "status", "message": "Calling model…"}
        from jarvis.inference.boundary import needs_local_runtime, provider_of

        try:
            if not needs_local_runtime(chat_model):
                raise LookupError("cloud target: no local model to warm")
            from jarvis.ollama_runtime import ensure_chat_model_ready

            # SSE layer already ensured GPU residency outside the first-progress
            # clock. Never unload/reload here — size_vram=0 reload was measured
            # burning the FIRST_PROGRESS budget on alternating follow-ups.
            ensure_chat_model_ready(chat_model, allow_reload=False)
        except LookupError:
            pass
        except Exception:
            try:
                from jarvis.ollama_runtime import free_slot_for_chat_model

                free_slot_for_chat_model(chat_model)
            except Exception:
                pass
        full: list[str] = []
        saved_user = False
        stopped = False
        usage: dict = {}
        t0 = time.perf_counter()
        try:
            from jarvis.latency_observability.trace import active_trace

            tr = active_trace()
            if tr is not None:
                tr.note_provider(provider=provider_of(chat_model), model=chat_model, role=chat_role)
                tr.note_model(model=chat_model, role=chat_role)
                tr.start_stage("provider_stream", model=chat_model)
        except Exception:
            pass
        from jarvis.chat_lanes import lane_for

        lane = lane_for(chat_model, explicit=self._model_override_selected(params), role=chat_role)
        stream = None
        if lane is not None:
            # Admission happens on the first chunk: hold the RX 7600 preference only for that.
            try:
                helper_stream = llm.ask_stream(lane.model, lane.fit(msgs), cancel_key=request_id, usage=usage,
                                               role=chat_role, **lane.kwargs)
                with lane.scope():
                    first = next(helper_stream, None)
                if first is not None:
                    chat_model = lane.model

                    def _with_note(first=first, rest=helper_stream):
                        yield first
                        yield from rest
                        yield f"\n\n{lane.note}"

                    stream = _with_note()
            except Exception as exc:  # noqa: BLE001 — helper unavailable: wait for the RTX as before
                logger.info("RX 7600 chat lane unavailable (%s); using %s", exc, chat_model)
                usage.clear()
        try:
            from jarvis.ollama_runtime import chat_priority_section

            with chat_priority_section():
                for chunk in stream or llm.ask_stream(
                    chat_model, msgs, cancel_key=request_id, usage=usage, role=chat_role,
                    explicit_model=self._model_override_selected(params),
                ):
                    if request_id and is_cancelled(request_id):
                        stopped = True
                        break
                    if not saved_user:
                        self._a.conversation.add_user(user_message)
                        saved_user = True
                    full.append(chunk)
                    try:
                        from jarvis.latency_observability.trace import active_trace

                        tr = active_trace()
                        if tr is not None and tr.stream.get("first_token_ms") is None:
                            tr.note_stream(first_token_ms=round((time.perf_counter() - t0) * 1000, 2))
                            tr.end_stage("provider_stream", first_token=True)
                    except Exception:
                        pass
                    if len(full) == 1:
                        try:
                            from jarvis.ollama_health import note_inference_success

                            note_inference_success(chat_model)
                        except Exception:
                            pass
                    yield {"type": "token", "content": chunk}
        except Exception as exc:
            from jarvis.inference.boundary import StreamInterrupted

            if saved_user:
                self._a.conversation.pop_last_user()
            category = _log_chat_failure(
                "provider_stream", exc, request_id=request_id, model=chat_model, usage=usage
            )
            failed = {
                "type": "done",
                "ok": False,
                "message": self._inference_error(params, exc),
                "error_category": category,
                "request_id": request_id,
                "retryable": category not in ("context_overflow", "model_missing", "not_permitted",
                                              "capability_mismatch", "cancelled"),
            }
            if isinstance(exc, StreamInterrupted):
                # The partial text already shown is incomplete; never saved as an answer.
                failed["interrupted"] = True
                failed["partial_chars"] = exc.partial_chars
            if usage.get("receipt"):
                failed["receipt"] = usage["receipt"]
            yield failed
            return
        finally:
            finish_cancel(request_id)

        if stopped:
            answer = "".join(full).strip()
            if saved_user and not answer:
                self._a.conversation.pop_last_user()
            yield {
                "type": "done",
                "ok": True,
                "message": answer or "*(stopped)*",
                "stopped": True,
                "uncensored": is_uncensored(),
            }
            return

        answer = "".join(full)
        if not answer.strip():
            if saved_user:
                self._a.conversation.pop_last_user()
            detail = f"Model `{chat_model}` returned empty"
            _record_backend_failure(detail)
            yield {
                "type": "done",
                "ok": False,
                "message": _sanitize_user_error(detail),
                "backend_error": detail,
            }
            return

        answer = self._apply_answer_integrity_gates(
            user_message,
            answer,
            memory_citations=stream_citations,
            context_warnings=context_warnings,
        )
        self._a.conversation.add_assistant(answer)
        self.auto_remember(message, answer)
        self._learn_preferences(chat_model)
        self._a.branches.persist(session=self._a.session)
        inference_ms = int((time.perf_counter() - t0) * 1000)
        done_payload = {
            "type": "done",
            "ok": True,
            "message": answer,
            "uncensored": is_uncensored(),
            "inference_ms": inference_ms,
            **usage,
            # The model that actually answered (a local fallback may differ from the request).
            "model": usage.get("execution_model") or chat_model,
            "requested_model": chat_model,
        }
        receipt = usage.get("receipt") if isinstance(usage.get("receipt"), dict) else {}
        if receipt.get("fallback_used"):
            if done_payload["model"] != chat_model:
                done_payload["fallback"] = {
                    "from": chat_model,
                    "to": done_payload["model"],
                    "reason": receipt.get("failure_category") or "",
                }
            else:
                done_payload["retried"] = receipt.get("failure_category") or True
        if context_warnings:
            done_payload["warnings"] = context_warnings
        if stream_citations:
            done_payload["memory_citations"] = stream_citations
        yield done_payload

    def branch_create(self, params: dict, message: str) -> dict:
        name = params.get("name") or message.strip() or "Branch"
        branch_id = self._a.create_branch(name)
        return _ok(
            f"Created branch **{name}** (`{branch_id}`). You're now on it.",
            module="general",
            branch_id=branch_id,
        )

    def branch_switch(self, params: dict, message: str) -> dict:
        branch_id = params.get("branch_id") or message.strip()
        if not self._a.switch_branch(branch_id):
            branches = self._a.branches.list_branches()
            lines = "\n".join(f"- `{item['id']}` {item['name']}" for item in branches)
            return _err(f"Unknown branch `{branch_id}`. Available:\n{lines}")
        return _ok(f"Switched to branch `{branch_id}`.", module="general", branch_id=branch_id)

    def branch_list(self, params: dict, message: str) -> dict:
        branches = self._a.branches.list_branches()
        active = self._a.branches.active_id
        lines = "\n".join(
            f"{'→' if item['id'] == active else ' '} `{item['id']}` **{item['name']}** ({item['messages']} msgs)"
            for item in branches
        )
        return _ok(f"**Chat branches:**\n\n{lines}", module="general")

    def branch_delete(self, params: dict, message: str) -> dict:
        raw = params.get("branch_ids") or params.get("branch_id") or message.strip()
        if isinstance(raw, list):
            ids = [str(item).strip() for item in raw if str(item).strip()]
        else:
            ids = [part.strip() for part in re.split(r"[\s,]+", str(raw)) if part.strip()]
        if not ids:
            return _err("Name one or more branch ids to delete (main cannot be removed).")
        result = self._a.delete_branches(ids)
        if not result["deleted"]:
            return _err("No branches deleted — check ids (main is protected).")
        names = ", ".join(f"`{item}`" for item in result["deleted"])
        return _ok(
            f"Deleted {len(result['deleted'])} branch(es): {names}. Active: `{result['active']}`.",
            module="general",
            branch_id=result["active"],
        )


def ensure_conversation_engine(assistant: JarvisAssistant) -> ConversationEngine:
    behavior = get_conversation_behavior()
    if behavior is not None:
        behavior.initialize(assistant)
    engine = getattr(assistant, "_conversation_engine", None)
    if engine is None:
        raise RuntimeError("Conversation engine not initialized")
    return engine


def get_conversation_behavior() -> ConversationBehavior | None:
    from jarvis.behaviors import get_behavior

    behavior = get_behavior("conversation")
    return behavior if isinstance(behavior, ConversationBehavior) else None


_CONVERSATION_ACTIONS = [
    "chat",
    "conversation_language",
    "branch_create",
    "branch_switch",
    "branch_list",
    "branch_delete",
]


@register_behavior
class ConversationBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="conversation",
            name="Conversation",
            category="Conversation",
            description="Chat context assembly, LLM dispatch, conversation persistence, and branches",
            module_path="jarvis.behaviors.conversation",
            test_module="tests.test_behaviors",
            action_names=list(_CONVERSATION_ACTIONS),
            dependencies=list(_CONVERSATION_DEPENDENCIES),
        )
        self._engine: ConversationEngine | None = None

    def initialize(self, assistant: JarvisAssistant) -> None:
        self._engine = ConversationEngine(assistant)
        assistant._conversation_engine = self._engine

    def attach(self) -> list[str]:
        register_action("chat", module="conversation", description="General chat")(
            self._chat_entry
        )
        register_action(
            "conversation_language",
            info=True,
            module="conversation",
            description="Report active conversation language",
        )(self._conversation_language_entry)
        register_action("branch_create", module="general", description="Create chat branch")(
            self._branch_entry("branch_create")
        )
        register_action("branch_switch", module="general", description="Switch chat branch")(
            self._branch_entry("branch_switch")
        )
        register_action("branch_list", info=True, module="general", description="List chat branches")(
            self._branch_entry("branch_list")
        )
        register_action("branch_delete", module="general", description="Delete chat branches")(
            self._branch_entry("branch_delete")
        )
        return []

    def validate(self) -> list[str]:
        import os

        checks = {
            "memory": "JARVIS_PLATFORM_MEMORY_ATTACHED",
            "retrieval": "JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED",
            "capability_registry": "JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED",
            "workflow_manager": "JARVIS_PLATFORM_WORKFLOW_ORCHESTRATION_ATTACHED",
        }
        warnings: list[str] = []
        for dep in self.dependencies:
            env_key = checks.get(dep)
            if env_key and os.getenv(env_key) != "1":
                warnings.append(f"dependency not attached: {dep}")
        return warnings

    def execute(
        self,
        assistant: JarvisAssistant,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        if action not in _CONVERSATION_ACTIONS:
            return None
        if action == "conversation_language":
            return self._conversation_language_entry(assistant, params, message)
        self.initialize(assistant)
        if not self._engine:
            return None
        if action == "chat":
            return self._engine.execute(params, message)
        handler = getattr(self._engine, action)
        return handler(params, message)

    def health(self) -> dict:
        report = super().health()
        report["validation_warnings"] = self.validate()
        report["engine_ready"] = self._engine is not None
        return report

    def shutdown(self) -> None:
        self._engine = None

    def _chat_entry(self, assistant: JarvisAssistant, params: dict, message: str) -> dict:
        return ensure_conversation_engine(assistant).execute(params, message)

    def _conversation_language_entry(
        self, assistant: JarvisAssistant, params: dict, message: str
    ) -> dict:
        from jarvis.lang_util import conversation_language

        prior: list[str] = []
        try:
            msgs = list(getattr(getattr(assistant, "conversation", None), "messages", []) or [])
            prior = [
                str(m.get("content") or "")
                for m in msgs
                if isinstance(m, dict) and m.get("role") == "user"
            ][-8:]
        except Exception:
            prior = []
        code = conversation_language(message or params.get("question") or "", prior_user_texts=prior)
        names = {
            "en": "English",
            "zh": "Chinese",
            "ru": "Russian",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
        }
        label = names.get(code, code)
        return _ok(
            f"We've been speaking in {label}.",
            module="conversation",
            language=code,
            source="language_subsystem",
        )

    def _branch_entry(self, action: str):
        def _entry(assistant: JarvisAssistant, params: dict, message: str) -> dict:
            self.initialize(assistant)
            if not self._engine:
                return _err("Conversation engine not initialized.", module="general")
            handler = getattr(self._engine, action)
            return handler(params, message)

        return _entry
