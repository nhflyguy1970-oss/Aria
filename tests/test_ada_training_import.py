"""Ada USB training row mapping for FunctionGemma export."""

import json

from jarvis.router_training import _parse_ada_row, load_ada_training_rows


def test_parse_ada_control_light():
    row = json.loads(
        '{"messages": [{"role": "user", "content": "Turn on bedroom"}, '
        '{"role": "assistant", "tool_calls": [{"function": {"name": "control_light", '
        '"arguments": {"action": "on", "device_name": "bedroom"}}}]}]}'
    )
    user, call = _parse_ada_row(row)
    assert user == "Turn on bedroom"
    assert "ha_control" in call
    assert "target: bedroom" in call
    assert "action: on" in call


def test_parse_ada_skips_calendar():
    row = json.loads(
        '{"messages": [{"role": "user", "content": "Lunch Monday"}, '
        '{"role": "assistant", "tool_calls": [{"function": {"name": "create_calendar_event", '
        '"arguments": {"title": "lunch"}}}]}]}'
    )
    assert _parse_ada_row(row) is None


def test_load_ada_rows_from_usb_if_present():
    rows = load_ada_training_rows()
    # USB may be unplugged in CI — only assert structure when rows exist.
    if rows:
        assert isinstance(rows[0][0], str)
        assert rows[0][1].startswith("call:")
