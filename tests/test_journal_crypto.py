"""Journal encryption unit tests."""

from __future__ import annotations

import pytest

from jarvis.journal_crypto import decrypt_import, encrypt_export, normalize_encrypted_envelope


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
    with pytest.raises(ValueError, match="Wrong password"):
        decrypt_import(enc, "bad-password")


def test_corrupt_payload():
    with pytest.raises(ValueError, match="Not a Jarvis encrypted journal file"):
        decrypt_import({"format": "nope"}, "x")


def test_unwrap_api_response_envelope():
    enc = encrypt_export({"marker": "ok"}, "good-password")
    wrapped = {"ok": True, "export": enc}
    assert normalize_encrypted_envelope(wrapped)["format"] == "jarvis-journal-v1"
    assert decrypt_import(wrapped, "good-password")["marker"] == "ok"


def test_plain_journal_hint():
    with pytest.raises(ValueError, match="unencrypted Journal JSON"):
        decrypt_import({"daily_log": {}, "index": {}}, "whatever-password")


def test_ui_body_shape():
    enc = encrypt_export({"x": 1}, "good-password")
    body = {"export": enc, "password": "good-password", "merge": True}
    out = decrypt_import(body["export"], body["password"])
    assert out["x"] == 1


def test_owner_aug08_shape_accepted_as_envelope():
    """Structure-only: Aug 8 owner files match current envelope (no decrypt with owner password)."""
    from pathlib import Path
    import json

    p = Path("/home/jeff/Downloads/jarvis-journal-encrypted-2026-08-08.json")
    if not p.exists():
        pytest.skip("owner export not present on this machine")
    data = json.loads(p.read_text())
    env = normalize_encrypted_envelope(data)
    assert env["format"] == "jarvis-journal-v1"
    with pytest.raises(ValueError, match="Wrong password"):
        decrypt_import(data, "not-the-owner-password-xxxx")
