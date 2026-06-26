# Source Generated with Decompyle++
# File: document_learning.cpython-312.pyc (Python 3.12)

'''Document learning — ingest files/URLs/OCR text and teach ARIA durable lessons.'''
from __future__ import annotations
import hashlib
import json
import logging
import re
import shutil
import urllib.error as urllib
import urllib.request as urllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from jarvis import llm
from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.document_pipeline import DOCUMENT_EXTENSIONS, DOCUMENTS_DIR, ParsedDocument, documents_dir, html_to_text, low_text_warning, parse_document, parse_text_content, _title_from_html
log = logging.getLogger('jarvis.document_learning')
LEARNING_NAMESPACE = 'learned'
DOCUMENT_LEARN_TAG = 'document-learn'
REGISTRY_FILE = DATA_DIR / 'document_learning.json'
_MAX_EXTRACT_CHARS = int(__import__('os').getenv('JARVIS_DOC_LEARN_CHARS', '14000'))
_MAX_FACTS = int(__import__('os').getenv('JARVIS_DOC_LEARN_FACTS', '8'))
_URL_RE = re.compile('https?://[^\\s<>\\"\']+', re.I)
_LEARN_DOC = re.compile('\\b(learn from|study|read and learn|memorize|teach yourself from|ingest and learn)\\b', re.I)
_INGEST_DOC = re.compile('\\b(ingest (?:this )?(?:doc|document|file|pdf|page)|add (?:this )?to (?:my )?(?:document )?library)\\b', re.I)
_LEARN_RECALL = re.compile('\\b(what did i learn from (?:documents?|files?|pdfs?|the library)|what have you learned from (?:documents?|my files?)|document learning recall)\\b', re.I)
_LEARN_RECALL_QUERY = re.compile('(?:what did i learn from (?:documents?|files?|pdfs?)(?: about)?|what have you learned from (?:documents?|my files?)(?: about)?|document learning recall(?: about)?)\\s+(.+)$', re.I)
IngestResult = <NODE:12>()
LearnResult = <NODE:12>()

def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _slugify(text = None):
    if not text:
        text
    s = re.sub('[^\\w\\s-]', '', ''.lower())
    s = re.sub('[\\s_]+', '-', s).strip('-')
    if not s[:60]:
        s[:60]
    return 'document'


def _load_registry():
    if not REGISTRY_FILE.is_file():
        return {
            'sources': [] }
    
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict) and isinstance(data.get('sources'), list):
            return data
        return {
            None: [] }
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt document learning registry: %s', exc)
        exc = None
        del exc
        return {
            'sources': [] }
        exc = None
        del exc



def _save_registry(data = None):
    REGISTRY_FILE.parent.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(REGISTRY_FILE)
    REGISTRY_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _source_id(title = None, path = None, url = None):
    raw = f'''{title}|{path}|{url}'''
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _register_source(*, title, path, source_type, chars, url, learned, lessons):
    data = _load_registry()
    sid = _source_id(title, path, url)
    entry = {
        'id': sid,
        'title': title,
        'path': path,
        'type': source_type,
        'url': url,
        'chars': chars,
        'ingested_at': _utc_now(),
        'learned_at': _utc_now() if learned else '',
        'lessons': lessons }
# WARNING: Decompyle incomplete


def list_sources(*, limit):
    return list(_load_registry().get('sources', []))[:limit]


def learning_stats():
    sources = list_sources(limit = 500)
# WARNING: Decompyle incomplete


def resolve_document_path(raw = None):
    '''Resolve a document path against project, data, uploads, and library.'''
    upload_dir = DATA_DIR / 'uploads'
    if not raw:
        raw
    text = ''.strip()
    if not text:
        return ''
    p = Path(text)
    if p.is_absolute() and p.exists():
        return str(p)
    for base in (None, DATA_DIR, upload_dir, documents_dir()):
        candidate = (base / text).resolve()
        if not candidate.exists():
            continue
        
        return (None, DATA_DIR, upload_dir, documents_dir()), str(candidate)
    if resolved.exists():
        return str(resolved)
    return p.expanduser()


def parse_url_from_message(message = None):
    if not message:
        message
    m = _URL_RE.search(''.strip())
    if m:
        return m.group(0).rstrip('.,);]')


def is_learn_from_document(message = None):
    if not message:
        message
    return bool(_LEARN_DOC.search(''.strip()))


def is_ingest_document(message = None):
    if not message:
        message
    return bool(_INGEST_DOC.search(''.strip()))


def is_document_learn_recall(message = None):
    if not message:
        message
    return bool(_LEARN_RECALL.search(''.strip()))


def parse_document_learn_recall_query(message = None):
    if not message:
        message
    m = _LEARN_RECALL_QUERY.search(''.strip())
    if m:
        return m.group(1).strip().rstrip('?.!')
    return None.rstrip('?.!')


def _document_path_in_message(message = None):
    exts = (lambda .0: pass# WARNING: Decompyle incomplete
)(sorted(DOCUMENT_EXTENSIONS)())
    m = re.search(f'''\\b(?:file|document|pdf|attached|open|in)\\s+[`\'\\"]?([\\w./-]+\\.(?:{exts}))[`\'\\"]?''', message, re.I)
    if re.search(f'''\\b(?:file|document|pdf|attached|open|in)\\s+[`\'\\"]?([\\w./-]+\\.(?:{exts}))[`\'\\"]?''', message, re.I):
        return m.group(1)
    paths = '|'.join.findall(f'''[`\'\\"]?([\\w./-]+\\.(?:{exts}))[`\'\\"]?''', message, re.I)
    if paths:
        return paths[-1]


def _copy_to_library(src = None):
    root = documents_dir()
    dest = root / src.name
    if dest.resolve() == src.resolve():
        return src
    if None.exists():
        suffix = dest.suffix
        stem = dest.stem
        for n in range(2, 1000):
            candidate = root / f'''{stem}_{n}{suffix}'''
            if candidate.exists():
                continue
            dest = candidate
            range(2, 1000)
    shutil.copy2(src, dest)
    return dest


def _save_text_to_library(text = None, *, title, subdir):
    root = documents_dir()
    folder = root / subdir if subdir else root
    folder.mkdir(parents = True, exist_ok = True)
    slug = _slugify(title)
    dest = folder / f'''{slug}.txt'''
    if dest.exists():
        for n in range(2, 1000):
            candidate = folder / f'''{slug}_{n}.txt'''
            if candidate.exists():
                continue
            dest = candidate
            range(2, 1000)
    dest.write_text(text, encoding = 'utf-8')
    return dest


def _reindex_library():
    build_index = build_index
    import jarvis.documents_rag
    return len(build_index(force = True))


def _source_type_for_path(path = None):
    ext = path.suffix.lower().lstrip('.')
    if not ext:
        ext
    return 'file'


def ingest_file(path = None, *, copy_to_library):
    raw = Path(path).expanduser()
    if not resolve_document_path(str(raw)):
        resolve_document_path(str(raw))
    resolved = str(raw)
    p = Path(resolved)
    if not p.exists():
        return IngestResult(False, p.name, str(p), 'file', message = f'''File not found: {p}''')
    
    try:
        if copy_to_library and p.suffix.lower() in DOCUMENT_EXTENSIONS:
            stored = _copy_to_library(p)
            doc = parse_document(stored)
            stored_path = str(stored)
        else:
            doc = parse_document(p)
            stored_path = str(p)
        sid = _register_source(title = doc.title, path = stored_path, source_type = _source_type_for_path(Path(stored_path)), chars = doc.char_count)
        chunks = _reindex_library()
        maybe_auto_learn_document = maybe_auto_learn_document
        import jarvis.document_brain_feed
        maybe_auto_learn_document(None, stored_path, title = doc.title)
        return IngestResult(True, doc.title, stored_path, _source_type_for_path(Path(stored_path)), chars = doc.char_count, message = f'''Indexed **{doc.title}** ({doc.char_count:,} chars, {chunks} chunks).''', source_id = sid)
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def fetch_web_page(url = None):
    '''Return (title, plain text) from a URL.'''
    req = urllib.request.Request(url, headers = {
        'User-Agent': 'Jarvis/1.0 (+document-learning)' })
# WARNING: Decompyle incomplete


def ingest_url(url = None):
    if not url:
        url
    url = ''.strip()
    if not url:
        return IngestResult(False, '', '', 'web', message = 'URL required.')
    
    try:
        (title, text) = fetch_web_page(url)
        if not text.strip():
            return IngestResult(False, title, '', 'web', url = url, message = 'No text extracted from page.')
        dest = None(text, title = title, subdir = 'web')
        doc = parse_document(dest)
        sid = _register_source(title = doc.title, path = str(dest), source_type = 'web', chars = doc.char_count, url = url)
        chunks = _reindex_library()
        maybe_auto_learn_document = maybe_auto_learn_document
        import jarvis.document_brain_feed
        maybe_auto_learn_document(None, str(dest), title = doc.title)
        return IngestResult(True, doc.title, str(dest), 'web', chars = doc.char_count, url = url, message = f'''Saved web page **{doc.title}** ({doc.char_count:,} chars, {chunks} chunks).''', source_id = sid)
    except ValueError:
        exc = None
        del exc
        return None
        None = 
        del exc



def ingest_text(text = None, *, title, source_type):
    if not text:
        text
    cleaned = ''.strip()
    if not cleaned:
        return IngestResult(False, title, '', source_type, message = 'No text to ingest.')
    subdir = 'ocr' if None == 'ocr' else 'text'
    dest = _save_text_to_library(cleaned, title = title, subdir = subdir)
    doc = parse_document(dest)
    sid = _register_source(title = doc.title, path = str(dest), source_type = source_type, chars = doc.char_count)
    chunks = _reindex_library()
    maybe_auto_learn_document = maybe_auto_learn_document
    import jarvis.document_brain_feed
    maybe_auto_learn_document(None, str(dest), title = doc.title)
    return IngestResult(True, doc.title, str(dest), source_type, chars = doc.char_count, message = f'''Saved **{doc.title}** ({doc.char_count:,} chars, {chunks} chunks).''', source_id = sid)


def extract_document_learnings(text = None, *, title, max_facts):
    '''Use LLM to pull durable facts/procedures from document text.'''
    if not text:
        text
    excerpt = ''.strip()
    if not excerpt:
        return []
    if None(excerpt) > _MAX_EXTRACT_CHARS:
        excerpt = excerpt[:_MAX_EXTRACT_CHARS] + '…'
# WARNING: Decompyle incomplete


def _store_lessons(memory = None, facts = None, *, title, source_type):
    TeachIntent = TeachIntent
    apply_explicit_teaching = apply_explicit_teaching
    infer_teaching_kind = infer_teaching_kind
    import jarvis.explicit_teaching
    stored = []
    src_tag = f'''doc-source:{_slugify(title)[:32]}'''
    for fact in facts:
        kind = infer_teaching_kind(fact)
        intent = TeachIntent(kind = kind, content = fact)
        result = apply_explicit_teaching(memory, intent, namespace = LEARNING_NAMESPACE, extra_tags = [
            DOCUMENT_LEARN_TAG,
            src_tag,
            f'''doc-type:{source_type}'''])
        stored.append(result.content)
    return stored
    except ValueError:
        exc = None
        log.debug('Skip lesson: %s', exc)
        exc = None
        del exc
        continue
        exc = None
        del exc


def learn_from_document(memory = None, doc = None, *, source_type, url, allow_low_text):
    warn = low_text_warning(doc)
    if not warn and allow_low_text:
        return LearnResult(False, doc.title, doc.path, source_type, message = warn, url = url)
    facts = None(doc.full_text, title = doc.title)
    if not facts:
        return LearnResult(False, doc.title, doc.path, source_type, message = 'Could not extract lessons from this document.', url = url)
    lessons = None(memory, facts, title = doc.title, source_type = source_type)
    sid = _register_source(title = doc.title, path = doc.path, source_type = source_type, chars = doc.char_count, url = url, learned = True, lessons = len(lessons))
    return LearnResult(True, doc.title, doc.path, source_type, lessons = lessons, message = f'''Learned **{len(lessons)}** lesson(s) from **{doc.title}**.''', url = url, source_id = sid)


def _in_library(p = None):
    
    try:
        return p.resolve().is_relative_to(documents_dir().resolve())
    except (ValueError, OSError):
        return False



def learn_from_file(memory = None, path = None, *, ingest, ocr_fallback, ocr_fn):
    '''Learn from a file. Skips re-copy if already under data/documents/. Optional OCR for scans.'''
    if not resolve_document_path(str(path)):
        resolve_document_path(str(path))
    resolved = str(path)
    p = Path(resolved)
    if not p.is_file():
        return LearnResult(False, p.name, str(path), 'file', message = f'''Document not found: {path}''')
# WARNING: Decompyle incomplete


def learn_from_url(memory = None, url = None):
    ing = ingest_url(url)
    if not ing.ok:
        return LearnResult(False, ing.title, ing.path, 'web', message = ing.message, url = url)
    doc = None(ing.path)
    result = learn_from_document(memory, doc, source_type = 'web', url = url)
    return result


def learn_from_text(memory = None, text = None, *, title):
    ing = ingest_text(text, title = title, source_type = 'ocr')
    if not ing.ok:
        return LearnResult(False, title, '', 'ocr', message = ing.message)
    doc = None(ing.path)
    return learn_from_document(memory, doc, source_type = 'ocr', allow_low_text = True)


def list_document_learnings(memory = None, *, query, limit):
    entries = memory.list_entries(entry_type = 'teaching', namespace = LEARNING_NAMESPACE)
# WARNING: Decompyle incomplete


def document_learning_context_for_chat(memory = None, message = None, *, limit):
    pass
# WARNING: Decompyle incomplete


def format_learnings_markdown(entries = None, *, sources):
    lines = []
    if sources:
        lines.append('**Ingested sources**')
        for s in sources[:15]:
            if not s.get('title'):
                s.get('title')
            title = s.get('path', 'document')
            typ = s.get('type', 'file')
            if not s.get('lessons'):
                s.get('lessons')
            lessons = 0
            learned = 'learned' if s.get('learned_at') else 'indexed only'
            lines.append(f'''- **{title}** ({typ}, {lessons} lessons, {learned})''')
        lines.append('')
    if not entries:
        lines.append('_No document lessons stored yet._')
        return '\n'.join(lines)
    None.append('**Lessons from documents**')
    for e in entries:
        lines.append(f'''• {e.get('content', '')}''')
    return '\n'.join(lines)

