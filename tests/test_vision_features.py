"""Vision features — product API and action coverage."""

from jarvis.vision_product.engine import ACTIONS, action_rail


def test_vision_actions_cover_spec():
    rail_ids = {a["id"] for a in action_rail()}
    assert "describe" in rail_ids
    assert "ocr" in rail_ids
    assert "compare" in ACTIONS
    assert "import" in ACTIONS
    assert "remember" in ACTIONS
