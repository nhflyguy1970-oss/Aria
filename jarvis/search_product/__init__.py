"""Search — Aria's federated find product (one shared engine)."""

from jarvis.search_product.engine import home_payload, product_status
from jarvis.search_product.pipeline import format_search_message, run_search
from jarvis.search_product.terminology import BOUNDARIES, FACETS, MENTAL_MODEL, TERMINOLOGY

__all__ = [
    "BOUNDARIES",
    "FACETS",
    "MENTAL_MODEL",
    "TERMINOLOGY",
    "format_search_message",
    "home_payload",
    "product_status",
    "run_search",
]
