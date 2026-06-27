"""ARIA self-diagnose and self-fix handlers."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action("aria_self_diagnose", module="coding", description="ARIA import + pytest health check")
def aria_self_diagnose_handler(assistant, params: dict, message: str) -> dict:
    from jarvis.aria_coder import aria_self_diagnose

    _ = message
    result = aria_self_diagnose(assistant.coding._base())
    if result.get("ok"):
        return ok("ARIA diagnostics pass.", module="coding", type="diagnose", **result)
    return err(
        "ARIA diagnostics failed — run **fix aria** to propose repairs.",
        module="coding",
        type="diagnose",
        **result,
    )


@register_action(
    "aria_self_fix",
    module="coding",
    description="Diagnose and fix ARIA via coding agent",
    queue="coding",
)
def aria_self_fix_handler(assistant, params: dict, message: str) -> dict:
    from jarvis.aria_coder import self_fix_aria

    apply = bool(params.get("apply")) or bool(
        __import__("os").environ.get("JARVIS_SELF_FIX_AUTO_APPLY", "").lower() in ("1", "true", "yes")
    )
    result = self_fix_aria(
        assistant,
        task=(params.get("task") or message or "").strip(),
        apply=apply,
        max_steps=int(params.get("max_steps") or 5),
    )
    if result.get("ok"):
        return ok(result.get("message", "Self-fix complete."), module="coding", type="self_fix", **{
            k: v for k, v in result.items() if k not in ("ok", "message")
        })
    return err(result.get("message", "Self-fix failed."), module="coding", type="self_fix", **{
        k: v for k, v in result.items() if k not in ("ok", "message")
    })
