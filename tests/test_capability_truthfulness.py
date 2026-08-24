"""Truthfulness for documents, exports and calendar writes.

Extends the media guard's rule to every externally consequential capability:

    ARIA must never claim it performed an action unless the capability actually
    performed it and there is authoritative evidence the result occurred.

The hard part is not catching lies — it is not suppressing the truth. An earlier
media guard replaced a correct answer to "How does video generation work?" with a
did-not-generate notice. So roughly half of these tests assert that explanations,
capability questions and hypotheticals survive untouched.
"""

from __future__ import annotations

import pytest

from jarvis.capability_truthfulness import verify_capability_claims as verify


# ---------------------------------------------------------------------------
# Phase 10 — Cases A/B/C: generic chat cannot claim it acted
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "message",
    [
        "I created the PDF for you.",
        "I've generated the Word document.",
        "Here's the document you asked for.",
        "Here's your PDF.",
        "I saved the report.",
        "Your document is ready.",
        "I created the file.",
    ],
)
def test_case_a_chat_cannot_claim_document_creation(message):
    out = verify({"ok": True, "message": message}, action="chat")
    assert out.get("fabricated_claim_removed") == "document", (
        f"fabricated document claim slipped through: {message!r}"
    )
    assert "did not actually create that document" in out["message"]


@pytest.mark.parametrize(
    "message",
    [
        "I exported the data to CSV.",
        "Here's your CSV.",
        "I've created the spreadsheet.",
        "Your export is ready.",
        "I saved the backup.",
        "Here's the archive.",
    ],
)
def test_case_b_chat_cannot_claim_an_export(message):
    out = verify({"ok": True, "message": message}, action="chat")
    assert out.get("fabricated_claim_removed") in {"export", "document"}, (
        f"fabricated export claim slipped through: {message!r}"
    )
    assert "did not actually" in out["message"]


@pytest.mark.parametrize(
    "message",
    [
        "I added it to your calendar.",
        "I've scheduled the meeting for tomorrow at 3.",
        "I created the event.",
        "I moved the appointment to Friday.",
        "I cancelled the event.",
        "I've updated your calendar.",
        "Your meeting is scheduled.",
        "I added the dentist appointment to your calendar.",
    ],
)
def test_case_c_chat_cannot_claim_a_calendar_write(message):
    out = verify({"ok": True, "message": message}, action="chat")
    assert out.get("fabricated_claim_removed") == "calendar", (
        f"fabricated calendar claim slipped through: {message!r}"
    )
    assert "nothing was scheduled" in out["message"].lower()


# ---------------------------------------------------------------------------
# Phase 10 — Cases D/E/F: real capability outcomes
# ---------------------------------------------------------------------------

def test_case_d_tool_failure_is_reported_as_failure():
    failed = {"ok": False, "message": "Export failed: dataset not loaded"}
    out = verify(failed, action="data_export")
    assert out["ok"] is False
    assert out["message"] == "Export failed: dataset not loaded"


def test_case_e_missing_export_artifact_is_not_success(tmp_path):
    out = verify(
        {
            "ok": True,
            "message": "Exported **sales.csv** to `/tmp/sales.csv`",
            "export_path": str(tmp_path / "never_written.csv"),
        },
        action="data_export",
    )
    assert out["ok"] is False
    assert "not on disk" in out["message"]
    assert out["artifact_missing"]


def test_case_f_real_export_keeps_its_confirmation(tmp_path):
    art = tmp_path / "sales.csv"
    art.write_text("a,b\n1,2\n", encoding="utf-8")
    original = {
        "ok": True,
        "message": f"Exported **sales.csv** to `{art}`",
        "export_path": str(art),
    }
    out = verify(dict(original), action="data_export")
    assert out == original, "a genuine export must not be altered"


def test_real_calendar_write_keeps_its_confirmation():
    """planner_add_event has no artifact file — action identity is the evidence."""
    original = {
        "ok": True,
        "module": "planner",
        "type": "planner",
        "message": "Scheduled **Dentist** at 15:00.",
    }
    out = verify(dict(original), action="planner_add_event")
    assert out == original


@pytest.mark.parametrize(
    "action",
    ["planner_add_event", "planner_add_task", "planner_set_alarm",
     "planner_set_timer", "journal_schedule"],
)
def test_every_calendar_write_action_is_recognised_as_authoritative(action):
    original = {"ok": True, "message": "I added it to your calendar.", "type": "planner"}
    out = verify(dict(original), action=action)
    assert out == original, f"{action} was treated as a fabrication"


def test_failed_calendar_write_is_not_rewritten():
    failed = {"ok": False, "module": "planner", "message": "Could not parse a date."}
    out = verify(dict(failed), action="planner_add_event")
    assert out == failed


# ---------------------------------------------------------------------------
# Phases 7/9/11 — questions, explanations and hypotheticals must survive
# ---------------------------------------------------------------------------

CAPABILITY_QUESTIONS = [
    "How do you create a PDF?",
    "Can you export CSV files?",
    "How does CSV export work?",
    "What document formats can you create?",
    "How does calendar integration work?",
    "Can you create calendar events?",
    "What happens when you schedule an event?",
    "How does calendar writing work?",
    "What is an .ics file?",
]

EXPLANATIONS = [
    "The calendar tool can create events in your calendar.",
    "CSV exports contain tabular data, one row per record.",
    "PDFs are useful for sharing documents that must not reflow.",
    "Here's how a PDF is created: the renderer lays out text, then embeds fonts.",
    "Calendar writes create events in your calendar via the planner store.",
    "Document generation works by rendering a template to a file.",
    "An export writes the current dataset to a file on disk.",
]

HYPOTHETICALS = [
    "Tell me about exporting files.",
    "Explain document creation.",
    "What would happen if I added this to my calendar?",
    "How would you schedule a meeting?",
    "Why would someone export to CSV?",
    "If I asked you to create the PDF, what would you do?",
    "Suppose I exported the data to CSV — what columns would appear?",
]


@pytest.mark.parametrize("message", CAPABILITY_QUESTIONS)
def test_capability_questions_are_never_treated_as_claims(message):
    out = verify({"ok": True, "message": message}, action="chat")
    assert not out.get("fabricated_claim_removed"), (
        f"a capability question was suppressed: {message!r}"
    )
    assert out["message"] == message


@pytest.mark.parametrize("message", EXPLANATIONS)
def test_explanations_are_never_treated_as_claims(message):
    out = verify({"ok": True, "message": message}, action="chat")
    assert not out.get("fabricated_claim_removed"), (
        f"an explanation was suppressed: {message!r}"
    )
    assert out["message"] == message


@pytest.mark.parametrize("message", HYPOTHETICALS)
def test_hypotheticals_are_never_treated_as_claims(message):
    out = verify({"ok": True, "message": message}, action="chat")
    assert not out.get("fabricated_claim_removed"), (
        f"a hypothetical was suppressed: {message!r}"
    )
    assert out["message"] == message


def test_ordinary_chat_is_untouched():
    plain = {"ok": True, "message": "Tuesday works well for most people."}
    assert verify(dict(plain), action="chat") == plain


# ---------------------------------------------------------------------------
# Phase 11 — the guard is not a keyword filter
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "message",
    [
        "The report was created by the finance team last quarter.",
        "Exported data is often stored as CSV.",
        "That document is created automatically each month.",
        "Events are scheduled in UTC and displayed in local time.",
        "Your calendar shows three meetings on Friday.",
    ],
)
def test_action_words_alone_do_not_trigger_the_guard(message):
    """Passive, third-person and descriptive sentences are not first-person claims."""
    out = verify({"ok": True, "message": message}, action="chat")
    assert not out.get("fabricated_claim_removed"), f"keyword false positive: {message!r}"


# ---------------------------------------------------------------------------
# Cross-capability
# ---------------------------------------------------------------------------

def test_media_guard_still_works_after_generalisation():
    out = verify(
        {"ok": True, "message": "Sure! Here's your meme:\n![m](https://via.placeholder.com/1)"},
        action="chat",
    )
    assert out.get("fabricated_claim_removed") == "media"


def test_video_generation_explanation_regression_stays_fixed():
    """The canonical over-correction: this must remain an honest explanation."""
    msg = (
        "Video generation works by denoising latents over many steps. "
        "The model generates the video frame by frame."
    )
    out = verify({"ok": True, "message": msg}, action="chat")
    assert not out.get("fabricated_claim_removed")
    assert out["message"] == msg


def test_guard_is_wired_at_the_single_choke_point():
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "jarvis" / "conversation_pipeline.py"
    text = src.read_text(encoding="utf-8")
    start = text.index("def decorate_result(")
    assert "verify_capability_claims" in text[start : start + 1500]


def test_all_families_are_covered():
    from jarvis.capability_truthfulness import FAMILIES

    assert {f.name for f in FAMILIES} == {"media", "document", "export", "calendar"}
