"""Conversation behavior — isolated chat engine extracted from JarvisAssistant."""

from __future__ import annotations

import re
import time
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from jarvis import llm
from jarvis.behaviors.lifecycle import ApplicationBehavior

from jarvis.behaviors import register_behavior
from jarvis.config import is_uncensored
from jarvis.handlers.registry import register_action
from jarvis.ollama_health import check_ollama
from jarvis.response import err as _err, ok as _ok, stream_done as _stream_done

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
        return {
            "id": entry.get("id"),
            "type": entry.get("type", "fact"),
            "date": (entry.get("created") or entry.get("date") or "")[:10],
            "content": (entry.get("content") or "")[:160],
        }

    def build_context_prefix(self, message: str) -> tuple[str, list[str], list[dict]]:
        parts: list[str] = []
        warnings: list[str] = []
        citations: list[dict] = []
        seen_ids: set[str] = set()

        def _cite(entry: dict, *, kind: str | None = None) -> None:
            eid = entry.get("id") or entry.get("content", "")[:40]
            if eid in seen_ids:
                return
            seen_ids.add(eid)
            citation = self.memory_citation(entry)
            if kind:
                citation["type"] = kind
            citations.append(citation)

        from jarvis import rag
        from jarvis.memory_context import contextualize_memory_for_chat, should_inject_resume_context
        from jarvis.router import is_codebase_question, is_general_knowledge_question, is_meta_self_question
        from jarvis.trust_memory import filter_trusted_content, trust_context_for_chat

        general = is_general_knowledge_question(message, self._a.session)
        skip_project_context = general or is_meta_self_question(message)
        if not llm.embed_available():
            warnings.append(
                f"Semantic memory/RAG unavailable — check embed model `{llm.embed_model()}`."
            )
        ns = self._a.session.memory_namespace
        profile = self._a.memory.list_entries(namespace="profile")
        lower_msg = message.lower()
        trust_ctx = trust_context_for_chat(self._a.memory, message, self._a.session)
        if trust_ctx and not general:
            parts.append(trust_ctx)
            for entry in self._a.memory.list_entries(entry_type="strategy")[:6]:
                if filter_trusted_content(entry.get("content", "")):
                    _cite(entry, kind="strategy")

        if profile and not skip_project_context:
            summary = next((p for p in profile if "summary" in (p.get("tags") or [])), None)
            if summary:
                parts.append(f"User profile:\n- {summary['content']}")
            elif len(profile) <= 6:
                parts.append(
                    "User profile:\n" + "\n".join(f"- {p['content']}" for p in profile[:6])
                )
            if re.search(
                r"\b(like to do|like doing|enjoy|hobby|hobbies|interest|passion|about me|about myself)\b",
                lower_msg,
            ):
                interests = next((p for p in profile if "interests" in (p.get("tags") or [])), None)
                if interests:
                    parts.append(
                        "Answer personal questions from this profile fact:\n"
                        f"- {interests['content']}"
                    )

        if should_inject_resume_context(message, self._a.session):
            cp_ns = ns if ns and ns != "default" else None
            checkpoint = self._a.memory.latest_checkpoint(cp_ns) or self._a.memory.latest_checkpoint()
            if checkpoint:
                cp_line = filter_trusted_content(checkpoint["content"])
                if cp_line:
                    parts.append(f"Project checkpoint (where user left off):\n- {cp_line}")

        if not skip_project_context:
            memories = self._a.memory.search(
                message,
                limit=3,
                namespace=ns if ns and ns != "default" else None,
            )
            if len(memories) < 2 and ns and ns != "default":
                memories = self._a.memory.search(message, limit=3)
            memory_lines = []
            for memory in memories:
                line = contextualize_memory_for_chat(memory["content"])
                line = filter_trusted_content(line) if line else None
                if line and line not in memory_lines:
                    memory_lines.append(line)
            if memory_lines:
                parts.append("Relevant memories:\n" + "\n".join(f"- {line}" for line in memory_lines))
            for memory in memories:
                _cite(memory)

        if not skip_project_context and re.search(
            r"\b(journal|task|todo|to-do|today|priorit|what('s| is) on my plate)\b",
            lower_msg,
        ):
            open_tasks = self._a.journal.format_open_tasks(limit=8)
            if open_tasks != "No open journal tasks.":
                parts.append(f"Open bullet journal tasks:\n{open_tasks}")

        if re.search(
            r"\b(weather|forecast|temperature|rain|snow|tomorrow|today|tonight)\b",
            lower_msg,
        ):
            from jarvis.journal_weather import parse_weather_day, weather_forecast_text

            parts.append(weather_forecast_text(parse_weather_day(message), message=message))

        if is_codebase_question(message, self._a.session):
            doc_ctx, rag_warnings = rag.context_for_query(message)
            warnings.extend(rag_warnings)
            if doc_ctx:
                parts.append(doc_ctx)

        from jarvis.knowledge import context_for_query as knowledge_context

        k_ctx, k_warnings = knowledge_context(message)
        warnings.extend(k_warnings)
        if k_ctx:
            parts.append(k_ctx)

        from jarvis.lang_util import detect_text_language, language_reply_hint

        lang = detect_text_language(message)
        lang_hint = language_reply_hint(lang)
        if lang_hint:
            parts.append(lang_hint)

        from jarvis import web_search
        from jarvis.profiles import web_search_disabled

        if (
            not web_search_disabled()
            and web_search.auto_search_enabled()
            and web_search.should_auto_search(message)
        ):
            hits = web_search.search(message, limit=5)
            if hits:
                parts.append(
                    "Web search snippets (cite [n] if used; say if insufficient):\n"
                    + web_search.format_results_for_llm(hits)
                )

        from jarvis.resource_router import chat_busy_hint

        busy_hint = chat_busy_hint()
        if busy_hint:
            parts.append(busy_hint)

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
        from jarvis.config import load_auto_memory_mode, load_memory_namespace
        from jarvis.memory_context import filter_extracted_facts, should_extract_auto_memory

        mode = load_auto_memory_mode()
        if not should_extract_auto_memory(user_msg, assistant_msg, mode):
            return
        facts = llm.extract_memories(user_msg)
        if mode == "smart":
            facts = filter_extracted_facts(facts, user_msg)
        ns = self._a.session.memory_namespace or load_memory_namespace()
        added = False
        for fact in facts[:2]:
            if not self._a.memory.similar_exists(fact):
                self._a.memory.add("auto", fact, tags=["auto-extracted"], namespace=ns)
                added = True
        if added:
            self._a.refresh_system_prompt()

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
        from jarvis.instruction_follow import is_strict_instruction_prompt, strict_instruction_context_prefix

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
        self._a.branches.persist(session=self._a.session)
        extra: dict = {"inference_ms": inference_ms, "model": model, **usage}
        if context_warnings:
            extra["warnings"] = context_warnings
        if memory_citations:
            extra["memory_citations"] = memory_citations
        return _ok(answer, module=None, **extra)

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
        from jarvis.instruction_follow import is_strict_instruction_prompt, strict_instruction_context_prefix

        if is_strict_instruction_prompt(user_message):
            hint = strict_instruction_context_prefix()
            context_prefix = f"{hint}\n\n{context_prefix}" if context_prefix else hint
        pending = self._a.conversation.messages + [{"role": "user", "content": user_message}]
        msgs = self.messages_for_llm(pending, context_prefix)
        from jarvis.chat_cancel import finish as finish_cancel, is_cancelled

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


@register_behavior
class ConversationBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="conversation",
            name="Conversation",
            category="Conversation",
            description="Chat context assembly, LLM dispatch, and conversation persistence",
            module_path="jarvis.behaviors.conversation",
            test_module="tests.test_behaviors",
            action_names=["chat"],
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
        if action != "chat":
            return None
        self.initialize(assistant)
        return self._engine.execute(params, message) if self._engine else None

    def health(self) -> dict:
        report = super().health()
        report["validation_warnings"] = self.validate()
        report["engine_ready"] = self._engine is not None
        return report

    def shutdown(self) -> None:
        self._engine = None

    def _chat_entry(self, assistant: JarvisAssistant, params: dict, message: str) -> dict:
        return ensure_conversation_engine(assistant).execute(params, message)
