# Source Generated with Decompyle++
# File: documents_rag.cpython-312.pyc (Python 3.12)

'''Semantic search over the document library (data/documents/).'''
from __future__ import annotations
import json
import logging
import re
from pathlib import Path
from jarvis import llm
from jarvis.config import DATA_DIR
from jarvis.document_pipeline import DOCUMENT_EXTENSIONS, DOCUMENTS_DIR, parse_document
log = logging.getLogger('jarvis.documents_rag')
INDEX_FILE = DATA_DIR / 'documents_index.json'
MAX_CHUNK = 1200
SIMILARITY_THRESHOLD = 0.22
_LAST_BUILD_WARNINGS: 'list[str]' = []

def last_index_warnings():
    return list(_LAST_BUILD_WARNINGS)


def _chunks(text = None, source = None, title = None):
    parts = []
    for i in range(0, len(text), MAX_CHUNK):
        chunk = text[i:i + MAX_CHUNK].strip()
        if not chunk:
            continue
        parts.append({
            'source': source,
            'title': title,
            'text': chunk })
    return parts


def _latest_document_mtime():
    if not DOCUMENTS_DIR.is_dir():
        return 0
    latest = 0
    for path in DOCUMENTS_DIR.rglob('*'):
        if path.is_file() or path.name.startswith('.'):
            continue
        if path.suffix.lower() not in DOCUMENT_EXTENSIONS:
            continue
        latest = max(latest, path.stat().st_mtime)
    return latest
    except OSError:
        continue


def index_needs_rebuild():
    if not INDEX_FILE.is_file():
        return True
    
    try:
        return _latest_document_mtime() > INDEX_FILE.stat().st_mtime
    except OSError:
        return True



def _read_index_file():
    if not INDEX_FILE.is_file():
        return None
    
    try:
        data = json.loads(INDEX_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, list):
            return data
        if None(data, dict) and isinstance(data.get('chunks'), list):
            return data['chunks']
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt documents index — rebuilding: %s', exc)
        exc = None
        del exc
        return None
        exc = None
        del exc



def _read_index_meta():
    if not INDEX_FILE.is_file():
        return { }
# WARNING: Decompyle incomplete


def _file_mtime(path = None):
    
    try:
        return path.stat().st_mtime
    except OSError:
        return 0



def _chunks_for_file(path = None):
    
    try:
        doc = parse_document(path)
        text = doc.full_text.strip()
        if not text:
            rel = str(path.relative_to(DOCUMENTS_DIR))
            log.warning('Skip empty document index %s', path)
            return ([], rel)
        rel = None(path.relative_to(DOCUMENTS_DIR))
        if not doc.title:
            doc.title
        return (_chunks(text, rel, path.stem), None)
    except Exception:
        exc = None
        rel = str(path.relative_to(DOCUMENTS_DIR)) if path.is_relative_to(DOCUMENTS_DIR) else path.name
        log.warning('Skip document index %s: %s', path, exc)
        del exc
        return None
        None = 
        del exc



def _write_index(chunks = None, file_mtimes = None):
    INDEX_FILE.parent.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(INDEX_FILE)
    payload = {
        'version': 2,
        'files': file_mtimes,
        'chunks': chunks }
    INDEX_FILE.write_text(json.dumps(payload, indent = 0), encoding = 'utf-8')


def build_index(*, force):
    pass
# WARNING: Decompyle incomplete


def _load_index(*, auto_refresh):
    if auto_refresh and index_needs_rebuild():
        return build_index(force = True)
    data = None()
# WARNING: Decompyle incomplete


def _keyword_search(query = None, chunks = None, limit = None):
    pass
# WARNING: Decompyle incomplete


def search(query = None, limit = None):
    chunks = _load_index()
    if not chunks:
        return []
# WARNING: Decompyle incomplete


def context_for_query(query = None, limit = None):
    warnings = []
    chunks = _load_index()
    if not chunks:
        warnings.append('Document library is empty — add files under data/documents/ or ingest a document.')
        return ('', warnings)
    if not None.embed_available():
        warnings.append('Embed model offline — using keyword document search.')
    hits = search(query, limit = limit)
    if not hits:
        return ('', warnings)
    ctx = '\n---\n'.join + (lambda .0: pass# WARNING: Decompyle incomplete
)(hits())
    return (ctx, warnings)


def format_hits_markdown(query = None, hits = None):
    if not hits:
        return f'''No document library matches for **{query}**.'''
    lines = [
        f'''{query}_''',
        '']
    for h in hits:
        if not h.get('title'):
            h.get('title')
        title = h.get('source', 'document')
        if not h.get('text'):
            h.get('text')
        excerpt = ''[:400].strip()
        lines.append(f'''- **{title}** — {excerpt}…''')
    lines.append('')
    lines.append('_Attach a file or say **summarize** with a path for full Q&A._')
    return '\n'.join(lines)

