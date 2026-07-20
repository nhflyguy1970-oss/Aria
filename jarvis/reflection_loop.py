"""Nightly reflection — distill today's activity into strategy updates."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from typing import Any

log = logging.getLogger("jarvis.reflection")

STRATEGIES_NAMESPACE = "strategies"
REFLECTION_TAG = "reflection"


def reflection_enabled() -> bool:
    if os.getenv("JARVIS_REFLECTION_DAILY", "1") == "0":
        return False
    from jarvis.world_state import jarvis_preset_enabled

    if jarvis_preset_enabled():
        return True
    return os.getenv("JARVIS_BRAIN_MODE", "").strip().lower() in ("1", "true", "yes")


def reflection_hour() -> int:
    try:
        return int(os.getenv("JARVIS_REFLECTION_HOUR", "22"))
    except ValueError:
        return 22


def reflection_status() -> dict[str, Any]:
    from jarvis.config import _load_chat_settings

    state = _load_chat_settings().get("reflection_loop") or {}
    return {
        "enabled": reflection_enabled(),
        "hour": reflection_hour(),
        "last_run_day": state.get("last_run_day") or "",
        "last_strategies": int(state.get("last_strategies") or 0),
    }


def _mark_run(day: str, count: int) -> None:
    from jarvis.config import _load_chat_settings, _write_chat_settings

    data = _load_chat_settings()
    data.setdefault("reflection_loop", {})["last_run_day"] = day
    data["reflection_loop"]["last_strategies"] = count
    _write_chat_settings(data)


def _gather_context(*, memory_store, journal, day: str) -> str:
    lines: list[str] = [f"Date: {day}"]

    try:
        from jarvis.experience_memory import EXPERIENCE_NAMESPACE

        for outcome in ("success", "failure"):
            rows = memory_store.list_entries(
                entry_type=outcome,
                namespace=EXPERIENCE_NAMESPACE,
            )
            today_rows = [r for r in rows if (r.get("timestamp") or "").startswith(day)]
            if today_rows:
                lines.append(f"\n{outcome.title()} experiences ({len(today_rows)}):")
                for r in today_rows[:8]:
                    lines.append(f"- {(r.get('content') or '')[:200]}")
    except Exception:
        pass

    try:
        page = journal.daily_get(day)
        bullets = page.get("bullets") or []
        done = [b for b in bullets if b.get("type") == "task" and b.get("status") == "done"]
        if done:
            lines.append(f"\nJournal completions ({len(done)}):")
            for b in done[:8]:
                lines.append(f"- {b.get('content', '')[:120]}")
    except Exception:
        pass

    try:
        from jarvis.action_confidence import snapshot

        conf = snapshot().get("actions") or {}
        if conf:
            lines.append("\nAction confidence:")
            for k, v in list(conf.items())[:6]:
                lines.append(f"- {k}: {v.get('confidence', '?')} ({v.get('tier', '?')})")
    except Exception:
        pass

    return "\n".join(lines) if len(lines) > 1 else ""


def _generate_strategies(context: str) -> list[str]:
    if not context.strip():
        return []
    prompt = (
        "You are ARIA's nightly reflection module. From today's activity, propose 1–3 short "
        "strategy rules Jeff should follow tomorrow. Each rule is one sentence, actionable, "
        "no markdown bullets. Address Jeff by name sparingly.\n\n"
        f"{context}\n\n"
        "Reply with one rule per line, no numbering."
    )
    try:
        from jarvis import llm
        from jarvis.capability_routing import apply_gateway_model

        model = apply_gateway_model(llm.reflection_model(), "reflection")
        raw = llm.ask_with_system(
            model,
            "You output concise strategy rules only.",
            prompt,
            role="reflection",
            options={"num_predict": 280},
        )
        rules = [ln.strip().lstrip("-• ").strip() for ln in (raw or "").splitlines() if ln.strip()]
        return [r for r in rules if len(r) > 10][:3]
    except Exception as exc:
        log.debug("Reflection LLM skipped: %s", exc)
        return []


def _store_strategies(memory_store, rules: list[str]) -> int:
    stored = 0
    for rule in rules:
        try:
            existing = memory_store.list_entries(entry_type="strategy", namespace=STRATEGIES_NAMESPACE)
            if any((e.get("content") or "").lower() == rule.lower() for e in existing):
                continue
            memory_store.add(
                "strategy",
                rule,
                tags=["trust", REFLECTION_TAG, "auto"],
                namespace=STRATEGIES_NAMESPACE,
            )
            stored += 1
        except Exception as exc:
            log.debug("Strategy store failed: %s", exc)
    return stored


def run_reflection(*, memory_store=None, journal=None, day: str | None = None, force: bool = False) -> dict[str, Any]:
    """Run reflection for a day; skip if already done unless force."""
    if not reflection_enabled() and not force:
        return {"ok": False, "skipped": True, "reason": "disabled"}

    if memory_store is None or journal is None:
        try:
            from jarvis.assistant_instance import get_assistant

            assistant = get_assistant()
            memory_store = memory_store or assistant.memory
            journal = journal or assistant.journal
        except Exception:
            return {"ok": False, "skipped": True, "reason": "no assistant"}

    d = day or date.today().isoformat()
    from jarvis.config import _load_chat_settings

    last = (_load_chat_settings().get("reflection_loop") or {}).get("last_run_day")
    if not force and last == d:
        return {"ok": True, "skipped": True, "reason": "already ran", "day": d}

    context = _gather_context(memory_store=memory_store, journal=journal, day=d)
    if not context:
        _mark_run(d, 0)
        return {"ok": True, "skipped": True, "reason": "no activity", "day": d}

    rules = _generate_strategies(context)
    count = _store_strategies(memory_store, rules)
    _mark_run(d, count)
    if count:
        try:
            from jarvis.assistant_instance import get_assistant

            get_assistant().refresh_system_prompt()
        except Exception:
            pass
    log.info("Reflection loop: stored %s strategies for %s", count, d)
    return {"ok": True, "day": d, "strategies": count, "rules": rules}


def run_scheduled(now: datetime | None = None) -> dict[str, Any] | None:
    """Called from proactive scheduler at configured hour."""
    if not reflection_enabled():
        return None
    now = now or datetime.now()
    if now.hour != reflection_hour() or now.minute > 10:
        return None
    return run_reflection()
