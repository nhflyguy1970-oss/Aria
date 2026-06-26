# Source Generated with Decompyle++
# File: test_prompt_history.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for image prompt history.'''
import builtins as @py_builtins

rewrite
from jarvis.prompt_history import add_entry, delete_entry, list_entries, toggle_favorite
delete_entry = delete_entry
list_entries = list_entries
toggle_favorite = toggle_favorite
import _pytest.assertion.rewrite, assertion

def test_prompt_history_roundtrip(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.prompt_history.HISTORY_FILE', data_dir / 'prompt_history.json')
    e = add_entry('a cat in space', enhanced = 'detailed cat', image_path = '/tmp/x.png')
    @py_assert0 = e['id']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None
    items = list_entries()
    @py_assert0 = items[0]['prompt']
    @py_assert3 = 'a cat in space'
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
    toggled = toggle_favorite(e['id'])
    @py_assert1 = []
    @py_assert0 = toggled
    if toggled:
        @py_assert4 = toggled['favorite']
        @py_assert7 = True
        @py_assert6 = @py_assert4 is @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_delete_entry(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.prompt_history.HISTORY_FILE', data_dir / 'prompt_history.json')
    e = add_entry('delete me')
    @py_assert1 = e['id']
    @py_assert3 = delete_entry(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(delete_entry) if 'delete_entry' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(delete_entry) else 'delete_entry',
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
    @py_assert1 = list_entries()
    @py_assert4 = []
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(list_entries) if 'list_entries' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_entries) else 'list_entries',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = 'missing'
    @py_assert3 = delete_entry(@py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(delete_entry) if 'delete_entry' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(delete_entry) else 'delete_entry',
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

