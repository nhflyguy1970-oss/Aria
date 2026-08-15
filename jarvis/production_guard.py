"""Production / test isolation — live owner data is never a test target.

pytest already redirects DATA_DIR via fixtures. This module is the server-side
boundary: a production process using the live data root must refuse test-shaped
writes and refuse to start as a QA/cert/smoke environment.
"""

from __future__ import annotations

import os
from pathlib import Path

from jarvis.config import PROJECT_ROOT

# Fixed at import — tests monkeypatch jarvis.config.DATA_DIR but must not weaken this.
LIVE_DATA_ROOT = (PROJECT_ROOT / "data").resolve()

TEST_ENVIRONMENTS = frozenset(
    {"qa", "test", "testing", "smoke", "certification", "cert", "demo", "development", "dev"}
)
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
QA_HEADERS = ("x-aria-qa-run", "x-aria-test", "x-aria-certification")


class ProductionIsolationError(RuntimeError):
    """Raised when a test/QA/cert payload would land in Jeff's live workspace."""


def environment_name() -> str:
    raw = (os.environ.get("JARVIS_ENVIRONMENT") or os.environ.get("ARIA_ENVIRONMENT") or "").strip().lower()
    return raw or "production"


def is_test_environment() -> bool:
    return environment_name() in TEST_ENVIRONMENTS


def is_production_workspace() -> bool:
    """True when this process is bound to Jeff's live data directory."""
    from jarvis.config import DATA_DIR

    try:
        return Path(DATA_DIR).resolve() == LIVE_DATA_ROOT
    except OSError:
        return False


def looks_like_test_payload(*parts: str | None) -> bool:
    from jarvis.integrity_product.tags import looks_like_dev_label

    blob = " ".join(str(p or "") for p in parts).strip()
    if not blob:
        return False
    return looks_like_dev_label(blob)


def assert_environment_consistent() -> None:
    """Refuse to run QA/cert/smoke against the live workspace."""
    if is_test_environment() and is_production_workspace():
        raise ProductionIsolationError(
            f"JARVIS_ENVIRONMENT={environment_name()!r} cannot use live DATA_DIR "
            f"({LIVE_DATA_ROOT}). Point JARVIS_DATA_DIR at a disposable directory."
        )


def assert_owner_write_allowed(*parts: str | None, store: str = "workspace") -> None:
    """Block test-shaped writes into the live production workspace.

    Isolated DATA_DIR (pytest tmp_path, cert harnesses) may write test tokens —
    that data is disposable with the directory.
    """
    from jarvis.live_data_guard import assert_live_write_allowed
    from jarvis.config import DATA_DIR

    assert_live_write_allowed(DATA_DIR)
    if not is_production_workspace():
        return
    if not looks_like_test_payload(*parts):
        return
    raise ProductionIsolationError(
        f"Refusing to write test/QA/certification data into production {store}."
    )


def qa_header_present(headers: dict[str, str] | None) -> bool:
    if not headers:
        return False
    lowered = {str(k).lower(): str(v or "") for k, v in headers.items()}
    return any(lowered.get(h) for h in QA_HEADERS)


def reject_live_test_request(method: str, headers: dict[str, str] | None) -> str | None:
    """Return an error message if a harness is mutating the live workspace."""
    if str(method or "").upper() not in MUTATING_METHODS:
        return None
    if not is_production_workspace():
        return None
    if is_test_environment():
        return (
            "This server is bound to live owner data and cannot run as "
            f"{environment_name()}. Use an isolated JARVIS_DATA_DIR."
        )
    if qa_header_present(headers):
        return (
            "Test/QA harness headers are not allowed against the live workspace. "
            "Start a server with JARVIS_DATA_DIR pointing at disposable storage."
        )
    return None
