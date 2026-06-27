"""Fly-tying images and video metadata."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from jarvis.flytying.config import images_root, recipe_source_path

_YT_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?(?:[^\"'\s]*&)?v=|youtu\.be/|youtube\.com/embed/|img\.youtube\.com/vi/)([A-Za-z0-9_-]{11})"
)
_VIMEO_ID_RE = re.compile(r"(?:player\.)?vimeo\.com/(?:video/)?(\d+)", re.I)


def _recipe_name(recipe: dict[str, Any]) -> str:
    return str(
        recipe.get("fly_name")
        or recipe.get("name")
        or recipe.get("instruction")
        or "Unknown"
    )


def youtube_id_from_text(text: str) -> list[str]:
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for vid in _YT_ID_RE.findall(str(text)):
        if vid not in seen:
            seen.add(vid)
            out.append(vid)
    return out


def vimeo_id_from_text(text: str) -> list[str]:
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for vid in _VIMEO_ID_RE.findall(str(text)):
        if vid not in seen:
            seen.add(vid)
            out.append(vid)
    return out


def video_dict_from_url(url: str, *, title: str = "") -> dict[str, Any] | None:
    """Parse a direct YouTube/Vimeo/Fly Fish Food URL into playable metadata."""
    raw = (url or "").strip()
    if not raw:
        return None
    low = raw.lower()
    for vid in youtube_id_from_text(raw):
        return {
            "provider": "youtube",
            "video_id": vid,
            "title": title or "YouTube tutorial",
            "embed_url": f"https://www.youtube.com/embed/{vid}",
            "watch_url": f"https://www.youtube.com/watch?v={vid}",
            "thumbnail": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
        }
    for vid in vimeo_id_from_text(raw):
        return {
            "provider": "vimeo",
            "video_id": vid,
            "title": title or "Vimeo tutorial",
            "embed_url": f"https://player.vimeo.com/video/{vid}",
            "watch_url": f"https://vimeo.com/{vid}",
            "thumbnail": "",
        }
    if "flyfishfood.com" in low:
        return {
            "provider": "flyfishfood",
            "video_id": "",
            "title": title or "Fly Fish Food tutorial",
            "embed_url": "",
            "watch_url": raw,
            "thumbnail": "",
        }
    return None


def recipe_youtube_ids(recipe: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in (
        recipe.get("youtube_id"),
        recipe.get("youtube_video_id"),
        recipe.get("hero_image"),
        recipe.get("source_url"),
        recipe.get("output"),
        recipe.get("video_description"),
    ):
        if not raw:
            continue
        for vid in youtube_id_from_text(str(raw)):
            if vid not in seen:
                seen.add(vid)
                out.append(vid)
    for url in recipe.get("source_urls") or []:
        for vid in youtube_id_from_text(str(url)):
            if vid not in seen:
                seen.add(vid)
                out.append(vid)
    for url in recipe.get("image_urls") or []:
        for vid in youtube_id_from_text(str(url)):
            if vid not in seen:
                seen.add(vid)
                out.append(vid)
    return out


def recipe_vimeo_ids(recipe: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in (
        recipe.get("source_url"),
        recipe.get("output"),
        recipe.get("video_description"),
        recipe.get("hero_image"),
    ):
        if not raw:
            continue
        for vid in vimeo_id_from_text(str(raw)):
            if vid not in seen:
                seen.add(vid)
                out.append(vid)
    for url in recipe.get("source_urls") or []:
        for vid in vimeo_id_from_text(str(url)):
            if vid not in seen:
                seen.add(vid)
                out.append(vid)
    return out


def _append_video(videos: list[dict[str, Any]], seen: set[str], row: dict[str, Any]) -> None:
    key = f"{row.get('provider')}:{row.get('video_id') or row.get('watch_url')}"
    if key in seen:
        return
    seen.add(key)
    videos.append(row)


def recipe_videos(recipe: dict[str, Any]) -> list[dict[str, Any]]:
    """YouTube, Vimeo, cached article embeds, and Fly Fish Food links."""
    from jarvis.flytying.videos_store import get_cached_videos

    name = _recipe_name(recipe)
    videos: list[dict[str, Any]] = []
    seen: set[str] = set()

    for vid in recipe_youtube_ids(recipe):
        _append_video(
            videos,
            seen,
            {
                "provider": "youtube",
                "video_id": vid,
                "title": name,
                "embed_url": f"https://www.youtube.com/embed/{vid}",
                "watch_url": f"https://www.youtube.com/watch?v={vid}",
                "thumbnail": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
            },
        )

    for vid in recipe_vimeo_ids(recipe):
        _append_video(
            videos,
            seen,
            {
                "provider": "vimeo",
                "video_id": vid,
                "title": name,
                "embed_url": f"https://player.vimeo.com/video/{vid}",
                "watch_url": f"https://vimeo.com/{vid}",
                "thumbnail": "",
            },
        )

    source = str(recipe.get("source_url") or "")
    for cached in get_cached_videos(source):
        row = dict(cached)
        row.setdefault("title", name)
        _append_video(videos, seen, row)

    if "flyfishfood.com" in source.lower():
        has_playable = any(v.get("embed_url") for v in videos)
        if not has_playable:
            _append_video(
                videos,
                seen,
                {
                    "provider": "flyfishfood",
                    "video_id": "",
                    "title": name,
                    "embed_url": "",
                    "watch_url": source,
                    "thumbnail": str(recipe.get("hero_image") or ""),
                },
            )
    return videos


_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff")
_IGNORED_URL_FRAGMENTS = (
    "favicon",
    "icon",
    "sprite",
    "pixel",
    "tracking",
    "analytics",
    "doubleclick",
    "googlesyndication",
    "facebook.com/tr",
    "widget",
    "emoji",
    "avatar",
    "profile",
    "gravatar",
    "1x1",
    "spacer",
    "blank",
    "loading",
    "spinner",
    "logo",
    "/icons/",
    "q_cdnize",
    "to_webp",
    "/s_webp/",
)
_BAD_REMOTE_HOSTS = (
    "midcurrent.com/gear/",
    "midcurrent.com/travel/",
    "midcurrent.com/v2/",
)


def _should_ignore_remote_url(url: str) -> bool:
    lower = str(url or "").strip().lower()
    if not lower.startswith(("http://", "https://")):
        return True
    if any(frag in lower for frag in _IGNORED_URL_FRAGMENTS):
        return True
    if any(host in lower for host in _BAD_REMOTE_HOSTS):
        return True
    return False


def _is_usable_remote_image(url: str) -> bool:
    u = str(url or "").strip()
    if not u or _should_ignore_remote_url(u):
        return False
    lower = u.lower()
    if "img.youtube.com/vi/" in lower:
        return True
    path = lower.split("?", 1)[0]
    if path.endswith(_IMAGE_EXTENSIONS):
        return True
    if any(token in lower for token in ("/uploads/", "/wp-content/", "/images/", "/media/", "/photo")):
        return not any(bad in lower for bad in ("logo", "icon", "banner", "avatar"))
    return False


def local_image_api_path(path: str | Path) -> str | None:
    """Map an on-disk image path to /api/flytying/images/… if under images_root."""
    root = images_root().resolve()
    raw = str(path or "").strip()
    if not raw or ".." in raw.replace("\\", "/"):
        return None
    candidates: list[Path] = []
    try:
        candidates.append(Path(raw).expanduser())
    except (OSError, ValueError):
        pass
    try:
        rel = Path(raw.replace("\\", "/").lstrip("/"))
        candidates.append(root / rel)
    except (OSError, ValueError):
        pass
    for candidate in candidates:
        try:
            p = candidate.resolve()
            if p.is_file() and p.is_relative_to(root):
                rel = p.relative_to(root).as_posix()
                return f"/api/flytying/images/{quote(rel, safe='/')}"
        except (OSError, ValueError):
            continue
    return None


def resolve_recipe_images(recipe: dict[str, Any]) -> list[dict[str, str]]:
    """Prefer Blackfly saved images served locally; filter broken remote hotlinks."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(url: str, *, kind: str, label: str = "") -> None:
        u = str(url or "").strip()
        if not u or u in seen:
            return
        seen.add(u)
        out.append({"url": u, "kind": kind, "label": label})

    for key, path in (recipe.get("saved_image_paths") or {}).items():
        api = local_image_api_path(path)
        if api:
            add(api, kind="local", label=str(key))

    hero = recipe.get("hero_image")
    if hero:
        api = local_image_api_path(hero)
        if api:
            add(api, kind="local", label="hero")
        elif _is_usable_remote_image(str(hero)):
            add(str(hero), kind="remote", label="hero")

    local_count = sum(1 for row in out if row.get("kind") == "local")
    remote_limit = 0 if local_count else 6
    remote_added = 0
    for url in recipe.get("image_urls") or []:
        if remote_added >= remote_limit:
            break
        u = str(url).strip()
        if not _is_usable_remote_image(u):
            continue
        add(u, kind="remote")
        remote_added += 1

    return out


def list_all_videos(
    *,
    q: str = "",
    limit: int = 100,
    recipes: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    from jarvis.flytying.videos_store import list_custom_videos

    path = recipe_source_path()
    needle = (q or "").strip().lower()
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def maybe_add(video: dict[str, Any], *, recipe_name: str = "", recipe_id: str = "", fly_type: str = "") -> None:
        name = recipe_name or video.get("recipe_name") or video.get("title") or ""
        if needle and needle not in name.lower() and needle not in str(fly_type or "").lower():
            if needle not in str(video.get("title") or "").lower():
                return
        key = f"{video.get('provider')}:{video.get('video_id') or video.get('watch_url')}"
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                **video,
                "recipe_id": recipe_id or video.get("recipe_id") or "",
                "recipe_name": name or video.get("title") or "Tutorial",
                "fly_type": fly_type or video.get("fly_type") or "",
            }
        )

    def ingest_recipe(recipe: dict[str, Any]) -> None:
        name = _recipe_name(recipe)
        rid = str(recipe.get("recipe_id") or recipe.get("content_hash") or name)
        for video in recipe_videos(recipe):
            maybe_add(video, recipe_name=name, recipe_id=rid, fly_type=str(recipe.get("type") or ""))

    if recipes:
        for recipe in recipes:
            if isinstance(recipe, dict):
                ingest_recipe(recipe)
    elif path.is_file():
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        recipe = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(recipe, dict):
                        ingest_recipe(recipe)
        except OSError:
            pass

    for video in list_custom_videos():
        maybe_add({**video, "custom": True})

    return rows[: max(1, min(limit, 500))]
