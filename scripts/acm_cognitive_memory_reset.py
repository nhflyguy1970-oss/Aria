#!/usr/bin/env python3
"""Archive then reset Aria embedded ACM autobiographical memory (operator tool).

Does NOT modify ACM architecture, organs, or source. Only runtime durable data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ARCHIVE_LABEL = "Pre-D041 Behavioral Validation"
ARCHIVE_MARK = (
    "Known contaminated identity data. Not suitable for future validation. "
    "Research archive only — never load during cognition."
)


def _default_persist() -> Path:
    from aria_core.acm_bridge import persist_path

    return Path(persist_path())


def _snapshot_counts(db_path: Path) -> dict:
    """Best-effort counts from live engine if DB readable; else file stats only."""
    out: dict = {
        "db_path": str(db_path),
        "db_bytes": db_path.stat().st_size if db_path.exists() else 0,
    }
    if not db_path.exists():
        return out
    try:
        from aria_core import acm_bridge

        acm_bridge.reset_for_tests()
        eng = acm_bridge.get_engine()
        store = eng.store
        out.update(
            {
                "experiences": len(store.experiences),
                "concepts": len(store.concepts),
                "associations": len(store.associations),
                "goals": len(store.goals),
                "adaptations": len(getattr(store, "adaptations", {}) or {}),
            }
        )
        for role in ("agent", "user", "project"):
            try:
                c = eng.identity.schema_concept(role)
                out[f"identity_{role}_attrs"] = [
                    {"key": a.key, "value": a.value[:120], "active": a.active}
                    for a in c.attributes
                ]
            except Exception as exc:  # noqa: BLE001
                out[f"identity_{role}_attrs"] = {"error": type(exc).__name__}
    except Exception as exc:  # noqa: BLE001
        out["engine_error"] = type(exc).__name__
    return out


def archive_and_reset(*, persist: Path, archive_root: Path) -> dict:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = archive_root / f"pre_d041_behavioral_validation_{ts}"
    dest.mkdir(parents=True, exist_ok=True)

    # Close engine / release SQLite handles before moving files
    from aria_core import acm_bridge

    pre = _snapshot_counts(persist)
    acm_bridge.reset_for_tests()
    eng = acm_bridge.get_engine()
    if getattr(eng, "durable", None) is not None:
        try:
            eng.durable.flush(kind="pre_archive_checkpoint")
        except Exception:
            pass
        try:
            eng.durable.close()
        except Exception:
            pass
    acm_bridge.reset_for_tests()

    files_moved: list[str] = []
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(persist) + suffix) if suffix else persist
        if src.exists():
            target = dest / src.name
            shutil.copy2(src, target)
            files_moved.append(str(target))

    manifest = {
        "label": ARCHIVE_LABEL,
        "mark": ARCHIVE_MARK,
        "archived_utc": ts,
        "source_persist_path": str(persist),
        "files": files_moved,
        "pre_reset_counts": pre,
        "suitable_for_cognition": False,
        "suitable_for_validation": False,
        "research_only": True,
    }
    (dest / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (dest / "README.md").write_text(
        f"# {ARCHIVE_LABEL}\n\n"
        f"{ARCHIVE_MARK}\n\n"
        f"- Archived UTC: `{ts}`\n"
        f"- Source: `{persist}`\n"
        f"- Do **not** point `ARIA_ACM_PERSIST_PATH` at this archive for production cognition.\n",
        encoding="utf-8",
    )

    # Remove live durable files
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(persist) + suffix) if suffix else persist
        if src.exists():
            src.unlink()

    # Create empty durable store
    persist.parent.mkdir(parents=True, exist_ok=True)
    acm_bridge.reset_for_tests()
    eng = acm_bridge.get_engine()
    if getattr(eng, "durable", None) is not None:
        eng.durable.flush(kind="post_reset_empty")
        eng.durable.close()
    acm_bridge.reset_for_tests()

    post = _snapshot_counts(persist)
    result = {
        "ok": True,
        "archive_dir": str(dest),
        "pre": pre,
        "post": post,
        "manifest": str(dest / "MANIFEST.json"),
    }
    (dest / "POST_RESET_VALIDATION.json").write_text(
        json.dumps({"post": post, "ok": _is_clean(post)}, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def _is_clean(counts: dict) -> bool:
    if int(counts.get("experiences") or 0) != 0:
        return False
    if int(counts.get("goals") or 0) != 0:
        return False
    if int(counts.get("associations") or 0) != 0:
        return False
    if int(counts.get("adaptations") or 0) != 0:
        return False
    # Learned concepts may include empty schema nuclei after ensure_schemas —
    # require no identity attribute values.
    for role in ("agent", "user", "project"):
        attrs = counts.get(f"identity_{role}_attrs") or []
        if isinstance(attrs, list) and any(a.get("active") and a.get("value") for a in attrs):
            return False
    # Non-schema concepts should be zero ideally; allow only identity schema shells
    concepts = int(counts.get("concepts") or 0)
    if concepts > 3:
        return False
    return True


def validate_only(*, persist: Path) -> dict:
    from aria_core import acm_bridge

    acm_bridge.reset_for_tests()
    counts = _snapshot_counts(persist)
    # Architecture smoke: classify + respond still work
    eng = acm_bridge.get_engine()
    classification = eng.classify_request("Who am I?")
    respond = eng.cognitive_respond("Who am I?")
    return {
        "clean": _is_clean(counts),
        "counts": counts,
        "architecture_ok": bool(classification) and isinstance(respond, dict),
        "classification_intent": (classification or {}).get("intent")
        if isinstance(classification, dict)
        else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--persist-path",
        type=Path,
        default=None,
        help="ACM durable path (default: aria_core.acm_bridge.persist_path())",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Archive root (default: <persist.parent>/archives)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate current store; do not archive/reset",
    )
    args = parser.parse_args()
    persist = args.persist_path or _default_persist()
    if args.validate_only:
        result = validate_only(persist=persist)
        print(json.dumps(result, indent=2))
        return 0 if result.get("clean") and result.get("architecture_ok") else 1

    archive_root = args.archive_root or (persist.parent / "archives")
    result = archive_and_reset(persist=persist, archive_root=archive_root)
    print(json.dumps(result, indent=2))
    # Re-validate
    v = validate_only(persist=persist)
    print(json.dumps({"validation": v}, indent=2))
    return 0 if result.get("ok") and v.get("clean") and v.get("architecture_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
