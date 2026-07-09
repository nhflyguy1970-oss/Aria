"""Platform PDF/DOCX reader adoption for Aria document pipeline."""

from __future__ import annotations

from pathlib import Path


def read_platform_document(path: Path) -> list[str] | None:
    """Use AI Platform binary readers when available; return page texts or None."""
    try:
        from aiplatform.intelligence.readers_binary import DocxReader, PdfReader
    except ImportError:
        return None

    suffix = path.suffix.lower()
    reader = PdfReader() if suffix == ".pdf" else DocxReader() if suffix == ".docx" else None
    if reader is None or not reader.can_read(str(path)):
        return None
    document = reader.read(str(path))
    if document is None or not document.content.strip():
        return None
    if suffix == ".pdf":
        chunks = [part.strip() for part in document.content.split("\n\n") if part.strip()]
        return chunks or [document.content.strip()]
    return [document.content.strip()]
