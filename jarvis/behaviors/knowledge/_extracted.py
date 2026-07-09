"""Knowledge operations extracted from JarvisAssistant."""

from __future__ import annotations

import re
from typing import Any

from jarvis.response import err as _err, ok as _ok


class KnowledgeOperations:
    """Retrieval, documents, web search, and topic learning handlers."""


    @classmethod
    def load_document(cls, ctx, params: dict, message: str) -> tuple[dict | None, Any]:
        from jarvis.document_pipeline import parse_document

        path = ctx.resolve_document_path(params)
        if not path:
            return _err(
                "No document loaded. Attach a PDF or Word file, or put warranty docs in `data/documents/`.",
                module="document",
            ), None
        try:
            return None, parse_document(path)
        except Exception as e:
            return _err(str(e), module="document"), None

    @classmethod
    def document_info(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.document_pipeline import format_document_info

        err, doc = KnowledgeOperations.load_document(ctx, params, message)
        if err:
            return err
        ctx.session.note_module("document")
        return _ok(format_document_info(doc), module="document", document=doc.to_dict())

    @classmethod
    def document_summarize(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.document_pipeline import summarize_document

        err, doc = KnowledgeOperations.load_document(ctx, params, message)
        if err:
            return err
        ctx.session.note_module("document")
        try:
            summary = summarize_document(doc)
        except Exception as e:
            return _err(str(e), module="document")
        header = f"**{doc.title}** · {doc.page_count} page(s)\n\n"
        return _ok(header + summary, module="document", document=doc.to_dict())

    @classmethod
    def document_query(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.document_pipeline import answer_document

        err, doc = KnowledgeOperations.load_document(ctx, params, message)
        if err:
            return err
        question = (params.get("question") or message or "").strip()
        if not question:
            return _err("Ask a question about the loaded document.", module="document")
        ctx.session.note_module("document")
        try:
            answer = answer_document(doc, question)
        except Exception as e:
            return _err(str(e), module="document")
        return _ok(answer, module="document", document=doc.to_dict())

    @classmethod
    def document_search(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.documents_rag import format_hits_markdown, search

        query = (params.get("query") or message or "").strip()
        for prefix in (
            r"^search (?:my )?(?:documents?|document library|files in library)[:\s]*",
            r"^find in (?:my )?(?:documents?|document library)[:\s]*",
        ):
            query = re.sub(prefix, "", query, flags=re.I).strip()
        if not query:
            return _err("Say what to search for, e.g. **search documents warranty coverage**.", module="document")
        hits = search(query, limit=5)
        ctx.session.note_module("document")
        return _ok(format_hits_markdown(query, hits), module="document", type="document_search", hits=hits)

    @classmethod
    def learn_about(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.knowledge import learn_topic, parse_learn_topic
        from jarvis.profiles import web_search_disabled

        if web_search_disabled():
            return _err(
                "Web search is disabled (offline profile). Switch profile to learn new topics.",
                module="general",
            )

        topic = (params.get("topic") or parse_learn_topic(message) or "").strip()
        result = learn_topic(topic)
        if not result.get("ok"):
            return _err(result.get("message", "Could not learn that topic."), module="general")

        ctx.session.note_knowledge(result["slug"])
        ctx.session.note_module("general")

        header = (
            f"**Learned about:** {result['topic']}\n"
            f"Saved to `{result['relative_path']}` "
            f"({result['result_count']} web source(s)).\n\n"
            "I'll use this brief in future chats when the topic comes up. "
            "Say **remember key points** to store bullets in memory.\n\n---\n\n"
        )
        return _ok(
            header + result["body"],
            module="general",
            type="knowledge_learned",
            topic=result["topic"],
            slug=result["slug"],
            knowledge_path=result["relative_path"],
            key_points=result.get("key_points") or [],
            show_remember_key_points=True,
        )

    @classmethod
    def learn_remember(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.knowledge import load_brief, remember_key_points

        slug = (params.get("slug") or ctx.session.last_knowledge_slug or "").strip()
        if not slug:
            return _err("Nothing to remember yet — run `learn about: …` first.", module="memory")

        brief = load_brief(slug)
        if not brief:
            return _err(f"No saved brief for `{slug}`.", module="memory")

        stored = remember_key_points(ctx.memory, brief["topic"], slug=slug)
        if not stored:
            return _err("No key points found in that brief.", module="memory")

        ctx.refresh_system_prompt()
        lines = "\n".join(f"- {p}" for p in stored)
        return _ok(
            f"Stored **{len(stored)}** key point(s) about **{brief['topic']}** in memory:\n\n{lines}",
            module="memory",
            type="remembered",
            remembered_count=len(stored),
        )

    @classmethod
    def web_search(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.profiles import web_search_disabled
        if web_search_disabled():
            return _err("Web search is disabled (offline profile). Switch profile in the sidebar.", module="general")
        from jarvis import web_search
        query = params.get("query") or re.sub(r"^(search (the )?web for|web search)[:\s]+", "", message, flags=re.I).strip()
        if not query:
            return _err("What should I search for?")
        results = web_search.search(query)
        if not results:
            return _err(
                f"No web results for that query ({web_search.backend_name()}). "
                "Try again or run: `./venv/bin/pip install ddgs`",
                module="general",
            )
        answer = web_search.synthesize_answer(query, results)
        return _ok(answer, module="general", type="web_search", results=results)

    @classmethod
    def _resolve_learning_path(cls, ctx, params: dict, message: str) -> str:
        from jarvis.document_learning import (
            _document_path_in_message,
            parse_url_from_message,
            resolve_document_path,
        )

        raw = (params.get("path") or "").strip()
        if raw:
            return resolve_document_path(raw) or ctx.session.resolve_document(raw)
        path = ctx.session.resolve_document("")
        if path:
            return path
        path = _document_path_in_message(message)
        if path:
            return resolve_document_path(path)
        return ""

    @classmethod
    def ingest_document(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.document_learning import ingest_file, ingest_text, ingest_url, parse_url_from_message

        url = (params.get("url") or parse_url_from_message(message)).strip()
        if url:
            result = ingest_url(url)
            if not result.ok:
                return _err(result.message, module="memory")
            ctx.session.note_document(result.path)
            return _ok(result.message, module="memory", source=result.__dict__)

        text = (params.get("text") or "").strip()
        if text:
            title = (params.get("title") or "pasted document").strip()
            result = ingest_text(text, title=title, source_type=params.get("source_type") or "text")
            if not result.ok:
                return _err(result.message, module="memory")
            ctx.session.note_document(result.path)
            return _ok(result.message, module="memory", source=result.__dict__)

        path = cls._resolve_learning_path(ctx, params, message)
        if not path:
            return _err(
                "Attach a PDF, Word, text, or HTML file — or say **ingest https://example.com/doc**.",
                module="memory",
            )
        result = ingest_file(path)
        if not result.ok:
            return _err(result.message, module="memory")
        ctx.session.note_document(result.path)
        ctx.refresh_system_prompt()
        return _ok(result.message, module="memory", source=result.__dict__)

    @classmethod
    def learn_from_document(cls, ctx, params: dict, message: str) -> dict:
        from pathlib import Path

        from jarvis.document_learning import (
            format_learnings_markdown,
            learn_from_file,
            learn_from_text,
            learn_from_url,
            parse_url_from_message,
        )
        from jarvis.modules.vision import IMAGE_EXTENSIONS

        url = (params.get("url") or parse_url_from_message(message)).strip()
        if url:
            result = learn_from_url(ctx.memory, url)
            if not result.ok:
                return _err(result.message, module="memory")
            ctx.session.note_document(result.path)
            ctx.refresh_system_prompt()
            body = result.message + "\n\n" + format_learnings_markdown(
                [{"content": x} for x in result.lessons]
            )
            return _ok(body, module="memory", lessons=result.lessons)

        text = (params.get("text") or "").strip()
        if text:
            title = (params.get("title") or "OCR document").strip()
            result = learn_from_text(ctx.memory, text, title=title)
            if not result.ok:
                return _err(result.message, module="memory")
            ctx.refresh_system_prompt()
            body = result.message + "\n\n" + format_learnings_markdown(
                [{"content": x} for x in result.lessons]
            )
            return _ok(body, module="memory", lessons=result.lessons)

        path = cls._resolve_learning_path(ctx, params, message)
        use_ocr = bool(params.get("ocr"))
        if not path and ctx.session.last_image_path and use_ocr:
            path = ctx.session.last_image_path

        if path and Path(path).suffix.lower() in IMAGE_EXTENSIONS and (use_ocr or "ocr" in message.lower()):
            ocr_text = ctx.vision.ocr(path)
            if ocr_text.startswith("ERROR:"):
                return _err(ocr_text, module="memory")
            result = learn_from_text(ctx.memory, ocr_text, title=Path(path).stem)
            if not result.ok:
                return _err(result.message, module="memory")
            ctx.refresh_system_prompt()
            body = result.message + "\n\n" + format_learnings_markdown(
                [{"content": x} for x in result.lessons]
            )
            return _ok(body, module="memory", lessons=result.lessons)

        if not path:
            return _err(
                "Attach a document or say **learn from https://example.com/page**.",
                module="memory",
            )

        result = learn_from_file(ctx.memory, path)
        if not result.ok and use_ocr and Path(path).suffix.lower() in {".pdf"}:
            ocr_text = ctx.vision.ocr(path)
            if not ocr_text.startswith("ERROR:"):
                result = learn_from_text(ctx.memory, ocr_text, title=Path(path).stem)

        if not result.ok:
            return _err(result.message, module="memory")

        ctx.session.note_document(result.path)
        ctx.refresh_system_prompt()
        body = result.message + "\n\n" + format_learnings_markdown(
            [{"content": x} for x in result.lessons]
        )
        return _ok(body, module="memory", lessons=result.lessons)

    @classmethod
    def learn_from_url(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.document_learning import (
            format_learnings_markdown,
            learn_from_url,
            parse_url_from_message,
        )

        url = (params.get("url") or parse_url_from_message(message)).strip()
        if not url:
            return _err("Provide a URL, e.g. **learn from https://docs.example.com/guide**.", module="memory")
        result = learn_from_url(ctx.memory, url)
        if not result.ok:
            return _err(result.message, module="memory")
        ctx.session.note_document(result.path)
        ctx.refresh_system_prompt()
        body = result.message + "\n\n" + format_learnings_markdown(
            [{"content": x} for x in result.lessons]
        )
        return _ok(body, module="memory", lessons=result.lessons)

    @classmethod
    def document_learn_recall(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.document_learning import (
            format_learnings_markdown,
            learning_stats,
            list_document_learnings,
            list_sources,
            parse_document_learn_recall_query,
        )

        query = (params.get("query") or parse_document_learn_recall_query(message) or "").strip()
        entries = list_document_learnings(ctx.memory, query=query)
        stats = learning_stats()
        sources = list_sources(limit=15)
        if not entries and not sources:
            return _ok(
                "No document learning yet. Say **learn from this document** with an attachment, "
                "or **learn from https://…** for a web page.",
                module="memory",
            )
        title = f"Document lessons about **{query}**" if query else "Document learning"
        footer = (
            f"\n\n_{stats['learned_sources']} source(s), {stats['total_lessons']} lesson(s) "
            f"in `{stats['namespace']}`._"
        )
        return _ok(
            title + "\n\n" + format_learnings_markdown(entries, sources=sources) + footer,
            module="memory",
        )

    @classmethod
    def knowledge_research_run(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.knowledge_research_daily import (
            get_category,
            research_category,
            run_nightly_research,
        )

        force = (params.get("force") or "").lower() in ("1", "true", "yes") or "force" in message.lower()
        category = (params.get("category") or "").strip()
        if not category:
            if match := re.search(r"\bresearch\s+(ai news|ollama|zorin|dependencies)\b", message, re.I):
                category = match.group(1).lower().replace(" ", "_")
            elif match := re.search(
                r"\b(ai news|ollama updates?|zorin updates?|dependency updates?)\b", message, re.I
            ):
                raw = match.group(1).lower()
                category = {
                    "ai news": "ai_news",
                    "ollama": "ollama",
                    "ollama update": "ollama",
                    "ollama updates": "ollama",
                    "zorin": "zorin",
                    "zorin update": "zorin",
                    "zorin updates": "zorin",
                    "dependency update": "dependencies",
                    "dependency updates": "dependencies",
                }.get(raw, "")

        if category:
            cat = get_category(category.replace(" ", "_"))
            if not cat:
                return _err(f"Unknown research category: {category}", module="general")
            result = research_category(cat["id"], memory=ctx.memory, force=force)
            if not result.get("ok"):
                return _err(result.get("message", "Research failed."), module="general")
            if result.get("skipped"):
                return _ok(f"**{cat['title']}** already researched today.", module="general")
            body = result.get("message", "Done.")
            if result.get("remembered"):
                ctx.refresh_system_prompt()
                body += f"\n\n_Remembered {result['remembered']} key point(s)._"
            return _ok(body, module="general", **{k: result[k] for k in ("slug", "path") if k in result})

        results = run_nightly_research(memory=ctx.memory, force=force)
        if len(results) == 1 and results[0].get("skipped"):
            return _ok(results[0].get("message", "Already completed tonight."), module="general")
        updated = [item for item in results if item.get("ok") and not item.get("skipped")]
        if not updated:
            msg = results[0].get("message") if results else "No research categories ran."
            return _err(msg, module="general") if results and not results[0].get("ok") else _ok(msg, module="general")
        lines = [f"• **{item.get('title') or item.get('slug')}**" for item in updated]
        remembered = sum(item.get("remembered") or 0 for item in updated)
        body = f"Nightly knowledge research ({len(updated)} topic(s)):\n\n" + "\n".join(lines)
        body += "\n\nSummaries saved under `data/knowledge/research/`."
        if remembered:
            ctx.refresh_system_prompt()
            body += f"\n\n_Remembered {remembered} key point(s) into memory._"
        return _ok(body, module="general", results=updated)

    @classmethod
    def knowledge_research_list(cls, ctx, params: dict, message: str) -> dict:
        from jarvis.knowledge_research_daily import list_research_briefs

        items = list_research_briefs()
        if not items:
            return _ok(
                "No nightly research briefs yet. Say **run nightly knowledge research** or wait for the 11 PM job.",
                module="general",
            )
        lines = [
            f"• **{item['title']}** (`{item['slug']}`) — last {item.get('last_day') or item.get('updated', '')}"
            for item in items
        ]
        return _ok("**Saved research briefs**\n\n" + "\n".join(lines), module="general")
