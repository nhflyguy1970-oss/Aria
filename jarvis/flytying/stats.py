"""Fast filesystem stats for the Blackfly fly-tying dataset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.flytying.config import (
    blackfly_data_available,
    blackfly_enablement,
    count_jsonl_lines,
    flytying_root,
    gold_recipes_path,
    output_dir,
    recipe_source_path,
    scraped_dataset_path,
)


def read_status() -> dict[str, Any]:
    root = flytying_root()
    scraped = scraped_dataset_path()
    gold = gold_recipes_path()
    source = recipe_source_path()
    out = output_dir()
    stats_file = out / "gold_stats.json"
    gold_count = 0
    types: dict[str, int] = {}
    index_built = (out / "gold_index").is_dir() or (out / "index").is_dir()
    # The index has already applied the quarantine, so its size is the honest
    # answer to "how many recipes are there": counting lines in the raw scrape
    # reported the fabricated records as part of the library.
    retrievable: int | None = None
    quarantined_count = 0
    try:
        from jarvis.flytying import index as recipe_index
        from jarvis.flytying.quarantine import quarantine_state

        rows = recipe_index.recipes()
        if rows:
            index_built = True
        retrievable = len(rows)
        quarantined_count = int(recipe_index._CACHE.get("quarantined") or 0)
        if quarantine_state()["status"] == "error":
            retrievable = 0
    except Exception:
        pass
    if stats_file.is_file():
        try:
            data = json.loads(stats_file.read_text(encoding="utf-8"))
            gold_count = int(data.get("gold_count") or data.get("count") or 0)
            types = dict(data.get("types") or {})
            index_built = bool(data.get("index_built", index_built))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    scraped_count = count_jsonl_lines(scraped)
    if gold_count == 0:
        gold_count = count_jsonl_lines(gold)
    loaded_count = count_jsonl_lines(source)
    source_line_count = loaded_count
    if retrievable is not None:
        loaded_count = retrievable
    enablement = blackfly_enablement()
    recipe_source_kind = "missing"
    if scraped.is_file():
        recipe_source_kind = "scraped"
    elif gold.is_file():
        recipe_source_kind = "gold"
    loaded = blackfly_data_available()
    return {
        "ok": True,
        "root": str(root),
        "scraped_path": str(scraped),
        "scraped_db_path": str(source),
        "scraped_exists": scraped.is_file(),
        "scraped_count": scraped_count,
        "gold_path": str(gold),
        "gold_exists": gold.is_file(),
        "gold_count": gold_count,
        "recipe_source_path": str(source),
        "recipe_source": recipe_source_kind,
        "recipe_source_note": "scraped JSONL preferred; gold is optional fallback when scrape missing",
        "recipe_count": loaded_count,
        "record_count": loaded_count,
        "source_line_count": source_line_count,
        "quarantined_count": quarantined_count,
        "loaded": loaded,
        "blackfly_loaded": loaded,
        "types": types,
        "index_built": index_built,
        "blackfly_enablement": enablement,
    }
