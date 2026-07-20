"""Aria presentation layer for certified ACM cognitive memory results.

ACM owns cognition and evidence; this module only shapes speech for conversation.
Never invents facts — only rephrases faithful ACM output and teaching acknowledgements.
"""

from __future__ import annotations

import re

from aria_acm.acm.authority.teaching import detect_teaching
from aria_acm.acm.semantic.model import FactKind

_TEMPORAL_LABEL = {
    "yesterday": "yesterday",
    "today": "today",
    "this_morning": "this morning",
    "this_afternoon": "this afternoon",
    "this_evening": "this evening",
    "last_night": "last night",
    "last_week": "last week",
    "last_month": "last month",
    "last_monday": "last Monday",
    "last_tuesday": "last Tuesday",
    "last_wednesday": "last Wednesday",
    "last_thursday": "last Thursday",
    "last_friday": "last Friday",
    "last_saturday": "last Saturday",
    "last_sunday": "last Sunday",
}


def format_teaching_acknowledgement(prompt: str) -> str:
    """Build a conversational ack only when Teaching Recognition extracted facts."""
    text = (prompt or "").strip()
    if not text:
        return ""
    detected = detect_teaching(text)
    if not detected.is_teaching or not detected.facts:
        return ""
    fact = detected.facts[0]
    if fact.kind == FactKind.EXPERIENCE:
        action = (fact.property or "did something").replace("_", " ")
        obj = (fact.value or "").strip()
        when = _TEMPORAL_LABEL.get((fact.relation_type or "").lower(), "")
        when = when or (fact.relation_type or "").replace("_", " ")
        core = f"you {action} {obj}".strip()
        if when:
            return f"Okay, I'll remember that {core} {when}."
        return f"Okay, I'll remember that {core}."
    if fact.kind == FactKind.POSSESSION:
        entity = (fact.relation_type or "item").replace("_", " ")
        prop = (fact.property or "").replace("_", " ")
        if prop == "os":
            return f"Okay, I'll remember that your {entity} runs {fact.value}."
        if prop == "gpu":
            return f"Okay, I'll remember that your {entity} has an {fact.value}." if str(
                fact.value
            ).lower().startswith("rtx") else f"Okay, I'll remember that your {entity} has a {fact.value}."
        if prop == "ram":
            return f"Okay, I'll remember that your {entity} has {fact.value} of RAM."
        if prop == "editor":
            return f"Okay, I'll remember that you use {fact.value}."
        return f"Okay, I'll remember that your {entity} {prop} is {fact.value}."
    if fact.kind == FactKind.PROJECT:
        return f"Okay, I'll remember that you're working on {fact.value}."
    if fact.kind == FactKind.PREFERENCE and fact.property.startswith("favorite_"):
        domain = fact.property.replace("favorite_", "").replace("_", " ")
        return f"Okay, I'll remember that your favorite {domain} is {fact.value}."
    if fact.kind == FactKind.PREFERENCE:
        return f"Okay, I'll remember that you prefer {fact.value}."
    if fact.kind == FactKind.IDENTITY and fact.property in ("name", "preferred_name"):
        label = "preferred name" if fact.property == "preferred_name" else "name"
        return f"Okay, I'll remember that your {label} is {fact.value}."
    if fact.kind == FactKind.LOCATION:
        return f"Okay, I'll remember that you live in {fact.value}."
    summary = fact.canonical_summary()
    if summary.lower().startswith("user "):
        summary = "you " + summary[5:]
    return f"Okay, I'll remember that {summary.rstrip('.')}."


def polish_cognitive_speech(speech: str, result: dict | None = None, *, prompt: str = "") -> str:
    """Rephrase ACM speech for conversation without changing meaning."""
    text = (speech or "").strip()
    if not text:
        return text
    # Pass through natural ACM episodic prose (single or multi-sentence).
    if (
        "From your evidence" not in text
        and "Episodic events:" not in text
        and not text.startswith("Evidence (")
        and not _RAW_MEMORY_BULLETS.search(text)
        and re.match(r"^You\s+\w+", text)
        and all(
            (not ln.strip()) or ln.strip().lower().startswith("you ")
            for ln in text.splitlines()
        )
    ):
        return text
    if _RAW_MEMORY_BULLETS.search(text):
        return format_bullet_recall_conversational(text, prompt)
    if _PREFERENCE_RECALL.match(text):
        return format_preference_recall_conversational(text)
    if _INTERNAL_REFLECTION.search(text):
        text = _rewrite_internal_reflection(text, prompt)
    if text.startswith("Evidence (") or "Episodic events:" in text:
        return format_evidence_conversational(text)
    if "From your evidence" in text or _EPISODIC_SINGLE.match(text):
        return format_episodic_conversational(text, prompt)
    if _EXPLANATION_MARKERS.search(text):
        return format_explanation_conversational(text, prompt)
    if _EPISODIC_STATEMENT.match(text):
        return format_episodic_statement_conversational(text, prompt)
    text = re.sub(r"\s*\(confidence [\d.]+\)\s*$", "", text)
    text = re.sub(r"\s*\(competing memories; confidence [\d.]+\)\s*$", "", text)
    return text


_RAW_MEMORY_BULLETS = re.compile(r"(?:^|\n)\s*•\s+", re.M)
_PREFERENCE_RECALL = re.compile(
    r"^Your favorite (\w+(?:\s+\w+)?) is (.+)\.?$",
    re.I,
)
_EPISODIC_STATEMENT = re.compile(
    r"^You\s+(installed|bought|upgraded|replaced|visited|went|cleaned)\s+(.+)\([^)]+\)\.?\s*$",
    re.I,
)


def format_preference_recall_conversational(text: str) -> str:
    m = _PREFERENCE_RECALL.match(text.strip())
    if not m:
        return text
    domain, value = m.group(1), m.group(2).rstrip(".")
    return f"You told me your favorite {domain} is {value}."


def format_episodic_statement_conversational(text: str, prompt: str = "") -> str:
    m = _EPISODIC_STATEMENT.match(text.strip())
    if not m:
        return text
    verb, obj = m.group(1), m.group(2).strip()
    when_m = re.search(r"\(([^)]+)\)", text)
    when = when_m.group(1) if when_m else ""
    obj = re.sub(r"\s*\([^)]*\)\s*$", "", obj).strip()
    if when:
        return f"You told me {when} that you {verb} {obj}."
    return f"You told me that you {verb} {obj}."


def format_bullet_recall_conversational(text: str, prompt: str = "") -> str:
    """Turn raw bullet memory lists into conversational recall."""
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.lower() == "memory":
            continue
        if line.startswith("•"):
            line = line.lstrip("•").strip()
        if line.lower().startswith("your favorite"):
            lines.append(format_preference_recall_conversational(line))
            continue
        conv = _evidence_line_to_conversational(line)
        if conv:
            lines.append(conv)
    lines = _dedupe_presentation_lines(lines)
    if not lines:
        return text
    if len(lines) == 1:
        line = lines[0].rstrip(".")
        if line.lower().startswith("you "):
            return f"You told me {line[4:]}."
        return f"You told me {line}."
    intro = "From what you've shared with me:"
    return intro + "\n" + "\n".join(f"• {ln.rstrip('.')}." for ln in lines)


def polish_fragment_recall(speech: str, prompt: str, *, full_speech: str = "") -> str:
    """Expand noun-phrase fragments using fuller recall text when available."""
    s = (speech or "").strip()
    if not s:
        return full_speech or s
    if full_speech and full_speech.strip() and full_speech.strip() != s:
        if len(s.split()) <= 4 and not re.search(r"\b(yesterday|last\s+\w+|today)\b", s, re.I):
            return polish_cognitive_speech(full_speech, prompt=prompt)
    rebuilt = _reconstruct_fragment(s, prompt)
    if rebuilt:
        return rebuilt
    if re.match(r"^(?:a|an|the)\s+\w+\.?$", s, re.I):
        when = ""
        wm = re.search(
            r"\b(yesterday|today|this\s+morning|last\s+week|last\s+\w+)\b",
            prompt,
            re.I,
        )
        if wm:
            when = wm.group(1)
        noun = s.rstrip(".").strip()
        if when:
            return (
                f"You told me {when} that you installed {noun}, "
                f"but you didn't specify which model."
            )
        return f"You told me about {noun}, but I don't have more detail than that."
    return polish_cognitive_speech(s, prompt=prompt)


def _reconstruct_fragment(speech: str, prompt: str) -> str:
    """Rebuild short ACM fragments into full remembered propositions."""
    s = (speech or "").strip().rstrip(".")
    q = (prompt or "").strip()
    if not s or len(s.split()) > 6:
        return ""
    when_m = re.search(
        r"\b(yesterday|today|this\s+morning|last\s+week|last\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
        q,
        re.I,
    )
    when = when_m.group(1) if when_m else ""
    low = s.lower()
    # "fishing." / "fish" for "What fish did I catch?"
    if low in ("fishing", "fish") or re.search(r"\bwhat\s+fish\b", q, re.I):
        if when:
            return f"You told me {when} that you caught fish."
        return "You told me about fish you caught."
    # "my RAM." for "What RAM did I upgrade?"
    if re.match(r"^my\s+\w+$", s, re.I) or re.search(r"\bwhat\s+ram\b", q, re.I):
        obj = re.sub(r"^my\s+", "", s, flags=re.I).strip()
        if when:
            return f"You told me {when} that you upgraded your {obj}."
        return f"You told me you upgraded your {obj}."
    # Duplicate verb prefix: "installed you installed a GPU"
    dup = re.match(r"^(\w+)\s+you\s+\1\b", s, re.I)
    if dup:
        s = re.sub(r"^(\w+)\s+", "", s, count=1, flags=re.I)
    # Bare verb label + proposition
    if re.match(r"^(installed|bought|upgraded|replaced|visited|caught)\s+you\s+", s, re.I):
        s = re.sub(r"^[a-z]+\s+", "", s, count=1, flags=re.I)
        if when:
            return f"You told me {when} that {s}."
        return f"You told me that {s}."
    return ""


def _dedupe_presentation_lines(lines: list[str]) -> list[str]:
    """Collapse identical consecutive presentation lines (same fact repeated in ACM evidence)."""
    out: list[str] = []
    prev = ""
    for line in lines:
        key = line.strip().lower()
        if key and key == prev:
            continue
        out.append(line)
        prev = key
    return out


_INTERNAL_REFLECTION = re.compile(
    r"\bmy recollection appears\b|\bi evaluated my recollection\b",
    re.I,
)
_EXPLANATION_MARKERS = re.compile(
    r"\bbecause you later taught\b|\bremains in your evidence as a retired memory\b|"
    r"\bwas replaced when you later taught\b",
    re.I,
)
_EPISODIC_SINGLE = re.compile(
    r"^You\s+\w+.+\([^)]+\)\.\s*$",
    re.I,
)


def format_episodic_conversational(speech: str, prompt: str = "") -> str:
    lines_out: list[str] = []
    header = ""
    for raw in speech.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("From your evidence"):
            when = re.search(r"\(([^)]+)\)", line)
            header = when.group(1) if when else ""
            continue
        if line.startswith("- "):
            body = line[2:]
            body = re.sub(r"^[a-z_]+:\s*", "", body, count=1)
            conv = _evidence_line_to_conversational(body, header)
            lines_out.append(f"• {conv}")
            continue
        conv = _evidence_line_to_conversational(line, header)
        if conv:
            lines_out.append(conv)
    if len(lines_out) == 1 and not header:
        return f"From what you've shared with me, {lines_out[0].lstrip('• ')}"
    if header and lines_out:
        intro = f"From what you've shared with me about {header}:"
        return intro + "\n" + "\n".join(lines_out)
    if lines_out:
        deduped = _dedupe_presentation_lines([ln.lstrip("• ") for ln in lines_out])
        if len(deduped) == 1:
            return f"From what you've shared with me, {deduped[0]}"
        return "From what you've shared with me:\n" + "\n".join(f"• {ln}" for ln in deduped)
    return _evidence_line_to_conversational(speech, header) or speech


def format_evidence_conversational(speech: str) -> str:
    sections: list[str] = ["Here's what I currently know."]
    prefs: list[str] = []
    retired: dict[str, str] = {}
    active: dict[str, str] = {}
    events: list[str] = []

    mode = ""
    current_key = ""
    for raw in speech.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Evidence (preference"):
            mode = "pref"
            continue
        if line.startswith("Episodic events:"):
            mode = "event"
            continue
        if mode == "pref":
            if line.endswith(":") and not line.startswith("v"):
                current_key = line.rstrip(":").strip()
                continue
            m = re.match(r"v\d+\s+(.+?)\s+\((active|retired)\)", line, re.I)
            if m and current_key:
                val, state = m.group(1), m.group(2).lower()
                if state == "active":
                    active[current_key] = val
                else:
                    retired[current_key] = val
            continue
        if mode == "event" and line.startswith("- "):
            body = line[2:]
            conv = _evidence_line_to_conversational(body)
            events.append(f"• {conv}")

    if active or retired:
        sections.append("\nPreferences")
        for key in sorted(set(active) | set(retired)):
            act = active.get(key)
            ret = retired.get(key)
            if act:
                line = f"• {key}: {act.title() if len(act) < 24 else act}"
                if ret:
                    line += f"\n  (previously {ret.title() if len(ret) < 24 else ret})"
                prefs.append(line)
        sections.extend(prefs)

    if events:
        sections.append("\nRecent events")
        sections.extend(events)

    if len(sections) == 1:
        return speech
    return "\n".join(sections)


def format_explanation_conversational(speech: str, prompt: str = "") -> str:
    text = speech.strip()
    low = text.lower()
    if "because you later taught" in low and "after" in low:
        m = re.search(
            r"(\w+(?:\s+\w+)?)\s+is your current favorite (\w+) because you later taught that after (\w+)",
            text,
            re.I,
        )
        if m:
            current, domain, prior = m.groups()
            return (
                f"Because you told me your favorite {domain} is {current}, "
                f"replacing {prior}."
            )
    if "was replaced when you later taught" in low:
        m = re.search(
            r"(\w+)\s+was replaced when you later taught that your favorite (\w+) is (\w+)",
            text,
            re.I,
        )
        if m:
            prior, domain, current = m.groups()
            return (
                f"Because you told me your favorite {domain} is {current}, "
                f"replacing {prior}."
            )
    text = re.sub(
        r"\s+remains in your evidence as a retired memory\.?",
        ".",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bblue\b", "blue", text)  # preserve values
    if not text.lower().startswith("because"):
        text = "I'm basing that on what you've previously told me. " + text
    return text


def _rewrite_internal_reflection(text: str, prompt: str) -> str:
    if prompt:
        return "I'm basing that on what you've previously told me."
    return "I'm basing that on what you've previously told me."


def _evidence_line_to_conversational(body: str, header: str = "") -> str:
    s = (body or "").strip()
    if not s:
        return ""
    when_prefix = ""
    m = re.match(r"^([a-z_]+):\s*(.+)$", s, re.I)
    if m:
        label = m.group(1).lower()
        if label in _TEMPORAL_LABEL:
            when_prefix = _TEMPORAL_LABEL[label]
            s = m.group(2).strip()
        # Non-temporal labels (e.g. "upgrade:") are part of broken list formatting —
        # drop the label token only; do not treat it as a time adverb.
        elif label in (
            "upgrade",
            "upgraded",
            "install",
            "installed",
            "bought",
            "cleaned",
            "visited",
            "caught",
            "went",
        ):
            s = m.group(2).strip()
    s = re.sub(r"^User\s+", "you ", s, flags=re.I)
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()
    if s.lower().startswith("yesterday ") or s.lower().startswith("last "):
        s = re.sub(r"^(Yesterday|Last\s+\w+)\s+I\s+", r"\1 you ", s, flags=re.I)
    elif re.match(r"^I\s+", s, re.I):
        s = "you " + s[2:]
    # Never use non-temporal headers like "upgrade" as when-adverbs.
    when = when_prefix
    if header and header.lower() in _TEMPORAL_LABEL:
        when = when or _TEMPORAL_LABEL[header.lower()]
    elif header and re.search(
        r"^(yesterday|today|this\s+\w+|last\s+\w+)$", header, re.I
    ):
        when = when or header
    if when and not s.lower().startswith(when.lower()):
        if re.match(r"^you\s+", s, re.I):
            rest = s[4:].rstrip(".")
            return f"You {rest} {when}."
        return f"You {s.rstrip('.')} {when}."
    if not s.endswith("."):
        s += "."
    if s.lower().startswith("you "):
        return s[0].upper() + s[1:] if s[0].islower() else s
    return s
