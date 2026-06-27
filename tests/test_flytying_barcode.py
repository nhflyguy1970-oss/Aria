"""Barcode and inventory scan tests."""

from __future__ import annotations

from jarvis.flytying.barcode import (
    barcode_kind,
    learn_barcode_mapping,
    list_barcode_mappings,
    lookup_barcode,
    make_custom_barcode,
    normalize_barcode,
)
from jarvis.flytying.user_store import (
    add_inventory_item,
    list_inventory_items,
    list_materials,
    remove_inventory_item,
    save_materials,
    scan_barcode_into_inventory,
)


def test_normalize_upc_padding():
    assert normalize_barcode("012345678905") == "012345678905"
    assert normalize_barcode("12345678905") == "012345678905"
    assert normalize_barcode("FT:olive-dubbing") == "FT:OLIVE-DUBBING"


def test_barcode_kind():
    assert barcode_kind("012345678905") == "upc_ean"
    assert barcode_kind("FT:thread-olive") == "custom"


def test_local_barcode_map_roundtrip(tmp_path, monkeypatch):
    from jarvis.flytying import barcode as bc

    monkeypatch.setattr(bc, "BARCODE_MAP_FILE", tmp_path / "map.json")
    learn_barcode_mapping("012345678905", "Test Thread", brand="Uni")
    hit = lookup_barcode("012345678905", online=False)
    assert hit["found"] is True
    assert "Test Thread" in hit["name"]
    assert "012345678905" in list_barcode_mappings()


def test_inventory_scan_needs_name(tmp_path, monkeypatch):
    from jarvis.flytying import barcode as bc
    from jarvis.flytying import user_store

    monkeypatch.setattr(user_store, "MATERIALS_FILE", tmp_path / "mats.json")
    monkeypatch.setattr(bc, "BARCODE_MAP_FILE", tmp_path / "map.json")
    result = scan_barcode_into_inventory("999999999999", online_lookup=False)
    assert result["needs_name"] is True
    assert result["added"] is False

    named = scan_barcode_into_inventory(
        "999999999999",
        name="Mystery Dubbing",
        online_lookup=False,
    )
    assert named["added"] is True
    assert "Mystery Dubbing" in list_materials()


def test_inventory_add_remove(tmp_path, monkeypatch):
    from jarvis.flytying import user_store

    monkeypatch.setattr(user_store, "MATERIALS_FILE", tmp_path / "mats.json")
    save_materials(["grizzly hackle"])
    add_inventory_item("Olive CDC", barcode="FT:OLIVE-CDC", source="scan_custom")
    assert len(list_inventory_items()) >= 2
    item = list_inventory_items()[-1]
    remove_inventory_item(str(item.get("id")))
    assert "Olive CDC" not in list_materials()


def test_custom_label_code():
    code = make_custom_barcode("Olive Dubbing")
    assert code.startswith("FT:olive-dubbing")
