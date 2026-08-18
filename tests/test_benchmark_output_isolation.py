"""The NLU benchmark report must never be written into the real repository.

jarvis.nlu.benchmark._write_report resolves DATA_DIR.parent / "docs" and falls
back to the repository's own docs/ directory when that path is missing. Under
test isolation DATA_DIR points into scratch/, so the isolated docs/ directory
has to exist or the fallback rewrites the tracked
docs/NLU_CLASSIFIER_BENCHMARK.md.
"""

from __future__ import annotations

from pathlib import Path

from jarvis.config import DATA_DIR

REPO_DOCS = Path(__file__).resolve().parents[1] / "docs"
REPO_REPORT = REPO_DOCS / "NLU_CLASSIFIER_BENCHMARK.md"


def _resolved_report_path() -> Path:
    """Mirror the resolution in jarvis.nlu.benchmark._write_report."""
    path = DATA_DIR.parent / "docs" / "NLU_CLASSIFIER_BENCHMARK.md"
    if not path.parent.is_dir():
        path = Path(__file__).resolve().parents[1] / "docs" / "NLU_CLASSIFIER_BENCHMARK.md"
    return path


def test_isolated_docs_dir_exists(data_dir: Path) -> None:
    """The directory whose absence triggers the repository fallback must exist."""
    assert (DATA_DIR.parent / "docs").is_dir()


def test_benchmark_report_resolves_inside_scratch(data_dir: Path) -> None:
    resolved = _resolved_report_path().resolve()
    assert data_dir.parent in resolved.parents, f"{resolved} escaped the scratch root"


def test_benchmark_report_is_not_the_repo_file(data_dir: Path) -> None:
    resolved = _resolved_report_path().resolve()
    assert resolved != REPO_REPORT.resolve()
    assert REPO_DOCS.resolve() not in resolved.parents


def test_write_report_does_not_touch_the_repo(data_dir: Path) -> None:
    """Actually run the writer and prove the tracked report is untouched."""
    from jarvis.nlu import benchmark

    before = REPO_REPORT.read_bytes() if REPO_REPORT.is_file() else None

    benchmark._write_report(
        {
            "model": "test-model",
            "device": "cpu",
            "benchmark_date": "test",
            "average_latency_ms": 0,
            "selection_reason": "isolation test",
            "results": [],
        }
    )

    written = _resolved_report_path()
    assert written.is_file()
    assert "test-model" in written.read_text(encoding="utf-8")

    after = REPO_REPORT.read_bytes() if REPO_REPORT.is_file() else None
    assert after == before, "benchmark wrote into the real repository docs/"
