"""Vision preprocess helpers."""

from jarvis.vision_media import apply_crop_bytes, parse_region


def test_parse_region_presets():
    assert parse_region("what's in the top-left?") is not None
    assert parse_region("center of the image")["w"] == 0.5


def test_apply_crop_noop():
    raw = b"not-image"
    assert apply_crop_bytes(raw, None) == raw
