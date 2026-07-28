"""Cognitive Memory services — ACM-aligned Home, forget, adopt, briefing.

Candidates live in a staging queue (not autobiographical SoT).
ACM PRIMARY remains the only cognitive authority.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.memory.services")

CANDIDATES_FILE = DATA_DIR / "memory_candidates.json"
USER_FACING_TYPES = frozenset({"fact", "preference", "project", "note", "auto"})
INTERNAL_TYPES = frozenset({"strategy", "failure", "success", "teaching"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clip(text: str, n: int = 160) -> str:
    t = (text or "").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


# --- Candidates (staging queue — NOT source of truth) ---


def _load_candidates() -> list[dict[str, Any]]:
    if not CANDIDATES_FILE.exists():
        return []
    try:
        data = json.loads(CANDIDATES_FILE.read_text(encoding="utf-8"))
        return list(data.get("candidates") or []) if isinstance(data, dict) else []
    except Exception:
        log.debug("candidates load failed", exc_info=True)
        return []


def _save_candidates(items: list[dict[str, Any]]) -> None:
    CANDIDATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(CANDIDATES_FILE)
    CANDIDATES_FILE.write_text(
        json.dumps({"version": 1, "candidates": items[-500:]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def propose_candidate(
    content: str,
    *,
    source: str = "chat",
    entry_type: str = "fact",
    namespace: str = "default",
    tags: list[str] | None = None,
    evidence: str = "",
    confidence: float = 0.5,
) -> dict[str, Any]:
    """Stage a memory candidate for user review. Does not encode into ACM."""
    text = (content or "").strip()
    if not text:
        raise ValueError("Empty candidate")
    items = _load_candidates()
    # Dedup pending by content+source
    for c in items:
        if c.get("status") == "pending" and (c.get("content") or "").strip() == text:
            return {"ok": True, "candidate": c, "duplicate": True}
    cand = {
        "id": uuid.uuid4().hex[:12],
        "content": text,
        "type": entry_type if entry_type in USER_FACING_TYPES else "fact",
        "namespace": namespace or "default",
        "tags": list(tags or []),
        "source": source,
        "evidence": (evidence or "").strip(),
        "confidence": max(0.0, min(1.0, float(confidence))),
        "status": "pending",
        "created": _now(),
        "requires_confirmation": True,
    }
    items.append(cand)
    _save_candidates(items)
    return {"ok": True, "candidate": cand, "duplicate": False}


def list_candidates(*, status: str = "pending") -> dict[str, Any]:
    items = _load_candidates()
    if status:
        items = [c for c in items if c.get("status") == status]
    return {"ok": True, "candidates": items, "count": len(items)}


def dismiss_candidate(candidate_id: str) -> dict[str, Any]:
    items = _load_candidates()
    found = False
    for c in items:
        if c.get("id") == candidate_id:
            c["status"] = "dismissed"
            c["updated"] = _now()
            found = True
            break
    if not found:
        return {"ok": False, "error": "candidate not found"}
    _save_candidates(items)
    return {"ok": True}


def adopt_candidate(memory_store, candidate_id: str) -> dict[str, Any]:
    """User adopts a candidate → encode into ACM via store.add (PRIMARY redirect)."""
    items = _load_candidates()
    cand = next((c for c in items if c.get("id") == candidate_id), None)
    if not cand:
        return {"ok": False, "error": "candidate not found"}
    if cand.get("status") != "pending":
        return {"ok": False, "error": f"candidate is {cand.get('status')}"}
    tags = list(cand.get("tags") or [])
    tags.append("adopted")
    tags.append(f"source:{cand.get('source') or 'unknown'}")
    entry = memory_store.add(
        cand.get("type") or "fact",
        cand["content"],
        tags=tags,
        namespace=cand.get("namespace") or "default",
    )
    cand["status"] = "adopted"
    cand["adopted"] = _now()
    cand["memory_id"] = getattr(entry, "get", lambda k, d=None: entry[k] if isinstance(entry, dict) else d)(
        "id"
    ) if isinstance(entry, dict) else getattr(entry, "id", None)
    if isinstance(entry, dict):
        cand["memory_id"] = entry.get("id")
    _save_candidates(items)
    mirror: dict[str, Any] = {"ok": True, "mirrored": 0}
    try:
        from jarvis.connections_services import mirror_adopted_memory

        mid = str(cand.get("memory_id") or "")
        mirror = mirror_adopted_memory(cand, memory_id=mid)
    except Exception as exc:
        mirror = {"ok": False, "error": str(exc), "mirrored": 0}
    return {
        "ok": True,
        "candidate": cand,
        "entry": memory_store.to_public(entry) if hasattr(memory_store, "to_public") else entry,
        "message": "Adopted into autobiographical memory (ACM).",
        "connections_mirror": mirror,
    }


# --- Forget / Correct ---


def forget_preview(memory_store, entry_id: str) -> dict[str, Any]:
    entry = memory_store.get(entry_id) if hasattr(memory_store, "get") else None
    if not entry:
        # try list scan
        for e in memory_store.list_entries() or []:
            if str(e.get("id")) == str(entry_id):
                entry = e
                break
    if not entry:
        return {"ok": False, "error": "Memory not found"}
    content = entry.get("content") or ""
    related = []
    try:
        hits = memory_store.search(content[:80], limit=6) if hasattr(memory_store, "search") else []
        for h in hits:
            if str(h.get("id")) == str(entry_id):
                continue
            related.append(
                {
                    "id": h.get("id"),
                    "content": _clip(h.get("content") or ""),
                    "type": h.get("type"),
                    "namespace": h.get("namespace"),
                }
            )
    except Exception:
        pass
    return {
        "ok": True,
        "entry": entry if isinstance(entry, dict) else {"id": entry_id, "content": str(entry)},
        "related": related[:5],
        "actions": [
            {
                "id": "cool",
                "label": "Cool (soft forget)",
                "explanation": "Reduce accessibility — Aria stops offering this, but the experience remains for lineage. Preferred ACM forget.",
                "reversible": True,
            },
            {
                "id": "correct",
                "label": "Correct",
                "explanation": "Revise this belief with new text. Old version stays in lineage; new version becomes active.",
                "reversible": False,
                "needs_text": True,
            },
            {
                "id": "erase",
                "label": "Erase (strong cool)",
                "explanation": "Strongly deactivate this memory. Experiences are not hard-deleted; accessibility drops further. Use for junk or sensitive mistakes.",
                "reversible": False,
            },
        ],
        "requires_confirmation": True,
        "message": "Forgetting changes what Aria believes. Confirm carefully.",
    }


def forget_execute(
    memory_store,
    entry_id: str,
    *,
    action: str,
    confirm: bool = False,
    correction_text: str = "",
) -> dict[str, Any]:
    if not confirm:
        return {"ok": False, "error": "Confirmation required", "requires_confirmation": True}
    action = (action or "").lower().strip()
    if action not in ("cool", "correct", "erase"):
        return {"ok": False, "error": "action must be cool|correct|erase"}

    try:
        from aria_core import acm_bridge
        from aria_core.acm_bridge import acm_is_authoritative
    except Exception:
        acm_bridge = None
        acm_is_authoritative = lambda: False  # type: ignore

    if action == "correct":
        text = (correction_text or "").strip()
        if not text:
            return {"ok": False, "error": "correction_text required"}
        if acm_bridge and acm_is_authoritative():
            out = acm_bridge.primary_correct(experience_id=entry_id, text=text)
            return {
                "ok": bool(out.get("ok")),
                "action": "correct",
                "result": out,
                "message": "Belief corrected with lineage (revise).",
            }
        ok = memory_store.update(entry_id, content=text)
        return {"ok": bool(ok), "action": "correct", "message": "Updated (legacy path)."}

    if acm_bridge and acm_is_authoritative():
        steps = 3 if action == "erase" else 1
        # Extend cool via engine when steps > 1
        if steps > 1:
            try:
                with acm_bridge.engine_exclusive() as engine:
                    concept_id = entry_id
                    if entry_id in engine.store.experiences:
                        exp = engine.store.experiences[entry_id]
                        concept_id = exp.concept_ids[0] if exp.concept_ids else entry_id
                    out = engine.cool_memory(str(concept_id), steps=steps)
                return {
                    "ok": bool(out.get("cooled")),
                    "action": action,
                    "cooled": True,
                    "steps": steps,
                    "message": "Strong cool applied — memory deactivated.",
                }
            except Exception as exc:
                log.exception("strong cool failed")
                return {"ok": False, "error": str(exc)}
        out = acm_bridge.primary_forget(entry_id=entry_id)
        return {
            "ok": bool(out.get("ok") or out.get("cooled")),
            "action": "cool",
            "result": out,
            "message": "Soft-forgotten (cooled). Experiences unchanged.",
        }

    # Legacy rollback path
    ok = memory_store.delete_id(entry_id) if hasattr(memory_store, "delete_id") else False
    return {"ok": bool(ok), "action": action, "message": "Removed (legacy path)."}


# --- Cognitive Home ---


def build_memory_home(memory_store, assistant=None) -> dict[str, Any]:
    """Cognitive Memory Home payload — projections only; ACM remains SoT."""
    about: list[dict[str, Any]] = []
    beliefs: list[dict[str, Any]] = []
    recent: list[dict[str, Any]] = []
    try:
        profile = memory_store.list_entries(namespace="profile") or []
        about = [
            _public_card(e)
            for e in profile
            if "summary" not in (e.get("tags") or [])
        ][:20]
    except Exception:
        log.debug("profile load failed", exc_info=True)

    try:
        all_entries = memory_store.list_entries() or []
        facing = [
            e
            for e in all_entries
            if (e.get("type") or "fact") in USER_FACING_TYPES
            and (e.get("namespace") or "") != "cheatsheet"
        ]
        # Prefer preference + fact for beliefs
        beliefs = [
            _public_card(e)
            for e in facing
            if (e.get("type") in ("preference", "fact") or e.get("namespace") == "profile")
        ][:24]
        # Recent by timestamp if present
        dated = sorted(
            facing,
            key=lambda e: e.get("timestamp") or e.get("created") or e.get("updated") or "",
            reverse=True,
        )
        recent = [_public_card(e) for e in dated[:12]]
    except Exception:
        log.debug("entries load failed", exc_info=True)

    conflicts = []
    try:
        from jarvis.memory_context import find_conflicts

        conflicts = find_conflicts(memory_store) or []
    except Exception:
        pass

    candidates = list_candidates(status="pending")
    trust = {}
    try:
        from jarvis.trust_memory import trust_status

        trust = trust_status(memory_store)
    except Exception:
        pass

    authority = {"primary": False, "source_of_truth": "unknown"}
    sleep_summary = {"ok": True, "message": "No sleep summary yet.", "outcomes": []}
    acm_dash = {}
    try:
        from aria_core.acm_bridge import acm_dashboard, acm_is_authoritative, acm_metrics

        authority = {
            "primary": bool(acm_is_authoritative()),
            "source_of_truth": "acm" if acm_is_authoritative() else "legacy_rollback",
            "metrics": acm_metrics() if acm_is_authoritative() else {},
        }
        if acm_is_authoritative():
            acm_dash = acm_dashboard(limit=30) or {}
            sleep_summary = _sleep_surface(acm_dash)
    except Exception:
        pass

    stats = {}
    try:
        stats = memory_store.stats() or {}
    except Exception:
        pass

    namespaces = list(stats.get("namespaces") or [])
    # Hide cheatsheet from primary namespace chips optionally still list it under safety

    return {
        "ok": True,
        "philosophy": {
            "title": "Autobiographical cognition",
            "body": "Memory is what Aria knows about you — encoded experiences, beliefs, and corrections — not a note database.",
        },
        "about_you": about,
        "beliefs": beliefs,
        "what_changed": {
            "recent": recent,
            "candidates_pending": candidates.get("count") or 0,
        },
        "recent_learning": {
            "candidates": (candidates.get("candidates") or [])[:20],
            "sources": ["journal", "documents", "chat", "coding", "voice", "vision"],
        },
        "conflicts": conflicts[:10],
        "health": {
            "total_facing": stats.get("total"),
            "by_type": {
                k: v
                for k, v in (stats.get("by_type") or {}).items()
                if k in USER_FACING_TYPES
            },
            "candidates_pending": candidates.get("count") or 0,
            "conflicts": len(conflicts),
            "trust": trust,
            "duplicates_hint": "Review candidates and conflicts regularly.",
        },
        "safety": {
            **authority,
            "fail_closed": True,
            "candidates_are_not_memory": True,
            "legacy_vault_forensic_only": True,
            "backup_hint": "Use Export for a portable snapshot. ACM PRIMARY remains authority.",
        },
        "sleep": sleep_summary,
        "namespaces": [n for n in namespaces if n != "cheatsheet"][:30],
        "projects": [n for n in namespaces if n not in ("default", "profile", "cheatsheet", "experience")][
            :20
        ],
    }


def _public_card(e: dict[str, Any]) -> dict[str, Any]:
    tags = e.get("tags") or []
    source = "profile" if e.get("namespace") == "profile" else "memory"
    for t in tags:
        if str(t).startswith("source:"):
            source = str(t).split(":", 1)[1]
            break
    return {
        "id": e.get("id"),
        "title": _clip(e.get("content") or "", 72),
        "content": e.get("content"),
        "type": e.get("type") or "fact",
        "namespace": e.get("namespace") or "default",
        "tags": [t for t in tags if t not in INTERNAL_TYPES],
        "confidence": e.get("confidence") or e.get("relevance") or 0.7,
        "source": source,
        "why": _why_remembered(e, source),
        "when_learned": e.get("timestamp") or e.get("created"),
        "last_recalled": e.get("last_access") or e.get("updated"),
        "provenance": {
            "source": source,
            "namespace": e.get("namespace"),
            "tags": tags[:8],
            "acm": e.get("source") == "acm" or True,
        },
    }


def _why_remembered(e: dict[str, Any], source: str) -> str:
    ns = e.get("namespace") or ""
    if ns == "profile":
        return "From your profile questionnaire — identity personalization."
    if "checkpoint" in (e.get("tags") or []):
        return "Project checkpoint — where you left off."
    if "adopted" in (e.get("tags") or []):
        return f"You adopted this from {source}."
    if e.get("type") == "preference":
        return "Recorded as a preference."
    if e.get("type") == "auto":
        return "Auto-extracted candidate that was encoded — prefer reviewing new autos as candidates."
    return f"Encoded from {source}."


def _sleep_surface(acm_dash: dict[str, Any]) -> dict[str, Any]:
    """Plain-language Sleep / consolidation outcomes — no internals."""
    outcomes = []
    recent = acm_dash.get("recent") or acm_dash.get("recent_events") or []
    if isinstance(recent, list):
        for ev in recent[:8]:
            if not isinstance(ev, dict):
                continue
            verb = str(ev.get("verb") or ev.get("acm_verb") or ev.get("op") or "")
            if verb in ("cool", "primary_cool", "sleep", "consolidate", "revise", "encode"):
                outcomes.append(
                    {
                        "plain": {
                            "cool": "Something became quieter (soft-forgotten).",
                            "primary_cool": "Something became quieter (soft-forgotten).",
                            "sleep": "Overnight reorganization ran.",
                            "consolidate": "Related experiences were strengthened together.",
                            "revise": "A belief was corrected with lineage.",
                            "encode": "Something new was learned.",
                        }.get(verb, "Memory activity."),
                        "when": ev.get("ts") or ev.get("time"),
                    }
                )
    metrics = acm_dash.get("metrics") or {}
    if not outcomes and metrics:
        outcomes.append(
            {
                "plain": "ACM is authoritative. Sleep consolidates patterns over time — nothing is rewritten silently into identity.",
                "when": None,
            }
        )
    return {
        "ok": True,
        "message": "Sleep reorganizes memory; it does not invent facts.",
        "outcomes": outcomes[:10],
        "metrics_hint": {
            "encodes": metrics.get("primary_encode") or metrics.get("encode"),
            "cools": metrics.get("primary_cool"),
            "revises": metrics.get("primary_revise"),
        },
    }


# --- Assist / briefing / conflicts ---


def memory_assistant(memory_store) -> dict[str, Any]:
    suggestions: list[dict[str, Any]] = []
    cands = list_candidates(status="pending")
    n = cands.get("count") or 0
    if n:
        suggestions.append(
            {
                "kind": "candidates",
                "title": f"{n} memory candidate(s) awaiting review",
                "action": "review_candidates",
                "requires_confirmation": True,
            }
        )
    try:
        from jarvis.memory_context import find_conflicts

        conflicts = find_conflicts(memory_store) or []
        if conflicts:
            suggestions.append(
                {
                    "kind": "conflicts",
                    "title": f"{len(conflicts)} belief conflict(s)",
                    "action": "review_conflicts",
                    "requires_confirmation": True,
                }
            )
    except Exception:
        pass
    # Low-signal autos
    try:
        autos = [
            e
            for e in (memory_store.list_entries(type="auto") or [])
            if (e.get("namespace") or "") != "cheatsheet"
        ]
        if len(autos) > 15:
            suggestions.append(
                {
                    "kind": "stale_auto",
                    "title": f"{len(autos)} auto memories — consider prune or cool",
                    "action": "prune_review",
                    "requires_confirmation": True,
                }
            )
    except Exception:
        pass
    return {
        "ok": True,
        "suggestions": suggestions,
        "requires_confirmation": True,
        "message": "Suggestions only — nothing was modified.",
    }


def memory_briefing(memory_store, *, days: int = 7) -> dict[str, Any]:
    """User-initiated weekly-style briefing."""
    home = build_memory_home(memory_store)
    lines = [
        "## Memory briefing",
        "",
        f"- Pending candidates: {home['health']['candidates_pending']}",
        f"- Conflicts: {home['health']['conflicts']}",
        f"- Authority: {home['safety'].get('source_of_truth')}",
        "",
        "### Recent beliefs",
    ]
    for b in (home.get("what_changed") or {}).get("recent") or []:
        lines.append(f"- {b.get('title')}")
    lines.extend(["", "### Sleep", home.get("sleep", {}).get("message", "")])
    for o in (home.get("sleep") or {}).get("outcomes") or []:
        lines.append(f"- {o.get('plain')}")
    return {
        "ok": True,
        "briefing": "\n".join(lines),
        "requires_confirmation": False,
        "message": "Generated on request — memory unchanged.",
    }


def conflict_coach(memory_store, conflict: dict[str, Any] | None = None) -> dict[str, Any]:
    conflicts = []
    try:
        from jarvis.memory_context import find_conflicts

        conflicts = find_conflicts(memory_store) or []
    except Exception:
        pass
    if conflict:
        conflicts = [conflict]
    explained = []
    for c in conflicts[:8]:
        a = c.get("a") or c.get("keep") or {}
        b = c.get("b") or c.get("drop") or {}
        if not isinstance(a, dict):
            a = {"content": str(a)}
        if not isinstance(b, dict):
            b = {"content": str(b)}
        explained.append(
            {
                "a": {"id": a.get("id"), "content": _clip(a.get("content") or ""), "provenance": a.get("namespace")},
                "b": {"id": b.get("id"), "content": _clip(b.get("content") or ""), "provenance": b.get("namespace")},
                "why": c.get("reason")
                or "Both look like beliefs about the same topic with different content.",
                "recommendation": "Keep the one you still believe, or Correct with a merged statement. Prefer Cool over hard delete.",
                "actions": ["keep_a", "keep_b", "merge", "correct"],
                "requires_confirmation": True,
            }
        )
    return {"ok": True, "conflicts": explained, "requires_confirmation": True}


def associative_recall(memory_store, query: str, *, limit: int = 8) -> dict[str, Any]:
    q = (query or "").strip()
    related = []
    if q and hasattr(memory_store, "search"):
        for h in (memory_store.search(q, limit=limit) or [])[:limit]:
            related.append(_public_card(h))
    # Optional Connections (Knowledge Graph) — never silent about failure mode
    kg_error = ""
    try:
        from jarvis import knowledge_graph as kg

        if q and hasattr(kg, "search"):
            for e in (kg.search(q, limit=5) or [])[:5]:
                related.append(
                    {
                        "id": e.get("id") or e.get("name"),
                        "title": _clip(str(e.get("name") or e.get("label") or e)),
                        "type": "entity",
                        "source": "connections",
                        "why": "Connections link — not autobiographical Memory.",
                    }
                )
    except Exception as exc:
        kg_error = str(exc)
    out: dict[str, Any] = {
        "ok": True,
        "query": q,
        "related": related,
        "message": "Associative surface for review — not a dump of all memories.",
    }
    if kg_error:
        out["connections_error"] = kg_error
    return out


def filter_user_facing(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        e
        for e in entries
        if (e.get("type") or "fact") in USER_FACING_TYPES
        and (e.get("namespace") or "") != "cheatsheet"
    ]
