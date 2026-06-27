"""Teach main ARIA chat fly tying — document library sync + context injection."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

FLYTYING_DOCS_DIR = DATA_DIR / "documents" / "flytying"
FLYTYING_RECIPES_DIR = FLYTYING_DOCS_DIR / "recipes"
SYNC_MARKER = DATA_DIR / "flytying_library_sync.json"
FLYTYING_MEMORY_NAMESPACE = "fly-tying"
MAX_CONTEXT_CHARS = 3200

_FLY_CHAT_RE = re.compile(
    r"\b(fly\s*tying|fly\s*pattern|dry\s*fly|wet\s*fly|nymph|emerger|streamer|"
    r"terrestrial|hackle|dubbing|marabou|cdc|parachute|woolly\s*bugger|adams|"
    r"elk\s*hair|tying\s*bench|vise|hook\s*size|bead\s*head|materials?\s+"
    r"(?:on\s+hand|i\s+have))\b",
    re.I,
)


def _slug(name: str = "", rid: str = "") -> str:
    base = re.sub(r"[^\w\s-]", "", (name or "pattern").lower())
    base = re.sub(r"[\s_]+", "-", base).strip("-")[:50] or "pattern"
    short = re.sub(r"[^\w]", "", rid or "")[:12]
    return f"{base}-{short}" if short else base


def _recipe_markdown(recipe: dict) -> str:
    name = str(recipe.get("fly_name") or recipe.get("name") or "Pattern")
    lines = [f"# {name}", ""]
    if recipe.get("type"):
        lines.append(f"Type: {recipe['type']}")
    if recipe.get("hook"):
        lines.append(f"Hook: {recipe['hook']}")
    mats = recipe.get("materials") or []
    if mats:
        lines.append("")
        lines.append("## Materials")
        for m in mats[:25]:
            lines.append(f"- {m}")
    steps = recipe.get("steps") or []
    if steps:
        lines.append("")
        lines.append("## Steps")
        for i, step in enumerate(steps[:30], 1):
            lines.append(f"{i}. {step}")
    if recipe.get("source_url"):
        lines.append("")
        lines.append(f"Source: {recipe['source_url']}")
    return "\n".join(lines).strip() + "\n"


def sync_library(*, force: bool = False) -> dict[str, Any]:
    """Export Blackfly library JSONL into data/documents/flytying/ (secondary mirror for documents_rag)."""
    from jarvis.flytying.config import blackfly_data_available, recipe_source_path, scraped_dataset_path

    if not blackfly_data_available():
        return {
            "ok": False,
            "message": "Blackfly scraped database missing",
            "exported": 0,
            "scraped_path": str(scraped_dataset_path()),
        }

    gold = recipe_source_path()
    if not gold.is_file():
        return {"ok": False, "message": "Blackfly recipe library missing", "exported": 0}

    FLYTYING_RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    exported = 0
    try:
        for line in gold.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            recipe = json.loads(line)
            rid = str(recipe.get("id") or recipe.get("recipe_id") or "")
            name = str(recipe.get("fly_name") or recipe.get("name") or "pattern")
            dest = FLYTYING_RECIPES_DIR / f"{_slug(name, rid)}.md"
            if dest.is_file() and not force:
                continue
            dest.write_text(_recipe_markdown(recipe), encoding="utf-8")
            exported += 1
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": str(exc), "exported": exported}

    marker = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "exported": exported,
        "source": str(gold),
    }
    SYNC_MARKER.parent.mkdir(parents=True, exist_ok=True)
    SYNC_MARKER.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    return {"ok": True, "message": f"Exported {exported} recipe doc(s)", "exported": exported}


def sync_status() -> dict[str, Any]:
    if not SYNC_MARKER.is_file():
        return {"synced": False, "exported": 0, "recipes_dir": str(FLYTYING_RECIPES_DIR)}
    try:
        data = json.loads(SYNC_MARKER.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {"synced": True, **data, "recipes_dir": str(FLYTYING_RECIPES_DIR)}
    except (OSError, json.JSONDecodeError):
        pass
    return {"synced": False, "exported": 0, "recipes_dir": str(FLYTYING_RECIPES_DIR)}


def seed_memory(memory, *, limit: int = 12) -> dict[str, Any]:
    """Store a small fly-tying cheat sheet in memory if not already present."""
    from jarvis.flytying import bridge

    if not bridge.gold_available():
        return {"ok": False, "message": "Blackfly scraped database not available"}
    if memory.similar_exists("Fly tying patterns and materials reference", namespace=FLYTYING_MEMORY_NAMESPACE):
        return {"ok": True, "skipped": True, "message": "Fly-tying memory already seeded"}

    rows = bridge.search_recipes("", limit=limit) or []
    if not rows:
        return {"ok": False, "message": "No recipes to seed"}

    lines = ["Fly tying patterns and materials reference:"]
    for r in rows[:limit]:
        name = r.get("fly_name") or r.get("name") or "pattern"
        typ = r.get("type") or r.get("fly_type") or ""
        hook = r.get("hook") or ""
        lines.append(f"- {name}" + (f" ({typ})" if typ else "") + (f", hook {hook}" if hook else ""))
    content = "\n".join(lines)
    memory.add("note", content, tags=["flytying-seed"], namespace=FLYTYING_MEMORY_NAMESPACE)
    return {"ok": True, "seeded": len(rows[:limit])}


def is_flytying_chat(message: str) -> bool:
    return bool(_FLY_CHAT_RE.search((message or "").strip()))


def flytying_context_for_chat(memory, message: str = "", *, limit: int = 6) -> str:
    if not is_flytying_chat(message):
        return ""
    from jarvis.flytying import bridge

    if not bridge.gold_available():
        return ""
    hits = bridge.search_recipes(message, limit=limit) or []
    lines: list[str] = []
    for hit in hits:
        rid = str(hit.get("recipe_id") or hit.get("name") or "")
        row = bridge.get_recipe(rid)
        if row and row.get("formatted"):
            lines.append(str(row["formatted"]))
    if not lines:
        return ""
    return "\n\n".join(lines)[:MAX_CONTEXT_CHARS]
