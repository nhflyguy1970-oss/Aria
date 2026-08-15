"""Fly-tying subsystem configuration — paths into the Blackfly scrape project."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

DEFAULT_FLYTYING_ROOT = Path("/media/jeff/C/fly_fishing_project")

_ROOT_CACHE: dict[str, object] = {"at": 0.0, "value": None}
_ENABLEMENT_CACHE: dict[str, object] = {"at": 0.0, "value": None}
_ROOT_CACHE_TTL_S = 60.0
_ENABLEMENT_CACHE_TTL_S = 30.0


def _discover_zenflow_roots() -> list[Path]:
    """Auto-discover Blackfly scrape outputs under ~/.zenflow/worktrees/*/output/."""
    base = Path.home() / ".zenflow" / "worktrees"
    if not base.is_dir():
        return []
    found: list[tuple[float, Path]] = []
    for dataset in base.glob("*/output/dataset.jsonl"):
        if dataset.is_file():
            found.append((dataset.stat().st_mtime, dataset.parent.parent))
    for gold in base.glob("*/output/gold_recipes.jsonl"):
        if gold.is_file():
            found.append((gold.stat().st_mtime, gold.parent.parent))
    found.sort(key=lambda pair: -pair[0])
    seen: set[str] = set()
    out: list[Path] = []
    for _, root in found:
        key = str(root.resolve())
        if key in seen:
            continue
        seen.add(key)
        out.append(root)
    return out


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    raw = (os.environ.get("JARVIS_FLYTYING_ROOT") or "").strip()
    if raw:
        roots.append(Path(raw).expanduser())
    fly_out = (os.environ.get("FLY_OUTPUT_DIR") or "").strip()
    if fly_out:
        p = Path(fly_out).expanduser()
        roots.append(p.parent if p.suffix == ".jsonl" else p)
        if p.is_dir() or p.suffix != ".jsonl":
            roots.append(p if p.is_dir() else p.parent)
    roots.extend(
        [
            DEFAULT_FLYTYING_ROOT,
            *_discover_zenflow_roots(),
        ]
    )
    seen: set[str] = set()
    out: list[Path] = []
    for root in roots:
        key = str(root.expanduser().resolve()) if root.expanduser().exists() else str(root.expanduser())
        if key in seen:
            continue
        seen.add(key)
        out.append(root.expanduser())
    return out


def _has_blackfly_output(root: Path) -> bool:
    out = root / "output"
    if (out / "dataset.jsonl").is_file() or (out / "gold_recipes.jsonl").is_file():
        return True
    # FLY_OUTPUT_DIR may point directly at output/ or a jsonl file's parent.
    if (root / "dataset.jsonl").is_file() or (root / "gold_recipes.jsonl").is_file():
        return True
    return False


def _root_stats(root: Path) -> tuple[int, int, bool]:
    """(gold_lines, scraped_lines, has_blackfly_modules)."""
    out = root / "output"
    bases = [out, root] if out.is_dir() else [root]
    gold_n = 0
    scraped_n = 0
    for base in bases:
        g = base / "gold_recipes.jsonl"
        s = base / "dataset.jsonl"
        if g.is_file():
            gold_n = max(gold_n, count_jsonl_lines(g))
        if s.is_file():
            scraped_n = max(scraped_n, count_jsonl_lines(s))
    has_modules = (root / "blackfly_rag.py").is_file() and (root / "blackfly_gold.py").is_file()
    return gold_n, scraped_n, has_modules


def flytying_root() -> Path:
    """Blackfly project root — prefer gold dataset + full Blackfly tree over tiny stubs."""
    now = time.monotonic()
    cached = _ROOT_CACHE.get("value")
    if (
        isinstance(cached, Path)
        and now - float(_ROOT_CACHE.get("at") or 0) < _ROOT_CACHE_TTL_S
    ):
        return cached

    scored: list[tuple[int, int, int, Path]] = []
    for root in _candidate_roots():
        if not _has_blackfly_output(root):
            continue
        gold_n, scraped_n, has_modules = _root_stats(root)
        scored.append((scraped_n, gold_n, 1 if has_modules else 0, root))
    if scored:
        scored.sort(key=lambda row: (-row[0], -row[1], -row[2], str(row[3])))
        chosen = scored[0][3].resolve()
    else:
        raw = (os.environ.get("JARVIS_FLYTYING_ROOT") or "").strip()
        if raw:
            chosen = Path(raw).expanduser().resolve()
        elif DEFAULT_FLYTYING_ROOT.is_dir():
            chosen = DEFAULT_FLYTYING_ROOT.resolve()
        else:
            zenflow = _discover_zenflow_roots()
            chosen = zenflow[0].resolve() if zenflow else DEFAULT_FLYTYING_ROOT
    _ROOT_CACHE["at"] = now
    _ROOT_CACHE["value"] = chosen
    return chosen


def output_dir() -> Path:
    fly_out = (os.environ.get("FLY_OUTPUT_DIR") or "").strip()
    if fly_out:
        p = Path(fly_out).expanduser().resolve()
        if p.suffix == ".jsonl":
            return p.parent
        if (p / "dataset.jsonl").is_file() or (p / "gold_recipes.jsonl").is_file():
            return p
        return p
    root = flytying_root()
    if (root / "dataset.jsonl").is_file() or (root / "gold_recipes.jsonl").is_file():
        return root
    return root / "output"


def scraped_dataset_path() -> Path:
    """Raw Blackfly scrape — primary authoritative store (JSONL)."""
    return output_dir() / "dataset.jsonl"


def gold_recipes_path() -> Path:
    """Quality-filtered recipes built from the scrape (JSONL)."""
    return output_dir() / "gold_recipes.jsonl"


def recipe_source_path() -> Path:
    """Active recipe library: scraped JSONL when available; gold is optional fallback."""
    scraped = scraped_dataset_path()
    if scraped.is_file():
        return scraped
    gold = gold_recipes_path()
    if gold.is_file():
        return gold
    return scraped


def images_root() -> Path:
    return output_dir() / "images"


def blackfly_data_available() -> bool:
    scraped = scraped_dataset_path()
    gold = gold_recipes_path()
    return scraped.is_file() or gold.is_file()


_JSONL_COUNT_CACHE: dict[str, tuple[int, int, float]] = {}


def count_jsonl_lines(path: Path) -> int:
    """Count non-empty lines; cache by path mtime/size so status probes stay cheap."""
    if not path.is_file():
        return 0
    try:
        st = path.stat()
    except OSError:
        return 0
    key = str(path.resolve())
    cached = _JSONL_COUNT_CACHE.get(key)
    if cached and cached[0] == st.st_mtime_ns and cached[1] == st.st_size:
        return cached[2]
    try:
        # Stream — do not load multi‑MB JSONL into one string on every status call.
        n = 0
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.strip():
                    n += 1
    except OSError:
        return 0
    _JSONL_COUNT_CACHE[key] = (st.st_mtime_ns, st.st_size, n)
    return n


def ensure_blackfly_on_path() -> Path:
    """Add Blackfly project root to sys.path so blackfly_rag / blackfly_gold can import."""
    root = flytying_root()
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    return root


def blackfly_enablement() -> dict[str, str | bool]:
    now = time.monotonic()
    cached = _ENABLEMENT_CACHE.get("value")
    if isinstance(cached, dict) and now - float(_ENABLEMENT_CACHE.get("at") or 0) < _ENABLEMENT_CACHE_TTL_S:
        return dict(cached)

    root = flytying_root()
    scraped = scraped_dataset_path()
    gold = gold_recipes_path()
    source = recipe_source_path()
    data_ok = blackfly_data_available()
    ensure_blackfly_on_path()
    rag_ok = False
    try:
        import blackfly_rag  # noqa: F401

        rag_ok = True
    except Exception:
        rag_ok = False
    hints: list[str] = []
    gold_n, scraped_n, has_modules = _root_stats(root)
    if not data_ok:
        hints.append(f"Mount or clone Blackfly scrape data at {DEFAULT_FLYTYING_ROOT}/output/dataset.jsonl")
        hints.append("Or set JARVIS_FLYTYING_ROOT=/path/to/fly_fishing_project in data/jarvis.env")
        hints.append("Or place dataset.jsonl under ~/.zenflow/worktrees/<worktree>/output/")
    elif gold_n <= 0 and scraped_n < 100:
        hints.append(
            f"Only {scraped_n} scraped recipes here (no gold) — mount your Blackfly project or set JARVIS_FLYTYING_ROOT"
        )
    elif not has_modules:
        hints.append("Blackfly Python modules missing in project root (blackfly_rag.py, blackfly_gold.py)")
    if data_ok and not rag_ok:
        hints.append("Semantic search: ensure blackfly_rag.py is in the Blackfly project root (same folder as blackfly_ai.py)")
    value: dict[str, str | bool] = {
        "project_root": str(root),
        "scraped_path": str(scraped),
        "scraped_db_path": str(source),
        "gold_path": str(gold),
        "gold_count": gold_n,
        "scraped_count": scraped_n,
        "has_blackfly_modules": has_modules,
        "data_available": data_ok,
        "loaded": data_ok,
        "record_count": count_jsonl_lines(source) if data_ok else 0,
        "rag_available": rag_ok,
        "hint": "; ".join(hints) if hints else "",
    }
    _ENABLEMENT_CACHE["at"] = now
    _ENABLEMENT_CACHE["value"] = value
    return dict(value)
