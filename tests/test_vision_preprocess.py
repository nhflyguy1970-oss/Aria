"""Tests for vision image preprocessing."""

from pathlib import Path

from jarvis.modules.vision import MAX_VISION_PIXELS, _prepare_image_b64
from PIL import Image


def test_large_image_is_downscaled(tmp_path: Path):
    img = tmp_path / "big.png"
    Image.new("RGB", (4000, 2000), "blue").save(img)
    cache: dict = {}
    _prepare_image_b64(img, cache)
    assert len(cache) == 1

    # Decoded JPEG should be much smaller than raw PNG dimensions would imply
    import base64
    import io

    raw = base64.b64decode(next(iter(cache.values())))
    with Image.open(io.BytesIO(raw)) as out:
        assert max(out.size) <= MAX_VISION_PIXELS
