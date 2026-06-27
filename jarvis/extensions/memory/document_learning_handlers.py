"""Document learning action handlers."""

from __future__ import annotations

from pathlib import Path

from jarvis.handlers.registry import register_action
from jarvis.modules.vision import IMAGE_EXTENSIONS
from jarvis.response import err, ok


def _resolve_path(assistant, params: dict, message: str) -> str:
    from jarvis.document_learning import (
        _document_path_in_message,
        parse_url_from_message,
        resolve_document_path,
    )

    raw = (params.get("path") or "").strip()
    if raw:
        return resolve_document_path(raw) or assistant.session.resolve_document(raw)
    path = assistant.session.resolve_document("")
    if path:
        return path
    path = _document_path_in_message(message)
    if path:
        return resolve_document_path(path)
    return ""


@register_action("ingest_document", module="memory", description="Add document to library")
def ingest_document(assistant, params: dict, message: str) -> dict:
    from jarvis.document_learning import ingest_file, ingest_text, ingest_url, parse_url_from_message

    url = (params.get("url") or parse_url_from_message(message)).strip()
    if url:
        result = ingest_url(url)
        if not result.ok:
            return err(result.message, module="memory")
        assistant.session.note_document(result.path)
        return ok(result.message, module="memory", source=result.__dict__)

    text = (params.get("text") or "").strip()
    if text:
        title = (params.get("title") or "pasted document").strip()
        result = ingest_text(text, title=title, source_type=params.get("source_type") or "text")
        if not result.ok:
            return err(result.message, module="memory")
        assistant.session.note_document(result.path)
        return ok(result.message, module="memory", source=result.__dict__)

    path = _resolve_path(assistant, params, message)
    if not path:
        return err(
            "Attach a PDF, Word, text, or HTML file — or say **ingest https://example.com/doc**.",
            module="memory",
        )
    result = ingest_file(path)
    if not result.ok:
        return err(result.message, module="memory")
    assistant.session.note_document(result.path)
    assistant.refresh_system_prompt()
    return ok(result.message, module="memory", source=result.__dict__)


@register_action("learn_from_document", module="memory", description="Learn from a document")
def learn_from_document(assistant, params: dict, message: str) -> dict:
    from jarvis.document_learning import (
        format_learnings_markdown,
        learn_from_file,
        learn_from_text,
        learn_from_url,
        parse_url_from_message,
    )

    url = (params.get("url") or parse_url_from_message(message)).strip()
    if url:
        result = learn_from_url(assistant.memory, url)
        if not result.ok:
            return err(result.message, module="memory")
        assistant.session.note_document(result.path)
        assistant.refresh_system_prompt()
        body = result.message + "\n\n" + format_learnings_markdown(
            [{"content": x} for x in result.lessons]
        )
        return ok(body, module="memory", lessons=result.lessons)

    text = (params.get("text") or "").strip()
    if text:
        title = (params.get("title") or "OCR document").strip()
        result = learn_from_text(assistant.memory, text, title=title)
        if not result.ok:
            return err(result.message, module="memory")
        assistant.refresh_system_prompt()
        body = result.message + "\n\n" + format_learnings_markdown(
            [{"content": x} for x in result.lessons]
        )
        return ok(body, module="memory", lessons=result.lessons)

    path = _resolve_path(assistant, params, message)
    use_ocr = bool(params.get("ocr"))

    if not path and assistant.session.last_image_path and use_ocr:
        path = assistant.session.last_image_path

    if path and Path(path).suffix.lower() in IMAGE_EXTENSIONS and (use_ocr or "ocr" in message.lower()):
        ocr_text = assistant.vision.ocr(path)
        if ocr_text.startswith("ERROR:"):
            return err(ocr_text, module="memory")
        result = learn_from_text(assistant.memory, ocr_text, title=Path(path).stem)
        if not result.ok:
            return err(result.message, module="memory")
        assistant.refresh_system_prompt()
        body = result.message + "\n\n" + format_learnings_markdown(
            [{"content": x} for x in result.lessons]
        )
        return ok(body, module="memory", lessons=result.lessons)

    if not path:
        return err(
            "Attach a document or say **learn from https://example.com/page**.",
            module="memory",
        )

    result = learn_from_file(assistant.memory, path)
    if not result.ok and use_ocr and Path(path).suffix.lower() in {".pdf"}:
        ocr_text = assistant.vision.ocr(path)
        if not ocr_text.startswith("ERROR:"):
            result = learn_from_text(assistant.memory, ocr_text, title=Path(path).stem)

    if not result.ok:
        return err(result.message, module="memory")

    assistant.session.note_document(result.path)
    assistant.refresh_system_prompt()
    body = result.message + "\n\n" + format_learnings_markdown(
        [{"content": x} for x in result.lessons]
    )
    return ok(body, module="memory", lessons=result.lessons)


@register_action("learn_from_url", module="memory", description="Learn from a web page")
def learn_from_url_action(assistant, params: dict, message: str) -> dict:
    from jarvis.document_learning import learn_from_url, parse_url_from_message

    url = (params.get("url") or parse_url_from_message(message)).strip()
    if not url:
        return err("Provide a URL, e.g. **learn from https://docs.example.com/guide**.", module="memory")
    result = learn_from_url(assistant.memory, url)
    if not result.ok:
        return err(result.message, module="memory")
    assistant.session.note_document(result.path)
    assistant.refresh_system_prompt()
    from jarvis.document_learning import format_learnings_markdown

    body = result.message + "\n\n" + format_learnings_markdown(
        [{"content": x} for x in result.lessons]
    )
    return ok(body, module="memory", lessons=result.lessons)


@register_action("document_learn_recall", module="memory", description="Recall document lessons")
def document_learn_recall(assistant, params: dict, message: str) -> dict:
    from jarvis.document_learning import (
        format_learnings_markdown,
        learning_stats,
        list_document_learnings,
        list_sources,
        parse_document_learn_recall_query,
    )

    query = (params.get("query") or parse_document_learn_recall_query(message) or "").strip()
    entries = list_document_learnings(assistant.memory, query=query)
    stats = learning_stats()
    sources = list_sources(limit=15)
    if not entries and not sources:
        return ok(
            "No document learning yet. Say **learn from this document** with an attachment, "
            "or **learn from https://…** for a web page.",
            module="memory",
        )
    title = f"Document lessons about **{query}**" if query else "Document learning"
    footer = (
        f"\n\n_{stats['learned_sources']} source(s), {stats['total_lessons']} lesson(s) "
        f"in `{stats['namespace']}`._"
    )
    return ok(
        title + "\n\n" + format_learnings_markdown(entries, sources=sources) + footer,
        module="memory",
    )
