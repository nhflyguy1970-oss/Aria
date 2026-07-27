"""Journal encryption unit tests."""

from __future__ import annotations

import pytest

from jarvis.journal_crypto import decrypt_import, encrypt_export


def test_encrypt_decrypt_roundtrip():
    payload = {"version": 1, "daily_log": {}, "collections": {"A": {"bullets": []}}}
    enc = encrypt_export(payload, "s3cret!")
    assert enc["format"] == "jarvis-journal-v1"
    assert "ciphertext" in enc
    out = decrypt_import(enc, "s3cret!")
    assert out["collections"]["A"]["bullets"] == []


def test_short_password_rejected():
    with pytest.raises(ValueError):
        encrypt_export({"a": 1}, "ab")


def test_wrong_password():
    enc = encrypt_export({"a": 1}, "good-password")
    with pytest.raises(ValueError):
        decrypt_import(enc, "bad-password")


def test_corrupt_payload():
    with pytest.raises(ValueError):
        decrypt_import({"format": "nope"}, "x")
