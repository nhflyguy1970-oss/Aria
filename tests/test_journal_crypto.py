"""Encrypted journal export/import."""

import pytest

pytest.importorskip("cryptography")
from jarvis.journal_crypto import decrypt_import, encrypt_export  # noqa: E402


def test_journal_encrypt_roundtrip():
    payload = {"daily_log": {"2026-06-01": []}, "index": []}
    enc = encrypt_export(payload, "test-pass")
    assert enc["format"] == "jarvis-journal-v1"
    got = decrypt_import(enc, "test-pass")
    assert got == payload


def test_journal_encrypt_wrong_password():
    enc = encrypt_export({"x": 1}, "right")
    with pytest.raises(ValueError, match="Wrong password"):
        decrypt_import(enc, "wrong")
