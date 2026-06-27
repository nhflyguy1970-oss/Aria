"""Nightly fly-tying learning — library sync, video embed enrichment, memory lessons."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.flytying.nightly")

STATE_FILE = DATA_DIR / "flytying_nightly_state.json"


def _env_flag(name: str, *, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "off", "no")


def nightly_enabled() -> bool:
    return _env_flag("JARVIS_FLYTYING_NIGHTLY_LEARNING", default=True)


def nightly_hour() -> int:
    try:
        return int(os.getenv("JARVIS_FLYTYING_LEARNING_HOUR", os.getenv("JARVIS_KNOWLEDGE_RESEARCH_HOUR", "23")))
    except ValueError:
        return 23


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.is_file():
        return {"days": {}}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"days": {}}
    except (OSError, json.JSONDecodeError):
        return {"days": {}}


def _save_state(data: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _today() -> str:
    return datetime.now().date().isoformat()


def _already_ran(day: str | None = None) -> bool:
    d = day or _today()
    return bool((_load_state().get("days") or {}).get(d, {}).get("completed"))


def _mark_ran(day: str, result: dict[str, Any]) -> None:
    data = _load_state()
    data.setdefault("days", {})[day] = {"completed": True, **result}
    if len(data["days"]) > 45:
        for old in sorted(data["days"])[:-30]:
            data["days"].pop(old, None)
    _save_state(data)


def enrich_article_embeds(*, limit: int = 8) -> dict[str, Any]:
    """Scrape Fly Fish Food / similar article pages for embedded YouTube/Vimeo."""
    import json as _json

    from jarvis.flytying.config import recipe_source_path
    from jarvis.flytying.media import recipe_videos, video_dict_from_url
    from jarvis.flytying.video_fetch import discover_videos_from_url
    from jarvis.flytying.videos_store import get_cached_videos, set_cached_videos

    path = recipe_source_path()
    if not path.is_file():
        return {"ok": False, "enriched": 0, "message": "Blackfly scraped database missing"}

    targets: list[tuple[str, str]] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    recipe = _json.loads(line)
                except _json.JSONDecodeError:
                    continue
                if not isinstance(recipe, dict):
                    continue
                source = str(recipe.get("source_url") or "")
                low = source.lower()
                if not any(s in low for s in ("flyfishfood.com", "midcurrent.com", "globalflyfisher.com")):
                    continue
                name = str(recipe.get("fly_name") or recipe.get("name") or recipe.get("instruction") or "")
                existing = recipe_videos(recipe)
                has_embed = any(v.get("embed_url") for v in existing if v.get("provider") != "flyfishfood")
                if has_embed:
                    continue
                if get_cached_videos(source):
                    continue
                targets.append((source, name))
    except OSError as exc:
        return {"ok": False, "enriched": 0, "message": str(exc)}

    enriched = 0
    for page_url, name in targets[: max(1, limit)]:
        try:
            found = discover_videos_from_url(page_url)
            rows = []
            for v in found:
                row = video_dict_from_url(v.get("watch_url") or v.get("embed_url") or page_url) or v
                row["recipe_name"] = name
                row["source_page"] = page_url
                rows.append(row)
            if rows:
                set_cached_videos(page_url, rows)
                enriched += 1
        except Exception as exc:
            log.debug("Embed enrich failed %s: %s", page_url[:60], exc)
    return {"ok": True, "enriched": enriched, "candidates": len(targets)}


def learn_recipe_of_the_day(*, memory_store=None) -> dict[str, Any]:
    """Add one short fly-tying fact to memory (rotates through gold library)."""
    import json as _json

    from jarvis.flytying.config import recipe_source_path
    from jarvis.flytying.knowledge import FLYTYING_MEMORY_NAMESPACE

    if memory_store is None:
        return {"ok": False, "skipped": True, "message": "no memory store"}

    path = recipe_source_path()
    if not path.is_file():
        return {"ok": False, "message": "Blackfly scraped database missing"}

    recipes: list[dict[str, Any]] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = _json.loads(line)
                except _json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    recipes.append(item)
    except OSError:
        return {"ok": False, "message": "read failed"}
    if not recipes:
        return {"ok": False, "message": "empty library"}

    day = _today()
    idx = sum(ord(c) for c in day) % len(recipes)
    recipe = recipes[idx]
    name = str(recipe.get("fly_name") or recipe.get("name") or recipe.get("instruction") or "Pattern")
    rtype = recipe.get("type") or "?"
    hook = recipe.get("hook") or ""
    mats = recipe.get("materials") or []
    mat_preview = "; ".join(str(m) for m in mats[:4])
    content = f"Pattern of the day: **{name}** ({rtype})."
    if hook:
        content += f" Hook: {hook}."
    if mat_preview:
        content += f" Key materials: {mat_preview}."
    tag = f"fly-tying-daily:{day}"
    for entry in memory_store.list_entries(namespace=FLYTYING_MEMORY_NAMESPACE):
        if tag in (entry.get("tags") or []):
            return {"ok": True, "skipped": True, "message": "already learned today", "pattern": name}
    memory_store.add(
        "note",
        content,
        tags=["fly-tying-daily", tag, "document-learn"],
        namespace=FLYTYING_MEMORY_NAMESPACE,
    )
    return {"ok": True, "pattern": name, "message": content}


def run_nightly_flytying_learning(
    *,
    memory=None,
    day: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    if not nightly_enabled() and not force:
        return {"ok": False, "message": "Nightly fly-tying learning disabled."}

    d = day or _today()
    if not force and _already_ran(d):
        return {"ok": True, "skipped": True, "message": f"Already completed fly-tying learning for {d}."}

    from jarvis.flytying.knowledge import seed_memory, sync_library

    sync_result = sync_library(force=False)
    embed_result = enrich_article_embeds(limit=int(os.getenv("JARVIS_FLYTYING_EMBED_PER_NIGHT", "8")))
    learn_result = learn_recipe_of_the_day(memory_store=memory)
    seeded = 0
    try:
        if memory is not None:
            seeded = seed_memory(memory)
    except Exception:
        pass

    result = {
        "ok": True,
        "day": d,
        "sync": sync_result,
        "embeds": embed_result,
        "lesson": learn_result,
        "memory_seeded": seeded,
        "message": f"Fly-tying nightly learning completed for {d}.",
    }
    _mark_ran(d, result)
    log.info(
        "Fly-tying nightly: sync=%s embeds=%s pattern=%s",
        sync_result.get("written") or sync_result.get("skipped"),
        embed_result.get("enriched"),
        learn_result.get("pattern"),
    )
    return result


def run_scheduled(now: datetime | None = None, *, memory=None) -> dict[str, Any]:
    if not nightly_enabled():
        return {"ok": False, "skipped": True}
    now = now or datetime.now()
    if now.hour != nightly_hour() or now.minute >= 20:
        return {"ok": False, "skipped": True}
    return run_nightly_flytying_learning(memory=memory)


def run_startup_catchup(*, memory=None) -> dict[str, Any]:
    if not nightly_enabled() or _already_ran():
        return {"ok": False, "skipped": True}
    now = datetime.now()
    if now.hour >= nightly_hour():
        return run_nightly_flytying_learning(memory=memory)
    return {"ok": False, "skipped": True}


def nightly_status() -> dict[str, Any]:
    state = _load_state()
    last_day = max((state.get("days") or {}).keys(), default="")
    last = (state.get("days") or {}).get(last_day) or {}
    return {
        "enabled": nightly_enabled(),
        "hour": nightly_hour(),
        "last_day": last_day,
        "last_result": last,
    }
