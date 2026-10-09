"""Follow-up edits to timers and alarms — update in place, never duplicate.

"Set a timer for 10 minutes" … "actually make it 15" changes *that* timer.
If it has already finished, or ARIA cannot tell which one was meant, the
reply says so (or asks) instead of quietly starting a second one.
"""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _fmt(seconds: int) -> str:
    m, s = divmod(max(0, int(seconds)), 60)
    h, m = divmod(m, 60)
    return (f"{h}h " if h else "") + (f"{m}m " if m or h else "") + f"{s}s"


def _ask(assistant, question: str, choices: list[dict], message: str) -> dict:
    session = getattr(assistant, "session", None)
    if session is not None:
        session.pending_clarification = {
            "type": "action_choice", "action": "clarify", "original_prompt": message,
            "choices": [c["label"] for c in choices], "choice_intents": [c["intent"] for c in choices],
            "clarification_question": question,
        }
    lines = [question, ""] + [f"{i}. {c['label']}" for i, c in enumerate(choices, 1)]
    return ok("\n".join(lines), module="planner", type="clarification", choices=[c["label"] for c in choices])


@register_action("planner_update_timer", module="planner", description="Change an existing timer's length")
def planner_update_timer(assistant, params: dict, message: str) -> dict:
    from jarvis import planner_store

    planner_store._init_db()
    duration = str(params.get("duration") or "").strip()
    if not duration:
        return err("How long should the timer be?", module="planner")
    timer_id = str(params.get("timer_id") or "")
    previous = str(params.get("previous_label") or "").strip().lower()
    active = planner_store.active_timers()
    if timer_id:
        matches = [t for t in active if t["id"] == timer_id]
    else:
        matches = [t for t in active if previous and t["label"].strip().lower() == previous] or (
            active if len(active) == 1 else [])
    if not matches and not active:
        return ok(f"That timer has already finished or was cancelled, so there's nothing to change — and I didn't "
                  f"start a second one. Say \"set a {duration} timer\" if you want a new one.", module="planner",
                  type="planner")
    if len(matches) != 1:
        pool = matches or active
        return _ask(assistant, f"Which timer should become {duration}?", [
            {"label": f"{t['label'] or 'timer'} ({_fmt(t['remaining_seconds'])} left)",
             "intent": {"action": "planner_update_timer", "params": {"timer_id": t["id"], "duration": duration}}}
            for t in pool[:6]], message)
    t = matches[0]
    relabel = None
    if t["label"].strip().lower() == previous and previous and any(ch.isdigit() for ch in previous):
        relabel = duration  # default label was the old duration
    try:
        updated = planner_store.update_timer(t["id"], duration=duration, label=relabel)
    except ValueError as exc:
        return err(str(exc), module="planner")
    return ok(f"Changed your **{t['label'] or 'timer'}** timer to {duration}, counting from now "
              f"(it had {_fmt(t['remaining_seconds'])} left). No second timer was started.",
              module="planner", type="planner", timer=updated)


@register_action("planner_update_alarm", module="planner", description="Move an existing alarm to a new time")
def planner_update_alarm(assistant, params: dict, message: str) -> dict:
    from jarvis import planner_store

    planner_store._init_db()
    time_str = str(params.get("time") or "").strip()
    if not time_str:
        return err("What time should the alarm be?", module="planner")
    alarm_id = str(params.get("alarm_id") or "")
    previous = str(params.get("previous_label") or "").strip().lower()
    alarms = planner_store.list_alarms()
    if alarm_id:
        matches = [a for a in alarms if a["id"] == alarm_id]
    else:
        matches = [a for a in alarms if previous and a["label"].strip().lower() == previous] or (
            alarms if len(alarms) == 1 else [])
    if not alarms:
        return ok("That alarm has already gone off or was removed, so there's nothing to move — and I didn't set "
                  f"another one. Say \"set an alarm for {time_str}\" if you want a new one.", module="planner",
                  type="planner")
    if len(matches) != 1:
        return _ask(assistant, f"Which alarm should move to {time_str}?", [
            {"label": f"{a['label']} ({a['fire_at'][11:16]})",
             "intent": {"action": "planner_update_alarm", "params": {"alarm_id": a["id"], "time": time_str}}}
            for a in (matches or alarms)[:6]], message)
    a = matches[0]
    relabel = f"Alarm {time_str}" if a["label"].lower().startswith("alarm ") else None
    try:
        updated = planner_store.update_alarm(a["id"], time_str=time_str, label=relabel)
    except ValueError as exc:
        return err(str(exc), module="planner")
    return ok(f"Moved **{a['label']}** to {updated['fire_at'][11:16]}. No second alarm was set.", module="planner",
              type="planner", alarm=updated)


@register_action("planner_cancel_timer", module="planner", description="Cancel a running timer")
def planner_cancel_timer(assistant, params: dict, message: str) -> dict:
    from jarvis import planner_store

    planner_store._init_db()
    out = planner_store.cancel_timer(str(params.get("timer_id") or ""))
    if not out.get("ok"):
        return err(out.get("message") or "Timer not found", module="planner")
    return ok(f"Cancelled the **{(out.get('timer') or {}).get('label') or 'timer'}** timer.", module="planner")


@register_action("planner_cancel_alarm", module="planner", description="Cancel an alarm")
def planner_cancel_alarm(assistant, params: dict, message: str) -> dict:
    from jarvis import planner_store

    planner_store._init_db()
    out = planner_store.cancel_alarm(str(params.get("alarm_id") or ""))
    if not out.get("ok"):
        return err(out.get("message") or "Alarm not found", module="planner")
    return ok(f"Cancelled **{(out.get('alarm') or {}).get('label') or 'the alarm'}**.", module="planner")
