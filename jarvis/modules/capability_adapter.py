"""Capability adapter — legacy tool invocation remains authoritative."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant

logger = logging.getLogger("jarvis.capability_adapter")

_APPLICATION_ID = "aria"
_SYNCED = False


def tool_capability_enabled() -> bool:
    if os.getenv("JARVIS_DISABLE_PLATFORM_TOOL_CAPABILITY", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED") == "1":
        return True
    try:
        from jarvis.platform_tool_capability import is_tool_capability_attached

        return is_tool_capability_attached()
    except ImportError:
        return False


def sync_capabilities(application_id: str = _APPLICATION_ID) -> int:
    global _SYNCED
    if not tool_capability_enabled():
        return 0
    try:
        from jarvis.handlers import ensure_handlers_loaded
        from jarvis.handlers.registry import all_actions

        ensure_handlers_loaded()
        from aiplatform.applications.tool_capability.bridge import register_capabilities

        count = register_capabilities(application_id, all_actions())
        _SYNCED = count > 0
        return count
    except Exception as exc:
        logger.warning("Capability sync failed (continuing): %s", exc)
        return 0


def capability_invoke(
    legacy_call: Callable[..., dict[str, Any]],
    assistant: JarvisAssistant,
    action: str,
    params: dict[str, Any],
    message: str,
    *,
    streaming: bool = False,
    cancelled: bool = False,
) -> dict[str, Any]:
    if tool_capability_enabled() and not _SYNCED:
        sync_capabilities()
    start = time.perf_counter()
    permission_denied = False
    if tool_capability_enabled():
        try:
            from aiplatform.applications.tool_capability.bridge import (
                action_to_capability,
                check_permission_shadow,
            )
            from aiplatform.applications.tool_capability.metrics import record_permission_denial

            spec_obj = None
            try:
                from jarvis.handlers.registry import get_spec

                spec_obj = get_spec(action)
            except Exception:
                spec_obj = None
            spec = {
                "action": action,
                "module": spec_obj.module if spec_obj else None,
                "queue": spec_obj.queue if spec_obj else None,
                "description": spec_obj.description if spec_obj else "",
                "registered": bool(spec_obj and spec_obj.handler),
            }
            cap = action_to_capability(_APPLICATION_ID, spec)
            allowed, denied = check_permission_shadow(cap.permissions)
            if not allowed:
                permission_denied = True
                record_permission_denial(_APPLICATION_ID, cap.id)
                logger.debug(
                    "Platform permission shadow denial for %s (%s); legacy proceeds",
                    action,
                    denied,
                )
        except Exception as exc:
            logger.debug("Capability permission shadow skipped: %s", exc)
    success = True
    try:
        result = legacy_call(assistant, action, params, message)
    except Exception:
        success = False
        raise
    finally:
        if tool_capability_enabled():
            try:
                from aiplatform.applications.tool_capability.bridge import capability_id
                from aiplatform.applications.tool_capability.metrics import record_invocation

                elapsed_ms = (time.perf_counter() - start) * 1000
                record_invocation(
                    _APPLICATION_ID,
                    capability_id(_APPLICATION_ID, action),
                    elapsed_ms=elapsed_ms,
                    success=success,
                    streaming=streaming,
                    cancelled=cancelled,
                    permission_denied=permission_denied,
                )
            except Exception as exc:
                logger.debug("Capability invocation metrics skipped: %s", exc)
    return result
