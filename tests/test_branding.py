# Source Generated with Decompyle++
# File: test_branding.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Assistant branding.'''
import builtins as @py_builtins

rewrite
import jarvis.branding as branding
import _pytest.assertion.rewrite, assertion

def test_default_branding(monkeypatch):
    monkeypatch.delenv('JARVIS_ASSISTANT_NAME', raising = False)
    monkeypatch.delenv('JARVIS_ASSISTANT_FULL_NAME', raising = False)
    @py_assert1 = branding.assistant_name
    @py_assert3 = @py_assert1()
    @py_assert6 = 'ARIA'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.assistant_name\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(branding) if 'branding' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(branding) else 'branding',
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
    @py_assert1 = branding.assistant_full_name
    @py_assert3 = @py_assert1()
    @py_assert6 = 'Adaptive Reasoning Intelligence Assistant'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.assistant_full_name\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(branding) if 'branding' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(branding) else 'branding',
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
    @py_assert0 = 'ARIA'
    @py_assert4 = branding.assistant_intro
    @py_assert6 = @py_assert4()
    @py_assert2 = @py_assert0 in @py_assert6
    if not @py_assert2:
        @py_format8 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = %(py3)s.assistant_intro\n}()\n}',), (@py_assert0, @py_assert6)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(branding) if 'branding' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(branding) else 'branding',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None


def test_branding_env_override(monkeypatch):
    monkeypatch.setenv('JARVIS_ASSISTANT_NAME', 'LARK')
    monkeypatch.setenv('JARVIS_ASSISTANT_FULL_NAME', 'Local Autonomous Reasoning Kit')
    @py_assert1 = branding.assistant_name
    @py_assert3 = @py_assert1()
    @py_assert6 = 'LARK'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.assistant_name\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(branding) if 'branding' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(branding) else 'branding',
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
    @py_assert0 = branding.branding_dict()['assistant_full_name']
    @py_assert3 = 'Local Autonomous Reasoning Kit'
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

