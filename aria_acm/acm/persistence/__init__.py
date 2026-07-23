"""Public persistence façade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from acm.core.store import CognitiveStore
from acm.persistence.codec import checksum_payload, export_store, import_store, verify_snapshot
from acm.persistence.schema import SCHEMA_VERSION
from acm.persistence.sqlite import SqliteDurableStore


class DurableCognitiveStore:
    """ACM-owned durable persistence. Hosts never own ACM storage files."""

    def __init__(
        self,
        path: str | Path,
        store: CognitiveStore | None = None,
        *,
        max_snapshots: int | None = None,
    ) -> None:
        self.backend = SqliteDurableStore(path, max_snapshots=max_snapshots)
        self.store = store or CognitiveStore()
        self.load_ok = True
        self.load_error: str | None = None
        try:
            self.backend.load_latest(self.store)
        except ValueError as exc:
            # Empty DB returns without raising. ValueError means corrupt snapshot —
            # never treat as first-open empty store (would auto_persist wipe SoT).
            self.load_ok = False
            self.load_error = str(exc)
            raise RuntimeError(
                f"ACM durable load failed (refusing empty overwrite): {exc}"
            ) from exc

    def flush(self, *, kind: str = "checkpoint") -> dict[str, Any]:
        return self.backend.save(self.store, kind=kind)

    def snapshot(self) -> dict[str, Any]:
        return export_store(self.store)

    def export(self, dest: str | Path) -> dict[str, Any]:
        return self.backend.export_file(self.store, dest)

    def import_snapshot(self, src: str | Path) -> dict[str, Any]:
        self.backend.import_file(src, store=self.store)
        return {"ok": True, "experiences": len(self.store.experiences)}

    def backup(self, dest: str | Path) -> dict[str, Any]:
        self.flush(kind="pre_backup")
        return self.backend.backup(dest)

    def restore(self, src: str | Path) -> dict[str, Any]:
        result = self.backend.restore_backup(src)
        self.backend.load_latest(self.store)
        return result

    def verify(self) -> dict[str, Any]:
        snap = export_store(self.store)
        errors = verify_snapshot(snap)
        integrity = self.backend.integrity()
        return {
            "snapshot_errors": errors,
            "checksum": snap.get("checksum"),
            "schema_version": SCHEMA_VERSION,
            "integrity": integrity,
            "ok": not errors and integrity.get("ok"),
        }

    def metrics(self) -> dict[str, Any]:
        return self.backend.metrics()

    def close(self) -> None:
        self.backend.close()


__all__ = [
    "DurableCognitiveStore",
    "SqliteDurableStore",
    "SCHEMA_VERSION",
    "export_store",
    "import_store",
    "verify_snapshot",
    "checksum_payload",
]
