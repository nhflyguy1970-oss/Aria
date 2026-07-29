"""Fly Tying media + video discovery / store shape tests."""

from __future__ import annotations

from unittest.mock import patch


def test_youtube_id_from_text():
    from jarvis.flytying.media import youtube_id_from_text

    ids = youtube_id_from_text("watch https://www.youtube.com/watch?v=dQw4w9WgXcQ now")
    assert "dQw4w9WgXcQ" in ids


def test_discover_videos_alias_matches_fetch():
    from jarvis.flytying import video_fetch

    sample = [{"provider": "youtube", "id": "abc12345678", "url": "https://youtu.be/abc12345678"}]
    with patch.object(video_fetch, "fetch_videos_from_url", return_value=sample):
        found = video_fetch.discover_videos_from_url("https://example.com/page")
    assert found
    assert found[0].get("watch_url") or found[0].get("url")
    assert "embed_url" in found[0]


def test_custom_video_add_delete_ok_shape(tmp_path, monkeypatch):
    from jarvis.flytying import videos_store as vs

    monkeypatch.setattr(vs, "CUSTOM_VIDEOS_FILE", tmp_path / "custom.json")
    monkeypatch.setattr(vs, "VIDEO_CACHE_FILE", tmp_path / "cache.json")
    added = vs.add_custom_video("https://www.youtube.com/watch?v=abcdefghijk", title="Demo")
    assert added["ok"] is True
    assert added["video"]["title"] == "Demo"
    key = added["video"].get("video_id") or added["video"].get("url")
    removed = vs.remove_custom_video(key)
    assert removed["ok"] is True


def test_set_cached_videos(tmp_path, monkeypatch):
    from jarvis.flytying import videos_store as vs

    monkeypatch.setattr(vs, "VIDEO_CACHE_FILE", tmp_path / "cache.json")
    out = vs.set_cached_videos("https://example.com", [{"url": "https://youtu.be/x"}])
    assert out["ok"] is True
    assert out["count"] == 1
    assert len(vs.get_cached_videos("https://example.com")) == 1
