"""Fetch and parse embedded videos from fly-tying article pages."""

from __future__ import annotations

import logging
import re
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urljoin

log = logging.getLogger("jarvis.flytying.video_fetch")

_USER_AGENT = "JarvisFlyTying/1.0 (+https://github.com/jarvis)"
_FETCH_TIMEOUT = 12
_YT_ID_RE = re.compile(
    r'(?:youtube\.com/watch\?(?:[^"\'\s]*&)?v=|youtu\.be/|youtube\.com/embed/|'
    r'img\.youtube\.com/vi/|data-video-id=["\'])([A-Za-z0-9_-]{11})'
)
_VIMEO_RE = re.compile(r"(?:player\.)?vimeo\.com/(?:video/)?(\d+)", re.I)
_IFRAME_SRC_RE = re.compile(r'<iframe[^>]+(?:src|data-src)=["\']([^"\']+)["\']', re.I)
_OG_VIDEO_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:video(?::url)?|twitter:player)["\']'
    r'[^>]+content=["\']([^"\']+)["\']',
    re.I,
)


def youtube_ids_from_html(html: str) -> list[str]:
    if not html:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for vid in _YT_ID_RE.findall(html):
        if vid in seen:
            continue
        seen.add(vid)
        out.append(vid)
    return out


def vimeo_ids_from_html(html: str) -> list[str]:
    if not html:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for vid in _VIMEO_RE.findall(html):
        if vid in seen:
            continue
        seen.add(vid)
        out.append(vid)
    return out


def embedded_video_urls_from_html(html: str, page_url: str = "") -> list[dict[str, Any]]:
    if not html:
        return []
    urls: list[str] = []
    for match in _IFRAME_SRC_RE.findall(html):
        urls.append(urljoin(page_url, match))
    for match in _OG_VIDEO_RE.findall(html):
        urls.append(urljoin(page_url, match))
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        item: dict[str, Any] = {"url": url}
        yt = _YT_ID_RE.search(url)
        if yt:
            item["provider"] = "youtube"
            item["id"] = yt.group(1)
        else:
            vm = _VIMEO_RE.search(url)
            if vm:
                item["provider"] = "vimeo"
                item["id"] = vm.group(1)
        out.append(item)
    for vid in youtube_ids_from_html(html):
        out.append({"provider": "youtube", "id": vid, "url": f"https://www.youtube.com/watch?v={vid}"})
    return out


def fetch_page_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_FETCH_TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        log.debug("video fetch failed for %s: %s", url, exc)
        return ""


def fetch_videos_from_url(url: str) -> list[dict[str, Any]]:
    html = fetch_page_html(url)
    if not html:
        return []
    return embedded_video_urls_from_html(html, page_url=url)
