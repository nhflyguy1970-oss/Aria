"""Fly tying aliases, user store, and search tests."""

from __future__ import annotations

from jarvis.flytying.aliases import expand_query
from jarvis.flytying.hook_utils import parse_hook
from jarvis.flytying.substitutions import suggest_substitutions
from jarvis.flytying.user_store import (
    add_structured_item,
    compose_material_name,
    list_materials,
    save_materials,
    toggle_favorite,
    update_inventory_item,
)


def test_expand_query_bwo():
    expanded, terms = expand_query("bwo")
    assert "bwo" in terms or expanded
    assert "blue wing olive" in expanded or "baetis" in expanded


def test_parse_hook_sizes():
    p = parse_hook("size 14 dry fly hook")
    assert p["size_min"] == 14
    assert p["size_max"] == 14


def test_substitutions_cdc():
    subs = suggest_substitutions("cdc")
    assert subs
    assert any(subs)


def test_user_materials_roundtrip(tmp_path, monkeypatch):
    from jarvis.flytying import user_store

    monkeypatch.setattr(user_store, "MATERIALS_FILE", tmp_path / "mats.json")
    save_materials(["olive dubbing", "grizzly hackle"])
    assert "olive dubbing" in list_materials()


def test_favorite_toggle(tmp_path, monkeypatch):
    from jarvis.flytying import user_store

    monkeypatch.setattr(user_store, "FAVORITES_FILE", tmp_path / "fav.json")
    r1 = toggle_favorite("recipe-1")
    assert r1["favorited"] is True
    r2 = toggle_favorite("recipe-1")
    assert r2["favorited"] is False


def test_unified_search_empty():
    from jarvis.flytying.search import unified_search

    out = unified_search("", limit=3)
    assert out["ok"] is True
    assert out["search_mode"] in ("browse", "empty", "keyword")


def test_compose_material_name():
    assert compose_material_name("dry hook", color="olive", size="14", brand="Uni") == "olive 14 dry hook (Uni)"
    assert compose_material_name("dubbing", color="olive") == "olive dubbing"
    assert compose_material_name("thread", brand="Uni") == "thread (Uni)"


def test_structured_add_and_update(tmp_path, monkeypatch):
    from jarvis.flytying import user_store

    monkeypatch.setattr(user_store, "MATERIALS_FILE", tmp_path / "mats.json")
    add = add_structured_item("dry hook", color="olive", size="14", brand="Uni")
    assert add["ok"] is True
    assert "olive 14 dry hook (Uni)" in list_materials()
    item_id = add["item"]["id"]
    upd = update_inventory_item(item_id, {"size": "16"})
    assert upd["ok"] is True
    assert "16" in upd["item"]["name"]
