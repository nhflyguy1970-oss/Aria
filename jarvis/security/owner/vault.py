"""Empty Owner Vault store — AEAD entries under Vault Root Key.

M1: create/load empty vault; put/get for isol tests only (no live migration).
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from jarvis.security.owner import crypto as C


class VaultError(Exception):
    """Vault operation failed (safe message; no secrets)."""


class VaultLockedError(VaultError):
    pass


class VaultAuthError(VaultError):
    pass


class OwnerVault:
    """Process-local vault with root key held only while unlocked."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._root: bytearray | None = None
        self._doc: dict[str, Any] | None = None
        self._entry_cache: dict[str, bytes] = {}

    # --- lifecycle ---

    def exists(self) -> bool:
        return self.path.is_file()

    def is_unlocked(self) -> bool:
        return self._root is not None

    def lock(self) -> None:
        """Best-effort clear of root + caches. Not a guaranteed RAM wipe."""
        self._entry_cache.clear()
        if self._root is not None:
            for i in range(len(self._root)):
                self._root[i] = 0
            self._root = None

    def status(self) -> dict[str, Any]:
        doc = self._load_doc_readonly() if self.exists() else None
        return {
            "exists": self.exists(),
            "unlocked": self.is_unlocked(),
            "format": (doc or {}).get("format"),
            "entry_count": len((doc or {}).get("entries") or {}),
            "kdf": ((doc or {}).get("master_kdf") or {}).get("name"),
            "recovery_configured": bool((doc or {}).get("recovery")),
            "created_at": (doc or {}).get("created_at"),
        }

    # --- setup / unlock / recovery ---

    def initialize(
        self,
        master_password: str,
        *,
        min_password_len: int = 12,
    ) -> dict[str, Any]:
        """Create empty vault. Returns recovery key once (caller must show Jeff)."""
        if self.exists():
            raise VaultError("Vault already exists")
        pw = (master_password or "").strip()
        if len(pw) < min_password_len:
            raise VaultError(f"Master password must be at least {min_password_len} characters")

        root = C.new_root_key()
        recovery_raw = C.new_recovery_key()
        master_kdf = C.KdfParams(salt=C.new_salt())
        recovery_kdf = C.KdfParams(salt=C.new_salt())

        master_unlock = C.derive_key(pw, master_kdf)
        recovery_unlock = C.derive_key(recovery_raw, recovery_kdf)

        aad = C.VAULT_FORMAT.encode("utf-8")
        doc = {
            "format": C.VAULT_FORMAT,
            "created_at": time.time(),
            "version": 1,
            "master_kdf": master_kdf.to_public_dict(),
            "wrapped_root_master": C.wrap_root(master_unlock, root, aad=aad),
            "recovery": {
                "kdf": recovery_kdf.to_public_dict(),
                "wrapped_root": C.wrap_root(recovery_unlock, root, aad=aad),
            },
            "entries": {},
            "meta": {"phase": "M1", "empty": True},
        }
        self._atomic_write(doc)
        self._doc = doc
        self._root = bytearray(root)
        self._entry_cache.clear()
        return {
            "ok": True,
            "recovery_key": C.format_recovery_key(recovery_raw),
            "recovery_ack_required": True,
            "message": (
                "Store this recovery key offline. Aria cannot recover a forgotten "
                "master password without it. This key is shown once."
            ),
        }

    def unlock(self, master_password: str) -> dict[str, Any]:
        if not self.exists():
            raise VaultError("Vault not initialized")
        doc = self._load_doc()
        kdf = C.KdfParams.from_dict(doc["master_kdf"])
        try:
            unlock = C.derive_key((master_password or "").strip(), kdf)
            root = C.unwrap_root(
                unlock,
                doc["wrapped_root_master"],
                aad=C.VAULT_FORMAT.encode("utf-8"),
            )
        except Exception as exc:
            raise VaultAuthError("Incorrect master password or corrupt vault") from exc
        self._doc = doc
        self._root = bytearray(root)
        self._entry_cache.clear()
        return {"ok": True, "unlocked": True}

    def change_master_password(self, current: str, new_password: str, *, min_password_len: int = 12) -> dict[str, Any]:
        """Re-wrap root under new master; entries unchanged."""
        self.unlock(current)
        assert self._root is not None
        pw = (new_password or "").strip()
        if len(pw) < min_password_len:
            raise VaultError(f"Master password must be at least {min_password_len} characters")
        doc = self._load_doc()
        root = bytes(self._root)
        master_kdf = C.KdfParams(salt=C.new_salt())
        unlock = C.derive_key(pw, master_kdf)
        aad = C.VAULT_FORMAT.encode("utf-8")
        doc["master_kdf"] = master_kdf.to_public_dict()
        doc["wrapped_root_master"] = C.wrap_root(unlock, root, aad=aad)
        doc["meta"] = {**(doc.get("meta") or {}), "master_rotated_at": time.time()}
        self._atomic_write(doc)
        self._doc = doc
        return {"ok": True, "rotated": True}

    def recover_with_key(self, recovery_key: str, new_master_password: str, *, min_password_len: int = 12) -> dict[str, Any]:
        """Unwrap root via recovery key; re-wrap under new master. Rotates master wrap."""
        if not self.exists():
            raise VaultError("Vault not initialized")
        pw = (new_master_password or "").strip()
        if len(pw) < min_password_len:
            raise VaultError(f"Master password must be at least {min_password_len} characters")
        doc = self._load_doc()
        recovery = doc.get("recovery") or {}
        try:
            raw = C.parse_recovery_key(recovery_key)
            kdf = C.KdfParams.from_dict(recovery["kdf"])
            unlock = C.derive_key(raw, kdf)
            root = C.unwrap_root(
                unlock,
                recovery["wrapped_root"],
                aad=C.VAULT_FORMAT.encode("utf-8"),
            )
        except Exception as exc:
            raise VaultAuthError("Incorrect recovery key or corrupt vault") from exc

        # Re-wrap under new master; also rotate recovery wrap with same recovery key
        # (recovery key itself unchanged — Jeff still holds it).
        master_kdf = C.KdfParams(salt=C.new_salt())
        master_unlock = C.derive_key(pw, master_kdf)
        aad = C.VAULT_FORMAT.encode("utf-8")
        doc["master_kdf"] = master_kdf.to_public_dict()
        doc["wrapped_root_master"] = C.wrap_root(master_unlock, root, aad=aad)
        # Keep recovery wrap valid for same key (re-encrypt under same recovery unlock)
        recovery_unlock = C.derive_key(raw, C.KdfParams.from_dict(recovery["kdf"]))
        doc["recovery"] = {
            "kdf": recovery["kdf"],
            "wrapped_root": C.wrap_root(recovery_unlock, root, aad=aad),
        }
        doc["meta"] = {**(doc.get("meta") or {}), "recovered_at": time.time()}
        self._atomic_write(doc)
        self._doc = doc
        self._root = bytearray(root)
        self._entry_cache.clear()
        return {"ok": True, "recovered": True, "unlocked": True}

    # --- entries ---

    def list_meta(self) -> list[dict[str, Any]]:
        doc = self._require_doc()
        out = []
        for eid, row in (doc.get("entries") or {}).items():
            out.append(
                {
                    "id": eid,
                    "kind": row.get("kind"),
                    "label": row.get("label"),
                    "meta": row.get("meta") or {},
                }
            )
        return out

    def put_secret(
        self,
        entry_id: str,
        secret: bytes | str,
        *,
        kind: str = "opaque",
        label: str = "",
        meta: dict | None = None,
    ) -> dict[str, Any]:
        root = self._require_root()
        doc = self._require_doc()
        if isinstance(secret, str):
            secret_b = secret.encode("utf-8")
        else:
            secret_b = secret
        blob = C.aead_encrypt(bytes(root), secret_b, aad=entry_id.encode("utf-8"))
        doc.setdefault("entries", {})[entry_id] = {
            "kind": kind,
            "label": label or entry_id,
            "meta": {**(meta or {}), "updated_at": time.time()},
            "ciphertext": blob,
        }
        doc["meta"] = {**(doc.get("meta") or {}), "empty": len(doc["entries"]) == 0}
        self._atomic_write(doc)
        self._doc = doc
        self._entry_cache[entry_id] = secret_b
        return {"ok": True, "id": entry_id}

    def get_secret(self, entry_id: str) -> bytes:
        root = self._require_root()
        if entry_id in self._entry_cache:
            return self._entry_cache[entry_id]
        doc = self._require_doc()
        row = (doc.get("entries") or {}).get(entry_id)
        if not row:
            raise VaultError(f"Unknown vault entry: {entry_id}")
        pt = C.aead_decrypt(bytes(root), row["ciphertext"], aad=entry_id.encode("utf-8"))
        self._entry_cache[entry_id] = pt
        return pt

    # --- internals ---

    def _require_root(self) -> bytearray:
        if self._root is None:
            raise VaultLockedError("Vault is locked")
        return self._root

    def _require_doc(self) -> dict[str, Any]:
        if self._doc is None:
            self._doc = self._load_doc()
        return self._doc

    def _load_doc_readonly(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise VaultError("Vault file unreadable") from exc

    def _load_doc(self) -> dict[str, Any]:
        doc = self._load_doc_readonly()
        if doc.get("format") != C.VAULT_FORMAT:
            raise VaultError("Unsupported vault format")
        return doc

    def _atomic_write(self, doc: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(doc, indent=2, ensure_ascii=False)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), prefix=".vault-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(raw)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
        finally:
            if os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
