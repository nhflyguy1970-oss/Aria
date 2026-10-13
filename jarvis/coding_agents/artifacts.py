"""Controller-owned evidence. No credential/session state is included in artifacts."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path


def capture(directory: Path, *, patch: str, tests: dict | None, logs: dict) -> dict:
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    rows = []
    payloads = {"changes.patch": patch.encode(), "tests.json": json.dumps(tests, sort_keys=True).encode()}
    for kind, raw in logs.items():
        path = Path(raw)
        if path.is_file() and not path.is_symlink():
            payloads[kind + ".log"] = path.read_bytes()
    if tests and tests.get("output_log"):
        path = Path(tests["output_log"])
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("test evidence is missing or redirected")
        payloads["verification.log"] = path.read_bytes()
    for name, data in payloads.items():
        path = directory / name
        path.write_bytes(data)
        path.chmod(0o600)
        rows.append({"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps(rows, indent=2))
    manifest.chmod(0o600)
    result = {"directory": str(directory), "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(), "files": rows}
    verify(result)
    return result


def verify(record: dict) -> None:
    directory = Path(record["directory"])
    if directory.is_symlink():
        raise RuntimeError("artifact directory redirected")
    manifest = directory / "manifest.json"
    if manifest.is_symlink() or hashlib.sha256(manifest.read_bytes()).hexdigest() != record["manifest_sha256"]:
        raise RuntimeError("artifact manifest changed")
    rows = json.loads(manifest.read_text())
    if rows != record["files"]:
        raise RuntimeError("artifact manifest does not match the receipt")
    for row in rows:
        if Path(row["name"]).name != row["name"]:
            raise RuntimeError("invalid artifact path")
        path = directory / row["name"]
        if path.is_symlink() or path.stat().st_size != row["bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise RuntimeError("artifact bytes changed: " + row["name"])
