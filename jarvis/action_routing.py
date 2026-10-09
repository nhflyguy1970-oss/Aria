"""Action routing repair (Phase 5).

The structural NLU stage answers ``chat`` (or, through orchestration policy,
``web_search``) for many plain commands — "Wake me at 5:30", "12-minute
timer" — and nothing after it got a chance. This module adds four layers,
each with a routing receipt on the intent it returns:

1. **Follow-ups** bound to the previous turn's action ("actually make it 15"
   after a timer, "and on Sunday?" after a forecast). Only the immediately
   previous action, and only for a few minutes.
2. **Deictic clarification** — "delete it", "turn it off" with nothing in
   the conversation for "it" to mean: ask, never guess.
3. **Rules** — high-precision patterns with argument extraction for requests
   that are unambiguous (timers, alarms, tasks, missions, …). Deterministic,
   no model.
4. **Shortlist + small model** — when NLU fell back to chat, rank actions by
   BM25 over registry metadata, curated aliases and the router training
   samples, and let the router-role model pick among the top few (plus chat
   and clarify). A side-effecting choice from the model is never executed
   directly: it becomes a yes/no confirmation.

The model never sees all ~444 actions; nothing here executes anything —
permission and safe-mode checks stay where they are, at execution.
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from typing import Any

FOLLOW_UP_TTL_S = 15 * 60
SHORTLIST_K = 6
MIN_SHORTLIST_SCORE = 4.0

# ---------------------------------------------------------------- helpers

_POLITE = re.compile(
    r"^(?:(?:hey|ok|okay)\s+)?(?:aria|jarvis)[,:]?\s+|"
    r"^(?:please|kindly)\s+|"
    r"^(?:can|could|would|will)\s+you\s+(?:please\s+)?|"
    r"^i\s+(?:want|need)\s+you\s+to\s+",
    re.I,
)

_CONCEPTUAL = re.compile(
    r"^(?:what\s+(?:is|are|was|were|does|do)\s+(?:a|an|the)?\b|"
    r"what's\s+(?:a|an|the\s+difference)\b|"
    r"how\s+(?:do|does|can|would|is|are|did)\b|why\b|who\b|when\s+(?:was|did)\b|"
    r"explain\b|can\s+you\s+explain\b|tell\s+me\s+about\b|define\b|"
    r"is\s+there\b|are\s+there\b|is\s+it\s+possible\b)",
    re.I,
)
_PERSONAL = re.compile(r"\b(?:my|mine|our|ours|i)\b", re.I)


def clean(message: str) -> str:
    text = (message or "").strip()
    for _ in range(3):
        stripped = _POLITE.sub("", text, count=1)
        if stripped == text:
            break
        text = stripped
    return text.strip().rstrip(".!").strip()


def is_conceptual_question(message: str) -> bool:
    """'What is inpainting?' — about a topic, not a request to act."""
    text = (message or "").strip()
    return bool(_CONCEPTUAL.match(text)) and not _PERSONAL.search(text)


def _receipt(method: str, **extra: Any) -> dict[str, Any]:
    return {"method": method, **{k: v for k, v in extra.items() if v not in (None, "", [], {})}}


def _intent(action: str, params: dict | None, method: str, stage: str, **receipt: Any) -> dict:
    return {
        "action": action,
        "params": dict(params or {}),
        "thinking": f"action routing: {method}",
        "route_reason": method,
        "route_handler": "ActionRouting",
        "route_confidence": 1.0 if method.startswith(("rule", "follow_up")) else 0.7,
        "router": "action_routing",
        "router_stage": stage,
        "routing_receipt": _receipt(method, **receipt),
    }


def clarification(question: str, method: str, stage: str, *, choices: list[dict] | None = None,
                  ctype: str = "action_clarify", **receipt: Any) -> dict:
    """A question back to the user. ``choices`` are ``{"label", "intent"}``."""
    choices = choices or []
    intent = _intent("clarify", {}, method, stage, **receipt)
    intent.update({
        "needs_clarification": True,
        "clarification_question": question,
        "clarification_type": ctype,
        "choices": [c["label"] for c in choices],
        "choice_intents": [c["intent"] for c in choices],
    })
    return intent


# ---------------------------------------------------------------- arguments

_UNITS = r"(?:seconds?|secs?|minutes?|mins?|hours?|hrs?)"
_WORD_NUM = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "forty-five": 45,
    "fifty": 50, "sixty": 60, "ninety": 90,
}
_DURATION = re.compile(
    rf"\b(?P<n>\d+|{'|'.join(sorted(_WORD_NUM, key=len, reverse=True))})\s*-?\s*(?P<unit>{_UNITS})\b",
    re.I,
)
_CLOCK = re.compile(r"\b(?P<t>\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)?)(?![\d:])", re.I)


def _unit(word: str) -> str:
    w = word.lower()
    if w.startswith(("h",)):
        return "hours"
    if w.startswith("s"):
        return "seconds"
    return "minutes"


def extract_duration(text: str) -> str | None:
    """'12-minute' → '12 minutes'; 'half an hour' → '30 minutes'."""
    if re.search(r"\bhalf\s+an?\s+hour\b", text, re.I):
        return "30 minutes"
    m = _DURATION.search(text)
    if not m:
        return None
    n = m.group("n").lower()
    num = int(n) if n.isdigit() else _WORD_NUM.get(n)
    return f"{num} {_unit(m.group('unit'))}" if num else None


def extract_clock_time(text: str) -> str | None:
    """'at 5:30 tomorrow' → '5:30'; '4:45 am' → '4:45am'; '6am' → '6am'."""
    candidates = []
    for m in _CLOCK.finditer(text):
        t = re.sub(r"\s+", "", m.group("t").lower()).replace(".", "")
        if ":" in t or t.endswith(("am", "pm")):
            candidates.append(t)
        elif re.search(rf"\b(?:at|for)\s+{re.escape(m.group('t').strip())}\b", text, re.I):
            candidates.append(t)
    return candidates[0] if candidates else None


def _strip_quotes(text: str) -> str:
    return text.strip().strip("'\"“”‘’").strip()


_MISSION_ID = r"(?P<id>[0-9a-f]{6,32})"

# ---------------------------------------------------------------- rules


def _rule_timer(text: str, lower: str, _session) -> dict | None:
    m = re.match(rf"^remind\s+me\s+in\s+(?P<d>.+?{_UNITS})\b(?:\s+to\s+(?P<label>.+))?$", text, re.I)
    if m:
        duration = extract_duration(m.group("d"))
        if duration:
            params = {"duration": duration}
            if m.group("label"):
                params["label"] = m.group("label").strip()
            return _intent("planner_set_timer", params, "rule:reminder_in", "action_rules")
    if not re.search(r"\b(?:timer|countdown)\b", lower):
        return None
    if is_conceptual_question(text) or re.search(r"\b(?:cancel|stop|delete|clear|how long|left on)\b", lower):
        return None
    duration = extract_duration(text)
    if not duration:
        if re.match(r"^(?:set|start|give\s+me|make)\b", lower):
            return clarification("How long should the timer run?", "rule:timer_needs_duration", "action_rules")
        return None
    params: dict[str, str] = {"duration": duration}
    if m := re.search(r"\btimer\s+for\s+(?:my|the|a)\s+(.+)$", text, re.I) or re.search(
        r"\bfor\s+(?:my|the)\s+(.+)$", text, re.I
    ):
        label = m.group(1).strip()
        if not _DURATION.search(label):
            params["label"] = label
    return _intent("planner_set_timer", params, "rule:timer", "action_rules")


def _rule_alarm(text: str, lower: str, _session) -> dict | None:
    if not re.match(
        r"^(?:set\s+(?:an?\s+|my\s+|the\s+)?alarm|wake\s+me(?:\s+up)?\b|alarm\s+(?:for|at)\b|"
        r"(?:give\s+me|i\s+need)\s+an?\s+alarm\b)",
        lower,
    ):
        return None
    time_str = extract_clock_time(text)
    if not time_str:
        return clarification("What time should the alarm go off?", "rule:alarm_needs_time", "action_rules")
    params = {"time": time_str}
    if m := re.search(r"\bfor\s+(?:the|my)\s+(.+)$", text, re.I):
        params["label"] = m.group(1).strip()
    return _intent("planner_set_alarm", params, "rule:alarm", "action_rules")


_LIST_WORDS = r"(?:to-?do(?:\s+list)?|todo(?:\s+list)?|task\s+list|tasks|planner|list)"


def _rule_task(text: str, lower: str, _session) -> dict | None:
    m = re.match(
        rf"^(?:add|put|stick|write)\s+(?P<t>.+?)\s+(?:to|on|in|onto)\s+(?:my|the)\s+{_LIST_WORDS}\b",
        text,
        re.I,
    )
    if m and not re.match(r"^(?:it|that|this|them)$", m.group("t").strip(), re.I):
        return _intent("planner_add_task", {"text": _strip_quotes(m.group("t"))}, "rule:add_to_list", "action_rules")
    m = re.match(
        r"^(?:add|create|make)\s+(?:a\s+|another\s+)?(?:new\s+)?(?:planner\s+|to-?do\s+)?task"
        r"(?:\s+(?:to|on|in)\s+(?:my\s+)?(?:planner|list))?\s*[:\-]?\s*(?P<t>.*)$",
        text,
        re.I,
    )
    if m:
        task = re.sub(r"^(?:to|for)\s+", "", m.group("t").strip(), flags=re.I)
        task = _strip_quotes(task)
        if not task:
            return clarification("What's the task?", "rule:task_needs_text", "action_rules")
        return _intent("planner_add_task", {"text": task}, "rule:add_task", "action_rules")
    return None


def _rule_event(text: str, lower: str, _session) -> dict | None:
    m = re.match(
        r"^(?:put|add|schedule)\s+(?P<title>.+?)\s+(?:on|to|in)\s+(?:my|the)\s+calendar\b\s*(?P<when>.*)$",
        text,
        re.I,
    )
    if not m:
        return None
    params = {"title": _strip_quotes(m.group("title"))}
    if m.group("when").strip():
        params["when"] = m.group("when").strip()
    return _intent("planner_add_event", params, "rule:calendar_event", "action_rules")


def _rule_mission(text: str, lower: str, _session) -> dict | None:
    if m := re.match(rf"^(?:cancel|abort|kill|stop)\s+(?:the\s+)?mission\s+{_MISSION_ID}\b", lower):
        return _intent("mission_cancel", {"mission_id": m.group("id")}, "rule:mission_cancel", "action_rules")
    if m := re.match(rf"^(?:pause|suspend|hold)\s+(?:the\s+)?mission\s+{_MISSION_ID}\b", lower):
        return _intent("mission_pause", {"mission_id": m.group("id")}, "rule:mission_pause", "action_rules")
    if m := re.search(
        rf"\b(?:status\s+of|how(?:'s|\s+is)|check(?:\s+on)?)\s+(?:the\s+)?mission\s+{_MISSION_ID}\b|"
        rf"\bmission\s+{_MISSION_ID.replace('id', 'id2')}(?:'s)?\s+status\b",
        lower,
    ):
        return _intent(
            "mission_status", {"mission_id": m.group("id") or m.group("id2")}, "rule:mission_status", "action_rules"
        )
    if re.match(
        r"^(?:list|show)(?:\s+me)?(?:\s+(?:my|all|the))?(?:\s+(?:active|running|open|current))?\s+missions\b|"
        r"^what\s+missions\s+(?:are|do\s+i\s+have)\b",
        lower,
    ):
        return _intent("mission_list", {}, "rule:mission_list", "action_rules")
    return None


def _rule_media(text: str, lower: str, session) -> dict | None:
    if m := re.match(
        r"^(?:generate|make|create|write|compose)\s+(?:me\s+)?(?:a\s+)?(?:new\s+)?song\b\s*(?:about|of|for)?\s*[:\-]?\s*(?P<t>.*)$",
        text,
        re.I,
    ):
        topic = m.group("t").strip()
        if not topic:
            return clarification("What should the song be about?", "rule:song_needs_topic", "action_rules")
        return _intent("generate_song", {"topic": topic}, "rule:song", "action_rules")
    if re.match(r"^play\s+(?:some\s+|me\s+some\s+)?(?:music|a\s+song|something|tunes)\b", lower):
        if session is not None and getattr(session, "last_audio", ""):
            return _intent("play_audio", {"path": session.last_audio}, "rule:play_last_audio", "action_rules")
        return clarification(
            "What should I play? Name a file from your audio library, or ask me to generate a song.",
            "rule:play_needs_source",
            "action_rules",
        )
    if (m := re.match(r"^(?:draw|paint|sketch|illustrate)\s+(?:me\s+)?(?P<p>.+)$", text, re.I)) and not re.search(
        r"\b(?:conclusion|comparison|attention|line|parallel|distinction|blank)\b", lower
    ):
        return _intent("generate_image", {"prompt": m.group("p").strip()}, "rule:draw", "action_rules")
    if re.match(r"^in-?paint\b", lower) and not (session is not None and session.last_image):
        return clarification(
            "Which image should I inpaint? Generate one or pick it from the Gallery first.",
            "rule:inpaint_needs_image",
            "action_rules",
        )
    if re.match(r"^transcribe\b", lower):
        if session is not None and session.last_audio and re.search(r"\b(?:this|that|it|the)\b", lower):
            return _intent("transcribe", {"path": session.last_audio}, "rule:transcribe_last", "action_rules")
        if not re.search(r"[\w./-]+\.(?:wav|mp3|m4a|flac|ogg|opus|webm)\b", lower):
            return clarification(
                "Which recording? Attach it or give me the file path.", "rule:transcribe_needs_file", "action_rules"
            )
    return None


_PRONOUN_TARGET = r"(?:it|that|this|them|those|these|everything|all)"


def _rule_home(text: str, lower: str, _session) -> dict | None:
    m = re.match(r"^(?:turn|switch)\s+(?P<a>on|off)\s+(?:the\s+)?(?P<t>.+)$", text, re.I) or re.match(
        r"^(?:turn|switch)\s+(?:the\s+)?(?P<t>.+?)\s+(?P<a>on|off)$", text, re.I
    )
    if not m:
        return None
    target = m.group("t").strip()
    if re.fullmatch(_PRONOUN_TARGET, target, re.I):
        return None
    return _intent("ha_control", {"action": m.group("a").lower(), "target": target}, "rule:home_switch", "action_rules")


def _rule_runtime(text: str, lower: str, _session) -> dict | None:
    if re.search(r"\bcpu\b", lower) and re.search(r"\b(?:load|usage|use|utili[sz]ation|busy|percent|hot|doing)\b", lower):
        return _intent("runtime_cpu", {}, "rule:cpu", "action_rules")
    if re.search(r"\bram\b", lower) and re.search(r"\b(?:free|used|usage|available|left|much)\b", lower):
        return _intent("runtime_ram", {}, "rule:ram", "action_rules")
    return None


def _rule_documents(text: str, lower: str, _session) -> dict | None:
    m = re.match(r"^search\s+(?:my|the)\s+(?:documents|docs|document\s+library|library)\s+for\s+(?P<q>.+)$", text, re.I)
    if m:
        return _intent("document_search", {"query": m.group("q").strip()}, "rule:document_search", "action_rules")
    return None


_CODE_FILE = r"(?P<path>[\w./-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|rb|sh|c|cc|cpp|h|hpp|css|html|sql|toml|yaml|yml))"


def _rule_coding(text: str, lower: str, _session) -> dict | None:
    m = re.match(rf"^(?:fix|debug|repair)\s+(?:the\s+)?(?P<what>.+?)\s+in\s+{_CODE_FILE}\b", text, re.I)
    if m:
        return _intent(
            "coding_fix", {"path": m.group("path"), "instruction": text}, "rule:coding_fix_file", "action_rules"
        )
    return None


def _rule_planner_review(text: str, lower: str, _session) -> dict | None:
    if re.search(r"\bjournal\b", lower) and re.search(r"\b(?:promote|convert|turn|move|copy|make)\b", lower) and \
            re.search(r"\b(?:planner|task)\b", lower):
        return clarification(
            "Which Journal note should become a Planner task for today? Give me its text, or ask me to show "
            "your open Journal items first.",
            "rule:journal_to_planner_needs_note", "action_rules",
        )
    if re.search(r"\bplanner\b", lower) and re.search(
        r"\b(?:focus|prioriti[sz]e|reprioriti[sz]e|organi[sz]e|what(?:'s| is)?\s+(?:on|in)|show|review)\b", lower
    ) and not re.match(r"^(?:add|put|create|delete|remove|promote|convert|move)\b", lower):
        return _intent("planner_today", {}, "rule:planner_review", "action_rules")
    return None


def _rule_research(text: str, lower: str, _session) -> dict | None:
    m = re.match(
        r"^(?:do|run|start|kick\s+off|launch)\s+(?:some\s+|a\s+)?(?:deep|thorough|in-?depth|exhaustive|overnight|long)\s+"
        r"research(?:\s+job)?\s+(?:overnight\s+|tonight\s+)?(?:on|into|about|regarding)\s+(?P<t>.+?)[.!]*$",
        text, re.I,
    ) or re.match(r"^research\s+(?P<t>.+?)\s+(?:overnight|tonight|in\s+depth|in\s+the\s+background)[.!]*$", text, re.I)
    if m:
        return _intent("research_create", {"objective": m.group("t").strip()}, "rule:deep_research", "action_rules")
    return None


# External actions ARIA has no integration for. Answer honestly instead of letting
# chat pretend, or web search look up the request text.
_PEOPLE = r"(?:mom|mother|dad|father|wife|husband|brother|sister|son|daughter|boss|friend|grandma|grandpa|uncle|aunt|cousin|neighbou?r)"
_MERCHANTS = r"(?:amazon|orvis|ebay|walmart|target|cabela'?s|bass\s+pro|etsy|[a-z0-9-]+\.(?:com|net|org))"
_UNSUPPORTED = [
    (r"^(?:start|unlock|lock|warm\s+up|remote[-\s]?start|honk)\s+(?:up\s+)?(?:my|the)\s+"
     r"(?:truck|car|vehicle|jeep|ranger|suv|van|engine)\b", "control a vehicle"),
    (r"^(?:book|reserve)\s+(?:me\s+)?(?:a\s+|an\s+)?(?:flight|hotel|table|room|rental|campsite|ticket)", "make bookings"),
    (r"^pay\s+(?:my\s+|the\s+)?(?:\w+\s+){0,2}(?:bill|rent|invoice|balance|mortgage)\b|"
     r"^(?:transfer|wire|venmo|send)\s+\$?\d", "move money or pay bills"),
    (rf"^(?:email|e-mail|text|message|sms|dm|call|phone|ring)\s+(?:my\s+)?{_PEOPLE}\b|"
     r"^(?:email|e-mail|text|message|sms)\s+(?:my\s+)?\w+\s+(?:that|saying|to\s+say)\b", "send messages or place calls"),
    (r"^(?:post|tweet|share)\s+(?:this|that|it)?\s*(?:on|to)\s+(?:facebook|twitter|x|instagram|reddit|linkedin)",
     "post to social media"),
    (rf"^(?:order|buy|purchase)\s+.+\b(?:from|on)\s+{_MERCHANTS}\b|^order\s+(?:me\s+)?(?:a\s+|an\s+|some\s+)?"
     r"(?:large\s+|small\s+|medium\s+)?(?:\w+\s+)?(?:pizza|takeout|delivery|food)\b", "place orders or buy things"),
]


def _rule_unsupported(text: str, lower: str, _session) -> dict | None:
    for pattern, what in _UNSUPPORTED:
        if re.match(pattern, lower):
            reply = (f"I can't {what} — no integration for that is connected to ARIA, so I won't pretend to. "
                     "I can add it to your Planner tasks or draft the text for you.")
            intent = _intent("chat", {"policy_fixed_reply": reply, "unsupported_capability": what},
                             "rule:unsupported_capability", "action_rules")
            return intent
    return None


def _rule_needs_artifact(text: str, lower: str, session) -> dict | None:
    """'Describe this image' / 'summarize this document' with nothing to act on."""
    if re.match(r"^(?:describe|caption|analy[sz]e|what(?:'s| is)\s+in)\s+(?:this|the|that)\s+(?:image|picture|photo|screenshot)\b",
                lower):
        image = getattr(session, "last_image", "") if session is not None else ""
        if image:
            return _intent("describe_image", {"path": image}, "rule:describe_last_image", "action_rules")
        return clarification("Which image? Attach it, or generate or open one first.", "rule:image_needs_artifact",
                             "action_rules")
    if re.match(r"^(?:summari[sz]e|summary\s+of|tl;?dr)\s+(?:this|the|that)\s+(?:document|doc|pdf|file|paper|report)\b",
                lower):
        doc = getattr(session, "last_document_path", "") if session is not None else ""
        if doc:
            return _intent("document_summarize", {"path": doc}, "rule:summarize_last_document", "action_rules")
        return clarification("Which document? Attach it or name the file, and I'll summarize it.",
                             "rule:document_needs_artifact", "action_rules")
    return None


_AGENT_NAMES = r"(?P<agent>codex|claude(?:\s+code)?|antigravity|agy)"


def _rule_coding_agents(text: str, lower: str, _session) -> dict | None:
    """Requests *to* or *about* the coding agents. A bare project name never matches."""
    if m := re.match(rf"^(?:ask|have|get|tell|let|use|run)\s+{_AGENT_NAMES}\s+(?:to\s+|on\s+|for\s+)?(?P<task>.+)$",
                     text, re.I):
        from jarvis.coding_agents.discovery import resolve_agent_name

        return _intent("coding_agent_plan", {"agent": resolve_agent_name(m.group("agent")), "task": m.group("task")},
                       "rule:coding_agent_request", "action_rules")
    if re.search(r"\b(?:which|what)\s+(?:changes|plans|promotions|work)\s+(?:are|is)\s+(?:awaiting|waiting\s+(?:on|for))\s+"
                 r"(?:my|your|the\s+owner'?s)?\s*(?:approval|review|decision)\b|\bpending\s+approvals?\b|"
                 r"\bwhat(?:'s|\s+is)\s+(?:waiting|awaiting|pending)\s+(?:for\s+|on\s+)?my\s+(?:approval|review|decision)\b",
                 lower):
        return _intent("coding_approvals_pending", {}, "rule:coding_awaiting_approval", "action_rules")
    if m := re.match(r"^(?:promote|apply|deploy)\s+(?:the\s+changes\s+(?:from|of)\s+)?(?:run\s+)?(?P<id>run_[0-9a-f]{6,})\b",
                     lower):
        return _intent("coding_promotion_propose", {"run_id": m.group("id")}, "rule:promotion_request", "action_rules")
    if m := re.match(r"^(?:roll\s*back|revert|undo)\s+(?:the\s+)?promotion(?:\s+(?P<id>prm_[0-9a-f]{6,}))?\b", lower):
        return _intent("coding_promotion_rollback", {"promotion_id": m.group("id") or ""}, "rule:promotion_rollback",
                       "action_rules")
    if m := re.search(rf"\bwhat\s+(?:changes\s+)?did\s+{_AGENT_NAMES}\s+(?:actually\s+)?(?:change|make|do|modify)\b",
                      lower):
        from jarvis.coding_agents.discovery import resolve_agent_name

        return _intent("coding_agent_changes", {"agent": resolve_agent_name(m.group("agent"))},
                       "rule:agent_changes", "action_rules")
    if m := re.search(rf"\bwhat\s+did\s+{_AGENT_NAMES}\s+(?:test|run|check|verify)\b", lower):
        from jarvis.coding_agents.discovery import resolve_agent_name

        return _intent("coding_agent_tests", {"agent": resolve_agent_name(m.group("agent"))}, "rule:agent_tests",
                       "action_rules")
    if m := re.search(r"\bwhich\s+(?:coding\s+)?agents?\s+worked\s+on\b", lower):
        return _intent("coding_agent_changes", {"agent": ""}, "rule:which_agent_worked", "action_rules")
    if m := re.match(r"^what\s+(?:were|was|are|have)\s+(?:we|i)\s+(?:been\s+)?(?:doing|working\s+on)\s+(?:with|on|in)\s+"
                     r"(?:the\s+)?(?P<p>.+?)\??$", text, re.I):
        from jarvis.coding_agents.projects import known_key

        if known_key(m.group("p")):
            return _intent("coding_project_activity", {"project": m.group("p")}, "rule:project_activity",
                           "action_rules")
    if re.match(r"^(?:continue|resume)\s+(?:the\s+)?(?:last\s+)?(?:unfinished|interrupted|previous)\s+coding\s+"
                r"(?:task|run|job|work)\b", lower):
        return _intent("coding_agent_resume", {}, "rule:coding_agent_resume", "action_rules")
    if re.search(r"\bwhat\s+(?:did|have)\s+(?:the\s+)?(?:coding\s+)?agents?\s+(?:do|done|accomplish(?:ed)?|"
                 r"finish(?:ed)?|get\s+done|achieve[d]?)\b", lower):
        return _intent("coding_agent_runs", {"when": text}, "rule:coding_agent_history", "action_rules")
    if re.search(r"\b(?:how(?:'s|\s+is)\s+the\s+(?:coding\s+)?agent\s+(?:doing|going)|coding[-\s]agent\s+progress)\b",
                 lower):
        return _intent("coding_agent_progress", {}, "rule:coding_agent_progress", "action_rules")
    if re.match(r"^(?:cancel|stop|abort|kill)\s+(?:the\s+)?(?:coding\s+)?agent(?:\s+run)?\b", lower):
        return _intent("coding_agent_cancel", {}, "rule:coding_agent_cancel", "action_rules")
    if re.match(r"^(?:which|what)\s+project\s+(?:were|are|was)\s+(?:we|i)\s+(?:working\s+on|on|in)\b", lower):
        return _intent("coding_project_which", {}, "rule:which_project", "action_rules")
    if re.match(r"^resume\s+(?:the\s+)?(?:unfinished|interrupted|last|previous|failed)\s+(?:coding\s+)?"
                r"(?:task|run|work|job)\b", lower):
        return _intent("coding_agent_resume", {}, "rule:coding_agent_resume", "action_rules")
    if m := re.match(r"^(?:continue|keep)\s+working\s+on\s+(?:the\s+)?(?P<p>.+?)$", text, re.I):
        from jarvis.coding_agents.projects import known_key

        if known_key(m.group("p")):
            return _intent("coding_agent_resume", {"project": m.group("p")}, "rule:continue_project", "action_rules")
    if re.search(r"\b(?:which|what)\s+coding\s+agents\b|\bcoding[-\s]agents?\s+status\b", lower):
        return _intent("coding_agents_status", {}, "rule:coding_agents_status", "action_rules")
    return None


def _rule_engineering_investigation(text: str, lower: str, session) -> dict | None:
    """Technical investigation requests remain read-only and ask for a file.

    Requiring both an imperative and a software failure target avoids turning
    general research, personal experiences or praise into coding work.
    """
    if (re.match(r"^(?:please\s+)?(?:investigate|diagnose|debug|trace|inspect|analy[sz]e)\b", lower)
        and re.search(r"\b(?:deadlock|traceback|stack\s+trace|race\s+condition|request[-\s](?:lock|lifecycle)|"
                      r"active[-\s]request|thread\s+(?:pool|lock)|stream\s+timeout|parser\s+(?:crash|error))\b", lower)):
        return _intent("coding_diagnose", {"path": getattr(session, "last_file", "") or "", "task": text},
                       "rule:engineering_investigation", "action_rules")
    return None


RULES = (
    _rule_unsupported,
    _rule_research,
    _rule_needs_artifact,
    _rule_coding_agents,
    _rule_engineering_investigation,
    _rule_mission,
    _rule_timer,
    _rule_alarm,
    _rule_task,
    _rule_event,
    _rule_media,
    _rule_home,
    _rule_runtime,
    _rule_documents,
    _rule_coding,
    _rule_planner_review,
)


def apply_rules(message: str, session=None) -> dict | None:
    text = clean(message)
    if not text or len(text) > 300:
        return None
    lower = text.lower()
    for rule in RULES:
        hit = rule(text, lower, session)
        if hit:
            return hit
    return None


# ---------------------------------------------------------------- follow-ups

_DAY = r"(?:today|tonight|tomorrow|(?:this\s+)?weekend|(?:mon|tues|wednes|thurs|fri|satur|sun)day)"


def _resolve_follow_up(message: str, session) -> dict | None:
    last = getattr(session, "last_action", "") or ""
    at = float(getattr(session, "last_action_at", 0.0) or 0.0)
    if not last or time.time() - at > FOLLOW_UP_TTL_S:
        return None
    text = clean(message)
    lower = text.lower().rstrip("?").strip()
    prev = dict(getattr(session, "last_action_params", None) or {})
    receipt = {"previous_action": last}

    change = re.match(
        r"^(?:actually[, ]+|no[, ]+|wait[, ]+|oh[, ]+)*(?:make|change|set)\s+(?:it|that)\s+(?:to\s+|for\s+)?(?P<v>.+)$",
        lower,
    )
    if last in ("planner_set_timer", "planner_update_timer") and change:
        v = change.group("v")
        duration = extract_duration(v)
        if not duration and (n := re.fullmatch(r"(\d+)", v.strip())):
            unit = (str(prev.get("duration") or "minutes").split() + ["minutes"])[1]
            duration = f"{n.group(1)} {unit}"
        if duration:
            # Update *that* timer; the handler explains instead of duplicating.
            previous = prev.get("label") or prev.get("duration") or ""
            return _intent("planner_update_timer", {"duration": duration, "previous_label": previous,
                                                    **({"timer_id": prev["timer_id"]} if prev.get("timer_id") else {})},
                           "follow_up:timer_change", "follow_up", **receipt)
    if last in ("planner_set_alarm", "planner_update_alarm") and change:
        t = extract_clock_time(change.group("v")) or (
            change.group("v").strip() if re.fullmatch(r"\d{1,2}(?::\d{2})?", change.group("v").strip()) else None
        )
        if t:
            previous = prev.get("label") or (f"Alarm {prev['time']}" if prev.get("time") else "")
            return _intent("planner_update_alarm", {"time": t, "previous_label": previous,
                                                    **({"alarm_id": prev["alarm_id"]} if prev.get("alarm_id") else {})},
                           "follow_up:alarm_change", "follow_up", **receipt)
    if last == "planner_add_task" and (
        m := re.match(r"^(?:and\s+)?(?:also\s+)?(?:add\s+)?(?:another(?:\s+one)?|one\s+more)(?:\s+task)?\s*(?:to|:|-)?\s+(?P<t>.+)$", lower)
    ):
        return _intent("planner_add_task", {"text": _strip_quotes(m.group("t"))}, "follow_up:another_task",
                       "follow_up", **receipt)
    if last == "weather_forecast" and (
        m := re.match(rf"^(?:and|what\s+about|how\s+about)\s+(?:on\s+|for\s+)?(?P<d>{_DAY})$", lower)
    ):
        return _intent("weather_forecast", {"day": m.group("d")}, "follow_up:weather_day", "follow_up", **receipt)
    if last == "mission_list" and re.match(
        r"^(?:cancel|pause|stop|abort|resume|show|open)\s+(?:the\s+)?(?:first|second|third|last|top|that|this)(?:\s+one)?$",
        lower,
    ):
        return clarification(
            "Which mission? Tell me its id from the list (for example `cancel mission 3f18c265`).",
            "follow_up:mission_needs_id",
            "follow_up",
            **receipt,
        )
    if re.match(r"^(?:do|run)\s+(?:it|that)\s+again$|^(?:same\s+again|again|repeat\s+that)$", lower):
        from jarvis.handlers.registry import is_info_action

        repeat = _intent(last, prev, "follow_up:repeat", "follow_up", **receipt)
        if is_info_action(last):
            return repeat
        return clarification(
            f"Run `{last}` again with the same settings?",
            "follow_up:repeat_confirm",
            "follow_up",
            choices=[{"label": "Yes", "intent": repeat}, {"label": "No", "intent": None}],
            ctype="action_choice",
            **receipt,
        )
    return None


def resolve_follow_up(message: str, session) -> dict | None:
    """Follow-ups; after a restart, a side-effecting one is confirmed, never just run."""
    hit = _resolve_follow_up(message, session)
    if not hit or hit.get("needs_clarification") or not getattr(session, "last_action_restored", False):
        return hit
    from jarvis.handlers.registry import is_info_action

    if is_info_action(hit["action"]):
        return hit
    return clarification(
        f"Your previous request (`{session.last_action}`) was before ARIA restarted. Still apply this to it?",
        "follow_up:confirm_after_restart", "follow_up",
        choices=[{"label": "Yes", "intent": hit}, {"label": "No", "intent": None}],
        ctype="action_choice", previous_action=session.last_action,
    )


# ---------------------------------------------------------------- "cancel it"

_CANCEL_REF = re.compile(r"^(?:please\s+)?(?:cancel|stop|abort|kill|end)\s+(?:it|that|this|that\s+one|this\s+one)$", re.I)


def cancel_reference(message: str, session) -> dict | None:
    """'Cancel it' with no reply in flight: name what could be cancelled, or say nothing is running.

    Returns None when another request is streaming — the reflex layer stops it.
    """
    if not _CANCEL_REF.match(clean(message).rstrip("?").strip()):
        return None
    try:
        from jarvis.chat_cancel import active_ids, current_request_id

        if [r for r in active_ids() if r != current_request_id()]:
            return None
    except Exception:
        pass
    choices: list[dict] = []
    try:
        from jarvis import planner_store

        for t in planner_store.active_timers()[:3]:
            choices.append({"label": f"timer {t['label'] or ''} ({t['remaining_seconds'] // 60}m left)".replace("  ", " "),
                            "intent": {"action": "planner_cancel_timer", "params": {"timer_id": t["id"]}}})
        for a in planner_store.list_alarms()[:3]:
            choices.append({"label": f"alarm {a['label']} ({a['fire_at'][11:16]})",
                            "intent": {"action": "planner_cancel_alarm", "params": {"alarm_id": a["id"]}}})
    except Exception:
        pass
    try:
        from jarvis.coding_agents import runs as agent_runs

        for r in agent_runs.list_runs(limit=5):
            if r["status"] in (agent_runs.PENDING, agent_runs.RUNNING):
                choices.append({"label": f"coding-agent run {r['id']} ({r['agent']})",
                                "intent": {"action": "coding_agent_cancel", "params": {"run_id": r["id"]}}})
    except Exception:
        pass
    try:
        from jarvis.missions import store as mission_store

        for m in mission_store.list_missions(limit=10):
            if m.get("state") in ("running", "queued", "paused"):
                choices.append({"label": f"mission {m['id']} — {str(m.get('objective') or '')[:40]}",
                                "intent": {"action": "mission_cancel", "params": {"mission_id": m["id"]}}})
    except Exception:
        pass
    if not choices:
        return clarification("Nothing is running right now that I can cancel — no reply in progress, timers, "
                             "alarms, agent runs or missions. What did you want to cancel?",
                             "cancel_nothing_active", "action_clarify", ctype="deictic")
    return clarification("Nothing is mid-reply. Which of these do you want to cancel?", "cancel_which",
                         "action_clarify", choices=choices[:6] + [{"label": "Nothing", "intent": None}],
                         ctype="action_choice")


# ---------------------------------------------------------------- deictic clarification

_DEICTIC = re.compile(
    r"^(?P<verb>fix|turn|switch|delete|remove|erase|wipe|cancel|undo|send|move|rename|close|open|set|run|"
    r"restart|kill|do|change|update|edit|save|share|post|push|deploy|apply|start|launch|install|book|buy)\s+"
    r"(?P<obj>it|that|this|them|those|these|the\s+thing|that\s+thing|this\s+thing|it\s+all)"
    r"(?P<rest>(?:\s+(?:on|off|up|down|back|again|now|please|for\s+me|today|tonight|tomorrow|later|"
    r"for\s+tomorrow|for\s+today|for\s+later|to\s+tomorrow|to\s+today|to\s+later|until\s+tomorrow|"
    r"right\s+now|asap))*)\s*\??$",
    re.I,
)


def deictic_clarification(message: str, session) -> dict | None:
    """'delete it' with nothing for 'it' to refer to → ask which."""
    text = clean(message).rstrip("?").strip()
    m = _DEICTIC.match(text)
    if not m:
        return None
    verb = m.group("verb").lower()
    if session is not None:
        # A referent this conversation established is resolved by the existing
        # coding / image follow-up paths, not here.
        if verb in ("fix", "edit", "open", "run", "save") and (session.last_file or session.last_image):
            return None
    return clarification(
        f"What should I {verb}{' ' + m.group('rest').strip() if m.group('rest').strip() else ''}? "
        f"I don't have anything in this conversation that \"{m.group('obj')}\" clearly refers to.",
        "deictic_clarify",
        "action_clarify",
        ctype="deictic",
    )


# ---------------------------------------------------------------- shortlist

# Phrases people use that registry names/descriptions don't contain.
ALIASES: dict[str, list[str]] = {
    "planner_set_timer": ["timer countdown minutes remind me in", "start a timer", "egg timer"],
    "planner_set_alarm": ["alarm wake me up at morning", "set an alarm clock"],
    "planner_add_task": ["add to my to-do list todo task", "remember to do chore errand"],
    "planner_add_event": ["calendar appointment meeting schedule event put on my calendar"],
    "planner_today": ["what is on my plate today agenda schedule planner focus"],
    "planner_list_tasks": ["show open tasks to-do list"],
    "weather_forecast": ["weather rain forecast temperature snow wind tomorrow weekend"],
    "mission_list": ["list missions running background missions"],
    "mission_status": ["mission status progress"],
    "mission_cancel": ["cancel abort stop mission"],
    "mission_pause": ["pause suspend mission"],
    "mission_create": ["start a mission long running autonomous task"],
    "generate_song": ["song lyrics compose write a song music track"],
    "generate_music": ["instrumental music background track beat"],
    "play_audio": ["play music audio file listen"],
    "generate_image": ["draw picture image illustration render paint"],
    "edit_image": ["edit the image change picture make it snowy"],
    "upscale_image": ["upscale enlarge higher resolution image"],
    "generate_video": ["video clip animation footage"],
    "generate_meme": ["meme top text bottom text"],
    "transcribe": ["transcribe recording speech to text audio file"],
    "ha_control": ["turn on off lights switch thermostat plug lamp fan home assistant"],
    "journal_log": ["journal log entry diary note today"],
    "document_search": ["search my documents files pdf warranty manual"],
    "coding_fix": ["fix bug error crash traceback broken code"],
    "coding_create": ["write a script program create code function"],
    "coding_diagnose": ["investigate diagnose why failing logs root cause"],
    "aria_self_diagnose": ["diagnose aria yourself what is wrong with you logs"],
    "git_status": ["git status uncommitted changes repo"],
    "runtime_cpu": ["cpu load processor usage"],
    "runtime_ram": ["ram memory free used"],
    "runtime_gpu": ["gpu graphics card vram"],
    "model_inventory": ["installed models which models do you have"],
    "web_search": ["search the web look up online internet google"],
    "research_create": ["deep research investigate thoroughly report sources"],
    "learn_about": ["learn about study topic teach yourself"],
    "remember": ["remember that note fact about me"],
    "memory_forget": ["forget that delete memory"],
    "continuity_recall": ["where did we leave off what did we decide last time"],
    "morning_briefing": ["brief me briefing morning summary news today"],
    "briefing_news_detail": ["latest news headlines"],
    "speak": ["say out loud read aloud tts voice"],
    "fly_recipe": ["fly pattern recipe tie tying materials hook"],
    "fly_ask": ["fly tying question"],
}

_STOP = set(
    "a an the to of for in on at by with and or is are be me my i you your it this that please can could would "
    "will do does what how some any from about up out into".split()
)


def _tokens(text: str) -> list[str]:
    out = []
    for tok in re.findall(r"[a-z0-9]+", (text or "").lower().replace("_", " ")):
        if tok in _STOP:
            continue
        if len(tok) > 4 and tok.endswith("s") and not tok.endswith("ss"):
            tok = tok[:-1]
        out.append(tok)
    return out


class _Index:
    def __init__(self) -> None:
        from jarvis.handlers import ensure_handlers_loaded
        from jarvis.handlers.registry import all_actions

        ensure_handlers_loaded()
        try:
            from jarvis.router_training import _functiongemma_training_samples

            samples = _functiongemma_training_samples()
        except Exception:
            samples = {}
        self.meta: dict[str, dict] = {}
        self.docs: dict[str, Counter] = {}
        for row in all_actions():
            name = row["action"]
            if not row.get("registered") or name in _NEVER_SHORTLIST:
                continue
            desc = (row.get("description") or "").strip()
            text = " ".join(
                [name.replace("_", " "), desc]
                + ALIASES.get(name, [])
                + [utter for utter, _ in samples.get(name, [])]
            )
            self.docs[name] = Counter(_tokens(text))
            self.meta[name] = {"description": desc or name.replace("_", " "), "info": bool(row.get("info"))}
        self.avgdl = sum(sum(c.values()) for c in self.docs.values()) / max(1, len(self.docs))
        df: Counter = Counter()
        for c in self.docs.values():
            df.update(set(c))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def rank(self, text: str, k: int = SHORTLIST_K) -> list[tuple[str, float]]:
        q = _tokens(text)
        scores = []
        for name, doc in self.docs.items():
            dl = sum(doc.values())
            s = 0.0
            for t in q:
                f = doc.get(t)
                if f:
                    s += self.idf[t] * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * dl / self.avgdl))
            if s > 0:
                scores.append((name, round(s, 2)))
        scores.sort(key=lambda x: -x[1])
        return scores[:k]


# Control/meta actions the shortlist must never propose from free text.
_NEVER_SHORTLIST = {
    "chat", "clarify", "nlu_clarify", "reflex_reply", "cognitive_compose", "session_interrupt",
    "self_upgrade_run", "self_upgrade_merge", "self_upgrade_abort", "platform_cutover_enable",
    "platform_cutover_rollback", "mcp_invoke_high_impact", "skill_invoke_high_impact", "health_emergency",
    "ha_set_token", "mcp_set_trust", "branch_delete", "skill_delete", "memory_prune", "git_sync_all",
    "workstation_down", "workstation_restart", "dev_task_commit", "git_commit", "git_pr", "git_sync",
    "coding_agent_execute", "coding_agent_run_step", "coding_agent_cancel",
    "coding_promotion_apply", "coding_promotion_rollback", "planner_cancel_timer", "planner_cancel_alarm",
}

_INDEX: _Index | None = None


def shortlist(message: str, k: int = SHORTLIST_K) -> list[tuple[str, float]]:
    global _INDEX
    if _INDEX is None:
        _INDEX = _Index()
    return _INDEX.rank(clean(message), k)


def action_meta(name: str) -> dict:
    if _INDEX is None:
        shortlist("")
    return (_INDEX.meta if _INDEX else {}).get(name, {"description": name, "info": False})


# ---------------------------------------------------------------- model chooser

_CHOOSER_PROMPT = """Choose what ARIA should do with the user's request.

Options:
{options}
- chat: just answer in conversation (questions, explanations, opinions, or anything the options above don't do)
- clarify: the request asks for an action but is too vague to act on

Request: "{message}"

Reply with only the option name."""


def model_choice_enabled() -> bool:
    import os

    # Off by default: measured end-to-end it lowered held-out accuracy, and every
    # installed model picked a wrong side-effecting action on ≥10/154 cases
    # (docs/ARIA_ACTION_ROUTING.md). Opt in with JARVIS_ROUTER_SHORTLIST_MODEL=1.
    return os.environ.get("JARVIS_ROUTER_SHORTLIST_MODEL", "0").strip().lower() in ("1", "true", "yes", "on")


def choose_with_model(message: str, *, nlu_action: str = "chat", model: str | None = None) -> dict | None:
    """Ask the router model to pick among the shortlist. None = keep NLU's answer."""
    text = clean(message)
    words = len(text.split())
    if not model_choice_enabled() or words < 2 or words > 40 or is_conceptual_question(message):
        return None
    candidates = [(a, s) for a, s in shortlist(text) if s >= MIN_SHORTLIST_SCORE * 0.5]
    if not candidates or candidates[0][1] < MIN_SHORTLIST_SCORE:
        return None
    options = "\n".join(f"- {a}: {action_meta(a)['description']}" for a, _ in candidates)
    prompt = _CHOOSER_PROMPT.format(options=options, message=text.replace('"', "'"))
    from jarvis import llm

    t0 = time.perf_counter()
    try:
        if model is None:
            from jarvis.capability_routing import apply_gateway_model

            model = apply_gateway_model(llm.router_model(), "router")
        raw, usage = llm.ask_with_usage(
            model, [{"role": "user", "content": prompt}], role="router", options={"num_predict": 24}
        )
    except Exception as exc:  # noqa: BLE001 — routing must not fail because the model did
        return {"_receipt": _receipt("shortlist_model_unavailable", error=type(exc).__name__,
                                     candidates=candidates)}
    ms = round((time.perf_counter() - t0) * 1000)
    answer = _parse_choice(raw, [a for a, _ in candidates])
    receipt = {
        "candidates": candidates,
        "model": model,
        "model_answer": (raw or "").strip()[:80],
        "model_ms": ms,
        "tokens": (usage or {}).get("prompt_tokens", 0) + (usage or {}).get("completion_tokens", 0),
        "nlu_action": nlu_action,
    }
    if answer in (None, "chat", "clarify"):
        # A small model's "clarify" proved unreliable (it fires on plain
        # questions); vague imperatives are caught by deictic_clarification.
        return {"_receipt": _receipt(f"shortlist_model_{answer or 'unparsed'}", **receipt)}
    chosen = _intent(answer, {}, "shortlist_model", "shortlist", **receipt)
    if action_meta(answer)["info"]:
        return chosen
    # Side effects need a rule-level match or the owner's yes.
    return clarification(
        f"Do you want me to {action_meta(answer)['description'].rstrip('.').lower()}?",
        "shortlist_model_confirm",
        "shortlist",
        choices=[{"label": "Yes", "intent": chosen}, {"label": "No, just answer", "intent": None}],
        ctype="action_choice",
        chosen=answer,
        **receipt,
    )


def _parse_choice(raw: str, allowed: list[str]) -> str | None:
    text = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S).strip().strip("`'\" .").lower()
    if not text:
        return None
    first = re.split(r"[\s,:;\n]", text, maxsplit=1)[0].strip("`'\" .")
    for name in (*allowed, "chat", "clarify"):
        if first == name:
            return name
    for name in sorted((*allowed, "chat", "clarify"), key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", text):
            return name
    return None


# ---------------------------------------------------------------- pending choices

_YES = re.compile(r"^(?:y|yes|yeah|yep|sure|ok(?:ay)?|do\s+it|go\s+ahead|please\s+do|confirm)\b", re.I)
_NO = re.compile(r"^(?:n|no|nope|nah|cancel|never\s*mind|don'?t)\b", re.I)


def resolve_pending_choice(reply: str, pending: dict) -> tuple[bool, dict | None]:
    """(answered, intent). answered=False → the reply is a new request."""
    labels = list(pending.get("choices") or [])
    intents = list(pending.get("choice_intents") or [])
    if not labels or len(labels) != len(intents):
        return False, None
    key = (reply or "").strip().rstrip(".!").strip().lower()
    idx = None
    if key.isdigit() and 1 <= int(key) <= len(labels):
        idx = int(key) - 1
    else:
        for i, label in enumerate(labels):
            if key == str(label).lower():
                idx = i
                break
        if idx is None and [str(x).lower() for x in labels][:1] == ["yes"]:
            if _YES.match(key):
                idx = 0
            elif _NO.match(key):
                idx = 1
    if idx is None:
        return False, None
    chosen = intents[idx]
    if not chosen:
        return True, {"action": "chat", "params": {"policy_fixed_reply": "Okay — I won't do that."},
                      "thinking": "action declined", "route_reason": "action_choice_declined"}
    return True, {**chosen, "route_reason": "action_choice_confirmed",
                  "routing_receipt": {**(chosen.get("routing_receipt") or {}), "confirmed_by_user": True}}


def note_routed(session, intent: dict) -> None:
    """Remember the action this turn routed to, for follow-ups next turn."""
    if session is None or intent.get("needs_clarification") or intent.get("action") in ("clarify", "nlu_clarify"):
        return
    session.last_action_restored = False
    session.last_action = str(intent.get("action") or "chat")
    session.last_action_params = {
        k: v for k, v in (intent.get("params") or {}).items() if isinstance(v, (str, int, float, bool))
    }
    session.last_action_at = time.time()
