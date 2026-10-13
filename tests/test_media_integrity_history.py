"""Media integrity vs. conversation history.

The capability-truthfulness gate replaced a correct recall of earlier turns with
"I did not actually generate that …" because the recalled transcript contained
"- I: Here's your image …" (2026-10-12, live Test C). Quoting the record is not
a new delivery claim. These tests keep both halves true: history may be quoted,
and fabricated deliveries are still caught.
"""

from __future__ import annotations

import time

import pytest

from jarvis.capability_truthfulness import FAMILIES, verify_capability_claims
from jarvis.continuity.retrieve import HITS, ContinuityResult, Item, answer

MEDIA_HONEST = FAMILIES[0].honest


def _gate(message: str, *, action: str = "chat", **extra) -> dict:
    return verify_capability_claims({"ok": True, "message": message, **extra}, action=action)


def _recall_reply(*turns: tuple[str, str]) -> str:
    now = time.time()
    items = [
        Item(section="excerpt", text=text, ts=now - 60 + i, actor=actor, ref=f"t{i}")
        for i, (actor, text) in enumerate(turns)
    ]
    return answer(ContinuityResult(status=HITS, query="", sections={"excerpt": items}))


def test_real_recall_answer_quoting_an_image_turn_survives():
    reply = _recall_reply(
        ("user", "make an image of a brook trout rising"),
        ("assistant", "Here's your image of a brook trout rising to a dry fly."),
        ("user", "What should we work on?"),
        ("assistant", "Let's finish the hatch-matching feature."),
    )
    assert "- I: Here's your image" in reply  # the real formatter quotes the turn
    out = _gate(reply, action="continuity_recall")
    assert out["message"] == reply
    assert "fabricated_claim_removed" not in out


@pytest.mark.parametrize(
    "message",
    [
        'Earlier I replied "Here\'s your image of the hatch chart" when you asked for one.',
        "You asked what I said. My reply was:\n> Here's your image: the brook trout.\n",
        "**What we were saying**\n- You: draw a trout\n- **I**: I've generated your image of the trout.",
        "Two turns ago:\n- ARIA: Here's your meme about waders.\n- You: ha, perfect",
    ],
)
def test_quoted_history_is_not_a_delivery_claim(message):
    out = _gate(message)
    assert out["message"] == message


@pytest.mark.parametrize(
    "message",
    [
        "The image we generated earlier had a brook trout; we could warm up the lighting.",
        "That picture from this morning used the SDXL model at 1024x1024.",
        "Yes — you liked the second trout image better than the first.",
    ],
)
def test_discussing_previous_images_is_untouched(message):
    out = _gate(message)
    assert out["message"] == message


def test_plain_text_reply_is_untouched():
    message = "We could tackle the fly-pattern search next, then the hatch calendar."
    assert _gate(message)["message"] == message


@pytest.mark.parametrize(
    "message",
    [
        "Sure! Here's your image of a trout rising.",
        "As I said, here's your image of the trout.",
        "- You: draw a trout\nHere's your image of the trout.",
        'I made the change. Here is your picture of the "evening hatch".',
    ],
)
def test_fabricated_delivery_is_still_caught(message):
    out = _gate(message)
    assert out["fabricated_claim_removed"] == "media"
    assert out["message"] == MEDIA_HONEST


def test_real_image_generation_keeps_its_confirmation(tmp_path):
    art = tmp_path / "image_1.png"
    art.write_bytes(b"\x89PNG\r\n")
    out = verify_capability_claims(
        {"ok": True, "type": "image_result", "message": "Here's your image of a trout.",
         "image_path": str(art)},
        action="generate_image",
    )
    assert out["ok"] is True
    assert out["message"] == "Here's your image of a trout."


def test_image_generation_with_missing_file_is_not_success(tmp_path):
    out = verify_capability_claims(
        {"ok": True, "type": "image_result", "message": "Here's your image of a trout.",
         "image_path": str(tmp_path / "never_written.png")},
        action="generate_image",
    )
    assert out["ok"] is False
    assert out["artifact_missing"]


def test_streamed_done_event_goes_through_the_same_gate(monkeypatch):
    from types import SimpleNamespace

    import jarvis.trust_memory
    from jarvis.conversation_pipeline import decorate_result

    monkeypatch.setattr(jarvis.trust_memory, "record_tool_outcome", lambda *a, **k: None)
    reply = _recall_reply(("assistant", "Here's your image of a brook trout."))
    session = SimpleNamespace(note_module=lambda *_: None, last_module="")
    assistant = SimpleNamespace(session=session, memory=None,
                                branches=SimpleNamespace(persist=lambda **_: None))
    out = decorate_result(
        assistant, {"ok": True, "message": reply, "module": "memory"},
        intent={}, action="continuity_recall", params={}, message="What were we just discussing?",
    )
    assert out["message"] == reply

    fabricated = decorate_result(
        assistant, {"ok": True, "message": "Here's your image of a trout!"},
        intent={}, action="chat", params={}, message="draw a trout",
    )
    assert fabricated["message"] == MEDIA_HONEST
