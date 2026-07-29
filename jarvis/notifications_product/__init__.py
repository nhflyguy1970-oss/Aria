"""Notifications — Aria's unified operator attention product."""

from jarvis.notifications_product.engine import home_payload, product_status
from jarvis.notifications_product.pipeline import publish
from jarvis.notifications_product.terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY

__all__ = [
    "BOUNDARIES",
    "MENTAL_MODEL",
    "TERMINOLOGY",
    "home_payload",
    "product_status",
    "publish",
]
