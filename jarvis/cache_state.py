"""Shared short-lived caches for API routes."""

from __future__ import annotations

import time

GALLERY_TTL = 10.0
_gallery: dict = {"at": 0.0, "images": None}


def get_gallery_cache() -> list | None:
    if _gallery["images"] is not None and time.time() - _gallery["at"] < GALLERY_TTL:
        return _gallery["images"]
    return None


def set_gallery_cache(images: list) -> None:
    _gallery["at"] = time.time()
    _gallery["images"] = images


def invalidate_gallery() -> None:
    _gallery["images"] = None
    _gallery["at"] = 0.0


_video: dict = {"at": 0.0, "videos": None}


def get_video_gallery_cache() -> list | None:
    if _video["videos"] is not None and time.time() - _video["at"] < GALLERY_TTL:
        return _video["videos"]
    return None


def set_video_gallery_cache(videos: list) -> None:
    _video["at"] = time.time()
    _video["videos"] = videos


def invalidate_video_gallery() -> None:
    _video["videos"] = None
    _video["at"] = 0.0


_meme: dict = {"at": 0.0, "memes": None}


def get_meme_gallery_cache() -> list | None:
    if _meme["memes"] is not None and time.time() - _meme["at"] < GALLERY_TTL:
        return _meme["memes"]
    return None


def set_meme_gallery_cache(memes: list) -> None:
    _meme["at"] = time.time()
    _meme["memes"] = memes


def invalidate_meme_gallery() -> None:
    _meme["memes"] = None
    _meme["at"] = 0.0
