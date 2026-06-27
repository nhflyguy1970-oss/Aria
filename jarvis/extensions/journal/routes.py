"""Journal fast-path routing rules."""

from __future__ import annotations

import re

from jarvis.journal_learning import is_journal_learn, is_journal_learn_recall, parse_journal_learn_recall_query
from jarvis.router_table import RouteRule


def journal_routes() -> list[RouteRule]:
    return [
        RouteRule(
            "journal_learn_recall",
            18,
            "journal learn recall",
            lambda m, lower, _s: is_journal_learn_recall(lower),
            params=lambda m: {"query": parse_journal_learn_recall_query(m)},
        ),
        RouteRule(
            "journal_learn",
            19,
            "journal learn",
            lambda m, lower, _s: is_journal_learn(m),
            params=lambda m: {"text": m},
        ),
        RouteRule(
            "project_journal_daily_update",
            18,
            "project journal daily update",
            lambda m, lower, _s: bool(
                re.search(r"\bupdate\s+(?:all\s+)?project journals?\b", lower)
                or re.search(r"\bproject journal\s+(?:daily|morning|evening)\b", lower)
                or re.search(r"\brefresh\s+project journal\b", lower)
            ),
            params=lambda m: {"text": m},
        ),
        RouteRule(
            "project_journal_list",
            19,
            "project journal list",
            lambda m, lower, _s: bool(re.search(r"\b(list|show)\s+project journals?\b", lower)),
        ),
        RouteRule(
            "project_journal_today",
            19,
            "project journal today",
            lambda m, lower, _s: bool(
                re.search(r"\bproject journal\b", lower)
                and re.search(r"\b(today|daily|show|what did i log)\b", lower)
            ),
        ),
        RouteRule(
            "project_journal_log",
            20,
            "project journal log",
            lambda m, lower, _s: bool(
                re.search(r"\blog to\s+[\w-]+\s+(?:project\s+)?journal\b", lower)
                or re.search(r"\bproject (?:journal|log)[:\s]+\S", lower)
            ),
            params=lambda m: {"text": m},
        ),
        RouteRule(
            "journal_today",
            20,
            "journal today",
            lambda m, lower, _s: bool(
                re.search(r"\b(what did i write|journal today|today'?s journal|daily log)\b", lower)
            ),
        ),
        RouteRule(
            "journal_monthly",
            21,
            "journal monthly",
            lambda m, lower, _s: bool(
                re.search(r"\b(monthly log|journal this month|month'?s journal|monthly journal)\b", lower)
            ),
        ),
        RouteRule(
            "journal_open_tasks",
            22,
            "journal tasks",
            lambda m, lower, _s: bool(
                re.search(
                    r"\b(open tasks|journal tasks|what('s| is) on my (plate|list)|my todos?|to-?do list)\b",
                    lower,
                )
            ),
        ),
        RouteRule(
            "journal_reflect",
            23,
            "journal reflect",
            lambda m, lower, _s: bool(
                re.search(r"\b(journal reflect|reflect on my journal|monthly review)\b", lower)
            ),
        ),
        RouteRule(
            "journal_migrate",
            24,
            "journal migrate",
            lambda m, lower, _s: bool(re.search(r"\b(migrate journal|monthly migration)\b", lower)),
        ),
        RouteRule(
            "journal_log",
            25,
            "journal log",
            lambda m, lower, _s: bool(
                re.search(r"\b(?:log|journal)[:\s]+(.+)", lower)
                and not re.search(
                    r"\b(remember (this )?bullet|save journal to memory|remember journal entry)\b",
                    lower,
                )
                and not re.search(r"\blog to\s+[\w-]+\s+(?:project\s+)?journal\b", lower)
                and not re.search(r"\bproject (?:journal|log)[:\s]", lower)
            ),
            params=lambda m: (
                {"text": mobj.group(1).strip()}
                if (mobj := re.search(r"\b(?:log|journal)[:\s]+(.+)", m, re.I))
                else {}
            ),
        ),
        RouteRule(
            "journal_search",
            26,
            "search journal",
            lambda m, lower, _s: bool(re.search(r"\bsearch journal\b", lower)),
            params=lambda m: {"query": m},
        ),
        RouteRule(
            "journal_review",
            27,
            "journal review",
            lambda m, lower, _s: bool(
                re.search(r"\b(month.?end review|weekly review|run journal review)\b", lower)
            ),
        ),
        RouteRule(
            "journal_remember",
            28,
            "remember journal",
            lambda m, lower, _s: bool(
                re.search(r"\b(remember (this )?bullet|save journal to memory|remember journal entry)\b", lower)
            ),
            params=lambda m: (
                {"bullet_id": mobj.group(1)}
                if (mobj := re.search(r"\b([a-f0-9]{8})\b", m))
                else {"bullet_id": ""}
            ),
        ),
        RouteRule(
            "journal_schedule",
            29,
            "schedule task",
            lambda m, lower, _s: bool(re.search(r"schedule\s+.+?\s+to\s+\d{4}-\d{2}\b", m, re.I)),
            params=lambda m: (
                {"task_query": mobj.group(1).strip(), "month": mobj.group(2)}
                if (mobj := re.search(r"schedule\s+(.+?)\s+to\s+(\d{4}-\d{2})\b", m, re.I))
                else {}
            ),
        ),
        RouteRule(
            "journal_thread",
            30,
            "thread task",
            lambda m, lower, _s: bool(
                re.search(r"\b(thread tasks to today|pull tasks to today)\b", lower)
                or re.search(r"thread\s+(.+?)\s+to\s+(today|\d{4}-\d{2}-\d{2})\b", m, re.I)
                or re.search(r"\b(thread .+ to today|thread to today)\b", lower)
            ),
            params=lambda m: _journal_thread_params(m),
        ),
    ]


def _journal_thread_params(message: str) -> dict:
    from jarvis.modules.journal import _today

    lower = message.lower()
    if re.search(r"\b(thread tasks to today|pull tasks to today)\b", lower):
        return {}
    m = re.search(r"thread\s+(.+?)\s+to\s+(today|\d{4}-\d{2}-\d{2})\b", message, re.I)
    if m:
        day = _today() if m.group(2).lower() == "today" else m.group(2)
        return {"task_query": m.group(1).strip(), "day": day}
    m = re.search(r"thread\s+(.+?)\s+to\s+today", message, re.I)
    if m:
        return {"task_query": m.group(1).strip()}
    return {}
