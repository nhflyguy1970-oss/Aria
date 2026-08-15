"""Password-protected journal export/import."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any

FORMAT = "jarvis-journal-v1"
_PBKDF2_ITERS = 200_000

# Top-level keys that indicate an unencrypted Journal export (not an encrypted envelope).
_PLAIN_JOURNAL_KEYS = frozenset(
    {
        "daily_log",
        "weekly_log",
        "monthly_log",
        "future_log",
        "collections",
        "habits",
        "index",
        "page_counter",
    }
)


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


def _is_envelope(data: dict[str, Any]) -> bool:
    return (
        data.get("format") == FORMAT
        and isinstance(data.get("salt"), str)
        and isinstance(data.get("ciphertext"), str)
    )


def _plain_journal_hint(data: dict[str, Any]) -> str | None:
    if _is_envelope(data):
        return None
    if data.keys() & _PLAIN_JOURNAL_KEYS and "ciphertext" not in data:
        return (
            "This looks like an unencrypted Journal JSON export. "
            "Use Import (not Import encrypted), or choose a "
            "jarvis-journal-encrypted-*.json file."
        )
    return None


def normalize_encrypted_envelope(data: Any) -> dict[str, Any]:
    """Return the jarvis-journal-v1 envelope, unwrapping common accidental wrappers.

    Accepts:
    - On-disk export shape: {format, salt, ciphertext}
    - Accidental full API response: {ok, export: {format, salt, ciphertext}}
    - Stringified JSON envelope
    Does not weaken format/crypto checks — still requires FORMAT + salt + ciphertext.
    """
    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError("Not a Jarvis encrypted journal file") from exc
    if not isinstance(data, dict):
        raise ValueError("Not a Jarvis encrypted journal file")

    hint = _plain_journal_hint(data)
    if hint:
        raise ValueError(hint)

    if _is_envelope(data):
        return data

    # Walk nested export / ok wrappers (max 2 levels).
    cur: Any = data
    for _ in range(2):
        if not isinstance(cur, dict):
            break
        inner = cur.get("export")
        if isinstance(inner, str):
            try:
                inner = json.loads(inner)
            except json.JSONDecodeError:
                break
        if isinstance(inner, dict):
            hint = _plain_journal_hint(inner)
            if hint:
                raise ValueError(hint)
            if _is_envelope(inner):
                return inner
            cur = inner
            continue
        break

    observed = sorted(data.keys())[:12]
    raise ValueError(
        "Not a Jarvis encrypted journal file "
        f"(expected format={FORMAT!r} with salt+ciphertext; "
        f"observed keys={observed}; format={data.get('format')!r})"
    )


def decrypt_import(data: dict[str, Any] | Any, password: str) -> dict[str, Any]:
    password = (password or "").strip()
    data = normalize_encrypted_envelope(data)
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
