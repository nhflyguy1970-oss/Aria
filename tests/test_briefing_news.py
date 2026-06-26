# Source Generated with Decompyle++
# File: test_briefing_news.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Briefing news headlines.'''
import builtins as @py_builtins

rewrite
import re = import _pytest.assertion.rewrite, assertion
from datetime import datetime, timezone
import pytest
from jarvis.briefing_news import _build_primary_query, _filter_local_headlines, _filter_quality_headlines, _is_quality_headline, _is_relevant_local_headline, _merge_local_headlines, briefing_news_intent, looks_like_general_expansion, match_headline, _parse_google_news_rss, _parse_rss_pub_date, fetch_briefing_news, format_news_markdown, load_recent_headlines, profile_location, resolve_local_news_scope, resolve_local_place
from jarvis.session import SessionContext
journal = (lambda data_dir, monkeypatch: monkeypatch.setattr('jarvis.modules.journal.JOURNAL_FILE', data_dir / 'journal' / 'bullet_journal.json')monkeypatch.setattr('jarvis.modules.journal.JOURNAL_DIR', data_dir / 'journal')(data_dir / 'journal').mkdir(parents = True, exist_ok = True)BulletJournal = BulletJournalimport jarvis.modules.journalBulletJournal(path = data_dir / 'journal' / 'bullet_journal.json'))()
store = (lambda data_dir, monkeypatch: monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
1,
0]))
    MemoryStore = MemoryStore
    import jarvis.modules.memory
    return MemoryStore(path = data_dir / 'memory.json')
)()
SAMPLE_RSS = b'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n  <channel>\n    <item>\n      <title>Major policy shift announced - Reuters</title>\n      <link>https://example.com/national</link>\n      <source>Reuters</source>\n      <pubDate>Mon, 08 Jun 2026 10:00:00 GMT</pubDate>\n    </item>\n    <item>\n      <title>Bridge repair scheduled downtown - Valley News</title>\n      <link>https://example.com/local</link>\n      <source>Valley News</source>\n      <pubDate>Mon, 08 Jun 2026 09:00:00 GMT</pubDate>\n    </item>\n  </channel>\n</rss>\n'
STALE_RSS = b'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n  <channel>\n    <item>\n      <title>Old town meeting recap - Valley News</title>\n      <link>https://example.com/old</link>\n      <source>Valley News</source>\n      <pubDate>Mon, 01 May 2026 09:00:00 GMT</pubDate>\n    </item>\n  </channel>\n</rss>\n'

def test_parse_google_news_rss():
    hits = _parse_google_news_rss(SAMPLE_RSS, limit = 5)
    @py_assert2 = len(hits)
    @py_assert5 = 2
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(hits) if 'hits' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hits) else 'hits',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = hits[0]['title']
    @py_assert3 = 'Major policy shift announced'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = hits[0]['source']
    @py_assert3 = 'Reuters'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = hits[1]['url']
    @py_assert3 = 'https://example.com/local'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_parse_google_news_rss_filters_by_age(monkeypatch):
    monkeypatch.setattr('jarvis.briefing_news.datetime', type('FrozenDateTime', (), {
        'now': staticmethod((lambda tz = (None,): datetime(2026, 6, 8, 12, 0, tzinfo = timezone.utc))),
        'fromisoformat': datetime.fromisoformat }))
    hits = _parse_google_news_rss(SAMPLE_RSS, limit = 5, max_age_days = 3)
    @py_assert2 = len(hits)
    @py_assert5 = 2
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(hits) if 'hits' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hits) else 'hits',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    hits = _parse_google_news_rss(STALE_RSS, limit = 5, max_age_days = 3)
    @py_assert2 = []
    @py_assert1 = hits == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (hits, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(hits) if 'hits' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hits) else 'hits',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_parse_rss_pub_date():
    dt = _parse_rss_pub_date('Mon, 08 Jun 2026 10:00:00 GMT')
    @py_assert2 = None
    @py_assert1 = dt is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (dt, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(dt) if 'dt' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(dt) else 'dt',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert1 = dt.year
    @py_assert4 = 2026
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.year\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(dt) if 'dt' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(dt) else 'dt',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = dt.month
    @py_assert4 = 6
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.month\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(dt) if 'dt' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(dt) else 'dt',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_build_primary_query_avoids_bare_charlestown():
    q = _build_primary_query('Charlestown, NH', max_age_days = 3)
    @py_assert0 = 'Charlestown, NH'
    @py_assert2 = @py_assert0 in q
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, q)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Charlestown NH'
    @py_assert2 = @py_assert0 in q
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, q)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'New Hampshire'
    @py_assert2 = @py_assert0 in q
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, q)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Sullivan County'
    @py_assert2 = @py_assert0 in q
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, q)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = re.search
    @py_assert3 = 'OR\\s+"Charlestown"\\s'
    @py_assert6 = @py_assert1(@py_assert3, q)
    @py_assert9 = None
    @py_assert8 = @py_assert6 is @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('is',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py2)s\n{%(py2)s = %(py0)s.search\n}(%(py4)s, %(py5)s)\n} is %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(re) if 're' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(re) else 're',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py5': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q',
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None
    @py_assert1 = q.endswith
    @py_assert3 = 'when:3d'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.endswith\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_filter_rejects_wrong_charlestown():
    scope = {
        'primary': 'Charlestown, NH',
        'towns': [],
        'label': 'test' }
    wrong = [
        {
            'title': 'Charlestown MA town council vote',
            'url': 'https://x.test',
            'source': 'Boston Globe' },
        {
            'title': 'Boston Charlestown development plan',
            'url': 'https://y.test',
            'source': 'WBUR' },
        {
            'title': 'Rhode Island Charlestown beach access',
            'url': 'https://z.test',
            'source': 'Providence Journal' }]
    kept = _filter_local_headlines(wrong, scope)
    @py_assert2 = []
    @py_assert1 = kept == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (kept, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(kept) if 'kept' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(kept) else 'kept',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_filter_keeps_charlestown_nh():
    scope = {
        'primary': 'Charlestown, NH',
        'towns': [],
        'label': 'test' }
    good = [
        {
            'title': 'Charlestown NH selectboard meeting',
            'url': 'https://a.test',
            'source': 'Eagle Times' },
        {
            'title': 'Bridge work near Charlestown',
            'url': 'https://b.test',
            'source': 'Valley News' },
        {
            'title': 'Upper Valley schools announce delay',
            'url': 'https://c.test',
            'source': 'Valley News' }]
    @py_assert1 = good[0]
    @py_assert4 = _is_relevant_local_headline(@py_assert1, scope)
    if not @py_assert4:
        @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n}' % {
            'py0': @pytest_ar._saferepr(_is_relevant_local_headline) if '_is_relevant_local_headline' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_is_relevant_local_headline) else '_is_relevant_local_headline',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(scope) if 'scope' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(scope) else 'scope',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert1 = good[1]
    @py_assert4 = _is_relevant_local_headline(@py_assert1, scope)
    if not @py_assert4:
        @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n}' % {
            'py0': @pytest_ar._saferepr(_is_relevant_local_headline) if '_is_relevant_local_headline' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_is_relevant_local_headline) else '_is_relevant_local_headline',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(scope) if 'scope' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(scope) else 'scope',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert1 = good[2]
    @py_assert4 = _is_relevant_local_headline(@py_assert1, scope)
    if not @py_assert4:
        @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n}' % {
            'py0': @pytest_ar._saferepr(_is_relevant_local_headline) if '_is_relevant_local_headline' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_is_relevant_local_headline) else '_is_relevant_local_headline',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(scope) if 'scope' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(scope) else 'scope',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert4 = _filter_local_headlines(good, scope)
    @py_assert6 = len(@py_assert4)
    @py_assert9 = 3
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py0)s(%(py5)s\n{%(py5)s = %(py1)s(%(py2)s, %(py3)s)\n})\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(_filter_local_headlines) if '_filter_local_headlines' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_filter_local_headlines) else '_filter_local_headlines',
            'py2': @pytest_ar._saferepr(good) if 'good' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(good) else 'good',
            'py3': @pytest_ar._saferepr(scope) if 'scope' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(scope) else 'scope',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None


def test_filter_rejects_stale_and_junk_headlines():
    scope = {
        'primary': 'Charlestown, NH',
        'towns': [],
        'label': 'test' }
    junk = [
        {
            'title': 'North Walpole, New Hampshire - Wikipedia',
            'url': 'https://en.wikipedia.org/wiki/North_Walpole' },
        {
            'title': 'Update: Drawdown Initiated – 8/1/23 - The Walpolean',
            'url': 'https://x.test' },
        {
            'title': 'NEWS - Walpole Outdoors',
            'url': 'https://x.test' },
        {
            'title': 'Connecticut River flooding - Facebook',
            'url': 'https://facebook.com/x' },
        {
            'title': 'John Smith obituary - Legacy.com',
            'url': 'https://www.legacy.com/us/obituaries/name/john-smith' },
        {
            'title': 'In loving memory of Jane Doe',
            'url': 'https://funeral.test' }]
    @py_assert2 = 3
    @py_assert4 = _filter_quality_headlines(junk, max_age_days = @py_assert2)
    @py_assert7 = []
    @py_assert6 = @py_assert4 == @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('==',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py1)s, max_age_days=%(py3)s)\n} == %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(_filter_quality_headlines) if '_filter_quality_headlines' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_filter_quality_headlines) else '_filter_quality_headlines',
            'py1': @pytest_ar._saferepr(junk) if 'junk' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(junk) else 'junk',
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
    @py_assert1 = junk[1]
    @py_assert3 = 3
    @py_assert5 = _is_quality_headline(@py_assert1, max_age_days = @py_assert3)
    @py_assert8 = False
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, max_age_days=%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(_is_quality_headline) if '_is_quality_headline' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_is_quality_headline) else '_is_quality_headline',
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
    @py_assert1 = junk[4]
    @py_assert3 = 3
    @py_assert5 = _is_quality_headline(@py_assert1, max_age_days = @py_assert3)
    @py_assert8 = False
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, max_age_days=%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(_is_quality_headline) if '_is_quality_headline' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_is_quality_headline) else '_is_quality_headline',
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


def test_match_headline_ignores_stopwords():
    headlines = [
        {
            'title': 'Under-16s to be banned from social media by next spring',
            'category': 'national' },
        {
            'title': 'Connecticut River drawdown | Local News',
            'category': 'local' }]
    @py_assert1 = 'expand on that news from my briefing'
    @py_assert4 = match_headline(@py_assert1, headlines)
    @py_assert7 = None
    @py_assert6 = @py_assert4 is @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('is',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n} is %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(match_headline) if 'match_headline' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(match_headline) else 'match_headline',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(headlines) if 'headlines' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(headlines) else 'headlines',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None
    @py_assert0 = match_headline('local headline 1', headlines)['category']
    @py_assert3 = 'local'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert1 = 'tell me more about connecticut river drawdown'
    @py_assert4 = match_headline(@py_assert1, headlines)
    @py_assert7 = None
    @py_assert6 = @py_assert4 is not @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('is not',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n} is not %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(match_headline) if 'match_headline' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(match_headline) else 'match_headline',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(headlines) if 'headlines' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(headlines) else 'headlines',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None


def test_load_recent_headlines_requires_today(monkeypatch):
    monkeypatch.setattr('jarvis.config._load_chat_settings', (lambda : {
'morning_briefing': {
'headlines_day': '2020-01-01',
'headlines': [
{
'title': 'Old story',
'category': 'local' }] } }))
    @py_assert1 = load_recent_headlines()
    @py_assert4 = []
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(load_recent_headlines) if 'load_recent_headlines' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(load_recent_headlines) else 'load_recent_headlines',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_merge_local_headlines_primary_first():
    primary = [
        {
            'title': 'Charlestown fire department drill',
            'url': 'https://a.test',
            'source': 'Eagle' },
        {
            'title': 'Shared headline',
            'url': 'https://b.test',
            'source': 'Eagle' }]
    regional = [
        {
            'title': 'Shared headline',
            'url': 'https://b.test',
            'source': 'Valley News' },
        {
            'title': 'Lebanon hospital expansion',
            'url': 'https://c.test',
            'source': 'Valley News' }]
    merged = _merge_local_headlines(primary, regional, limit = 3)
# WARNING: Decompyle incomplete


def test_profile_location(store):
    store.add('fact', 'User is based in Charlestown, NH.', namespace = 'profile')
    @py_assert2 = profile_location(store)
    @py_assert5 = 'Charlestown, NH'
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(profile_location) if 'profile_location' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(profile_location) else 'profile_location',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_resolve_local_place_prefers_env(monkeypatch, store):
    monkeypatch.setenv('JARVIS_NEWS_LOCAL', 'Lebanon, NH')
    @py_assert2 = resolve_local_place(memory_store = store)
    @py_assert5 = 'Lebanon, NH'
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(memory_store=%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(resolve_local_place) if 'resolve_local_place' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_local_place) else 'resolve_local_place',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_resolve_local_news_scope_defaults(monkeypatch, store):
    monkeypatch.delenv('JARVIS_NEWS_LOCAL', raising = False)
    monkeypatch.delenv('JARVIS_NEWS_LOCAL_PRIMARY', raising = False)
    scope = resolve_local_news_scope(memory_store = store, weather = {
        'location': 'Charlestown, NH' })
    @py_assert0 = scope['primary']
    @py_assert3 = 'Charlestown, NH'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'Walpole NH'
    @py_assert3 = scope['towns']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'Bellows Falls VT'
    @py_assert3 = scope['towns']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'Hartland VT'
    @py_assert3 = scope['towns']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'Charlestown'
    @py_assert3 = ' '
    @py_assert5 = @py_assert3.join
    @py_assert7 = scope['towns']
    @py_assert9 = @py_assert5(@py_assert7)
    @py_assert2 = @py_assert0 not in @py_assert9
    if not @py_assert2:
        @py_format11 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py10)s\n{%(py10)s = %(py6)s\n{%(py6)s = %(py4)s.join\n}(%(py8)s)\n}',), (@py_assert0, @py_assert9)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert0 = 'Connecticut River'
    @py_assert3 = scope['label']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_format_news_markdown():
    news = {
        'enabled': True,
        'national': [
            {
                'title': 'Headline A',
                'url': 'https://a.test',
                'source': 'AP' }],
        'local': [
            {
                'title': 'Town meeting',
                'url': 'https://b.test',
                'source': 'Local' }],
        'local_place': 'Connecticut River Valley (Charlestown–Lebanon, NH & VT)',
        'local_primary': 'Charlestown, NH' }
    lines = format_news_markdown(news)
    text = '\n'.join(lines)
    @py_assert0 = '**National headlines**'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = '**Local headlines (Connecticut River Valley (Charlestown–Lebanon, NH & VT) · Charlestown, NH first)**'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = '1. [Headline A]'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Town meeting'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'local headline 2'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_fetch_briefing_news_offline(monkeypatch, store):
    monkeypatch.setattr('jarvis.briefing_news.news_available', (lambda : False))
    bundle = fetch_briefing_news(memory_store = store)
    @py_assert0 = bundle['enabled']
    @py_assert3 = False
    @py_assert2 = @py_assert0 is @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = bundle['national']
    @py_assert3 = []
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_fetch_briefing_news_uses_rss(monkeypatch, store):
    monkeypatch.setattr('jarvis.briefing_news.news_available', (lambda : True))
    monkeypatch.setenv('JARVIS_NEWS_LOCAL', 'Charlestown, NH')
    monkeypatch.setattr('jarvis.briefing_news.datetime', type('FrozenDateTime', (), {
        'now': staticmethod((lambda tz = (None,): datetime(2026, 6, 8, 12, 0, tzinfo = timezone.utc))),
        'fromisoformat': datetime.fromisoformat }))
    
    def fake_fetch(url, timeout = (10,)):
        if 'search' in url:
            return SAMPLE_RSS

    monkeypatch.setattr('jarvis.briefing_news._fetch_bytes', fake_fetch)
    monkeypatch.setattr('jarvis.briefing_news._CACHE', { })
    bundle = fetch_briefing_news(memory_store = store, national_limit = 2, local_limit = 2)
    @py_assert0 = bundle['enabled']
    @py_assert3 = True
    @py_assert2 = @py_assert0 is @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert1 = bundle['national']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 1
    @py_assert5 = @py_assert3 >= @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('>=',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} >= %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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
    @py_assert0 = bundle['local_primary']
    @py_assert3 = 'Charlestown, NH'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'Connecticut River'
    @py_assert3 = bundle['local_place']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_build_briefing_includes_news(journal, store, monkeypatch):
    monkeypatch.setattr('jarvis.modules.journal._today', (lambda : '2026-06-08'))
    monkeypatch.setattr('jarvis.morning_briefing.weather_for_day', (lambda day: {
'date': day,
'condition': 'Clear',
'high': 72,
'low': 58,
'unit': '°F',
'location': 'Charlestown, NH',
'icon': '☀️' }))
    monkeypatch.setattr('jarvis.briefing_news.fetch_briefing_news', (lambda : {
'enabled': True,
'national': [
{
'title': 'Budget vote passes',
'url': 'https://n.test',
'source': 'AP' }],
'local': [
{
'title': 'School board meets',
'url': 'https://l.test',
'source': 'Valley News' }],
'local_place': 'Connecticut River Valley (Charlestown–Lebanon, NH & VT)',
'local_primary': 'Charlestown, NH',
'skipped': None }))
    build_briefing = build_briefing
    import jarvis.morning_briefing
    briefing = build_briefing(journal = journal, memory_store = store, day = '2026-06-08', reference = datetime(2026, 6, 8, 8, 30))
    @py_assert0 = 'National headlines'
    @py_assert3 = briefing['markdown']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'Budget vote passes'
    @py_assert3 = briefing['markdown']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'School board meets'
    @py_assert3 = briefing['markdown']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_match_headline_by_index():
    headlines = [
        {
            'title': 'Bridge repair scheduled downtown',
            'url': 'https://a.test',
            'category': 'national' },
        {
            'title': 'School board meets Tuesday',
            'url': 'https://b.test',
            'category': 'national' },
        {
            'title': 'River drawdown planned',
            'url': 'https://c.test',
            'category': 'local' }]
    hit = match_headline('tell me more about local headline 1', headlines)
    @py_assert1 = []
    @py_assert0 = hit
    if hit:
        @py_assert4 = hit['title']
        @py_assert7 = 'River drawdown planned'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_match_headline_by_words():
    headlines = [
        {
            'title': 'Bridge repair scheduled downtown',
            'url': 'https://a.test' },
        {
            'title': 'School board meets Tuesday',
            'url': 'https://b.test' }]
    hit = match_headline('more about the bridge repair story', headlines)
    @py_assert1 = []
    @py_assert0 = hit
    if hit:
        @py_assert4 = 'Bridge repair'
        @py_assert7 = hit['title']
        @py_assert6 = @py_assert4 in @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_briefing_news_intent_routes_detail():
    session = SessionContext()
    session.note_briefing_headlines([
        {
            'title': 'Bridge repair scheduled downtown',
            'url': 'https://a.test',
            'source': 'Valley News',
            'category': 'local' }])
    intent = briefing_news_intent('tell me more about the bridge repair', session)
    if not intent:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(intent) if 'intent' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(intent) else 'intent' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert0 = intent['action']
    @py_assert3 = 'briefing_news_detail'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = intent['params']['title']
    @py_assert3 = 'Bridge repair scheduled downtown'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_briefing_news_intent_vague_still_routes():
    session = SessionContext()
    session.note_briefing_headlines([
        {
            'title': 'Bridge repair scheduled downtown',
            'category': 'local' }])
    intent = briefing_news_intent('expand on that news from my briefing', session)
    if not intent:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(intent) if 'intent' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(intent) else 'intent' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert0 = intent['action']
    @py_assert3 = 'briefing_news_detail'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = intent['params']['title']
    @py_assert3 = ''
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_general_expand_does_not_route_to_briefing():
    session = SessionContext()
    session.note_briefing_headlines([
        {
            'title': 'Bridge repair scheduled downtown',
            'category': 'local' }])
    for msg in ('expand on my essay', 'can you expand that section', 'expand this to 2000 words', 'explain that idea more', 'expand on the garage layout'):
        @py_assert2 = looks_like_general_expansion(msg)
        if not @py_assert2:
            @py_format4 = (@pytest_ar._format_assertmsg(msg) + '\n>assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}') % {
                'py0': @pytest_ar._saferepr(looks_like_general_expansion) if 'looks_like_general_expansion' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(looks_like_general_expansion) else 'looks_like_general_expansion',
                'py1': @pytest_ar._saferepr(msg) if 'msg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(msg) else 'msg',
                'py3': @pytest_ar._saferepr(@py_assert2) }
            raise AssertionError(@pytest_ar._format_explanation(@py_format4))
        @py_assert2 = None
        @py_assert3 = briefing_news_intent(msg, session)
        @py_assert6 = None
        @py_assert5 = @py_assert3 is @py_assert6
        if not @py_assert5:
            @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py1)s, %(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
                'py0': @pytest_ar._saferepr(briefing_news_intent) if 'briefing_news_intent' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(briefing_news_intent) else 'briefing_news_intent',
                'py1': @pytest_ar._saferepr(msg) if 'msg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(msg) else 'msg',
                'py2': @pytest_ar._saferepr(session) if 'session' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session) else 'session',
                'py4': @pytest_ar._saferepr(@py_assert3),
                'py7': @pytest_ar._saferepr(@py_assert6) }
            @py_format10 = (@pytest_ar._format_assertmsg(msg) + '\n>assert %(py9)s') % {
                'py9': @py_format8 }
            raise AssertionError(@pytest_ar._format_explanation(@py_format10))
        @py_assert3 = None
        @py_assert5 = None
        @py_assert6 = None
    @py_assert1 = 'expand'
    @py_assert4 = briefing_news_intent(@py_assert1, session)
    @py_assert7 = None
    @py_assert6 = @py_assert4 is @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('is',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n} is %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(briefing_news_intent) if 'briefing_news_intent' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(briefing_news_intent) else 'briefing_news_intent',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(session) if 'session' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session) else 'session',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None


def test_briefing_followup_after_briefing_module():
    session = SessionContext()
    session.last_module = 'briefing'
    session.note_briefing_headlines([
        {
            'title': 'Bridge repair scheduled downtown',
            'category': 'local' }])
    intent = briefing_news_intent('expand on that', session)
    if not intent:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(intent) if 'intent' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(intent) else 'intent' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert0 = intent['action']
    @py_assert3 = 'briefing_news_detail'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_word_overlap_alone_does_not_route():
    session = SessionContext()
    session.note_briefing_headlines([
        {
            'title': 'Bridge repair scheduled downtown',
            'url': 'https://a.test' }])
    @py_assert1 = 'repair the bridge design in my CAD file'
    @py_assert4 = briefing_news_intent(@py_assert1, session)
    @py_assert7 = None
    @py_assert6 = @py_assert4 is @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('is',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n} is %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(briefing_news_intent) if 'briefing_news_intent' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(briefing_news_intent) else 'briefing_news_intent',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(session) if 'session' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session) else 'session',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None

