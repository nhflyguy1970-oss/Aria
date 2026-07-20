"""Memory evolution — historical lineage, change detection, and timeline reconstruction.

Reuses inactive attribute versions + chronological experience fact metadata.
Never invents; never uses world knowledge.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from acm.remembering.semantic import UNKNOWN, SemanticFact, _indefinite_article


@dataclass(frozen=True)
class HistoryEvent:
    """One chronological autobiographical change event."""

    kind: str
    property: str
    value: str
    entity: str = ""
    update_op: str = "set"
    experience_id: str = ""
    t_start: float = 0.0
    sequence: int = 0
    active: bool = True


def collect_semantic_history(store: Any) -> list[HistoryEvent]:
    """Chronological semantic events from experiences (full lineage, not active-only)."""
    events: list[HistoryEvent] = []
    experiences = sorted(
        store.experiences.values(),
        key=lambda e: (getattr(e, "t_start", 0.0), getattr(e, "sequence", 0)),
    )
    for exp in experiences:
        meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
        t0 = float(getattr(exp, "t_start", 0.0) or 0.0)
        seq = int(getattr(exp, "sequence", 0) or 0)
        eid = getattr(exp, "id", "") or ""
        for i in range(12):
            kind = meta.get(f"fact_{i}_kind")
            if not kind:
                continue
            if kind == "experience":
                continue
            prop = meta.get(f"fact_{i}_property") or ""
            value = meta.get(f"fact_{i}_value") or ""
            if not value:
                continue
            entity = meta.get(f"fact_{i}_relation") or ""
            op = meta.get(f"fact_{i}_update_op") or "set"
            events.append(
                HistoryEvent(
                    kind=kind,
                    property=prop,
                    value=value,
                    entity=entity,
                    update_op=op,
                    experience_id=eid,
                    t_start=t0,
                    sequence=seq,
                    active=True,
                )
            )
    return events


def retired_entities(history: list[HistoryEvent]) -> set[str]:
    retired: set[str] = set()
    for ev in history:
        if ev.kind == "possession" and ev.property == "status" and ev.value.lower() == "retired":
            if ev.entity:
                retired.add(ev.entity.lower())
    return retired


def finished_projects(history: list[HistoryEvent]) -> set[str]:
    done: set[str] = set()
    for ev in history:
        if ev.kind == "project" and ev.property == "status":
            if ev.value.lower() in ("finished", "complete", "completed", "retired", "done"):
                title = (ev.entity or ev.value).strip()
                if title and title.lower() not in (
                    "finished",
                    "complete",
                    "completed",
                    "retired",
                    "done",
                ):
                    done.add(title.casefold())
    return done


def active_projects_from_history(history: list[HistoryEvent]) -> list[str]:
    """Project titles still active after finish events."""
    order: list[str] = []
    active: set[str] = set()
    done = set()
    for ev in history:
        if ev.kind != "project":
            continue
        if ev.property == "status" and ev.value.lower() in (
            "finished",
            "complete",
            "completed",
            "retired",
            "done",
        ):
            title = (ev.entity or "").strip()
            if title:
                done.add(title.casefold())
                active.discard(title.casefold())
            continue
        if ev.property in ("project", "title") and ev.value:
            key = ev.value.casefold()
            if key in done:
                continue
            if key not in active:
                order.append(ev.value)
                active.add(key)
            elif ev.value not in order:
                # refresh display name
                order = [ev.value if x.casefold() == key else x for x in order]
    return [n for n in order if n.casefold() in active]


def all_projects_from_history(history: list[HistoryEvent]) -> list[str]:
    """Active + historical project titles in first-seen order."""
    order: list[str] = []
    seen: set[str] = set()
    for ev in history:
        if ev.kind != "project":
            continue
        if ev.property in ("project", "title") and ev.value:
            key = ev.value.casefold()
            if key not in seen:
                seen.add(key)
                order.append(ev.value)
        elif ev.property == "status" and ev.entity:
            key = ev.entity.casefold()
            if key not in seen and key not in (
                "finished",
                "complete",
                "completed",
                "retired",
                "done",
            ):
                seen.add(key)
                order.append(ev.entity)
    return order


def lineage_values(
    history: list[HistoryEvent],
    *,
    kind: str,
    property: str,
    entity: str = "",
) -> list[str]:
    """Ordered unique values for a slot (historical + current)."""
    out: list[str] = []
    seen: set[str] = set()
    for ev in history:
        if ev.kind != kind or ev.property.lower() != property.lower():
            continue
        if entity and (ev.entity or "").lower() != entity.lower():
            continue
        if ev.property == "status":
            continue
        key = ev.value.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(ev.value)
    return out


def is_memory_evolution_query(cue: str) -> bool:
    text = (cue or "").strip()
    if not text:
        return False
    return bool(
        re.search(
            r"\b("
            r"has\s+(?:my|the)\b.+\bchanged\b|"
            r"have\s+(?:my|the)\b.+\bchanged\b|"
            r"how\s+has\s+my\b.+\bchanged\b|"
            r"how\s+has\s+.+\bchanged\s+over\s+time\b|"
            r"what\s+operating\s+systems?\s+has\s+my\b|"
            r"what\s+oses?\s+has\s+my\b|"
            r"what\s+projects?\s+have\s+i\s+worked\s+on\b|"
            r"projects?\s+have\s+i\s+worked\b|"
            r"tell\s+me\s+about\s+my\s+computers?\b|"
            r"what\s+(?:phone|printer|truck|vehicle|kayak|car)\s+do\s+i\s+(?:own|have)\b|"
            r"what\s+vehicles?\s+do\s+i\s+own\b|"
            r"have\s+my\s+(?:ai\s+)?preferences?\s+changed\b"
            r")\b",
            text,
            re.I,
        )
    )


def answer_evolution_query(
    cue: str,
    history: list[HistoryEvent],
    *,
    active_facts: list[SemanticFact] | None = None,
) -> str | None:
    """Answer historical / change / timeline / ownership questions, or None."""
    text = (cue or "").strip()
    if not text:
        return None
    low = text.lower()
    active_facts = active_facts or []

    if re.search(r"\bwhat\s+operating\s+systems?\s+has\s+my\b|\bwhat\s+oses?\s+has\s+my\b", low):
        return _answer_os_history(low, history)

    if re.search(r"\bwhat\s+projects?\s+have\s+i\s+worked\b|\bprojects?\s+have\s+i\s+worked\b", low):
        return _answer_projects_all(history)

    if re.search(r"\bhave\s+my\s+(?:ai\s+)?preferences?\s+changed\b", low):
        return _answer_pref_changed(history)

    if re.search(r"\bhas\s+my\s+desktop\s+(?:hardware|gpu|graphics)\s+changed\b", low) or (
        "desktop" in low and "changed" in low and re.search(r"\bhardware|gpu|graphics\b", low)
    ):
        return _answer_hardware_changed(history, entity="desktop", prop="gpu")

    if re.search(r"\bhow\s+has\s+my\s+ai\s+setup\s+changed\b|\bai\s+setup\s+changed\s+over\s+time\b", low):
        return _answer_ai_timeline(history)

    if re.search(r"\bhow\s+has\s+my\s+computer\s+changed\b|\bcomputers?\s+changed\s+over\s+time\b", low):
        return _answer_computer_timeline(history)

    if re.search(r"\btell\s+me\s+about\s+my\s+computers?\b", low):
        return _answer_computers_current_vs_historical(history, active_facts)

    if re.search(r"\bwhat\s+phone\s+do\s+i\s+(?:own|have)\b", low):
        return _answer_owned_model(history, active_facts, entity="phone")

    if re.search(r"\bwhat\s+printer\s+do\s+i\s+(?:own|have)\b", low):
        return _answer_owned_model(history, active_facts, entity="printer")

    if re.search(r"\bwhat\s+(?:truck|vehicle|car|kayak)\s+do\s+i\s+(?:own|have)\b", low):
        ent = "truck" if "truck" in low else (
            "kayak" if "kayak" in low else ("car" if "car" in low else "vehicle")
        )
        return _answer_owned_model(history, active_facts, entity=ent)

    if re.search(r"\bwhat\s+vehicles?\s+do\s+i\s+own\b", low):
        return _answer_vehicles(history, active_facts)

    return None


def _answer_os_history(low: str, history: list[HistoryEvent]) -> str:
    entity = "laptop" if "laptop" in low else ("desktop" if "desktop" in low else "")
    vals = lineage_values(history, kind="possession", property="os", entity=entity)
    if not vals:
        # fallback any computer entity
        vals = lineage_values(history, kind="possession", property="os", entity="")
        if entity:
            vals = [
                v
                for ev in history
                if ev.kind == "possession"
                and ev.property == "os"
                and (not entity or ev.entity == entity)
                for v in [ev.value]
            ]
            # unique preserve order
            seen: set[str] = set()
            uniq: list[str] = []
            for v in vals:
                if v.casefold() in seen:
                    continue
                seen.add(v.casefold())
                uniq.append(v)
            vals = uniq
    if not vals:
        return UNKNOWN
    label = entity or "computer"
    if len(vals) == 1:
        return f"Your {label} has used {vals[0]}."
    return f"Your {label} has used " + ", ".join(vals[:-1]) + f", and {vals[-1]}."


def _answer_projects_all(history: list[HistoryEvent]) -> str:
    names = all_projects_from_history(history)
    if not names:
        return UNKNOWN
    active = {n.casefold() for n in active_projects_from_history(history)}
    done = finished_projects(history)
    current = [n for n in names if n.casefold() in active]
    historical = [n for n in names if n.casefold() in done or n.casefold() not in active]
    parts: list[str] = []
    if current:
        parts.append(
            "You are currently working on "
            + (
                current[0]
                if len(current) == 1
                else (" and ".join(current) if len(current) == 2 else ", ".join(current[:-1]) + f", and {current[-1]}")
            )
            + "."
        )
    if historical:
        parts.append(
            "You have also worked on "
            + (
                historical[0]
                if len(historical) == 1
                else (
                    " and ".join(historical)
                    if len(historical) == 2
                    else ", ".join(historical[:-1]) + f", and {historical[-1]}"
                )
            )
            + "."
        )
    if not parts:
        return "You have worked on " + ", ".join(names[:-1]) + f", and {names[-1]}." if len(names) > 1 else f"You have worked on {names[0]}."
    return " ".join(parts)


def _answer_pref_changed(history: list[HistoryEvent]) -> str:
    vals = lineage_values(history, kind="preference", property="prefer_ai")
    if len(vals) < 2:
        # also scan preference values mentioning ai
        ai_vals: list[str] = []
        seen: set[str] = set()
        for ev in history:
            if ev.kind != "preference":
                continue
            if "ai" not in ev.property and "ai" not in ev.value.lower() and "local" not in ev.value.lower() and "cloud" not in ev.value.lower():
                continue
            key = ev.value.casefold()
            if key in seen:
                continue
            seen.add(key)
            ai_vals.append(ev.value)
        vals = ai_vals
    if len(vals) < 2:
        return "I don't currently know of a change in your AI preferences."
    return (
        f"Yes. Your AI preference changed from {vals[0]} to {vals[-1]}."
    )


def _answer_hardware_changed(history: list[HistoryEvent], *, entity: str, prop: str) -> str:
    vals = lineage_values(history, kind="possession", property=prop, entity=entity)
    if len(vals) < 2:
        return f"I don't currently know of a change to your {entity} {prop}."
    return (
        f"Yes. Your {entity} {prop.upper() if prop == 'gpu' else prop} changed "
        f"from {vals[0]} to {vals[-1]}."
    )


def _answer_ai_timeline(history: list[HistoryEvent]) -> str:
    lines: list[str] = []
    seen_proj: set[str] = set()
    for ev in history:
        if ev.kind == "project" and ev.property in ("project", "title") and ev.value:
            key = ev.value.casefold()
            if key not in seen_proj:
                seen_proj.add(key)
                lines.append(f"Started {ev.value}")
        elif ev.kind == "project" and ev.property == "status":
            title = ev.entity or ""
            if title and ev.value.lower() in ("finished", "complete", "completed", "retired", "done"):
                lines.append(f"Finished {title}")
        elif ev.kind == "possession" and ev.property == "os" and ev.entity:
            # detect change relative to previous same entity
            prev = [
                e
                for e in history
                if e.kind == "possession"
                and e.property == "os"
                and e.entity == ev.entity
                and (e.t_start, e.sequence) < (ev.t_start, ev.sequence)
            ]
            if prev and prev[-1].value.casefold() != ev.value.casefold():
                lines.append(
                    f"Changed {ev.entity} from {prev[-1].value} to {ev.value}"
                )
            elif not prev:
                lines.append(f"Set {ev.entity} OS to {ev.value}")
        elif ev.kind == "possession" and ev.property == "gpu":
            prev = [
                e
                for e in history
                if e.kind == "possession"
                and e.property == "gpu"
                and (e.entity or "") == (ev.entity or "")
                and (e.t_start, e.sequence) < (ev.t_start, ev.sequence)
            ]
            if prev and prev[-1].value.casefold() != ev.value.casefold():
                lines.append(f"Replaced {prev[-1].value} with {ev.value}")
            elif not prev:
                lines.append(
                    f"Added {_indefinite_article(ev.value)} {ev.value}"
                    + (f" to your {ev.entity}" if ev.entity else "")
                )
        elif ev.kind == "preference" and (
            "ai" in ev.property or "ai" in ev.value.lower() or "local" in ev.value.lower() or "cloud" in ev.value.lower()
        ):
            prev = [
                e
                for e in history
                if e.kind == "preference"
                and (
                    "ai" in e.property
                    or "ai" in e.value.lower()
                    or "local" in e.value.lower()
                    or "cloud" in e.value.lower()
                )
                and (e.t_start, e.sequence) < (ev.t_start, ev.sequence)
            ]
            if prev and prev[-1].value.casefold() != ev.value.casefold():
                lines.append(
                    f"Changed AI preference from {prev[-1].value} to {ev.value}"
                )
            elif not prev:
                lines.append(f"Set AI preference to {ev.value}")
        elif ev.kind == "possession" and ev.property == "status" and ev.value.lower() == "retired":
            lines.append(f"Stopped using your {ev.entity}")

    # Deduplicate consecutive identical lines
    out: list[str] = []
    for line in lines:
        if out and out[-1].lower() == line.lower():
            continue
        out.append(line)
    if not out:
        return UNKNOWN
    return "\n".join(out)


def _answer_computer_timeline(history: list[HistoryEvent]) -> str:
    return _answer_ai_timeline(
        [
            ev
            for ev in history
            if ev.kind == "possession"
            or (ev.kind == "project")
        ]
    )


def _answer_computers_current_vs_historical(
    history: list[HistoryEvent],
    active_facts: list[SemanticFact],
) -> str:
    retired = retired_entities(history)
    computer_ents = frozenset(
        {"laptop", "desktop", "computer", "pc", "workstation", "machine", "server", "nas"}
    )
    by_ent: dict[str, dict[str, str]] = {}
    for f in active_facts:
        if f.kind != "possession" or f.property == "status":
            continue
        ent = f.entity or "computer"
        if ent not in computer_ents:
            continue
        by_ent.setdefault(ent, {})[f.property] = f.value

    current_bits: list[str] = []
    for ent, attrs in sorted(by_ent.items()):
        if ent in retired:
            continue
        parts: list[str] = []
        if "os" in attrs:
            parts.append(f"runs {attrs['os']}")
        if "gpu" in attrs:
            parts.append(f"has {_indefinite_article(attrs['gpu'])} {attrs['gpu']}")
        if "ram" in attrs:
            parts.append(f"has {attrs['ram']}")
        if parts:
            current_bits.append(f"Your {ent} " + " and ".join(parts) + ".")

    hist_bits: list[str] = []
    for ent in sorted(e for e in retired if e in computer_ents):
        vals_os = lineage_values(history, kind="possession", property="os", entity=ent)
        vals_gpu = lineage_values(history, kind="possession", property="gpu", entity=ent)
        detail: list[str] = []
        if vals_os:
            detail.append("ran " + (" / ".join(vals_os)))
        if vals_gpu:
            detail.append("had " + (" / ".join(vals_gpu)))
        if detail:
            hist_bits.append(f"Your {ent} (historical) " + " and ".join(detail) + ".")
        else:
            hist_bits.append(f"Your {ent} is historical — you no longer use it.")

    if not current_bits and not hist_bits:
        return UNKNOWN
    sections: list[str] = []
    if current_bits:
        sections.append("Current: " + " ".join(current_bits))
    if hist_bits:
        sections.append("Historical: " + " ".join(hist_bits))
    return " ".join(sections)


def _answer_owned_model(
    history: list[HistoryEvent],
    active_facts: list[SemanticFact],
    *,
    entity: str,
) -> str:
    for f in active_facts:
        if f.kind == "possession" and f.entity == entity and f.property in ("model", "attribute"):
            return f"Your {entity} is {f.value}."
    vals = lineage_values(history, kind="possession", property="model", entity=entity)
    if vals:
        return f"Your {entity} is {vals[-1]}."
    return UNKNOWN


def _answer_vehicles(
    history: list[HistoryEvent],
    active_facts: list[SemanticFact],
) -> str:
    ents = ("truck", "vehicle", "car", "van", "boat", "kayak")
    found: list[str] = []
    for ent in ents:
        for f in active_facts:
            if f.kind == "possession" and f.entity == ent and f.property in ("model", "attribute"):
                found.append(f"a {f.value} ({ent})")
                break
        else:
            vals = lineage_values(history, kind="possession", property="model", entity=ent)
            if vals:
                found.append(f"a {vals[-1]} ({ent})")
    if not found:
        return UNKNOWN
    if len(found) == 1:
        return f"You own {found[0]}."
    return "You own " + ", ".join(found[:-1]) + f", and {found[-1]}."
