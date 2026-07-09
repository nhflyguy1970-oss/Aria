"""Knowledge source types and status enums."""

from __future__ import annotations

SOURCE_TYPES = (
    "git_repository",
    "project_folder",
    "documentation",
    "pdf",
    "docx",
    "markdown",
    "notes",
    "website",
    "youtube",
    "dataset",
    "conversation",
    "archive",
    "code_index",
    "document_library",
    "mixed",
)

INDEX_STATUSES = ("indexed", "stale", "empty", "error", "unknown", "indexing")
EMBED_STATUSES = ("ready", "partial", "offline", "none")
HEALTH_STATUSES = ("healthy", "degraded", "offline", "error")
