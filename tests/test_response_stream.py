from jarvis.response import cap_stream_payload, stream_done


def test_stream_done_trims_embedded_code_from_proposal_message():
    payload = stream_done({
        "ok": True,
        "message": "I wrote a script.\n\n```python\nprint('hi')\n```\n\nApply it.",
        "type": "proposal",
        "proposal_id": "abc123",
        "diff": "--- a\n+++ b\n+print('hi')",
    })
    assert payload["type"] == "done"
    assert "```" not in payload["message"]
    assert "Apply it" in payload["message"]


def test_cap_stream_payload_truncates_huge_diff():
    big = "\n".join(f"+line {i}" for i in range(500))
    capped = cap_stream_payload({"diff": big, "proposal_id": "x"})
    assert capped.get("diff_truncated") is True
    assert capped["diff_total_lines"] == 500
    assert len(capped["diff"].splitlines()) <= 180


def test_cap_stream_payload_lite_ui_omits_diff():
    capped = cap_stream_payload(
        {"diff": "+hello", "proposal_id": "x", "message": "Done"},
        lite_ui=True,
    )
    assert "diff" not in capped
    assert capped.get("diff_omitted") is True
