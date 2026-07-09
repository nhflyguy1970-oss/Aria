"""Observation learning action handlers."""

from __future__ import annotations

from pathlib import Path

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok
from jarvis.vision_media import IMAGE_EXTENSIONS


def _format_result(result) -> dict:
    from jarvis.observation_learning import format_observations_markdown

    body = result.message
    if result.notes:
        body += "\n\n" + format_observations_markdown([{"content": n} for n in result.notes])
    return ok(body, module="memory", notes=result.notes, source_type=result.source_type)


@register_action("observe", module="memory", description="Observe text and create notes")
def observe(assistant, params: dict, message: str) -> dict:
    from jarvis.observation_learning import observe_text, parse_terminal_text

    text = (params.get("text") or parse_terminal_text(message) or "").strip()
    source_type = (params.get("source_type") or "terminal").strip().lower()
    title = (params.get("title") or source_type).strip()
    if not text:
        return err(
            "Paste output to observe, e.g. **observe terminal:**\n```\n$ pytest -q\n...\n```",
            module="memory",
        )
    result = observe_text(assistant.memory, text, source_type=source_type, title=title)
    if not result.ok:
        return err(result.message, module="memory")
    assistant.refresh_system_prompt()
    return _format_result(result)


@register_action("observe_log", module="memory", description="Observe log file tail")
def observe_log_action(assistant, params: dict, message: str) -> dict:
    from jarvis.observation_learning import observe_log

    lines = params.get("lines")
    try:
        result = observe_log(assistant.memory, message=message, lines=int(lines) if lines else None)
    except FileNotFoundError as exc:
        return err(str(exc), module="memory")
    if not result.ok:
        return err(result.message, module="memory")
    assistant.refresh_system_prompt()
    return _format_result(result)


@register_action("observe_terminal", module="memory", description="Observe terminal output")
def observe_terminal_action(assistant, params: dict, message: str) -> dict:
    from jarvis.observation_learning import observe_terminal, parse_terminal_text

    text = (params.get("text") or parse_terminal_text(message) or assistant.session.last_terminal_output).strip()
    if not text:
        return err(
            "No terminal output. Run a command first or paste output after **observe terminal:**",
            module="memory",
        )
    title = (params.get("title") or "terminal").strip()
    result = observe_terminal(assistant.memory, text, title=title)
    if not result.ok:
        return err(result.message, module="memory")
    assistant.refresh_system_prompt()
    return _format_result(result)


@register_action("observe_screenshot", module="memory", description="Observe screenshot/image")
def observe_screenshot_action(assistant, params: dict, message: str) -> dict:
    from jarvis.observation_learning import observe_screenshot

    path = (params.get("path") or assistant.session.resolve_image("") or "").strip()
    if not path:
        return err("Attach a screenshot or image to observe.", module="memory")
    if Path(path).suffix.lower() not in IMAGE_EXTENSIONS:
        return err("Observation needs an image file (png, jpg, webp, …).", module="memory")
    result = observe_screenshot(assistant.memory, assistant.vision, path)
    if not result.ok:
        return err(result.message, module="memory")
    assistant.session.note_image(path)
    assistant.refresh_system_prompt()
    return _format_result(result)


@register_action("observe_camera", module="memory", description="Capture camera and observe")
def observe_camera_action(assistant, params: dict, message: str) -> dict:
    from jarvis.observation_learning import observe_camera

    device = (params.get("device") or "").strip() or None
    result = observe_camera(assistant.memory, assistant.vision, device=device)
    if not result.ok:
        return err(result.message, module="memory")
    if result.path:
        assistant.session.note_image(result.path)
    assistant.refresh_system_prompt()
    return _format_result(result)


@register_action("observe_action_log", module="memory", description="Observe recent actions")
def observe_action_log_action(assistant, params: dict, message: str) -> dict:
    from jarvis.observation_learning import observe_action_log

    limit = int(params.get("limit") or 50)
    result = observe_action_log(assistant.memory, limit=limit)
    if not result.ok:
        return err(result.message, module="memory")
    assistant.refresh_system_prompt()
    return _format_result(result)


@register_action("observation_recall", module="memory", description="Recall observation notes")
def observation_recall(assistant, params: dict, message: str) -> dict:
    from jarvis.observation_learning import (
        format_observations_markdown,
        list_observation_sources,
        list_observations,
        observation_stats,
        parse_observation_recall_query,
    )

    query = (params.get("query") or parse_observation_recall_query(message) or "").strip()
    source_type = (params.get("source_type") or "").strip().lower() or None
    entries = list_observations(assistant.memory, query=query, source_type=source_type)
    stats = observation_stats()
    sources = list_observation_sources(limit=12)
    if not entries and not sources:
        return ok(
            "No observations yet. Try **observe the log**, **observe this screenshot**, "
            "or **observe terminal:** with pasted output.",
            module="memory",
        )
    title = f"Observations about **{query}**" if query else "Observation notes"
    footer = (
        f"\n\n_{stats['total_sources']} source(s), {stats['total_notes']} note(s) "
        f"in `{stats['namespace']}`._"
    )
    return ok(
        title + "\n\n" + format_observations_markdown(entries, sources=sources) + footer,
        module="memory",
    )
