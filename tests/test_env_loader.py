"""Tests for jarvis.env auto-reload."""

import importlib
from pathlib import Path


def test_env_reload_on_file_change(data_dir, monkeypatch):
    import jarvis.env_loader as el

    importlib.reload(el)
    monkeypatch.setattr("jarvis.env_loader.load_jarvis_env", el.load_jarvis_env)

    env_file = data_dir / "jarvis.env"
    env_file.write_text('export JARVIS_HA_ENABLED="1"\n', encoding="utf-8")
    monkeypatch.setattr(el, "ENV_FILE", env_file)
    el._LOADED = False
    el._ENV_DIGEST = ""

    import os

    monkeypatch.delenv("JARVIS_HA_TOKEN", raising=False)
    el.load_jarvis_env(force=True)
    assert os.getenv("JARVIS_HA_TOKEN") is None

    env_file.write_text(
        env_file.read_text()
        + 'export JARVIS_HA_TOKEN="eyJhbGciOiJIUzI1NiJ9.abc.defghijklmnopqrstuvwxyz"\n',
        encoding="utf-8",
    )
    el.load_jarvis_env()
    assert os.getenv("JARVIS_HA_TOKEN", "").startswith("eyJ")
