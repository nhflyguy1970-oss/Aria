#!/usr/bin/env python3
"""M4e — Archive legacy MemoryStore files to cold vault (operator tool; never auto).

Copies memory.json / memory.db into JARVIS_DATA_DIR/vault/memory_pre_acm_<date>.*.
Does not delete live files unless --remove-active (dangerous; opt-in).
Vault is read-only forensic — Cap Bus does not query it when ACM PRIMARY.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path


def _checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Override JARVIS_DATA_DIR / config DATA_DIR",
    )
    parser.add_argument(
        "--remove-active",
        action="store_true",
        help="After successful vault copy, remove active memory.json/db (opt-in)",
    )
    args = parser.parse_args()

    if args.data_dir:
        data = args.data_dir
    else:
        try:
            from jarvis.config import DATA_DIR

            data = Path(DATA_DIR)
        except Exception:
            data = Path("data")

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    vault = data / "vault"
    vault.mkdir(parents=True, exist_ok=True)

    candidates = [
        data / "memory.json",
        data / "memory.db",
        data / "memory.sqlite",
        data / "memory.sqlite3",
    ]
    copied = []
    for src in candidates:
        if not src.exists():
            continue
        dest = vault / f"memory_pre_acm_{stamp}{src.suffix}"
        shutil.copy2(src, dest)
        checksum = _checksum(dest)
        report = dest.with_suffix(dest.suffix + ".sha256")
        report.write_text(f"{checksum}  {dest.name}\n", encoding="utf-8")
        copied.append({"src": str(src), "dest": str(dest), "sha256": checksum})
        if args.remove_active:
            src.unlink()
            print(f"removed active: {src}")

    if not copied:
        print("No legacy memory files found to vault.")
        return 0
    for row in copied:
        print(f"vaulted {row['src']} -> {row['dest']} sha256={row['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
