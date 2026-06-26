"""Cheatsheets stored in memory — seeded defaults, editable, resettable."""

from __future__ import annotations

import re
from pathlib import Path

CHEATSHEET_NAMESPACE = "cheatsheet"
TAG_CHEATSHEET = "cheatsheet"
TAG_PROTECTED = "protected"
DEFAULTS_DIR = Path(__file__).parent / "cheatsheet_defaults"

ALIASES: dict[str, str] = {
    "mem": "memory",
    "memories": "memory",
    "code": "coding",
    "dev": "coding",
    "csv": "data",
    "spreadsheet": "data",
    "bujo": "journal",
    "bullet journal": "journal",
    "pic": "image",
    "images": "image",
    "generate": "image",
    "see": "vision",
    "ocr": "vision",
    "chat": "general",
}


def key_tag(key: str) -> str:
    return f"key:{key.strip().lower()}"


def parse_key(entry: dict) -> str | None:
    for tag in entry.get("tags") or []:
        if tag.startswith("key:"):
            return tag[4:]
    return None


def is_cheatsheet_entry(entry: dict) -> bool:
    tags = entry.get("tags") or []
    return entry.get("namespace") == CHEATSHEET_NAMESPACE and TAG_CHEATSHEET in tags


def default_keys() -> list[str]:
    if not DEFAULTS_DIR.is_dir():
        return []
    return sorted(p.stem for p in DEFAULTS_DIR.glob("*.md"))


def load_default_content(key: str) -> str | None:
    path = DEFAULTS_DIR / f"{key}.md"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


def default_title(key: str, content: str) -> str:
    first = content.splitlines()[0].strip() if content else key
    if first.startswith("#"):
        return first.lstrip("#").strip()
    return key.replace("-", " ").title()


def normalize_key(raw: str) -> str | None:
    k = (raw or "").strip().lower()
    if not k:
        return None
    if k in default_keys():
        return k
    return ALIASES.get(k)


def find_by_key(memory_store, key: str) -> dict | None:
    want = normalize_key(key) or key.lower()
    for entry in memory_store._data.get("entries", []):
        if parse_key(entry) == want and is_cheatsheet_entry(entry):
            return entry
    return None


def list_cheatsheets(memory_store) -> list[dict]:
    out = []
    for entry in memory_store._data.get("entries", []):
        if not is_cheatsheet_entry(entry):
            continue
        key = parse_key(entry)
        if not key:
            continue
        content = entry.get("content", "")
        out.append({
            "key": key,
            "title": default_title(key, content),
            "id": entry.get("id"),
            "updated": entry.get("timestamp"),
        })
    return sorted(out, key=lambda x: x["key"])


def seed_cheatsheets(memory_store, *, keys: list[str] | None = None) -> list[str]:
    """Insert bundled defaults for missing keys only."""
    seeded: list[str] = []
    for key in keys or default_keys():
        if find_by_key(memory_store, key):
            continue
        content = load_default_content(key)
        if not content:
            continue
        memory_store.add(
            "note",
            content,
            tags=[TAG_CHEATSHEET, TAG_PROTECTED, key_tag(key)],
            namespace=CHEATSHEET_NAMESPACE,
        )
        seeded.append(key)
    return seeded


def upsert_cheatsheet(memory_store, key: str, content: str) -> dict:
    key = normalize_key(key) or key.lower()
    content = (content or "").strip()
    if not content:
        raise ValueError("Empty cheatsheet content")
    existing = find_by_key(memory_store, key)
    if existing:
        memory_store.update(existing["id"], content=content)
        return memory_store.get(existing["id"]) or existing
    return memory_store.add(
        "note",
        content,
        tags=[TAG_CHEATSHEET, TAG_PROTECTED, key_tag(key)],
        namespace=CHEATSHEET_NAMESPACE,
    )


def reset_cheatsheet(memory_store, key: str) -> dict | None:
    key = normalize_key(key) or key.lower()
    content = load_default_content(key)
    if not content:
        return None
    existing = find_by_key(memory_store, key)
    if existing:
        memory_store.update(existing["id"], content=content)
        return memory_store.get(existing["id"])
    return memory_store.add(
        "note",
        content,
        tags=[TAG_CHEATSHEET, TAG_PROTECTED, key_tag(key)],
        namespace=CHEATSHEET_NAMESPACE,
    )


def resolve_key_from_message(message: str) -> str | None:
    lower = message.lower()
    if m := re.search(r"\b(?:reset|restore)\s+(?:the\s+)?(?:[\w-]+\s+)?cheatsheet(?:\s+for|\s+on)?\s+([\w-]+)", lower):
        return normalize_key(m.group(1))
    if m := re.search(r"\bcheatsheet(?:\s+for|\s+on)?\s+([\w\s-]+?)(?:\?|$)", lower):
        return normalize_key(m.group(1).strip())
    for alias, key in sorted(ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(alias)}\s+cheatsheet\b", lower):
            return key
    for key in default_keys():
        if re.search(rf"\b{re.escape(key)}\s+cheatsheet\b", lower):
            return key
        if key in lower and "cheatsheet" in lower:
            return key
    return None
