"""Memory engine — conversational memory, search, namespaces, and consolidation."""

from __future__ import annotations

import random
import re
import time
from datetime import UTC
from pathlib import Path
from typing import Any

from jarvis import llm
from jarvis.behaviors.memory.context import MemoryContext
from jarvis.response import err, ok


class MemoryEngine:
    """Isolated memory domain logic."""

    @staticmethod
    def _acm_authority_speak(question: str) -> tuple[dict[str, Any], str]:
        """Memory Authority path with teaching ack + conversational presentation."""
        from aria_core import acm_bridge

        from jarvis.behaviors.memory.cognitive_presentation import (
            format_teaching_acknowledgement,
            polish_cognitive_speech,
            polish_fragment_recall,
        )
        from jarvis.nlu.episodic_patterns import reformulate_for_acm_recall

        def _speak(q: str) -> tuple[dict[str, Any], str, str]:
            cog = acm_bridge.primary_cognitive_speak(q)
            result = cog.get("result") if isinstance(cog.get("result"), dict) else {}
            raw = str(cog.get("speech") or "").strip()
            return result, raw, q

        def _is_bad_recall(question: str, speech: str) -> bool:
            s = (speech or "").strip().rstrip(".")
            if not s or len(s.split()) <= 2:
                return True
            if MemoryEngine._is_misrouted_identity_answer(question, s):
                return True
            return bool(re.match(r"^(?:fishing|fish|my\s+\w+)$", s, re.I))

        result, raw, used_q = _speak(question)
        alt = reformulate_for_acm_recall(question)
        if alt and alt.lower() != (question or "").strip().lower():
            if not raw or not result.get("is_memory_request") or _is_bad_recall(question, raw):
                alt_result, alt_raw, _ = _speak(alt)
                if alt_raw and (
                    alt_result.get("is_memory_request")
                    or len(alt_raw.split()) > len((raw or "").split())
                ):
                    result, raw, used_q = alt_result, alt_raw, alt

        path = list(result.get("reasoning_path") or [])

        if "teaching_encoded" in path:
            ack = format_teaching_acknowledgement(question)
            if ack:
                MemoryEngine._trace_memory_presentation("cognitive_presentation", "teaching_ack")
                return result, ack

        if result.get("is_memory_request"):
            if raw:
                polished = polish_cognitive_speech(raw, result, prompt=used_q)
                if len(polished.split()) <= 4 and alt and alt != used_q:
                    _, alt_raw, _ = _speak(alt)
                    if alt_raw and len(alt_raw.split()) > len(polished.split()):
                        polished = polish_fragment_recall(polished, used_q, full_speech=alt_raw)
                else:
                    polished = polish_fragment_recall(polished, used_q)
                MemoryEngine._trace_memory_presentation("cognitive_presentation", "memory_recall")
                return result, polished
            if (result.get("status") or "").lower() == "unknown":
                return result, "I don't currently know."

        if alt and not raw:
            alt_result, alt_raw, _ = _speak(alt)
            if alt_raw:
                polished = polish_cognitive_speech(alt_raw, alt_result, prompt=alt)
                MemoryEngine._trace_memory_presentation("cognitive_presentation", "memory_recall")
                return alt_result, polished

        return result, raw

    @staticmethod
    def _is_misrouted_identity_answer(question: str, speech: str) -> bool:
        q = (question or "").lower()
        s = (speech or "").strip().rstrip(".")
        if not re.search(r"\b(prefer|favorite|favourite|kind of|hooks?|color|coffee)\b", q):
            return False
        return bool(re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$", s))

    @staticmethod
    def _trace_memory_presentation(layer: str, response_kind: str) -> None:
        try:
            from jarvis.routing_trace import record_presentation

            record_presentation(layer=layer, response_kind=response_kind)
        except Exception:
            pass

    @staticmethod
    def memory_citation(entry: dict) -> dict:
        return {
            "id": entry.get("id"),
            "type": entry.get("type", "fact"),
            "date": (entry.get("created") or entry.get("date") or "")[:10],
            "content": (entry.get("content") or "")[:160],
        }

    @classmethod
    def prepare_context(
        cls,
        ctx: MemoryContext,
        message: str,
        *,
        general: bool = False,
        skip_project_context: bool = False,
    ) -> tuple[list[str], list[dict]]:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            try:
                parts = acm_bridge.primary_context_fragments(message, limit=5)
                return parts, []
            except Exception:
                return [], []

        parts: list[str] = []
        citations: list[dict] = []
        seen_ids: set[str] = set()

        def _cite(entry: dict, *, kind: str | None = None) -> None:
            eid = entry.get("id") or entry.get("content", "")[:40]
            if eid in seen_ids:
                return
            seen_ids.add(eid)
            citation = cls.memory_citation(entry)
            if kind:
                citation["type"] = kind
            citations.append(citation)

        from jarvis.memory_context import (
            contextualize_memory_for_chat,
            should_inject_resume_context,
        )
        from jarvis.trust_memory import filter_trusted_content, trust_context_for_chat

        lower_msg = message.lower()
        ns = ctx.session.memory_namespace
        profile = ctx.memory.list_entries(namespace="profile")
        trust_ctx = trust_context_for_chat(ctx.memory, message, ctx.session)
        if trust_ctx and not general:
            parts.append(trust_ctx)
            for entry in ctx.memory.list_entries(entry_type="strategy")[:6]:
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

        if should_inject_resume_context(message, ctx.session):
            cp_ns = ns if ns and ns != "default" else None
            checkpoint = ctx.memory.latest_checkpoint(cp_ns) or ctx.memory.latest_checkpoint()
            if checkpoint:
                cp_line = filter_trusted_content(checkpoint["content"])
                if cp_line:
                    parts.append(f"Project checkpoint (where user left off):\n- {cp_line}")

        if not skip_project_context:
            from jarvis.memory.hierarchy import hierarchical_search
            from jarvis.modules.memory_common import is_user_facing_entry

            memories = hierarchical_search(
                ctx.memory,
                message,
                limit=3,
                namespace=ns if ns and ns != "default" else None,
            )
            if len(memories) < 2 and ns and ns != "default":
                memories = hierarchical_search(ctx.memory, message, limit=3)
            memories = [m for m in memories if is_user_facing_entry(m)]
            memory_lines = []
            for memory in memories:
                line = contextualize_memory_for_chat(memory["content"])
                line = filter_trusted_content(line) if line else None
                if line and line not in memory_lines:
                    memory_lines.append(line)
            if memory_lines:
                parts.append(
                    "Relevant memories:\n" + "\n".join(f"- {line}" for line in memory_lines)
                )
            for memory in memories:
                _cite(memory)

        return parts, citations

    @classmethod
    def auto_remember(cls, ctx: MemoryContext, user_msg: str, assistant_msg: str) -> None:
        from jarvis.config import load_auto_memory_mode, load_memory_namespace
        from jarvis.memory_context import filter_extracted_facts, should_extract_auto_memory

        mode = load_auto_memory_mode()
        if not should_extract_auto_memory(user_msg, assistant_msg, mode):
            return
        facts = llm.extract_memories(user_msg)
        if mode == "smart":
            facts = filter_extracted_facts(facts, user_msg)
        ns = ctx.session.memory_namespace or load_memory_namespace()
        added = False
        for fact in facts[:2]:
            if not ctx.memory.similar_exists(fact):
                ctx.memory.add("auto", fact, tags=["auto-extracted"], namespace=ns)
                added = True
        if added:
            ctx.refresh_system_prompt()

    @classmethod
    def sync_project_namespace(cls, ctx: MemoryContext) -> str | None:
        from jarvis.config import load_auto_namespace
        from jarvis.memory_context import detect_project_namespace

        if not load_auto_namespace():
            return None
        ns = detect_project_namespace()
        if ns and ns != ctx.session.memory_namespace:
            ctx.session.note_memory_namespace(ns)
        return ns

    @classmethod
    def project_namespace(cls, ctx: MemoryContext) -> str:
        from jarvis.config import load_auto_namespace, load_memory_namespace
        from jarvis.memory_context import detect_project_namespace

        if load_auto_namespace():
            return detect_project_namespace()
        ns = ctx.session.memory_namespace
        if ns and ns != "default":
            return ns
        return load_memory_namespace()

    @classmethod
    def auto_checkpoint(cls, ctx: MemoryContext, *, reason: str = "exit") -> dict:
        from datetime import datetime, timedelta

        from jarvis.config import load_auto_checkpoint
        from jarvis.memory_context import build_quick_checkpoint
        from jarvis.modules.memory import _parse_ts

        if not load_auto_checkpoint():
            return {"ok": False, "skipped": True, "reason": "disabled"}

        ns = cls.project_namespace(ctx)
        existing = ctx.memory.latest_checkpoint(ns)
        if existing:
            try:
                age = datetime.now(UTC) - _parse_ts(existing.get("timestamp", ""))
                if age < timedelta(minutes=30) and "Auto-saved on exit" in existing.get(
                    "content", ""
                ):
                    return {"ok": False, "skipped": True, "reason": "recent"}
            except (TypeError, ValueError):
                pass

        text = build_quick_checkpoint(
            ctx.session,
            ctx.conversation.messages,
            ctx.task_manager,
        )
        if not text:
            return {"ok": False, "skipped": True, "reason": "empty"}

        ctx.memory.upsert_checkpoint(text, namespace=ns)
        ctx.refresh_system_prompt()
        return {"ok": True, "checkpoint": text, "namespace": ns, "reason": reason}

    @classmethod
    def run_consolidation(cls, ctx: MemoryContext) -> dict:
        from jarvis.memory_consolidation import run_consolidation

        return run_consolidation(ctx.memory)

    @classmethod
    def remember(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from aria_core import acm_bridge
        from aria_core import memory as core_memory
        from jarvis.config import load_memory_namespace
        from jarvis.modules.memory import MemoryStore
        from jarvis.trust_memory import parse_strategy_remember, record_strategy

        if acm_bridge.acm_is_authoritative():
            try:
                raw = params.get("text") or message
                content, entry_type, parsed_ns = MemoryStore.parse_remember(raw)
                namespace = (
                    params.get("namespace")
                    or parsed_ns
                    or ctx.session.memory_namespace
                    or load_memory_namespace()
                )
                if not content:
                    return err("What should I remember?")
                entry = core_memory.remember(
                    content, entry_type=entry_type or "fact", namespace=namespace
                )
                ctx.session.note_module("memory")
                ctx.refresh_system_prompt()
                body = (entry or {}).get("content") or content
                return ok(
                    f"Stored via ACM:\n\n{body}",
                    module="memory",
                    remembered=body,
                    source="acm",
                )
            except Exception as exc:
                return err(f"ACM remember failed: {type(exc).__name__}")

        raw = params.get("text") or message
        strategy = parse_strategy_remember(raw)
        if strategy:
            namespace = ctx.session.memory_namespace or load_memory_namespace()
            entry = record_strategy(ctx.memory, strategy, namespace=namespace)
            ctx.session.note_module("memory")
            ctx.refresh_system_prompt()
            return ok(
                f"Got it — stored as **strategy** rule in `{namespace}`.\n\n{entry['content']}",
                module="memory",
                remembered=entry["content"],
            )

        content, entry_type, parsed_ns = MemoryStore.parse_remember(raw)
        namespace = (
            params.get("namespace")
            or parsed_ns
            or ctx.session.memory_namespace
            or load_memory_namespace()
        )
        if not content:
            return err("What should I remember?")
        facts = MemoryStore.split_remember_facts(content)
        stored: list[str] = []
        try:
            for fact in facts:
                if ctx.memory.similar_exists(fact):
                    continue
                entry = ctx.memory.add(entry_type, fact, namespace=namespace)
                from jarvis.memory.hierarchy import infer_layer, tag_layer

                layer = infer_layer({**entry, "type": entry_type, "namespace": namespace})
                tagged = tag_layer(entry, layer)
                ctx.memory.update(entry["id"], tags=tagged.get("tags"))
                stored.append(fact)
        except ValueError as exc:
            return err(str(exc))
        if not stored:
            return ok("Those facts are already stored.", module="memory")
        ctx.session.note_module("memory")
        ctx.refresh_system_prompt()
        from jarvis.learning_notice import learning_notice

        notice = learning_notice(
            "long_term" if namespace == "default" else "project", detail=namespace
        )
        if len(stored) == 1:
            body = stored[0]
        else:
            body = "\n".join(f"• {fact}" for fact in stored)
        return ok(
            f"{notice}\n\nStored **{len(stored)}** {entry_type}{'s' if len(stored) != 1 else ''} in `{namespace}`:\n\n{body}",
            module="memory",
            remembered=stored[0] if len(stored) == 1 else body,
            remembered_count=len(stored),
        )

    @classmethod
    def recall(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            try:
                query = (params.get("query") or message or "").strip()
                request = acm_bridge._memory_request_for_search(query or "about me")
                result, speech = cls._acm_authority_speak(request)
                if not result.get("is_memory_request") or not speech:
                    return ok(
                        "I don't have a clear memory for that yet.", module="memory", source="acm"
                    )
                hits = acm_bridge.cognitive_result_to_hits(result, speech=speech, limit=5)
                return ok(
                    speech,
                    module="memory",
                    source="acm",
                    memories=hits,
                    cognitive_status=result.get("status"),
                )
            except Exception as exc:
                return err(f"ACM recall failed: {type(exc).__name__}")

        from jarvis.modules.memory_common import filter_user_facing, format_recall_answer
        from jarvis.trust_memory import filter_entry_list

        profile = filter_entry_list(
            ctx.memory.list_entries(namespace="profile"), user_facing_only=True
        )
        ns = ctx.session.memory_namespace
        other = ctx.memory.list_entries(namespace=ns if ns and ns != "default" else None)
        if not other:
            other = [e for e in ctx.memory.list_entries() if e.get("namespace") != "profile"]
        other = filter_entry_list(other, user_facing_only=True)
        entries = filter_user_facing(profile + other)
        if not entries:
            return ok(
                "I don't have anything stored yet. Just tell me what to remember.", module="memory"
            )
        # Explicit list/recall still summarizes in natural language, not a metadata dump.
        lines = "\n".join(f"• {format_recall_answer(e)}" for e in entries[:25])
        return ok(f"Here's what I remember:\n\n{lines}", module="memory")

    @classmethod
    def memory_about_user(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            try:
                question = (params.get("question") or message or "").strip()
                result, speech = cls._acm_authority_speak(question)
                path = list(result.get("reasoning_path") or [])
                if speech:
                    return ok(
                        speech,
                        module="memory",
                        source="acm",
                        cognitive_status=result.get("status"),
                    )
                if any(str(p).startswith("teaching_") for p in path):
                    return ok(
                        "I couldn't store that as memory.",
                        module="memory",
                        source="acm",
                        cognitive_status=result.get("status"),
                    )
                return ok(
                    "I'm still learning about you. Tell me preferences or facts to remember.",
                    module="memory",
                    source="acm",
                )
            except Exception as exc:
                return err(f"ACM memory-about failed: {type(exc).__name__}")

        from jarvis.modules.memory_common import (
            filter_user_facing,
            format_recall_answer,
            is_preference_summary_query,
        )
        from jarvis.trust_memory import filter_entry_list

        lower = (params.get("question") or message).lower()
        profile = filter_entry_list(
            ctx.memory.list_entries(namespace="profile"), user_facing_only=True
        )
        prefs = filter_user_facing(
            [
                e
                for e in ctx.memory.list_entries(entry_type="preference")
                if e.get("namespace") != "profile"
            ]
        )
        facts = filter_user_facing(
            [
                e
                for e in ctx.memory.list_entries(entry_type="fact")
                if e.get("namespace") not in ("profile",)
            ]
        )

        if is_preference_summary_query(message) or "preference" in lower:
            if not prefs:
                return ok(
                    "I don't have stored preferences yet. Tell me things like "
                    "**Remember that I prefer concise answers.**",
                    module="memory",
                )
            lines = "\n".join(f"• {format_recall_answer(p)}" for p in prefs[:12])
            return ok(f"Here are preferences I know about you:\n\n{lines}", module="memory")

        if not profile and not prefs and not facts:
            hits = filter_entry_list(
                ctx.memory.search(message, limit=8, user_facing_only=True),
                user_facing_only=True,
            )
            if hits:
                summary = " ".join(format_recall_answer(h) for h in hits[:4])
                return ok(summary, module="memory")
            return ok(
                "I don't have a profile yet. Complete the **About you** questionnaire when it appears, "
                "or say **Remember that I enjoy …**",
                module="memory",
            )

        interests = next((p for p in profile if "interests" in (p.get("tags") or [])), None)
        name = next((p for p in profile if "name" in (p.get("tags") or [])), None)

        if re.search(r"\b(name|call me|who am i)\b", lower):
            if name:
                return ok(name["content"], module="memory")
            summary = next((p for p in profile if "summary" in (p.get("tags") or [])), None)
            if summary:
                return ok(summary["content"], module="memory")

        if re.search(
            r"\b(like to do|like doing|enjoy|hobby|hobbies|interest|passion|something i like|fun)\b",
            lower,
        ):
            if interests:
                text_i = interests["content"]
                if ": " in text_i:
                    text_i = text_i.split(": ", 1)[1]
                items = [item.strip() for item in re.split(r",| and ", text_i) if item.strip()]
                if items:
                    pick = random.choice(items)
                    rest = [item for item in items if item != pick][:4]
                    extra = f" You also enjoy {', '.join(rest)}." if rest else ""
                    who = ""
                    if name and "Jeff" in name.get("content", ""):
                        who = "Jeff, "
                    elif name:
                        who = name["content"].split()[-1].rstrip(".") + ", "
                    return ok(
                        f"{who}you like **{pick}**.{extra}",
                        module="memory",
                    )

        parts: list[str] = []
        summary = next((p for p in profile if "summary" in (p.get("tags") or [])), None)
        if summary:
            parts.append(summary["content"])
        elif profile:
            parts.extend(format_recall_answer(p) for p in filter_user_facing(profile)[:4])
        if prefs:
            parts.append(
                "Preferences:\n" + "\n".join(f"• {format_recall_answer(p)}" for p in prefs[:8])
            )
        if facts:
            parts.append("Facts:\n" + "\n".join(f"• {format_recall_answer(f)}" for f in facts[:8]))
        if not parts:
            return ok(
                "I'm still learning about you. Tell me preferences or facts to remember.",
                module="memory",
            )
        return ok("Here's what I know about you:\n\n" + "\n\n".join(parts), module="memory")

    @classmethod
    def memory_search(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            try:
                query = (params.get("query") or message or "").strip()
                from jarvis.nlu.episodic_patterns import (
                    is_episodic_memory_query,
                    is_past_event_memory_question,
                )

                if is_episodic_memory_query(query) or is_past_event_memory_question(query):
                    return cls.memory_about_user(
                        ctx, {"question": query}, message or query
                    )
                result, speech = cls._acm_authority_speak(query or "about me")
                if speech:
                    hits = acm_bridge.cognitive_result_to_hits(result, speech=speech, limit=8)
                    return ok(
                        speech,
                        module="memory",
                        source="acm",
                        memories=hits,
                        cognitive_status=result.get("status"),
                    )
                if result.get("is_memory_request"):
                    return ok("I don't currently know.", module="memory", source="acm")
                return ok("No matching memories.", module="memory", source="acm")
            except Exception as exc:
                return err(f"ACM search failed: {type(exc).__name__}")

        from jarvis.memory.retrieval_diagnostics import rank_for_query
        from jarvis.modules.memory_common import (
            format_recall_answer,
            is_fact_question,
            normalize_memory_query,
        )

        raw_query = params.get("query") or message
        _ = normalize_memory_query(raw_query)
        ns = ctx.session.memory_namespace
        pool = list(ctx.memory.list_entries(namespace=ns if ns and ns != "default" else None))
        if ns and ns != "default":
            default_entries = ctx.memory.list_entries(namespace="default")
            seen = {e.get("id") for e in pool}
            pool.extend(e for e in default_entries if e.get("id") not in seen)
        if not pool:
            pool = list(ctx.memory.list_entries())

        t0 = time.perf_counter()
        hits, decision = rank_for_query(
            pool,
            raw_query,
            intent="memory_search",
            limit=8,
            fact_mode=is_fact_question(raw_query),
        )
        decision["retrieval_latency_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        if not hits:
            return ok(
                "No matching memories found.",
                module="memory",
                memory_retrieval=decision,
            )

        if is_fact_question(raw_query) or re.search(
            r"\bwhat\s+is\s+my\b|\bwhat'?s\s+my\b|\bwhat\s+do\s+you\s+know\s+about\s+(?!me\b)",
            raw_query,
            re.I,
        ):
            return ok(
                format_recall_answer(hits[0]),
                module="memory",
                remembered=hits[0]["content"],
                memory_retrieval=decision,
            )

        lines = "\n".join(f"• {e['content']}" for e in hits)
        return ok(
            f"Found these memories:\n\n{lines}",
            module="memory",
            memory_retrieval=decision,
        )

    @classmethod
    def memory_forget(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        query = params.get("query") or message
        query = re.sub(
            r"^(please\s+)?(forget|delete|remove)\s+(that|about|the memory)?\s*",
            "",
            query,
            flags=re.I,
        ).strip()
        if not query:
            return err("What should I forget? Give me a phrase to search for.")

        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            try:
                out = acm_bridge.primary_forget(query=query)
                ctx.refresh_system_prompt()
                if out.get("cooled"):
                    return ok(
                        "Cooled that memory (soft forget — experiences retained).",
                        module="memory",
                        source="acm",
                        cooled=True,
                        deleted=False,
                    )
                return ok("No matching memories to cool.", module="memory", source="acm")
            except Exception as exc:
                return err(f"ACM forget failed: {type(exc).__name__}")

        from jarvis.modules.memory_common import select_forget_targets

        targets = select_forget_targets(ctx.memory.list_entries(), query, limit=3)
        if not targets:
            return ok("No matching memories to delete.", module="memory")
        removed_lines: list[str] = []
        for entry in targets:
            if ctx.memory.delete_id(entry["id"]):
                removed_lines.append(entry["content"][:120])
        ctx.refresh_system_prompt()
        if not removed_lines:
            return ok("No matching memories to delete.", module="memory")
        lines = "\n".join(f"• {line}" for line in removed_lines)
        return ok(
            f"Removed **{len(removed_lines)}** memor{'y' if len(removed_lines) == 1 else 'ies'}:\n\n{lines}",
            module="memory",
        )

    @classmethod
    def memory_correct(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.trust_memory import correct_memory, parse_memory_correct

        new_fact = (params.get("new_fact") or "").strip()
        search_hint = (params.get("search_hint") or "").strip()
        if not new_fact:
            parsed = parse_memory_correct(message)
            if not parsed:
                return err("What should I correct? Try: `correct that mom's birthday is June 9`")
            search_hint, new_fact = parsed

        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            try:
                out = acm_bridge.primary_correct(query=search_hint or new_fact, text=new_fact)
                ctx.refresh_system_prompt()
                entry = out.get("entry") or {}
                body = entry.get("content") or new_fact
                return ok(
                    f"Updated memory via ACM revise:\n\n**{body}**",
                    module="memory",
                    remembered=body,
                    source="acm",
                    revised=bool(out.get("revised")),
                )
            except Exception as exc:
                return err(f"ACM correct failed: {type(exc).__name__}")

        removed, entry, strategy_created = correct_memory(
            ctx.memory, new_fact, search_hint=search_hint
        )
        ctx.refresh_system_prompt()
        msg = f"Updated memory — stored:\n\n**{entry['content']}**"
        if removed:
            msg = f"Replaced **{removed}** old entr{'y' if removed == 1 else 'ies'}. " + msg
        if strategy_created:
            msg += "\n\n_Also saved as a behavior strategy from your correction._"
        return ok(
            msg, module="memory", remembered=entry["content"], strategy_created=strategy_created
        )

    @classmethod
    def memory_prune(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        removed = ctx.memory.prune()
        return ok(f"Pruned **{removed}** stale auto-extracted memories.", module="memory")

    @classmethod
    def memory_consolidate(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.memory.hierarchy import consolidate, format_hierarchy_markdown

        dry_run = bool(params.get("dry_run"))
        result = consolidate(ctx.memory, dry_run=dry_run)
        prefix = "Dry run — " if dry_run else ""
        return ok(
            prefix + format_hierarchy_markdown(ctx.memory),
            module="memory",
            data=result,
        )

    @classmethod
    def memory_hierarchy(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.memory.hierarchy import format_hierarchy_markdown, layer_summary

        return ok(
            format_hierarchy_markdown(ctx.memory),
            module="memory",
            data=layer_summary(ctx.memory),
        )

    @classmethod
    def memory_summarize(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.config import load_memory_namespace

        recent = [
            m for m in ctx.conversation.messages[-12:] if m.get("role") in ("user", "assistant")
        ]
        if len(recent) < 2:
            return err("Not enough conversation to summarize yet.")
        blob = "\n".join(f"{m['role']}: {m['content'][:500]}" for m in recent)
        facts = llm.extract_memories(blob)
        if not facts:
            return ok("Nothing new worth storing from this conversation.", module="memory")
        ns = ctx.session.memory_namespace or load_memory_namespace()
        added = 0
        for fact in facts[:5]:
            if not ctx.memory.similar_exists(fact):
                ctx.memory.add("auto", fact, tags=["conversation-summary"], namespace=ns)
                added += 1
        if added:
            ctx.refresh_system_prompt()
        lines = "\n".join(f"• {fact}" for fact in facts[:5])
        return ok(f"Stored **{added}** facts from this conversation:\n\n{lines}", module="memory")

    @classmethod
    def memory_namespace(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.config import save_memory_namespace

        ns = params.get("namespace") or ""
        if not ns:
            match = re.search(
                r"\b(?:namespace|project)\s+[`'\"]?(\w[\w-]*)[`'\"]?",
                message,
                re.I,
            )
            ns = match.group(1) if match else ""
        if not ns:
            return err("Which namespace? Example: `set memory namespace work`")
        save_memory_namespace(ns)
        ctx.session.note_memory_namespace(ns)
        ctx.refresh_system_prompt()
        return ok(
            f"Memory namespace set to **{ns}**. New memories go there until changed.",
            module="memory",
        )

    @classmethod
    def project_checkpoint(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.config import PROJECT_ROOT

        ns = params.get("namespace") or cls.project_namespace(ctx)
        recent = [
            m for m in ctx.conversation.messages[-14:] if m.get("role") in ("user", "assistant")
        ]
        blob = "\n".join(f"{m['role']}: {m['content'][:600]}" for m in recent)
        session_bits = ctx.session.context_summary()
        task_hint = ""
        task = ctx.task_manager.active()
        if task:
            task_hint = (
                f"Active coding task: {task.title} ({task.status}), "
                f"path={task.path or task.checkpoint.get('path', '')}"
            )

        prompt = (
            "Summarize where the user left off on their project so they can resume tomorrow. "
            "Include: goal, current file(s), what was done, next steps, blockers. "
            "Write 2-5 sentences, factual, no markdown headers.\n\n"
            f"Project: {PROJECT_ROOT.name}\nSession: {session_bits}\n{task_hint}\n\n"
            f"Recent chat:\n{blob}\n\n"
            f"User note: {message or 'save checkpoint'}"
        )
        summary = llm.ask(
            llm.summarization_model(),
            [{"role": "user", "content": prompt}],
            role="summarization",
        ).strip()
        if not summary:
            return err("Could not build a checkpoint summary.")
        note = params.get("note") or ""
        if note:
            summary = f"{summary} Note: {note.strip()}"
        ctx.memory.upsert_checkpoint(summary, namespace=ns)
        ctx.session.note_module("memory")
        ctx.refresh_system_prompt()
        return ok(
            f"Saved project checkpoint under **`{ns}`**.\n\n{summary}\n\n"
            "After restart, ask **where did I leave off?** or just continue chatting — I'll see this.",
            module="memory",
        )

    @classmethod
    def project_resume(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        ns = params.get("namespace") or cls.project_namespace(ctx)
        checkpoint = ctx.memory.latest_checkpoint(ns) or ctx.memory.latest_checkpoint()
        if not checkpoint:
            return ok(
                "No project checkpoint saved yet. Say **save where I left off** before shutting down.",
                module="memory",
            )
        extra = ""
        if ctx.session.last_file:
            extra = f"\n\nSession still has **last file**: `{ctx.session.last_file}`"
        elif checkpoint.get("namespace"):
            extra = f"\n\nCheckpoint namespace: `{checkpoint.get('namespace')}`"
        return ok(
            f"Here's where you left off:\n\n{checkpoint['content']}{extra}",
            module="memory",
        )

    @classmethod
    def cheatsheet_list(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.cheatsheets import CHEATSHEET_NAMESPACE, list_cheatsheets, seed_cheatsheets

        if not list_cheatsheets(ctx.memory):
            seed_cheatsheets(ctx.memory)
        items = list_cheatsheets(ctx.memory)
        lines = "\n".join(f"• **{item['key']}** — {item['title']}" for item in items)
        return ok(
            f"Cheatsheets in memory (`{CHEATSHEET_NAMESPACE}` namespace):\n\n{lines}\n\n"
            "Say **memory cheatsheet** or **cheatsheet for coding**. Edit in Memory tab → Cheatsheets.",
            module="memory",
        )

    @classmethod
    def cheatsheet_show(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.cheatsheets import (
            default_keys,
            find_by_key,
            normalize_key,
            resolve_key_from_message,
            seed_cheatsheets,
        )

        key = normalize_key(params.get("key", "")) or resolve_key_from_message(message)
        if not key:
            return cls.cheatsheet_list(ctx, params, message)
        if not find_by_key(ctx.memory, key):
            seed_cheatsheets(ctx.memory, keys=[key])
        entry = find_by_key(ctx.memory, key)
        if not entry:
            return err(f"Unknown cheatsheet `{key}`. Available: {', '.join(default_keys())}")
        return ok(entry["content"], module="memory")

    @classmethod
    def cheatsheet_reset(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.cheatsheets import normalize_key, reset_cheatsheet, resolve_key_from_message

        key = normalize_key(params.get("key", "")) or resolve_key_from_message(message)
        if not key:
            return err("Which cheatsheet? Example: **reset memory cheatsheet**")
        updated = reset_cheatsheet(ctx.memory, key)
        if not updated:
            return err(f"No default cheatsheet for `{key}`.")
        return ok(f"Restored **{key}** cheatsheet to default.", module="memory")

    @classmethod
    def remember_image(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_image(params.get("path", ""))
        if not path:
            return err("Attach an image to remember.")
        hint = (params.get("hint") or message or "").strip()
        ocr = ctx.vision.ocr(path)
        if ocr.startswith("ERROR:"):
            summary = ctx.vision.analyze("Summarize this image in one paragraph.", path)
            if summary.startswith("ERROR:"):
                return err(summary)
            content = summary
        else:
            content = ocr
        label = re.sub(
            r"^(please\s+)?(remember|don't forget|note that|keep in mind)\s*(that\s+)?",
            "",
            hint,
            flags=re.I,
        ).strip()
        fact = f"{label}: {content}" if label else f"From image {Path(path).name}: {content}"
        ctx.memory.add("fact", fact[:4000])
        return ok(
            f"Stored image content in memory.\n\n{fact[:500]}…",
            module="memory",
            remembered=fact[:200],
        )

    @classmethod
    def journal_remember(cls, ctx: MemoryContext, params: dict, message: str) -> dict:
        from jarvis.memory_context import normalize_journal_memory_text
        from jarvis.modules.journal import _format_bullet

        bullet_id = params.get("bullet_id") or ""
        if not bullet_id:
            match = re.search(r"\b([a-f0-9]{8})\b", message)
            bullet_id = match.group(1) if match else ""
        if bullet_id:
            content = ctx.journal.bullet_remember_text(bullet_id)
            if not content:
                return err("Journal bullet not found.")
        else:
            page = ctx.journal.daily_get()
            bullets = page.get("bullets", [])
            if not bullets:
                return err("Nothing on today's journal to remember.")
            lines = "\n".join(_format_bullet(bullet) for bullet in bullets)
            content = f"From bullet journal ({page.get('date')}):\n{lines}"
        content = normalize_journal_memory_text(content)
        ns = ctx.session.memory_namespace or "default"
        ctx.memory.add("fact", content, namespace=ns)
        ctx.session.note_module("memory")
        return ok(f"Saved to memory (`{ns}`):\n\n{content}", module="journal")

    @classmethod
    def memory_stats(cls, ctx: MemoryContext) -> dict[str, Any]:
        from jarvis.brain_memory import consolidation_enabled

        stats = ctx.memory.stats()
        return {
            "total": stats.get("total", 0),
            "namespaces": stats.get("namespaces", []),
            "consolidation_enabled": consolidation_enabled(),
        }
