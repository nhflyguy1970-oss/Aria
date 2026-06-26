"""Stale journal memory and resume-context gating."""

from datetime import date

from jarvis.memory_context import (
    contextualize_memory_for_chat,
    normalize_journal_memory_text,
    should_inject_resume_context,
)
from jarvis.router import is_meta_self_question
from jarvis.session import SessionContext


def test_meta_self_skips_resume_context():
    msg = "how hard would it be for you to fix or upgrade yourself"
    assert is_meta_self_question(msg)
    assert not should_inject_resume_context(msg, SessionContext())


def test_resume_context_for_coding_followup():
    session = SessionContext(last_module="coding")
    assert should_inject_resume_context("hello", session)
    assert should_inject_resume_context("debug until tests pass for foo.py", SessionContext())


def test_normalize_birthday_journal_memory():
    raw = "From bullet journal (daily:2026-06-09): — Today is mom's birthday."
    assert normalize_journal_memory_text(raw) == "Mom's birthday is June 9."


def test_contextualize_stale_birthday_as_permanent_fact():
    raw = "From bullet journal (daily:2026-06-09): — Today is mom's birthday."
    out = contextualize_memory_for_chat(raw, today=date(2026, 6, 13))
    assert out == "Mom's birthday is June 9."


def test_contextualize_stale_today_note_dropped():
    raw = "From bullet journal (daily:2026-06-08): — Today I need to call the bank."
    assert contextualize_memory_for_chat(raw, today=date(2026, 6, 13)) is None
