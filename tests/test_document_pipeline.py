"""Document pipeline — extract, route, summarize."""

from pathlib import Path

import pytest

from jarvis.document_pipeline import (
    ParsedDocument,
    document_attachment_action,
    format_document_info,
    is_document_path,
    select_context,
)
from jarvis.router import _document_path_in_message, route
from jarvis.session import SessionContext


def test_is_document_path():
    assert is_document_path("warranty.pdf")
    assert is_document_path("letter.docx")
    assert not is_document_path("notes.txt")


def test_document_attachment_action():
    assert document_attachment_action("") == "summarize"
    assert document_attachment_action("Summarize this warranty PDF") == "summarize"
    assert document_attachment_action("What does clause 4 say about coverage?") == "query"
    assert document_attachment_action("Read all text in this document") == "vision"


def test_select_context_prefers_relevant_chunk():
    doc = ParsedDocument(
        path="/tmp/warranty.pdf",
        title="warranty",
        pages=[
            "Introduction and parties.",
            "Coverage includes parts and labor for twelve months from purchase date.",
            "Exclusions: cosmetic damage and misuse.",
        ],
        page_count=3,
        char_count=120,
    )
    ctx = select_context(doc, "coverage labor months", for_summary=False)
    assert "Coverage includes" in ctx
    assert "twelve months" in ctx


def test_format_document_info():
    doc = ParsedDocument(
        path="/tmp/x.pdf",
        title="Acme Warranty",
        pages=["Hello world text long enough to preview."],
        page_count=1,
        char_count=40,
        source="pymupdf",
    )
    text = format_document_info(doc)
    assert "Acme Warranty" in text
    assert "Pages: 1" in text


def test_document_path_in_message():
    assert _document_path_in_message('summarize data/documents/warranty.pdf') == "data/documents/warranty.pdf"


def test_route_document_attachment():
    intent = route(
        "Summarize this warranty PDF",
        SessionContext(),
        {"path": "/tmp/warranty.pdf", "kind": "document", "name": "warranty.pdf"},
    )
    assert intent["action"] == "document_summarize"


def test_route_document_follow_up(session=None):
    session = SessionContext(last_document_path="/tmp/warranty.pdf", last_module="document")
    intent = route("What is the coverage period?", session)
    assert intent["action"] == "document_query"


def test_save_upload_pdf_as_document(assistant, tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.assistant.UPLOAD_DIR", tmp_path)
    content = b"%PDF-1.4 minimal"
    result = assistant.save_upload("warranty.pdf", content)
    assert result["kind"] == "document"
    assert Path(result["path"]).exists()
    assert assistant.session.last_document_path == result["path"]


def test_document_summarize_handler(assistant, tmp_path, monkeypatch):
    pdf = tmp_path / "warranty.pdf"
    pdf.write_bytes(b"placeholder")
    monkeypatch.setattr(
        "jarvis.document_pipeline.parse_document",
        lambda path, use_cache=True: ParsedDocument(
            path=str(pdf),
            title="warranty",
            pages=["Coverage lasts twelve months."],
            page_count=1,
            char_count=28,
            source="test",
        ),
    )
    monkeypatch.setattr(
        "jarvis.document_pipeline.summarize_document",
        lambda doc: "Coverage is twelve months.",
    )
    result = assistant._document_summarize({"path": str(pdf)}, "summarize")
    assert result["ok"]
    assert "twelve months" in result["message"]
