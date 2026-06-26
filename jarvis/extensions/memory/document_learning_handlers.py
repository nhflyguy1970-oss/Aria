# Source Generated with Decompyle++
# File: document_learning_handlers.cpython-312.pyc (Python 3.12)

'''Document learning action handlers.'''
from __future__ import annotations
import os
import re
import tempfile
from pathlib import Path
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok
from jarvis.vision_media import IMAGE_EXTENSIONS, extract_pdf_page

def _ocr_max_pages():
    
    try:
        return max(1, int(os.getenv('JARVIS_DOCUMENT_OCR_MAX_PAGES', '5')))
    except ValueError:
        return 5



def _message_requests_ocr(message = None, params = None):
    if params.get('ocr'):
        return True
    if not message:
        message
    lower = ''.lower()
    return bool(re.search('\\b(ocr|scanned|scan(ned)?|image[- ]only)\\b', lower))


def _ocr_pdf_pages(assistant = None, path = None, *, max_pages):
    '''Render PDF page images and OCR each page; return combined text.'''
    p = Path(path)
    content = p.read_bytes()
# WARNING: Decompyle incomplete


def _resolve_path(assistant = None, params = None, message = None):
    _document_path_in_message = _document_path_in_message
    parse_url_from_message = parse_url_from_message
    resolve_document_path = resolve_document_path
    import jarvis.document_learning
    if not params.get('path'):
        params.get('path')
    raw = ''.strip()
    if raw:
        if not resolve_document_path(raw):
            resolve_document_path(raw)
        return assistant.session.resolve_document(raw)
    path = None.session.resolve_document('')
    if path:
        return path
    path = _document_path_in_message(message)
    if path:
        return resolve_document_path(path)

ingest_document = (lambda assistant = None, params = None, message = register_action('ingest_document', module = 'memory', extension = 'memory', description = 'Add document to library'): ingest_file = ingest_fileingest_text = ingest_textingest_url = ingest_urlparse_url_from_message = parse_url_from_messageimport jarvis.document_learningif not params.get('url'):
params.get('url')url = parse_url_from_message(message).strip()if url:
result = ingest_url(url)if not result.ok:
err(result.message, module = 'memory')None.session.note_document(result.path)ok(result.message, module = 'memory', source = result.__dict__)if not None.get('text'):
None.get('text')text = ''.strip()if text:
if not params.get('title'):
params.get('title')title = 'pasted document'.strip()if not params.get('source_type'):
params.get('source_type')result = ingest_text(text, title = title, source_type = 'text')if not result.ok:
err(result.message, module = 'memory')None.session.note_document(result.path)ok(result.message, module = 'memory', source = result.__dict__)path = None(assistant, params, message)if not path:
err('Attach a PDF, Word, text, or HTML file — or say **ingest https://example.com/doc**.', module = 'memory')result = ingest_file(path)if not result.ok:
err(result.message, module = 'memory')None.session.note_document(result.path)assistant.refresh_system_prompt()ok(result.message, module = 'memory', source = result.__dict__))()
learn_from_document = (lambda assistant = None, params = None, message = register_action('learn_from_document', module = 'memory', extension = 'memory', description = 'Learn from a document'): format_learnings_markdown = format_learnings_markdownlearn_from_file = learn_from_filelearn_from_text = learn_from_textlearn_from_url = learn_from_urllow_text_warning = low_text_warningparse_document = parse_documentparse_url_from_message = parse_url_from_messageimport jarvis.document_learningif not params.get('url'):
params.get('url')url = parse_url_from_message(message).strip()# WARNING: Decompyle incomplete
)()
learn_from_url_action = (lambda assistant = None, params = None, message = register_action('learn_from_url', module = 'memory', extension = 'memory', description = 'Learn from a web page'): learn_from_url = learn_from_urlparse_url_from_message = parse_url_from_messageimport jarvis.document_learningif not params.get('url'):
params.get('url')url = parse_url_from_message(message).strip()if not url:
err('Provide a URL, e.g. **learn from https://docs.example.com/guide**.', module = 'memory')result = learn_from_url(assistant.memory, url)if not result.ok:
err(result.message, module = 'memory')None.session.note_document(result.path)assistant.refresh_system_prompt()format_learnings_markdown = format_learnings_markdownimport jarvis.document_learning# WARNING: Decompyle incomplete
)()
document_learn_recall = (lambda assistant = None, params = None, message = register_action('document_learn_recall', module = 'memory', extension = 'memory', description = 'Recall document lessons'): format_learnings_markdown = format_learnings_markdownlearning_stats = learning_statslist_document_learnings = list_document_learningslist_sources = list_sourcesparse_document_learn_recall_query = parse_document_learn_recall_queryimport jarvis.document_learningif not params.get('query'):
params.get('query')if not parse_document_learn_recall_query(message):
parse_document_learn_recall_query(message)query = ''.strip()entries = list_document_learnings(assistant.memory, query = query)stats = learning_stats()sources = list_sources(limit = 15)if not entries and sources:
ok('No document learning yet. Say **learn from this document** with an attachment, or **learn from https://…** for a web page.', module = 'memory')title = f'''Document lessons about **{query}**''' if None else 'Document learning'footer = f'''\n\n_{stats['learned_sources']} source(s), {stats['total_lessons']} lesson(s) in `{stats['namespace']}`._'''ok(title + '\n\n' + format_learnings_markdown(entries, sources = sources) + footer, module = 'memory'))()
