"""Browser product — live web interaction agent for Aria OS.

Owns navigation, screenshots, DOM/vision automation, safe sessions.
Does not own Documents, Memory, Chat, Automation, Mission Control, or Models.
"""

from __future__ import annotations

from jarvis.browser_product.terminology import BOUNDARIES, TERMINOLOGY

__all__ = ["BOUNDARIES", "TERMINOLOGY"]
