"""Self-upgrade pipeline handlers — branch, test, merge on approval."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action(
    "self_upgrade_run",
    module="coding",
    description="Semi-auto self-upgrade: branch, change, test, report",
    queue="background",
)
def self_upgrade_run(assistant, params: dict, message: str) -> dict:
    from jarvis.self_upgrade import parse_self_upgrade_task, run_pipeline

    task = (params.get("task") or parse_self_upgrade_task(message) or "").strip()
    max_steps = int(params.get("max_steps") or 4)
    result = run_pipeline(assistant, task, max_steps=max_steps)
    if result.get("ok"):
        return ok(result["message"], module="coding", **{k: result[k] for k in result if k not in ("ok", "message")})
    return err(result.get("message", "Self-upgrade failed."), module="coding", **{k: result[k] for k in result if k not in ("ok", "message")})


@register_action("self_upgrade_merge", module="coding", description="Merge approved self-upgrade branch")
def self_upgrade_merge(assistant, params: dict, message: str) -> dict:
    from jarvis.self_upgrade import merge_force, merge_pipeline

    force = (params.get("force") or "").lower() in ("1", "true", "yes") or merge_force(message)
    result = merge_pipeline(assistant, force=force)
    if result.get("ok"):
        return ok(result["message"], module="coding", **{k: result[k] for k in result if k not in ("ok", "message")})
    return err(result.get("message", "Merge failed."), module="coding")


@register_action("self_upgrade_abort", module="coding", description="Abort self-upgrade branch")
def self_upgrade_abort(assistant, params: dict, message: str) -> dict:
    from jarvis.self_upgrade import abort_pipeline

    result = abort_pipeline(assistant)
    if result.get("ok"):
        return ok(result["message"], module="coding")
    return err(result.get("message", "Abort failed."), module="coding")
