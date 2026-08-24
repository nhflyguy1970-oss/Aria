"""Defect #4 — media requests must reach media capabilities, and chat may not lie.

Two failures compounded in production:

1. `_image_edit_route` captures "make …" with an *optional* image noun, so once any
   image was in session, "make a meme …" resolved to `edit_image` — which was not in
   the list of actions allowed to beat a weak NLU verdict, so it was discarded and
   answered as generic chat.
2. Generic chat then fabricated the result: "Sure! Here's your meme:" plus an invented
   placeholder image URL. No job, no artifact, and it read as success.

These tests pin both halves: the routing contract, and the rule that ARIA never claims
to have produced media that it did not produce.
"""

from __future__ import annotations

import pytest

from jarvis.session import SessionContext

IMG = "/media/jeff/AI/jarvis/data/generated/image_20260824_095903.png"
MEDIA_ACTIONS = {
    "generate_image", "generate_video", "generate_meme", "storyboard_video",
    "edit_image", "inpaint_image", "upscale_image",
}


@pytest.fixture
def weak_nlu(monkeypatch):
    """Reproduce production: NLU answers a confident but useless `chat`."""
    monkeypatch.setattr("jarvis.nlu.pipeline.nlu_enabled", lambda: True)
    monkeypatch.setattr(
        "jarvis.nlu.pipeline.route_via_nlu",
        lambda message, session, attachment=None: {"action": "chat", "params": {}},
    )


def _session(with_image: bool) -> SessionContext:
    s = SessionContext()
    if with_image:
        s.note_image(IMG)
    return s


def _route(message: str, *, with_image: bool) -> str:
    from jarvis.router import route

    return str(route(message, _session(with_image)).get("action") or "")


# ---------------------------------------------------------------------------
# Phase 5 — the two observed failures
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("with_image", [False, True])
@pytest.mark.parametrize(
    "message",
    [
        "make a meme",
        "make a meme about fly fishing",
        "make a meme with top HELLO and bottom WORLD",
        "create a meme about tests passing",
        "generate a meme about mondays",
    ],
)
def test_meme_requests_never_fall_through_to_chat(weak_nlu, message, with_image):
    """The exact production failure, in both session states."""
    action = _route(message, with_image=with_image)
    assert action != "chat", f"{message!r} fell through to generic chat"
    assert action == "generate_meme", f"{message!r} routed to {action}"


def test_meme_request_survives_an_image_in_session(weak_nlu):
    """The specific trigger: a generated image in session hijacked "make a meme"."""
    assert _route("make a meme about fly fishing", with_image=False) == "generate_meme"
    assert _route("make a meme about fly fishing", with_image=True) == "generate_meme"


# ---------------------------------------------------------------------------
# Phase 6 — all four repaired routes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "message,expected",
    [
        ("make a meme about fly fishing", {"generate_meme"}),
        ("upscale the image 2x", {"upscale_image"}),
        ("enlarge the picture", {"upscale_image"}),
        ("edit the image to add falling snow", {"edit_image", "inpaint_image"}),
        ("inpaint the top left corner with a fly rod", {"inpaint_image"}),
    ],
)
def test_repaired_media_routes_reach_a_media_action(weak_nlu, message, expected):
    action = _route(message, with_image=True)
    assert action in expected, f"{message!r} routed to {action}, expected one of {expected}"


@pytest.mark.parametrize(
    "message,expected",
    [
        ("generate an image of a trout", "generate_image"),
        ("generate a video of a river", "generate_video"),
    ],
)
@pytest.mark.parametrize("with_image", [False, True])
def test_already_working_media_routes_are_not_regressed(weak_nlu, message, expected, with_image):
    assert _route(message, with_image=with_image) == expected


def test_media_actions_may_override_a_weak_nlu_verdict():
    """Every media action _quick_route can resolve must be allowed to win."""
    import inspect

    from jarvis import router

    src = inspect.getsource(router.route)
    start = src.index("quick_override = _quick_route")
    block = src[start : start + 1400]
    for action in ("edit_image", "inpaint_image", "upscale_image", "generate_meme"):
        assert f'"{action}"' in block, (
            f"{action} cannot override a weak NLU verdict, so a correctly "
            "resolved media request would be answered as chat"
        )


# ---------------------------------------------------------------------------
# Phase 9 — questions about media stay conversation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "message",
    [
        "What is a meme?",
        "What makes a good fishing meme?",
        "Can you explain image upscaling?",
        "What is inpainting?",
        "How does video generation work?",
        "why do memes go viral?",
        "explain how image generation models work",
    ],
)
@pytest.mark.parametrize("with_image", [False, True])
def test_questions_about_media_do_not_launch_media_jobs(weak_nlu, message, with_image):
    action = _route(message, with_image=with_image)
    assert action not in MEDIA_ACTIONS, (
        f"asking about media launched {action}: {message!r}"
    )


# ---------------------------------------------------------------------------
# Phase 7 — truthfulness guard
# ---------------------------------------------------------------------------

FABRICATED_MEME = {
    "ok": True,
    "message": (
        "Sure! Here's your meme:\n\n**Top Text:** WHEN THE TEST PASSES\n"
        "**Bottom Text:** FIRST TRY\n\n"
        "![Meme Image](https://via.placeholder.com/350x150?text=WHEN+THE+TEST+PASSES)"
    ),
}


def test_case_a_chat_cannot_fabricate_an_image():
    from jarvis.capability_truthfulness import verify_media_claims

    out = verify_media_claims(
        {"ok": True, "message": "Here's your image of a trout!\n![img](http://example.com/a.png)"},
        action="chat",
    )
    assert out.get("fabricated_media_claim_removed") is True
    assert "did not actually generate" in out["message"]
    assert "example.com" not in out["message"]


def test_case_b_chat_cannot_fabricate_a_meme():
    from jarvis.capability_truthfulness import verify_media_claims

    out = verify_media_claims(dict(FABRICATED_MEME), action="chat")
    assert out.get("fabricated_media_claim_removed") is True
    assert "via.placeholder.com" not in out["message"]
    assert "Here's your meme" not in out["message"]


def test_case_c_failed_media_operation_still_reports_failure():
    from jarvis.capability_truthfulness import verify_media_claims

    failed = {"ok": False, "type": "image_result", "message": "ComfyUI refused the workflow"}
    out = verify_media_claims(failed, action="generate_image")
    assert out["ok"] is False
    assert out["message"] == "ComfyUI refused the workflow", "a real failure must pass through"


def test_case_d_missing_artifact_is_not_a_success(tmp_path):
    from jarvis.capability_truthfulness import verify_media_claims

    out = verify_media_claims(
        {
            "ok": True,
            "type": "image_result",
            "message": "Here's your image",
            "image_path": str(tmp_path / "never_written.png"),
        },
        action="generate_image",
    )
    assert out["ok"] is False, "an artifact-less media result must not report success"
    assert "not on disk" in out["message"]
    assert out["artifact_missing"]


def test_case_e_real_media_result_passes_through_untouched(tmp_path):
    from jarvis.capability_truthfulness import verify_media_claims

    art = tmp_path / "real.png"
    art.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    original = {
        "ok": True,
        "type": "image_result",
        "message": "Here's your image — **a brook trout**",
        "image_path": str(art),
    }
    out = verify_media_claims(dict(original), action="generate_image")
    assert out == original, "a genuine media result must not be altered"


def test_queued_media_job_is_not_treated_as_a_fabrication():
    """The pending stub says work is under way — that claim is true."""
    from jarvis.capability_truthfulness import verify_media_claims

    queued = {
        "ok": True,
        "type": "media_job",
        "pending": True,
        "job_id": "abc123",
        "message": "**Image generation** queued in the background.",
    }
    assert verify_media_claims(dict(queued), action="generate_image") == queued


def test_ordinary_chat_is_untouched():
    from jarvis.capability_truthfulness import verify_media_claims

    plain = {"ok": True, "message": "A meme is an idea that spreads from person to person."}
    assert verify_media_claims(dict(plain), action="chat") == plain


@pytest.mark.parametrize(
    "explanation",
    [
        "Video generation works by denoising latents over many steps. The model "
        "generates the video frame by frame.",
        "Image upscaling increases resolution using a model created for that purpose.",
        "Inpainting fills a masked region. The model generates the image content "
        "that belongs there.",
        "When I generate an image, a diffusion model turns noise into pixels.",
        "A meme is an idea or image that spreads from person to person.",
    ],
)
def test_explaining_media_is_not_claiming_media(explanation):
    """Regression: the first guard replaced a real answer to "How does video
    generation work?" with the did-not-generate notice. Describing a feature is
    not delivering an artifact."""
    from jarvis.capability_truthfulness import verify_media_claims

    out = verify_media_claims({"ok": True, "message": explanation}, action="chat")
    assert not out.get("fabricated_media_claim_removed"), (
        f"explanatory answer was wrongly treated as a fabricated claim: {explanation!r}"
    )
    assert out["message"] == explanation


@pytest.mark.parametrize(
    "delivery",
    [
        "Sure! Here's your meme:\n![Meme](https://via.placeholder.com/350x150)",
        "Here's your image of a trout.",
        "I've generated your video, enjoy!",
        "I just created your meme.",
    ],
)
def test_delivery_phrasing_is_always_caught(delivery):
    from jarvis.capability_truthfulness import verify_media_claims

    out = verify_media_claims({"ok": True, "message": delivery}, action="chat")
    assert out.get("fabricated_media_claim_removed") is True, (
        f"fabricated delivery slipped through: {delivery!r}"
    )


def test_guard_runs_on_every_dispatched_result():
    """Wiring check: the guard must sit at the shared result choke point."""
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "jarvis" / "conversation_pipeline.py"
    text = src.read_text(encoding="utf-8")
    start = text.index("def decorate_result(")
    assert "verify_capability_claims" in text[start : start + 1500], (
        "the truthfulness guard is not applied in decorate_result"
    )
