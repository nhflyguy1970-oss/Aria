"""Conversation behavior — isolated chat engine extracted from JarvisAssistant."""

from __future__ import annotations

import re
import time
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

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
        parts: list[str] = []
        warnings: list[str] = []
        citations: list[dict] = []

        from jarvis.router import is_general_knowledge_question, is_meta_self_question
        from jarvis.runtime_routing import is_runtime_routing_question

        runtime_self = is_runtime_routing_question(message)
        general = is_general_knowledge_question(message, self._a.session)
        skip_project_context = general or is_meta_self_question(message) or runtime_self

        from jarvis.behaviors.knowledge import get_knowledge_behavior
        from jarvis.behaviors.memory import get_memory_behavior
        from jarvis.behaviors.planning import get_planning_behavior

        memory_behavior = get_memory_behavior()
        if memory_behavior is not None:
            mem_parts, mem_citations = memory_behavior.prepare_context(
                self._a,
                message,
                general=general,
                skip_project_context=skip_project_context,
            )
            parts.extend(mem_parts)
            citations.extend(mem_citations)

        planning_behavior = get_planning_behavior()
        if planning_behavior is not None:
            plan_parts, _plan_citations = planning_behavior.prepare_context(
                self._a,
                message,
                skip_project_context=skip_project_context,
            )
            parts.extend(plan_parts)

        knowledge_behavior = get_knowledge_behavior()
        if knowledge_behavior is not None:
            know_parts, know_citations = knowledge_behavior.prepare_context(
                self._a,
                message,
                general=general,
                skip_project_context=skip_project_context,
            )
            parts.extend(know_parts)
            citations.extend(know_citations)
            know_warnings = getattr(knowledge_behavior, "_last_warnings", [])
            warnings.extend(know_warnings)

        from jarvis.lang_util import detect_text_language, language_reply_hint

        lang = detect_text_language(message)
        lang_hint = language_reply_hint(lang)
        if lang_hint:
            parts.append(lang_hint)

        from jarvis.resource_router import chat_busy_hint

        busy_hint = chat_busy_hint()
        if busy_hint:
            parts.append(busy_hint)

        if not skip_project_context and not skip_unified_extras:
            try:
                from jarvis.context.builder import append_context_extras

                meta: dict = {}
                append_context_extras(parts, self._a, message, meta)
            except Exception:
                pass

        return "\n\n".join(parts), warnings, citations

    def messages_for_llm(self, messages: list[dict], context_prefix: str) -> list[dict]:
        if not context_prefix or not messages or messages[-1].get("role") != "user":
            return messages
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
        model = (self._a.session.chat_model or "").strip() or llm.general_model()
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
        answer, _ = llm.ask_with_usage(model, msgs, temperature=0)
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

    def execute(self, params: dict, message: str) -> dict:
        from jarvis.branding import assistant_name

        ollama = check_ollama()
        if not ollama["running"]:
            return _err(
                "Ollama is still starting. Wait a few seconds and try again — "
                f"{assistant_name()} starts it automatically.",
                module=None,
            )

        user_message = self.prepare_user_message(message, params)
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
        model = (params.get("model") or self._a.session.chat_model or "").strip() or llm.general_model()
        usage: dict = {}
        try:
            msgs = self.messages_for_llm(self._a.conversation.messages, context_prefix)
            t0 = time.perf_counter()
            answer, usage = llm.ask_with_usage(model, msgs)
            inference_ms = int((time.perf_counter() - t0) * 1000)
        except Exception as exc:
            self._a.conversation.pop_last_user()
            return _err(str(exc), module=None)
        if not answer.strip():
            self._a.conversation.pop_last_user()
            return _err(
                f"Model `{llm.general_model()}` returned empty. Try: `ollama pull {llm.general_model()}`",
                module=None,
            )
        self._a.conversation.add_assistant(answer)
        self.auto_remember(message, answer)
        self._learn_preferences(model)
        self._a.branches.persist(session=self._a.session)
        display = answer
        if retrieval_hint:
            from jarvis.learning_notice import append_retrieval_to_message

            display = append_retrieval_to_message(answer, retrieval_hint)
        extra: dict = {"inference_ms": inference_ms, "model": model, **usage}
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

        ollama = check_ollama()
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
        piped = self.try_strict_instructions(user_message)
        if piped:
            self._a.conversation.add_user(user_message)
            self._a.conversation.add_assistant(piped)
            self._a.branches.persist(session=self._a.session)
            yield _stream_done(_ok(piped, module=None, type="instruction_follow"))
            return

        yield {"type": "status", "message": "Gathering context…"}
        context_prefix, context_warnings, stream_citations = self.build_context_prefix(user_message)
        from jarvis.instruction_follow import (
            is_strict_instruction_prompt,
            strict_instruction_context_prefix,
        )

        if is_strict_instruction_prompt(user_message):
            hint = strict_instruction_context_prefix()
            context_prefix = f"{hint}\n\n{context_prefix}" if context_prefix else hint
        pending = self._a.conversation.messages + [{"role": "user", "content": user_message}]
        msgs = self.messages_for_llm(pending, context_prefix)
        from jarvis.chat_cancel import finish as finish_cancel
        from jarvis.chat_cancel import is_cancelled

        chat_model = (params.get("model") or self._a.session.chat_model or "").strip() or llm.general_model()
        full: list[str] = []
        saved_user = False
        stopped = False
        usage: dict = {}
        t0 = time.perf_counter()
        try:
            for chunk in llm.ask_stream(chat_model, msgs, cancel_key=request_id, usage=usage):
                if request_id and is_cancelled(request_id):
                    stopped = True
                    break
                if not saved_user:
                    self._a.conversation.add_user(user_message)
                    saved_user = True
                full.append(chunk)
                yield {"type": "token", "content": chunk}
        except Exception as exc:
            if saved_user:
                self._a.conversation.pop_last_user()
            yield {"type": "done", "ok": False, "message": str(exc)}
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
            yield {
                "type": "done",
                "ok": False,
                "message": (
                    f"Model `{llm.general_model()}` returned empty. "
                    f"Try: `ollama pull {llm.general_model()}`"
                ),
            }
            return

        self._a.conversation.add_assistant(answer)
        self.auto_remember(message, answer)
        self._learn_preferences(model)
        self._a.branches.persist(session=self._a.session)
        inference_ms = int((time.perf_counter() - t0) * 1000)
        done_payload = {
            "type": "done",
            "ok": True,
            "message": answer,
            "uncensored": is_uncensored(),
            "model": chat_model,
            "inference_ms": inference_ms,
            **usage,
        }
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

    def _branch_entry(self, action: str):
        def _entry(assistant: JarvisAssistant, params: dict, message: str) -> dict:
            self.initialize(assistant)
            if not self._engine:
                return _err("Conversation engine not initialized.", module="general")
            handler = getattr(self._engine, action)
            return handler(params, message)

        return _entry
