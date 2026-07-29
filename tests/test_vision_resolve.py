"""Vision path resolve behavior."""

import pytest

from jarvis.modules.vision import _resolve_image_path


def test_resolve_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        _resolve_image_path(str(tmp_path / "missing.png"))
