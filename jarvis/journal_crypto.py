"""Password-protected journal export/import."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any

FORMAT = "jarvis-journal-v1"
_PBKDF2_ITERS = 200_000


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise RuntimeError(
            "Encrypted journal requires: pip install cryptography"
        ) from exc
    return Fernet


def _derive_key(password: str, salt: bytes) -> bytes:
    raw = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERS,
        dklen=32,
    )
    return base64.urlsafe_b64encode(raw)


def encrypt_export(payload: dict[str, Any], password: str) -> dict[str, str]:
    password = (password or "").strip()
    if len(password) < 4:
        raise ValueError("Export password must be at least 4 characters")
    Fernet = _fernet()
    salt = os.urandom(16)
    token = Fernet(_derive_key(password, salt))
    blob = token.encrypt(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    return {
        "format": FORMAT,
        "salt": salt.hex(),
        "ciphertext": base64.b64encode(blob).decode("ascii"),
    }


def decrypt_import(data: dict[str, Any], password: str) -> dict[str, Any]:
    password = (password or "").strip()
    if data.get("format") != FORMAT:
        raise ValueError("Not a Jarvis encrypted journal file")
    try:
        salt = bytes.fromhex(data["salt"])
        blob = base64.b64decode(data["ciphertext"])
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("Corrupt encrypted journal file") from exc
    Fernet = _fernet()
    token = Fernet(_derive_key(password, salt))
    try:
        raw = token.decrypt(blob)
    except Exception as exc:
        raise ValueError("Wrong password or corrupt file") from exc
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Invalid journal payload")
    return parsed
