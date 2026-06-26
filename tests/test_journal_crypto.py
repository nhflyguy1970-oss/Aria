# Source Generated with Decompyle++
# File: test_journal_crypto.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Encrypted journal export/import.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
pytest.importorskip('cryptography')
from jarvis.journal_crypto import decrypt_import, encrypt_export

def test_journal_encrypt_roundtrip():
    payload = {
        'daily_log': {
            '2026-06-01': [] },
        'index': [] }
    enc = encrypt_export(payload, 'test-pass')
    @py_assert0 = enc['format']
    @py_assert3 = 'jarvis-journal-v1'
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
    got = decrypt_import(enc, 'test-pass')
    @py_assert1 = got == payload
    if not @py_assert1:
        @py_format3 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py2)s',), (got, payload)) % {
            'py0': @pytest_ar._saferepr(got) if 'got' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(got) else 'got',
            'py2': @pytest_ar._saferepr(payload) if 'payload' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(payload) else 'payload' }
        @py_format5 = 'assert %(py4)s' % {
            'py4': @py_format3 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None


def test_journal_encrypt_wrong_password():
    enc = encrypt_export({
        'x': 1 }, 'right')
    pytest.raises(ValueError, match = 'Wrong password')
    decrypt_import(enc, 'wrong')
    None(None, None)
    return None
    with None:
        if not None:
            pass

