# Source Generated with Decompyle++
# File: media.cpython-312.pyc (Python 3.12)

'''Fly-tying images and video metadata.'''
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote
from jarvis.flytying.config import gold_recipes_path, images_root
_YT_ID_RE = re.compile('(?:youtube\\.com/watch\\?(?:[^\\"\'\\s]*&)?v=|youtu\\.be/|youtube\\.com/embed/|img\\.youtube\\.com/vi/)([A-Za-z0-9_-]{11})')
_VIMEO_ID_RE = re.compile('(?:player\\.)?vimeo\\.com/(?:video/)?(\\d+)', re.I)

def _recipe_name(recipe = None):
    if not recipe.get('fly_name'):
        recipe.get('fly_name')
        if not recipe.get('name'):
            recipe.get('name')
            if not recipe.get('instruction'):
                recipe.get('instruction')
    return str('Unknown')


def youtube_id_from_text(text = None):
    if not text:
        return []
    seen = None()
    out = []
    for vid in _YT_ID_RE.findall(str(text)):
        if not vid not in seen:
            continue
        seen.add(vid)
        out.append(vid)
    return out


def vimeo_id_from_text(text = None):
    if not text:
        return []
    seen = None()
    out = []
    for vid in _VIMEO_ID_RE.findall(str(text)):
        if not vid not in seen:
            continue
        seen.add(vid)
        out.append(vid)
    return out


def video_dict_from_url(url = None, *, title):
    '''Parse a direct YouTube/Vimeo/Fly Fish Food URL into playable metadata.'''
    if not url:
        url
    raw = ''.strip()
    if not raw:
        return None
    low = raw.lower()
    for vid in youtube_id_from_text(raw):
        if not title:
            title
        
        return youtube_id_from_text(raw), {
            'provider': 'youtube',
            'video_id': vid,
            'title': 'YouTube tutorial',
            'embed_url': f'''https://www.youtube.com/embed/{vid}''',
            'watch_url': f'''https://www.youtube.com/watch?v={vid}''',
            'thumbnail': f'''https://img.youtube.com/vi/{vid}/hqdefault.jpg''' }
    for None in vimeo_id_from_text(raw):
        if not title:
            title
        return None, {
            'provider': 'vimeo',
            'video_id': vid,
            'title': 'Vimeo tutorial',
            'embed_url': f'''https://player.vimeo.com/video/{vid}''',
            'watch_url': f'''https://vimeo.com/{vid}''',
            'thumbnail': '' }
    if 'flyfishfood.com' in low:
        if not title:
            title
        return {
            'provider': 'flyfishfood',
            'video_id': '',
            'title': 'Fly Fish Food tutorial',
            'embed_url': '',
            'watch_url': raw,
            'thumbnail': '' }


def recipe_youtube_ids(recipe = None):
    seen = set()
    out = []
    for raw in (recipe.get('youtube_id'), recipe.get('hero_image'), recipe.get('source_url'), recipe.get('output'), recipe.get('video_description')):
        if not raw:
            continue
        for vid in youtube_id_from_text(str(raw)):
            if not vid not in seen:
                continue
            seen.add(vid)
            out.append(vid)
    if not recipe.get('source_urls'):
        recipe.get('source_urls')
    for url in []:
        for vid in youtube_id_from_text(str(url)):
            if not vid not in seen:
                continue
            seen.add(vid)
            out.append(vid)
    if not recipe.get('image_urls'):
        recipe.get('image_urls')
    for url in []:
        for vid in youtube_id_from_text(str(url)):
            if not vid not in seen:
                continue
            seen.add(vid)
            out.append(vid)
    return out


def recipe_vimeo_ids(recipe = None):
    seen = set()
    out = []
    for raw in (recipe.get('source_url'), recipe.get('output'), recipe.get('video_description'), recipe.get('hero_image')):
        if not raw:
            continue
        for vid in vimeo_id_from_text(str(raw)):
            if not vid not in seen:
                continue
            seen.add(vid)
            out.append(vid)
    if not recipe.get('source_urls'):
        recipe.get('source_urls')
    for url in []:
        for vid in vimeo_id_from_text(str(url)):
            if not vid not in seen:
                continue
            seen.add(vid)
            out.append(vid)
    return out


def _append_video(videos = None, seen = None, row = None):
    if not row.get('video_id'):
        row.get('video_id')
    key = f'''{row.get('provider')}:{row.get('watch_url')}'''
    if key in seen:
        return None
    seen.add(key)
    videos.append(row)


def recipe_videos(recipe = None):
    '''YouTube, Vimeo, cached article embeds, and Fly Fish Food links.'''
    get_cached_videos = get_cached_videos
    import jarvis.flytying.videos_store
    name = _recipe_name(recipe)
    videos = []
    seen = set()
    for vid in recipe_youtube_ids(recipe):
        _append_video(videos, seen, {
            'provider': 'youtube',
            'video_id': vid,
            'title': name,
            'embed_url': f'''https://www.youtube.com/embed/{vid}''',
            'watch_url': f'''https://www.youtube.com/watch?v={vid}''',
            'thumbnail': f'''https://img.youtube.com/vi/{vid}/hqdefault.jpg''' })
    for vid in recipe_vimeo_ids(recipe):
        _append_video(videos, seen, {
            'provider': 'vimeo',
            'video_id': vid,
            'title': name,
            'embed_url': f'''https://player.vimeo.com/video/{vid}''',
            'watch_url': f'''https://vimeo.com/{vid}''',
            'thumbnail': '' })
    if not recipe.get('source_url'):
        recipe.get('source_url')
    source = str('')
    for cached in get_cached_videos(source):
        row = dict(cached)
        row.setdefault('title', name)
        _append_video(videos, seen, row)
    if 'flyfishfood.com' in source.lower():
        has_playable = (lambda .0: pass# WARNING: Decompyle incomplete
)(videos())
        if not has_playable:
            if not recipe.get('hero_image'):
                recipe.get('hero_image')
            _append_video(videos, seen, {
                'provider': 'flyfishfood',
                'video_id': '',
                'title': name,
                'embed_url': '',
                'watch_url': source,
                'thumbnail': str('') })
    return videos


def local_image_api_path(path = None):
    '''Map an on-disk image path to /api/flytying/images/… if under images_root.'''
    
    try:
        p = Path(path).resolve()
        root = images_root().resolve()
        if not p.is_file() or p.is_relative_to(root):
            return None
            
            try:
                rel = p.relative_to(root).as_posix()
                return f'''/api/flytying/images/{quote(rel, safe = '/')}'''
            except (OSError, ValueError):
                return None




def resolve_recipe_images(recipe = None):
    '''Remote URLs plus proxied local saved_image_paths.'''
    out = []
    seen = set()
    if not recipe.get('saved_image_paths'):
        recipe.get('saved_image_paths')
    for key, path in { }.items():
        api = local_image_api_path(path)
        if not api:
            continue
        if not api not in seen:
            continue
        seen.add(api)
        out.append({
            'url': api,
            'kind': 'local',
            'label': str(key) })
    hero = recipe.get('hero_image')
    if hero:
        api = local_image_api_path(hero)
        if not api:
            api
        url = str(hero)
        if url not in seen:
            seen.add(url)
            out.append({
                'url': url,
                'kind': 'local' if api else 'remote',
                'label': 'hero' })
    if not recipe.get('image_urls'):
        recipe.get('image_urls')
    for url in []:
        u = str(url).strip()
        if not u:
            continue
        if not u not in seen:
            continue
        seen.add(u)
        out.append({
            'url': u,
            'kind': 'remote',
            'label': '' })
    return out


def list_all_videos(*, q, limit, recipes):
    pass
# WARNING: Decompyle incomplete

