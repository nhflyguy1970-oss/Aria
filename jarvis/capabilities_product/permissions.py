"""Human-readable permission helpers."""

from __future__ import annotations

from jarvis.capabilities_product.models import PERMISSION_LABELS


def label_for(permission_id: str) -> str:
    return PERMISSION_LABELS.get(permission_id, permission_id)


def summarize(permissions: list[str] | None) -> list[dict[str, str]]:
    return [{"id": p, "label": label_for(p)} for p in (permissions or [])]
