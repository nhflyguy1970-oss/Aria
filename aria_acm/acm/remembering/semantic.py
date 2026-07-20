"""Semantic autobiographical memory — reconstruct personal knowledge from learned facts.

Answers only from stored experience metadata and active concept attributes.
Never invents, never uses world knowledge.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


UNKNOWN = "I don't currently know."


def _indefinite_article(value: str) -> str:
    """Choose a/an for hardware labels (RTX is spoken 'are-tee-ex')."""
    v = (value or "").strip()
    if not v:
        return "a"
    low = v.lower()
    if low.startswith(("rtx", "rx ", "ssd", "hdd", "nvme", "oled", "lcd", "hdmi")):
        return "an"
    return "an" if low[0] in "aeiou" else "a"


_SEMANTIC_PROP_KEYS = frozenset(
    {
        "os",
        "gpu",
        "ram",
        "editor",
        "attribute",
        "project",
        "preference",
    }
)


@dataclass(frozen=True)
class SemanticFact:
    kind: str
    property: str
    value: str
    entity: str = ""
    experience_id: str = ""

    @property
    def identity_key(self) -> tuple[str, str, str, str]:
        return (
            self.kind,
            self.property.lower(),
            (self.entity or "").lower(),
            self.value.casefold(),
        )


def collect_semantic_facts(store: Any) -> list[SemanticFact]:
    """Gather active semantic autobiographical facts from experiences + concepts."""
    by_slot: dict[tuple[str, str, str], SemanticFact] = {}
    extras: list[SemanticFact] = []  # identity/skill/location without slot overwrite

    def _slot_key(fact: SemanticFact) -> tuple[str, str, str] | None:
        if fact.kind == "possession":
            return (fact.kind, fact.property.lower(), (fact.entity or "").lower())
        if fact.kind == "preference":
            return (fact.kind, fact.property.lower(), "")
        if fact.kind == "project":
            # Each project title is its own slot (do not overwrite Aria with BlackFly).
            return (fact.kind, "project", fact.value.casefold())
        return None

    def _add(fact: SemanticFact) -> None:
        slot = _slot_key(fact)
        if slot is not None:
            by_slot[slot] = fact  # later call wins
        else:
            # Deduplicate identity-like extras by property.
            extras[:] = [
                e
                for e in extras
                if not (e.kind == fact.kind and e.property == fact.property)
            ]
            extras.append(fact)

    def _ingest_attr_concept() -> None:
        for concept in store.concepts.values():
            labels = " ".join(getattr(concept, "labels", []) or []).lower()
            for attr in getattr(concept, "attributes", []) or []:
                if not getattr(attr, "active", False):
                    continue
                key = getattr(attr, "key", "") or ""
                value = str(getattr(attr, "value", "") or "")
                if not value:
                    continue
                if key in (
                    "mentioned",
                    "statement",
                    "cue",
                    "token",
                    "surface",
                    "surface_form",
                    "category",
                    "instance_of",
                ):
                    continue
                if key.startswith("favorite_") or key.startswith("prefer_") or key == "preference":
                    _add(
                        SemanticFact(
                            kind="preference",
                            property=key,
                            value=value,
                            entity="",
                        )
                    )
                elif key == "project" or key == "title":
                    _add(
                        SemanticFact(
                            kind="project",
                            property="project",
                            value=value,
                            entity="",
                        )
                    )
                elif key in _SEMANTIC_PROP_KEYS or key in ("os", "gpu", "ram", "editor"):
                    entity = labels.split()[0] if labels else ""
                    # Never treat identity schema labels as owned entities.
                    if entity in ("user", "agent") or labels.startswith("agent:"):
                        continue
                    _add(
                        SemanticFact(
                            kind="possession",
                            property=key,
                            value=value,
                            entity=entity,
                        )
                    )
                elif key in ("name", "preferred_name", "role", "location", "capability"):
                    # Only the user identity schema — never assistant/agent labels.
                    labs = labels.strip()
                    if labs.startswith("agent") or "agent:" in labs or labs.startswith("project"):
                        continue
                    if labs and labs != "user" and "user" not in labs.split():
                        if key in ("name", "preferred_name", "role"):
                            continue
                    _add(
                        SemanticFact(
                            kind="identity" if key != "capability" else "skill",
                            property=key,
                            value=value,
                            entity="",
                        )
                    )

    def _ingest_experiences() -> None:
        experiences = sorted(
            store.experiences.values(),
            key=lambda e: (getattr(e, "t_start", 0.0), getattr(e, "sequence", 0)),
        )
        for exp in experiences:
            meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
            for i in range(12):
                kind = meta.get(f"fact_{i}_kind")
                if not kind:
                    continue
                prop = meta.get(f"fact_{i}_property") or ""
                value = meta.get(f"fact_{i}_value") or ""
                if not value:
                    continue
                entity = meta.get(f"fact_{i}_relation") or ""
                if kind == "experience":
                    continue
                if kind in (
                    "possession",
                    "preference",
                    "project",
                    "goal",
                    "identity",
                    "skill",
                    "location",
                    "relationship",
                ):
                    _add(
                        SemanticFact(
                            kind=kind,
                            property=prop,
                            value=value,
                            entity=entity,
                            experience_id=getattr(exp, "id", "") or "",
                        )
                    )

    # Concepts seed the index; experience lineage overwrites (active teaching wins).
    _ingest_attr_concept()
    _ingest_experiences()
    return list(by_slot.values()) + extras


def is_semantic_autobiography_query(cue: str) -> bool:
    """True for semantic personal-knowledge queries (not episodic event recall)."""
    text = (cue or "").strip()
    if not text:
        return False
    # Leave pure episodic event questions to episodic reconstruction.
    if re.search(
        r"\b(what\s+happened|what\s+did\s+i\s+\w+|where\s+did\s+i\s+go|"
        r"yesterday|last\s+(?:week|friday|tuesday)|this\s+morning)\b",
        text,
        re.I,
    ) and not re.search(
        r"\b(operating\s+system|graphics\s+card|gpu|projects?|prefer|computer|"
        r"laptop|desktop|summarize|ai\s+setup|know\s+about\s+my)\b",
        text,
        re.I,
    ):
        return False
    return bool(
        re.search(
            r"\b("
            r"operating\s+system|what\s+os\b|runs\s+on\s+my|"
            r"graphics\s+card|what\s+gpu\b|how\s+much\s+ram\b|"
            r"what\s+projects?\b|projects?\s+am\s+i|"
            r"ai\s+projects?|building|"
            r"what\s+do\s+i\s+prefer|what\s+kind\s+of\s+responses?|"
            r"prefer\s+local|local\s+or\s+cloud|"
            r"know\s+about\s+my\s+(?:computer|laptop|desktop|ai|setup|machines?)|"
            r"tell\s+me\s+what\s+you\s+know\s+about\s+my|"
            r"summarize\s+what\s+you\s+know|"
            r"which\s+computer\b.+\b(?:better|training|ai\s+models?)|"
            r"better\s+for\s+training|"
            r"favorite\s+editor|what\s+editor\b"
            r")\b",
            text,
            re.I,
        )
    )


def answer_semantic_query(cue: str, facts: list[SemanticFact]) -> str | None:
    """Answer a semantic autobiographical cue from collected facts, or None."""
    text = (cue or "").strip()
    if not text:
        return None
    low = text.lower()

    if re.search(r"\bsummarize\s+what\s+you\s+know\b|\bwhat\s+do\s+you\s+know\s+about\s+me\b", low):
        return format_personal_summary(facts)

    if re.search(r"\bknow\s+about\s+my\s+(?:computer|laptop|desktop|machines?)\b", low):
        return format_computer_summary(facts)

    if re.search(r"\bknow\s+about\s+my\s+ai\b|\bai\s+setup\b", low):
        return format_ai_setup_summary(facts)

    if re.search(r"\bwhich\s+computer\b|\bbetter\s+for\s+training\b", low):
        return cross_reason_training(facts)

    if re.search(r"\bwhat\s+do\s+i\s+prefer\b", low):
        return format_preferences(facts)

    if re.search(r"\blocal\b.+\bcloud\b|\bcloud\b.+\blocal\b|\bprefer\s+local\b", low):
        return answer_local_vs_cloud(facts)

    if re.search(r"\bresponses?\b.+\bdebug|\bdebug.+\blike\b|\bkind\s+of\s+responses?\b", low):
        return answer_debugging_preference(facts)

    if re.search(r"\boperating\s+system\b|\bwhat\s+os\b", low):
        return answer_os_query(facts, low)

    if re.search(r"\bgraphics\s+card\b|\bwhat\s+gpu\b|\bgpu\b", low):
        return answer_gpu_query(facts, low)

    if re.search(r"\bprojects?\b|\bbuilding\b|\bworking\s+on\b", low):
        return answer_projects_query(facts, low)

    if re.search(r"\beditor\b", low):
        return answer_editor_query(facts)

    return None


def _possessions(facts: list[SemanticFact]) -> list[SemanticFact]:
    return [f for f in facts if f.kind == "possession"]


def _projects(facts: list[SemanticFact]) -> list[SemanticFact]:
    out: list[SemanticFact] = []
    seen: set[str] = set()
    for f in facts:
        if f.kind != "project":
            continue
        key = f.value.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def _preferences(facts: list[SemanticFact]) -> list[SemanticFact]:
    out: list[SemanticFact] = []
    seen: set[str] = set()
    for f in facts:
        if f.kind != "preference":
            continue
        key = f.property.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def answer_os_query(facts: list[SemanticFact], low: str) -> str:
    entity = ""
    if "laptop" in low:
        entity = "laptop"
    elif "desktop" in low:
        entity = "desktop"
    elif "phone" in low or "tablet" in low:
        entity = "phone" if "phone" in low else "tablet"
    elif "computer" in low or "pc" in low:
        entity = "computer"
    matches = [f for f in _possessions(facts) if f.property == "os"]
    if entity and entity != "computer":
        matches = [f for f in matches if f.entity == entity]
    elif entity == "computer":
        matches = [f for f in matches if f.entity in ("computer", "desktop", "laptop", "pc")]
    if not matches:
        return UNKNOWN
    if len(matches) == 1:
        f = matches[0]
        return f"Your {f.entity or 'computer'} runs {f.value}."
    parts = [f"your {f.entity} runs {f.value}" for f in matches]
    return _lead_cap("; ".join(parts) + ".")


def answer_gpu_query(facts: list[SemanticFact], low: str) -> str:
    entity = "desktop" if "desktop" in low else ("laptop" if "laptop" in low else "")
    matches = [f for f in _possessions(facts) if f.property == "gpu"]
    if entity:
        matches = [f for f in matches if f.entity == entity]
    if not matches:
        return UNKNOWN
    f = matches[-1]
    article = _indefinite_article(f.value)
    return f"Your {f.entity or 'computer'} has {article} {f.value}."


def answer_editor_query(facts: list[SemanticFact]) -> str:
    for f in _possessions(facts):
        if f.property == "editor":
            return f"Your favorite editor is {f.value}." if "favorite" in f.property else f"You use {f.value}."
    for f in _preferences(facts):
        if "editor" in f.property:
            return f"Your favorite editor is {f.value}."
    return UNKNOWN


def answer_projects_query(facts: list[SemanticFact], low: str) -> str:
    projects = _projects(facts)
    if not projects:
        return UNKNOWN
    names = [p.value for p in projects]
    if "ai" in low:
        # Prefer projects whose names look AI-related; if none tagged, return all taught projects.
        aiish = [n for n in names if re.search(r"\b(aria|ai|blackfly|fly|model|llm)\b", n, re.I)]
        names = aiish or names
        if not names:
            return UNKNOWN
    if len(names) == 1:
        return f"You are working on {names[0]}."
    if len(names) == 2:
        return f"You are working on {names[0]} and {names[1]}."
    return "You are working on " + ", ".join(names[:-1]) + f", and {names[-1]}."


def format_preferences(facts: list[SemanticFact]) -> str:
    prefs = _preferences(facts)
    if not prefs:
        return UNKNOWN
    lines: list[str] = []
    for f in prefs:
        if f.property.startswith("favorite_"):
            domain = f.property.replace("favorite_", "").replace("_", " ")
            lines.append(f"Your favorite {domain} is {f.value}.")
        elif f.property.startswith("prefer_"):
            domain = f.property.replace("prefer_", "").replace("_", " ")
            lines.append(f"You prefer {f.value}.")
        else:
            lines.append(f"You prefer {f.value}.")
    return "\n".join(lines)


def answer_local_vs_cloud(facts: list[SemanticFact]) -> str:
    for f in _preferences(facts):
        low = f.value.lower()
        if "local" in low and "ai" in low:
            return "You prefer local AI models."
        if "cloud" in low and "ai" in low:
            return "You prefer cloud AI models."
        if f.property in ("prefer_ai", "prefer_models") or "ai" in f.property:
            if "local" in low:
                return "You prefer local AI models."
            if "cloud" in low:
                return "You prefer cloud AI models."
            return f"You prefer {f.value}."
    return UNKNOWN


def answer_debugging_preference(facts: list[SemanticFact]) -> str:
    for f in _preferences(facts):
        low = f.value.lower()
        if "debug" in low or "step-by-step" in low or "step by step" in low:
            return f"You like {f.value}."
        if "debug" in f.property:
            return f"You like {f.value}."
    return UNKNOWN


def format_computer_summary(facts: list[SemanticFact]) -> str:
    poss = _possessions(facts)
    if not poss:
        return UNKNOWN
    by_entity: dict[str, dict[str, str]] = {}
    for f in poss:
        ent = f.entity or "computer"
        by_entity.setdefault(ent, {})[f.property] = f.value
    sentences: list[str] = []
    for ent, attrs in sorted(by_entity.items()):
        bits: list[str] = []
        if "os" in attrs:
            bits.append(f"runs {attrs['os']}")
        if "gpu" in attrs:
            bits.append(f"has {_indefinite_article(attrs['gpu'])} {attrs['gpu']}")
        if "ram" in attrs:
            bits.append(f"has {attrs['ram']} of RAM" if "ram" not in attrs["ram"].lower() else f"has {attrs['ram']}")
        if "editor" in attrs and ent == "editor":
            sentences.append(f"You use {attrs['editor']} as your editor.")
            continue
        if bits:
            sentences.append(f"Your {ent} " + " and ".join(bits) + ".")
    return " ".join(sentences) if sentences else UNKNOWN


def format_ai_setup_summary(facts: list[SemanticFact]) -> str:
    parts: list[str] = []
    projects = _projects(facts)
    if projects:
        names = [p.value for p in projects]
        if len(names) == 1:
            parts.append(f"You are working on {names[0]}.")
        else:
            parts.append(
                "You are working on "
                + (" and ".join(names) if len(names) == 2 else ", ".join(names[:-1]) + f", and {names[-1]}")
                + "."
            )
    for f in _preferences(facts):
        if "ai" in f.property or "ai" in f.value.lower() or "local" in f.value.lower():
            parts.append(f"You prefer {f.value}.")
            break
    for f in _possessions(facts):
        if f.property == "gpu":
            parts.append(
                f"Your {f.entity or 'desktop'} has {_indefinite_article(f.value)} {f.value}."
            )
    return " ".join(parts) if parts else UNKNOWN


def format_personal_summary(facts: list[SemanticFact]) -> str:
    """Organized active-only personal summary from learned semantic facts."""
    lines: list[str] = []

    for f in facts:
        if f.kind == "identity" and f.property in ("name", "preferred_name"):
            label = "preferred name" if f.property == "preferred_name" else "name"
            lines.append(f"Your {label} is {f.value}.")
        elif f.kind == "identity" and f.property == "role":
            lines.append(f"You are {f.value}.")
        elif f.kind == "location":
            lines.append(f"You live in {f.value}.")
        elif f.kind == "skill":
            lines.append(f"You can {f.value}.")

    for f in _preferences(facts):
        if f.property.startswith("favorite_"):
            domain = f.property.replace("favorite_", "").replace("_", " ")
            lines.append(f"Your favorite {domain} is {f.value}.")
        else:
            lines.append(f"You prefer {f.value}.")

    projects = _projects(facts)
    if projects:
        names = [p.value for p in projects]
        if len(names) == 1:
            lines.append(f"You are working on {names[0]}.")
        elif len(names) == 2:
            lines.append(f"You are working on {names[0]} and {names[1]}.")
        else:
            lines.append(
                "You are working on " + ", ".join(names[:-1]) + f", and {names[-1]}."
            )

    computer = format_computer_summary(facts)
    if computer != UNKNOWN:
        lines.append(computer)

    # Deduplicate lines
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        key = line.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return "\n".join(out) if out else UNKNOWN


def cross_reason_training(facts: list[SemanticFact]) -> str:
    """Compare remembered machines for AI training suitability — facts only."""
    by_entity: dict[str, dict[str, str]] = {}
    for f in _possessions(facts):
        ent = f.entity or ""
        if not ent:
            continue
        by_entity.setdefault(ent, {})[f.property] = f.value

    if not by_entity:
        return UNKNOWN

    scores: list[tuple[str, int, list[str]]] = []
    for ent, attrs in by_entity.items():
        score = 0
        reasons: list[str] = []
        if "gpu" in attrs:
            score += 3
            reasons.append(f"has {_indefinite_article(attrs['gpu'])} {attrs['gpu']}")
        if "ram" in attrs:
            score += 2
            reasons.append(f"has {attrs['ram']} RAM")
        if "os" in attrs:
            reasons.append(f"runs {attrs['os']}")
        scores.append((ent, score, reasons))

    scores.sort(key=lambda t: t[1], reverse=True)
    best_ent, best_score, best_reasons = scores[0]
    if best_score <= 0:
        return UNKNOWN
    # Require a distinguishing signal (GPU/RAM), not OS alone.
    if best_score < 2:
        return UNKNOWN
    if len(scores) > 1 and scores[1][1] == best_score:
        return (
            f"From what you've told me, your {best_ent} and your {scores[1][0]} "
            "look similarly capable for larger AI training based on remembered specs."
        )
    reason = "; ".join(best_reasons) if best_reasons else "remembered hardware"
    return (
        f"Based on what you've told me, your {best_ent} would probably be better "
        f"for training larger AI models because it {reason}."
    )


def _lead_cap(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return s
    for i, ch in enumerate(s):
        if ch.isalpha():
            return s[:i] + ch.upper() + s[i + 1 :]
    return s
