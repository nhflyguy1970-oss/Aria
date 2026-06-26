# Source Generated with Decompyle++
# File: test_document_learning.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Document learning tests.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.document_learning import DOCUMENT_LEARN_TAG, LEARNING_NAMESPACE, extract_document_learnings, ingest_file, ingest_text, is_learn_from_document, learn_from_text, list_document_learnings, parse_url_from_message
from jarvis.document_pipeline import html_to_text, parse_text_content
from jarvis.modules.memory import MemoryStore
store = (lambda data_dir, monkeypatch: monkeypatch.delenv('JARVIS_GRAPH_BACKEND', raising = False)monkeypatch.delenv('JARVIS_VECTOR_BACKEND', raising = False)monkeypatch.setattr('jarvis.llm.embed_available', (lambda : False))
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
0.1,
0.2]))
    return MemoryStore(path = data_dir / 'memory.json')
)()

def test_html_to_text():
    html = '<html><head><title>Guide</title></head><body><p>Hello <b>world</b></p></body></html>'
    text = html_to_text(html)
    @py_assert1 = []
    @py_assert2 = 'Hello'
    @py_assert4 = @py_assert2 in text
    @py_assert0 = @py_assert4
    if @py_assert4:
        @py_assert9 = 'world'
        @py_assert11 = @py_assert9 in text
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete


def test_parse_text_content():
    doc = parse_text_content('Line one.\nLine two.', title = 'Test doc', source = 'ocr')
    @py_assert1 = doc.char_count
    @py_assert4 = 0
    @py_assert3 = @py_assert1 > @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('>',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.char_count\n} > %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(doc) if 'doc' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(doc) else 'doc',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = doc.title
    @py_assert4 = 'Test doc'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.title\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(doc) if 'doc' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(doc) else 'doc',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert0 = 'Line one'
    @py_assert4 = doc.full_text
    @py_assert2 = @py_assert0 in @py_assert4
    if not @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py5)s\n{%(py5)s = %(py3)s.full_text\n}',), (@py_assert0, @py_assert4)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(doc) if 'doc' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(doc) else 'doc',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None


def test_is_learn_from_document():
    @py_assert1 = 'learn from this PDF please'
    @py_assert3 = is_learn_from_document(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_learn_from_document) if 'is_learn_from_document' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_learn_from_document) else 'is_learn_from_document',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = 'study the attached warranty doc'
    @py_assert3 = is_learn_from_document(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_learn_from_document) if 'is_learn_from_document' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_learn_from_document) else 'is_learn_from_document',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = 'learn about Python'
    @py_assert3 = is_learn_from_document(@py_assert1)
    @py_assert5 = not @py_assert3
    if not @py_assert5:
        @py_format6 = 'assert not %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_learn_from_document) if 'is_learn_from_document' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_learn_from_document) else 'is_learn_from_document',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_parse_url():
    @py_assert1 = 'learn from https://example.com/guide.html'
    @py_assert3 = parse_url_from_message(@py_assert1)
    @py_assert6 = 'https://example.com/guide.html'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_url_from_message) if 'parse_url_from_message' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_url_from_message) else 'parse_url_from_message',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_ingest_text_and_file(data_dir, monkeypatch, tmp_path):
    monkeypatch.setattr('jarvis.document_learning.DOCUMENTS_DIR', data_dir / 'documents')
    monkeypatch.setattr('jarvis.document_pipeline.DOCUMENTS_DIR', data_dir / 'documents')
    monkeypatch.setattr('jarvis.document_pipeline.CACHE_DIR', data_dir / 'documents' / '.cache')
    monkeypatch.setattr('jarvis.documents_rag.DOCUMENTS_DIR', data_dir / 'documents')
    monkeypatch.setattr('jarvis.documents_rag.INDEX_FILE', data_dir / 'documents_index.json')
    monkeypatch.setattr('jarvis.document_learning.REGISTRY_FILE', data_dir / 'document_learning.json')
    monkeypatch.setattr('jarvis.llm.embed_available', (lambda : False))
    result = ingest_text('Important warranty covers labor for 12 months.', title = 'warranty-notes')
    @py_assert1 = result.ok
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.ok\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    @py_assert2 = result.path
    @py_assert4 = Path(@py_assert2)
    @py_assert6 = @py_assert4.is_file
    @py_assert8 = @py_assert6()
    if not @py_assert8:
        @py_format10 = 'assert %(py9)s\n{%(py9)s = %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s.path\n})\n}.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(Path) if 'Path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(Path) else 'Path',
            'py1': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    src = tmp_path / 'manual.txt'
    src.write_text('Chapter 1: Setup instructions.', encoding = 'utf-8')
    ing = ingest_file(src)
    @py_assert1 = ing.ok
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.ok\n}' % {
            'py0': @pytest_ar._saferepr(ing) if 'ing' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ing) else 'ing',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None


def test_extract_and_learn(monkeypatch, store, data_dir):
    monkeypatch.setattr('jarvis.document_learning.DOCUMENTS_DIR', data_dir / 'documents')
    monkeypatch.setattr('jarvis.document_pipeline.DOCUMENTS_DIR', data_dir / 'documents')
    monkeypatch.setattr('jarvis.document_pipeline.CACHE_DIR', data_dir / 'documents' / '.cache')
    monkeypatch.setattr('jarvis.documents_rag.DOCUMENTS_DIR', data_dir / 'documents')
    monkeypatch.setattr('jarvis.documents_rag.INDEX_FILE', data_dir / 'documents_index.json')
    monkeypatch.setattr('jarvis.document_learning.REGISTRY_FILE', data_dir / 'document_learning.json')
    monkeypatch.setattr('jarvis.llm.ask', (lambda : '{"facts": ["The warranty covers parts for twelve months.", "Claims must be filed within 30 days."]}'))
    facts = extract_document_learnings('Warranty text here.', title = 'Warranty')
    @py_assert2 = len(facts)
    @py_assert5 = 2
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(facts) if 'facts' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(facts) else 'facts',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    result = learn_from_text(store, 'The server runs on port 8765. Backups run nightly at 2am.', title = 'ops-runbook')
    @py_assert1 = result.ok
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.ok\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    @py_assert2 = result.lessons
    @py_assert4 = len(@py_assert2)
    @py_assert7 = 1
    @py_assert6 = @py_assert4 >= @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('>=',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s.lessons\n})\n} >= %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None
    entries = list_document_learnings(store)
    if not entries:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(entries) if 'entries' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(entries) else 'entries' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert0 = entries[0]['namespace']
    @py_assert2 = @py_assert0 == LEARNING_NAMESPACE
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py3)s',), (@py_assert0, LEARNING_NAMESPACE)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(LEARNING_NAMESPACE) if 'LEARNING_NAMESPACE' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(LEARNING_NAMESPACE) else 'LEARNING_NAMESPACE' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_low_text_warning_blocks_learn(data_dir, store, monkeypatch):
    learn_from_document = learn_from_document
    import jarvis.document_learning
    ParsedDocument = ParsedDocument
    low_text_warning = low_text_warning
    import jarvis.document_pipeline
    doc = ParsedDocument(path = '/tmp/scan.pdf', title = 'scan', pages = [
        'x'], page_count = 3, char_count = 5, source = 'pymupdf')
    @py_assert2 = low_text_warning(doc)
    if not @py_assert2:
        @py_format4 = 'assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(low_text_warning) if 'low_text_warning' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(low_text_warning) else 'low_text_warning',
            'py1': @pytest_ar._saferepr(doc) if 'doc' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(doc) else 'doc',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert2 = None
    result = learn_from_document(store, doc)
    @py_assert1 = result.ok
    @py_assert3 = not @py_assert1
    if not @py_assert3:
        @py_format4 = 'assert not %(py2)s\n{%(py2)s = %(py0)s.ok\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = []
    @py_assert2 = 'scanned'
    @py_assert6 = result.message
    @py_assert8 = @py_assert6.lower
    @py_assert10 = @py_assert8()
    @py_assert4 = @py_assert2 in @py_assert10
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert15 = 'ocr'
        @py_assert19 = result.message
        @py_assert21 = @py_assert19.lower
        @py_assert23 = @py_assert21()
        @py_assert17 = @py_assert15 in @py_assert23
        @py_assert0 = @py_assert17
# WARNING: Decompyle incomplete


def test_pdf_ocr_learn_path(monkeypatch, store, tmp_path):
    pass
# WARNING: Decompyle incomplete


def test_documents_rag_in_chat_context(assistant, monkeypatch):
    monkeypatch.setattr('jarvis.documents_rag.context_for_query', (lambda q, limit = (4,): ('Document library:\n[warranty] Coverage for 12 months', [])))
    monkeypatch.setattr('jarvis.llm.embed_available', (lambda : False))
    monkeypatch.setattr('jarvis.router.is_general_knowledge_question', (lambda m, s: False))
    monkeypatch.setattr('jarvis.router.is_meta_self_question', (lambda m: False))
    monkeypatch.setattr('jarvis.trust_memory.trust_context_for_chat', (lambda : ''))
    (prefix, warnings, _cites) = assistant._chat_context_prefix('What does my warranty say about coverage?')
    @py_assert0 = 'Document library'
    @py_assert2 = @py_assert0 in prefix
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, prefix)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(prefix) if 'prefix' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(prefix) else 'prefix' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = []
    @py_assert2 = 'warranty'
    @py_assert6 = prefix.lower
    @py_assert8 = @py_assert6()
    @py_assert4 = @py_assert2 in @py_assert8
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert13 = 'Coverage'
        @py_assert15 = @py_assert13 in prefix
        @py_assert0 = @py_assert15
# WARNING: Decompyle incomplete


def test_documents_upload_api(monkeypatch, tmp_path):
    TestClient = TestClient
    import fastapi.testclient
    monkeypatch.setattr('jarvis.document_learning.ingest_file', (lambda path, copy_to_library = (True,): type('R', (), {
'ok': True,
'title': 'manual',
'path': str(path),
'source_type': 'pdf',
'chars': 100,
'message': 'Indexed manual',
'source_id': 'abc' })()))
    monkeypatch.setattr('jarvis.document_brain_feed.maybe_auto_learn_document', (lambda : pass))
    app = app
    import jarvis.gui.server
    client = TestClient(app)
    res = client.post('/api/documents/upload', files = {
        'file': ('test.txt', b'hello warranty world', 'text/plain') }, data = {
        'learn': '0' })
    @py_assert1 = res.status_code
    @py_assert4 = 200
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    body = res.json()
    @py_assert1 = body.get
    @py_assert3 = 'ok'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(body) if 'body' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(body) else 'body',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None

