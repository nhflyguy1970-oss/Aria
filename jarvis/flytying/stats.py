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
    try:
        from jarvis.flytying import index as recipe_index

        if recipe_index.recipes():
            index_built = True
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
        "loaded": loaded,
        "blackfly_loaded": loaded,
        "types": types,
        "index_built": index_built,
        "blackfly_enablement": enablement,
    }
