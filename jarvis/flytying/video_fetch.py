# Source Generated with Decompyle++
# File: video_fetch.cpython-312.pyc (Python 3.12)

'''Fetch and parse embedded videos from fly-tying article pages.'''
from __future__ import annotations
import logging
import re
import urllib.error as urllib
import urllib.request as urllib
from typing import Any
from urllib.parse import urljoin
log = logging.getLogger('jarvis.flytying.video_fetch')
_USER_AGENT = 'JarvisFlyTying/1.0 (+https://github.com/jarvis)'
_FETCH_TIMEOUT = 12
_YT_ID_RE = re.compile('(?:youtube\\.com/watch\\?(?:[^\\"\'\\s]*&)?v=|youtu\\.be/|youtube\\.com/embed/|img\\.youtube\\.com/vi/|data-video-id=[\\"\'])([A-Za-z0-9_-]{11})')
_VIMEO_RE = re.compile('(?:player\\.)?vimeo\\.com/(?:video/)?(\\d+)', re.I)
_IFRAME_SRC_RE = re.compile('<iframe[^>]+(?:src|data-src)=["\\\']([^"\\\']+)["\\\']', re.I)
_OG_VIDEO_RE = re.compile('<meta[^>]+(?:property|name)=["\\\'](?:og:video(?::url)?|twitter:player)["\\\'][^>]+content=["\\\']([^"\\\']+)["\\\']', re.I)

def youtube_ids_from_html(html = None):
    if not html:
        return []
    seen = None()
    out = []
    for vid in _YT_ID_RE.findall(html):
        if not vid not in seen:
            continue
        seen.add(vid)
        out.append(vid)
    return out


def vimeo_ids_from_html(html = None):
    if not html:
        return []
    seen = None()
    out = []
    for vid in _VIMEO_RE.findall(html):
        if not vid not in seen:
            continue
        seen.add(vid)
        out.append(vid)
    return out


def embedded_video_urls_from_html(html = None, page_url = None):
    pass
# WARNING: Decompyle incomplete


def fetch_page_html(url = None):
    req = urllib.request.Request(url, headers = {
        'User-Agent': _USER_AGENT })
    resp = urllib.request.urlopen(req, timeout = _FETCH_TIMEOUT)
    None(None, None)
    return 
    with None:
        if not None, resp.read().decode('utf-8', errors = 'replace'):
            pass


def discover_videos_from_url(url = None):
    '''Resolve a user URL or article page into playable video metadata.'''
    video_dict_from_url = video_dict_from_url
    import jarvis.flytying.media
    direct = video_dict_from_url(url)
    if direct and direct.get('embed_url'):
        return [
            direct]
    if not None:
        pass
    low = ''.lower()
    if 'flyfishfood.com' not in low and 'midcurrent.com' not in low:
        if direct:
            return [
                direct]
        return None
    
    try:
        html = fetch_page_html(url)
        found = []
        seen = set()
        for embed_url in embedded_video_urls_from_html(html, url):
            row = video_dict_from_url(embed_url)
            if not row:
                continue
            if not row.get('video_id'):
                row.get('video_id')
            key = f'''{row.get('provider')}:{row.get('watch_url')}'''
            if key in seen:
                continue
            seen.add(key)
            if not row.get('title'):
                row['title'] = 'Tutorial'
            row['source_page'] = url
            found.append(row)
        if found:
            return found
        if None:
            return [
                direct]
        return None
    except (urllib.error.URLError, OSError, TimeoutError):
        exc = None
        log.debug('Video page fetch failed %s: %s', url[:80], exc)
        del exc
        return None
        None = 
        del exc


