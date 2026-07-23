"""Explicit relationship-memory presentation (B21 / D044).

Answers only when the user explicitly asks about the user↔assistant
relationship. Never invents Experiences. Never contaminates simple
Who am I / Who are you paths (those remain isolated elsewhere).
"""

from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

from acm.authority.mode import read_only
from acm.identity.rendering import is_relationship_identity_request

if TYPE_CHECKING:
    from acm.core.store import CognitiveStore
    from acm.identity.organ import IdentityOrgan

SCHEMA = "acm.identity.relationship_presentation.v1"

_SHARED_WORK = re.compile(
    r"\b(?:we|together|our\s+project|collaborat|working\s+on|building)\b",
    re.I,
)


def present_relationship_memory(
    *,
    store: CognitiveStore,
    identity: IdentityOrgan | None,
    request: str,
    agent_id: str = "",
) -> dict[str, Any]:
    """Build an evidence-bounded relationship answer (read-only)."""
    with read_only():
        if not is_relationship_identity_request(request):
            return {
                "schema": SCHEMA,
                "status": "not_relationship_request",
                "memory": None,
                "invents_experiences": False,
                "store_write": False,
                "relationship_allowed": False,
            }

        lines: list[str] = []
        evidence_ids: list[str] = []
        sources: list[str] = []

        low = (request or "").lower()
        want_learned = any(
            c in low
            for c in (
                "learned about me",
                "what have you learned",
            )
        )
        want_work = any(
            c in low
            for c in (
                "worked",
                "together",
                "know each other",
                "relationship",
                "between us",
                "you and i",
                "you and me",
            )
        )

        # --- what I've learned about the user (schema attrs) ---
        if identity is not None and (want_learned or want_work):
            user = identity.schema_concept("user")
            learned_bits: list[str] = []
            for attr in user.attributes:
                if not attr.active:
                    continue
                if attr.key in {"name", "preferred_name", "location", "role"}:
                    if attr.key == "name":
                        learned_bits.append(f"your name is {attr.value}")
                    elif attr.key == "preferred_name":
                        learned_bits.append(f"you prefer to be called {attr.value}")
                    elif attr.key == "location":
                        learned_bits.append(f"you live in {attr.value}")
                    else:
                        learned_bits.append(f"your {attr.key} is {attr.value}")
                    for eid in getattr(attr, "evidence_ids", None) or []:
                        evidence_ids.append(str(eid))
            # Preferences as attributes on concepts / experiences (lightweight)
            for exp in store.experiences.values():
                text = (getattr(exp, "summary", None) or "").strip()
                meta = getattr(exp, "meta_dict", None) or {}
                if not isinstance(meta, dict):
                    meta = dict(getattr(exp, "metadata", ()) or ())
                if not text:
                    continue
                if meta.get("preference") or re.search(
                    r"\b(?:i\s+prefer|my\s+favorite|favorite\s+\w+\s+is)\b", text, re.I
                ):
                    if len(learned_bits) < 6 and text not in learned_bits:
                        # paraphrase lightly without inventing
                        learned_bits.append(text.rstrip("."))
                        evidence_ids.append(str(exp.id))
            if learned_bits:
                # Deduplicate while preserving order
                seen: set[str] = set()
                uniq: list[str] = []
                for b in learned_bits:
                    k = b.casefold()
                    if k not in seen:
                        seen.add(k)
                        uniq.append(b)
                lines.append("I've learned that " + "; ".join(uniq[:5]) + ".")
                sources.append("user_schema_and_preferences")

        # --- shared work / how we know each other ---
        if want_work or not lines:
            shared: list[str] = []
            for exp in store.experiences.values():
                text = (getattr(exp, "summary", None) or "").strip()
                if not text or not _SHARED_WORK.search(text):
                    continue
                # Skip pure identity declarations
                if re.match(r"^\s*my\s+name\s+is\b", text, re.I):
                    continue
                shared.append(text.rstrip("."))
                evidence_ids.append(str(exp.id))
                if len(shared) >= 4:
                    break
            # Autobiographical associations involving assistant / projects
            agent_name = ""
            if identity is not None:
                agent = identity.schema_concept("agent")
                for attr in agent.attributes:
                    if attr.active and attr.key == "name":
                        agent_name = str(attr.value)
                        break
            aid = (agent_id or agent_name or "").casefold()
            for assoc in store.associations.values():
                if not getattr(assoc, "active", False):
                    continue
                meta = getattr(assoc, "metadata", {}) or {}
                if not meta.get("autobiographical"):
                    continue
                ev = list(getattr(assoc, "evidence_ids", []) or [])
                if not ev:
                    continue
                src = store.concepts.get(assoc.source_id)
                tgt = store.concepts.get(assoc.target_id)
                if src is None or tgt is None:
                    continue
                sl = _label(src)
                tl = _label(tgt)
                if not sl or not tl:
                    continue
                rel = str(meta.get("learned_relation") or getattr(assoc.relation, "value", ""))
                pair = f"{sl} {rel.replace('_', ' ')} {tl}".strip()
                if aid and aid not in pair.casefold() and "project" not in pair.casefold():
                    # keep project/goal relations even without assistant name
                    if rel not in {"supports_goal", "part_of", "uses", "supports"}:
                        continue
                if pair not in shared:
                    shared.append(pair)
                    evidence_ids.extend(str(e) for e in ev)
                if len(shared) >= 6:
                    break
            if shared:
                # Deduplicate
                seen_s: set[str] = set()
                uniq_s: list[str] = []
                for s in shared:
                    k = s.casefold()
                    if k not in seen_s:
                        seen_s.add(k)
                        uniq_s.append(s)
                lines.append(
                    "We've worked together on: " + "; ".join(uniq_s[:4]) + "."
                )
                sources.append("shared_experiences_and_relations")

        # --- framing when describing the relationship ---
        if "relationship" in low or "know each other" in low:
            asst = agent_id or "the assistant"
            if identity is not None:
                agent = identity.schema_concept("agent")
                for attr in agent.attributes:
                    if attr.active and attr.key == "name" and attr.value:
                        asst = str(attr.value)
                        break
            frame = (
                f"I am {asst}, and I remember our collaboration from stored "
                "experiences and relationship evidence."
            )
            if frame not in lines:
                lines.insert(0, frame)
                sources.append("relationship_frame")

        # Dedupe evidence
        ev_out: list[str] = []
        seen_e: set[str] = set()
        for e in evidence_ids:
            if e and e not in seen_e:
                seen_e.add(e)
                ev_out.append(e)

        if not lines:
            return {
                "schema": SCHEMA,
                "status": "unknown",
                "memory": None,
                "evidence_ids": [],
                "sources": [],
                "invents_experiences": False,
                "store_write": False,
                "relationship_allowed": True,
                "confidence": 0.0,
            }

        memory = " ".join(lines)
        return {
            "schema": SCHEMA,
            "status": "known",
            "memory": memory,
            "evidence_ids": ev_out,
            "sources": sources,
            "invents_experiences": False,
            "store_write": False,
            "relationship_allowed": True,
            "confidence": 0.86 if ev_out else 0.7,
            "explanation_class": "experience",
        }


def _label(concept: Any) -> str:
    for attr in getattr(concept, "attributes", []) or []:
        if getattr(attr, "active", False) and attr.key in {"name", "label", "title"}:
            return str(attr.value)
    name = getattr(concept, "name", None)
    if name:
        return str(name)
    return ""
