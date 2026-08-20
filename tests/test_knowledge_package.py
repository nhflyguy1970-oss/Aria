"""Knowledge package exports — learn commands available from jarvis.knowledge."""

from __future__ import annotations

from pathlib import Path


def test_is_learn_command_importable():
    from jarvis.knowledge import is_learn_command, parse_learn_topic

    assert is_learn_command("learn about: Python typing")
    assert parse_learn_topic("learn about: Python typing") == "Python typing"


def test_document_path_resolution_imports_cleanly(data_dir):
    """jarvis.config never exported UPLOAD_DIR, so every document action that
    resolved a path died with ImportError before doing any work."""
    from unittest.mock import MagicMock

    from jarvis.behaviors.knowledge.context import KnowledgeContext

    uploads = data_dir / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    (uploads / "probe.txt").write_text("hello", encoding="utf-8")

    ctx = KnowledgeContext(memory=MagicMock(), session=MagicMock(), _orchestrator=MagicMock())
    resolved = ctx.resolve_document_path({"path": "uploads/probe.txt"})

    assert resolved.endswith("uploads/probe.txt")
    assert Path(resolved).exists()
