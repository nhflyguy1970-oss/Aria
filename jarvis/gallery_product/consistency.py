"""Keep Gallery deletions/restores consistent across Chat, Jobs, and filesystem truth."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _walk_branch_messages(mutator) -> None:
    try:
        from jarvis.assistant_instance import get_assistant

        a = get_assistant()
        bm = getattr(a, "branches", None)
        if bm is not None:
            data = getattr(bm, "_data", {}) or {}
            for bid, branch in (data.get("branches") or {}).items():
                mutator(branch.get("messages") or [])
                conv = getattr(bm, "_conversations", {}).get(bid)
                if conv is not None and getattr(conv, "messages", None) is not None:
                    mutator(conv.messages)
            bm._save()
            return
    except Exception:
        pass
    try:
        import json

        from jarvis.branches import BRANCHES_FILE

        if BRANCHES_FILE.exists():
            data = json.loads(BRANCHES_FILE.read_text(encoding="utf-8"))
            for branch in (data.get("branches") or {}).values():
                mutator(branch.get("messages") or [])
            BRANCHES_FILE.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
    except Exception:
        pass


def scrub_chat_gallery_refs(image_name: str) -> dict[str, Any]:
    """Replace durable Chat embeds for a deleted gallery image everywhere."""
    name = Path(str(image_name or "")).name
    if not name:
        return {"ok": False, "scrubbed": 0, "message": "No image name"}

    marker = f"/api/gallery/{name}"
    md_re = re.compile(rf"!\[[^\]]*\]\(/api/gallery/{re.escape(name)}(?:\?[^)]*)?\)")
    bare_re = re.compile(rf"/api/gallery/{re.escape(name)}(?:\?[^\s)]*)?")
    replacement = f"*[Image removed from Gallery: `{name}`]*"
    scrubbed = 0

    def _scrub_text(text: str) -> str:
        nonlocal scrubbed
        if marker not in text and f"`{name}`" not in text:
            return text
        out = md_re.sub(replacement, text)
        if marker in out:
            out = bare_re.sub(replacement, out)
        if out != text:
            scrubbed += 1
        return out

    def _scrub_messages(messages: list) -> None:
        for m in messages or []:
            if not isinstance(m, dict):
                continue
            content = m.get("content")
            if isinstance(content, str) and marker in content:
                m["content"] = _scrub_text(content)

    _walk_branch_messages(_scrub_messages)
    return {"ok": True, "scrubbed": scrubbed, "name": name}


def restore_chat_gallery_refs(original_name: str, *, restored_name: str | None = None) -> dict[str, Any]:
    """After trash restore: put durable Chat gallery embeds back."""
    original = Path(str(original_name or "")).name
    restored = Path(str(restored_name or original)).name
    if not original:
        return {"ok": False, "restored": 0, "message": "No image name"}

    removed_re = re.compile(
        rf"\*?\[Image removed from Gallery: `{re.escape(original)}`\]\*?",
        re.I,
    )
    removed_restored_re = re.compile(
        rf"\*?\[Image removed from Gallery: `{re.escape(restored)}`\]\*?",
        re.I,
    )
    embed = f"![generated](/api/gallery/{restored})"
    fixed = 0

    def _fix_text(text: str) -> str:
        nonlocal fixed
        out = removed_re.sub(embed, text)
        if restored != original:
            out = removed_restored_re.sub(embed, out)
        if out != text:
            fixed += 1
        return out

    def _fix_messages(messages: list) -> None:
        for m in messages or []:
            if not isinstance(m, dict):
                continue
            content = m.get("content")
            if isinstance(content, str) and "Image removed from Gallery" in content:
                m["content"] = _fix_text(content)

    _walk_branch_messages(_fix_messages)
    return {"ok": True, "restored": fixed, "original": original, "name": restored}


def mark_jobs_asset_gone(image_name: str, *, path: str | None = None) -> dict[str, Any]:
    try:
        from jarvis.media_jobs import mark_asset_missing

        return mark_asset_missing(image_name, path=path)
    except Exception as exc:
        return {"ok": False, "message": str(exc), "updated": 0}


def mark_jobs_asset_restored(
    original_name: str, *, restored_name: str | None = None, path: str | None = None
) -> dict[str, Any]:
    try:
        from jarvis.media_jobs import clear_asset_missing

        return clear_asset_missing(
            original_name, restored_name=restored_name or original_name, path=path
        )
    except Exception as exc:
        return {"ok": False, "message": str(exc), "updated": 0}


def on_gallery_asset_removed(image_name: str, *, path: str | None = None) -> dict[str, Any]:
    chat = scrub_chat_gallery_refs(image_name)
    jobs = mark_jobs_asset_gone(image_name, path=path)
    return {"ok": True, "chat": chat, "jobs": jobs}


def on_gallery_asset_restored(
    original_name: str, *, restored_name: str | None = None, path: str | None = None
) -> dict[str, Any]:
    """After trash restore — Chat + Jobs must match Gallery again."""
    name = restored_name or original_name
    chat = restore_chat_gallery_refs(original_name, restored_name=name)
    jobs = mark_jobs_asset_restored(original_name, restored_name=name, path=path)
    return {"ok": True, "chat": chat, "jobs": jobs}
