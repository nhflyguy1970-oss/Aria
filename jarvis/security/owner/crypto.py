"""Owner vault cryptography — Argon2id + AES-GCM only.

KDF runs only at setup / unlock / step-up verify / password change / recovery.
Never per Room or per credential get.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import Final

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Fixed Argon2id parameters (documented; not tunable at runtime for M1).
ARGON2_TIME_COST: Final[int] = 3
ARGON2_MEMORY_KIB: Final[int] = 65_536  # 64 MiB
ARGON2_PARALLELISM: Final[int] = 4
ARGON2_HASH_LEN: Final[int] = 32
ARGON2_SALT_LEN: Final[int] = 16
ROOT_KEY_LEN: Final[int] = 32
RECOVERY_KEY_LEN: Final[int] = 32
NONCE_LEN: Final[int] = 12

KDF_NAME: Final[str] = "argon2id"
VAULT_FORMAT: Final[str] = "aria-owner-vault-v1"


@dataclass(frozen=True)
class KdfParams:
    name: str = KDF_NAME
    time_cost: int = ARGON2_TIME_COST
    memory_kib: int = ARGON2_MEMORY_KIB
    parallelism: int = ARGON2_PARALLELISM
    hash_len: int = ARGON2_HASH_LEN
    salt: bytes = b""

    def to_public_dict(self) -> dict:
        return {
            "name": self.name,
            "time_cost": self.time_cost,
            "memory_kib": self.memory_kib,
            "parallelism": self.parallelism,
            "hash_len": self.hash_len,
            "salt_hex": self.salt.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KdfParams":
        if data.get("name") != KDF_NAME:
            raise ValueError(f"Unsupported KDF: {data.get('name')!r}")
        salt_hex = data.get("salt_hex") or data.get("salt") or ""
        return cls(
            name=KDF_NAME,
            time_cost=int(data["time_cost"]),
            memory_kib=int(data["memory_kib"]),
            parallelism=int(data["parallelism"]),
            hash_len=int(data.get("hash_len") or ARGON2_HASH_LEN),
            salt=bytes.fromhex(str(salt_hex)),
        )


def new_salt() -> bytes:
    return os.urandom(ARGON2_SALT_LEN)


def new_root_key() -> bytes:
    return os.urandom(ROOT_KEY_LEN)


def new_recovery_key() -> bytes:
    return os.urandom(RECOVERY_KEY_LEN)


def format_recovery_key(raw: bytes) -> str:
    """Human-portable recovery key (hex groups)."""
    hx = raw.hex()
    return "-".join(hx[i : i + 8] for i in range(0, len(hx), 8))


def parse_recovery_key(text: str) -> bytes:
    cleaned = "".join(ch for ch in (text or "") if ch.isalnum())
    if len(cleaned) != RECOVERY_KEY_LEN * 2:
        raise ValueError("Recovery key has incorrect length")
    return bytes.fromhex(cleaned)


def derive_key(secret: bytes | str, params: KdfParams) -> bytes:
    """Argon2id KDF. `secret` is master password (utf-8) or raw recovery key bytes."""
    if isinstance(secret, str):
        secret_b = secret.encode("utf-8")
    else:
        secret_b = secret
    if not secret_b:
        raise ValueError("Empty secret")
    if not params.salt or len(params.salt) < ARGON2_SALT_LEN:
        raise ValueError("Invalid KDF salt")
    if (
        params.time_cost != ARGON2_TIME_COST
        or params.memory_kib != ARGON2_MEMORY_KIB
        or params.parallelism != ARGON2_PARALLELISM
        or params.hash_len != ARGON2_HASH_LEN
    ):
        # Allow reading stored params that match our fixed policy only.
        # Reject weaker or alternate parameter sets in M1.
        if params.name != KDF_NAME:
            raise ValueError("Unsupported KDF")
        # Accept exact stored values if they equal fixed constants; else reject.
        raise ValueError("Vault KDF parameters do not match Aria M1 policy")
    return hash_secret_raw(
        secret=secret_b,
        salt=params.salt,
        time_cost=params.time_cost,
        memory_cost=params.memory_kib,
        parallelism=params.parallelism,
        hash_len=params.hash_len,
        type=Type.ID,
    )


def aead_encrypt(key: bytes, plaintext: bytes, *, aad: bytes = b"") -> dict[str, str]:
    if len(key) != 32:
        raise ValueError("AES-GCM key must be 32 bytes")
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(key).encrypt(nonce, plaintext, aad or None)
    return {"nonce_hex": nonce.hex(), "ciphertext_hex": ct.hex()}


def aead_decrypt(key: bytes, blob: dict, *, aad: bytes = b"") -> bytes:
    nonce = bytes.fromhex(blob["nonce_hex"])
    ct = bytes.fromhex(blob["ciphertext_hex"])
    return AESGCM(key).decrypt(nonce, ct, aad or None)


def wrap_root(unlock_key: bytes, root_key: bytes, *, aad: bytes) -> dict[str, str]:
    return aead_encrypt(unlock_key, root_key, aad=aad)


def unwrap_root(unlock_key: bytes, blob: dict, *, aad: bytes) -> bytes:
    root = aead_decrypt(unlock_key, blob, aad=aad)
    if len(root) != ROOT_KEY_LEN:
        raise ValueError("Invalid vault root key length")
    return root


def random_token() -> str:
    return secrets.token_urlsafe(32)


def token_verifier(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
