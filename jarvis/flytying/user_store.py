# Source Generated with Decompyle++
# File: user_store.cpython-312.pyc (Python 3.12)

'''User fly-tying data: materials inventory, favorites, queue, notes.'''
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.flytying.barcode import barcode_kind, normalize_barcode
MATERIALS_FILE = DATA_DIR / 'flytying_materials.json'
FAVORITES_FILE = DATA_DIR / 'flytying_favorites.json'
QUEUE_FILE = DATA_DIR / 'flytying_queue.json'
NOTES_FILE = DATA_DIR / 'flytying_notes.json'

def _read(path, default):
    if not path.is_file():
        return default
    
    try:
        data = json.loads(path.read_text(encoding = 'utf-8'))
        if isinstance(data, type(default)):
            return data
        return None
    except (OSError, json.JSONDecodeError):
        return 



def _write(path = None, data = None):
    path.parent.mkdir(parents = True, exist_ok = True)
    path.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _new_item_id():
    return f'''m-{uuid.uuid4().hex[:10]}'''


def compose_material_name(what = None, *, color, size, brand):
    '''Build a recipe-matching label, e.g. olive size 14 dry hook (Uni).'''
    if not what:
        what
    w = ''.strip()
    if not w:
        return ''
    if not color:
        color
    if not size:
        size
# WARNING: Decompyle incomplete


def _ensure_item_name(item = None):
    row = dict(item)
    if not row.get('what'):
        row.get('what')
    what = str('').strip()
    if what:
        if not row.get('color'):
            row.get('color')
        if not row.get('size'):
            row.get('size')
        if not row.get('brand'):
            row.get('brand')
        row['name'] = compose_material_name(what, color = str(''), size = str(''), brand = str(''))
    return row


def _item_key(item = None):
    row = _ensure_item_name(item)
    if not row.get('name'):
        row.get('name')
    return str('').strip().lower()


def _structured_entry(what = None, *, color, size, brand, notes, source, barcode):
    if not what:
        what
    w = ''.strip()
    if not color:
        color
    if not size:
        size
    if not brand:
        brand
    if not source:
        source
    if not 'manual'.strip():
        'manual'.strip()
    entry = {
        'id': _new_item_id(),
        'what': w,
        'color': ''.strip(),
        'size': ''.strip(),
        'brand': ''.strip(),
        'source': 'manual',
        'added_at': _now() }
    if notes:
        if not notes:
            notes
        entry['notes'] = ''.strip()
    code = normalize_barcode(barcode) if barcode else ''
    if code:
        entry['barcode'] = code
        entry['barcode_kind'] = barcode_kind(code)
    return _ensure_item_name(entry)


def _load_inventory_raw():
    if not MATERIALS_FILE.is_file():
        return {
            'version': 2,
            'items': [] }
    
    try:
        raw = json.loads(MATERIALS_FILE.read_text(encoding = 'utf-8'))
        if isinstance(raw, list):
            items = []
            for m in raw:
                name = str(m).strip()
                if not name:
                    continue
                items.append({
                    'id': _new_item_id(),
                    'name': name,
                    'source': 'manual',
                    'added_at': _now() })
            store = {
                'version': 2,
                'items': items }
            _write(MATERIALS_FILE, store)
            return store
        if None(raw, dict) and isinstance(raw.get('items'), list):
            return raw
        return {
            'version': None,
            'items': [] }
    except (OSError, json.JSONDecodeError):
        return 



def _save_inventory_items(items = None):
    _write(MATERIALS_FILE, {
        'version': 2,
        'items': items[-500:] })


def list_inventory_items():
    store = _load_inventory_raw()
    if not store.get('items'):
        store.get('items')
    items = []
    out = []
    for i in items:
        if not isinstance(i, dict):
            continue
        row = _ensure_item_name(dict(i))
        if not row.get('name'):
            row.get('name')
        if not str('').strip():
            if not row.get('what'):
                row.get('what')
            if not str('').strip():
                continue
        out.append(row)
    return out


def list_materials():
    names = []
    seen = set()
    for item in list_inventory_items():
        if not item.get('name'):
            item.get('name')
        name = str('').strip()
        low = name.lower()
        if not name:
            continue
        if not low not in seen:
            continue
        seen.add(low)
        names.append(name)
    return names


def save_materials(materials = None):
    '''Merge manual material names into inventory (legacy textarea save).'''
    items = list_inventory_items()
# WARNING: Decompyle incomplete


def replace_materials(materials = None):
    '''Replace inventory with an exact name list (used when removing items).'''
    items = []
    seen = set()
    if not materials:
        materials
    for m in []:
        name = str(m).strip()
        low = name.lower()
        if name or low in seen:
            continue
        seen.add(low)
        items.append({
            'id': _new_item_id(),
            'what': name,
            'name': name,
            'source': 'manual',
            'added_at': _now() })
    _save_inventory_items(items)
    names = list_materials()
    return {
        'ok': True,
        'materials': names,
        'inventory': items,
        'count': len(names),
        'replaced': True }


def replace_inventory_items(rows = None):
    '''Replace inventory with structured rows (client sync / legacy fallback).'''
    items = []
    seen = set()
    if not rows:
        rows
    for raw in []:
        if not isinstance(raw, dict):
            continue
        if not raw.get('what'):
            raw.get('what')
            if not raw.get('name'):
                raw.get('name')
        what = str('').strip()
        if not what:
            continue
        if not raw.get('color'):
            raw.get('color')
        if not raw.get('size'):
            raw.get('size')
        if not raw.get('brand'):
            raw.get('brand')
        if not raw.get('notes'):
            raw.get('notes')
        if not raw.get('source'):
            raw.get('source')
        if not raw.get('barcode'):
            raw.get('barcode')
        entry = _structured_entry(what, color = str(''), size = str(''), brand = str(''), notes = str(''), source = str('manual'), barcode = str(''))
        if raw.get('id'):
            entry['id'] = str(raw['id'])
        key = _item_key(entry)
        if key or key in seen:
            continue
        seen.add(key)
        items.append(entry)
    _save_inventory_items(items)
    names = list_materials()
    return {
        'ok': True,
        'materials': names,
        'inventory': items,
        'count': len(names),
        'replaced': True }


def add_structured_item(what = None, *, color, size, brand, notes, source, barcode):
    if not what:
        what
    w = ''.strip()
    if not w:
        return {
            'ok': False,
            'message': 'what required' }
    entry = None(w, color = color, size = size, brand = brand, notes = notes, source = source, barcode = barcode)
    key = _item_key(entry)
    items = list_inventory_items()
    for item in items:
        if not _item_key(item) == key:
            continue
        
        return items, {
            'ok': True,
            'item': item,
            'merged': True,
            'inventory': items,
            'materials': list_materials() }
    items.append(entry)
    _save_inventory_items(items)
    return {
        'ok': True,
        'item': entry,
        'merged': False,
        'inventory': items,
        'materials': list_materials() }


def update_inventory_item(item_id = None, fields = None):
    if not item_id:
        item_id
    iid = ''.strip()
    if not iid:
        return {
            'ok': False,
            'message': 'item_id required' }
    items = None()
    target = None
    for item in items:
        if not item.get('id'):
            item.get('id')
        if not str('') == iid:
            continue
        target = item
        items
# WARNING: Decompyle incomplete


def find_inventory_item(*, item_id, barcode):
    if not item_id:
        item_id
    iid = ''.strip()
    code = normalize_barcode(barcode) if barcode else ''
    for item in list_inventory_items():
        if iid:
            if not item.get('id'):
                item.get('id')
            if str('') == iid:
                
                return list_inventory_items(), item
            if not list_inventory_items():
                continue
        if not item.get('barcode'):
            item.get('barcode')
        if not normalize_barcode(str('')) == code:
            continue
        
        return None, item


def add_inventory_item(name = None, *, what, color, size, barcode, source, brand, qty, notes, merge_on_barcode):
    if not what:
        what
    w = ''.strip()
    if w:
        return add_structured_item(w, color = color, size = size, brand = brand, notes = notes, source = source, barcode = barcode)
    if not None:
        pass
    label = ''.strip()
    if not label:
        return {
            'ok': False,
            'message': 'name required' }
    code = normalize_barcode(barcode) if None else ''
    items = list_inventory_items()
    now = _now()
# WARNING: Decompyle incomplete


def remove_inventory_item(item_id = None):
    if not item_id:
        item_id
    iid = ''.strip()
    if not iid:
        return {
            'ok': False,
            'message': 'item_id required' }
# WARNING: Decompyle incomplete


def scan_barcode_into_inventory(raw_barcode = None, *, name, brand, learn, online_lookup):
    learn_barcode_mapping = learn_barcode_mapping
    lookup_barcode = lookup_barcode
    import jarvis.flytying.barcode
    code = normalize_barcode(raw_barcode)
    if not code:
        return {
            'ok': False,
            'message': 'barcode required' }
    lookup = lookup_barcode(code, online = online_lookup)
    if not name:
        name
    if not ''.strip():
        ''.strip()
        if not lookup.get('name'):
            lookup.get('name')
    resolved_name = str('').strip()
    if not brand:
        brand
    if not ''.strip():
        ''.strip()
        if not lookup.get('brand'):
            lookup.get('brand')
    resolved_brand = str('').strip()
    if not resolved_name:
        if not lookup.get('message'):
            lookup.get('message')
        return {
            'ok': True,
            'added': False,
            'lookup': lookup,
            'barcode': code,
            'needs_name': True,
            'message': 'Name this barcode to add it to inventory.' }
    if None and resolved_name:
        if not name or lookup.get('found'):
            learn_barcode_mapping(code, resolved_name, brand = resolved_brand)
        elif lookup.get('source') not in ('local_map',):
            learn_barcode_mapping(code, resolved_name, brand = resolved_brand)
    source = 'scan_upc' if lookup.get('kind') in ('upc_ean', 'ean') else 'scan_custom'
    if code.startswith('FT:'):
        source = 'scan_custom'
    add_result = add_inventory_item(resolved_name, barcode = code, source = source, brand = resolved_brand, merge_on_barcode = True)
# WARNING: Decompyle incomplete


def list_favorites():
    rows = _read(FAVORITES_FILE, [])
# WARNING: Decompyle incomplete


def toggle_favorite(recipe_id = None):
    if not recipe_id:
        recipe_id
    rid = ''.strip()
    if not rid:
        return {
            'ok': False,
            'message': 'recipe_id required' }
    favs = None()
    if rid in favs:
        favs.remove(rid)
        added = False
    else:
        favs.append(rid)
        added = True
    _write(FAVORITES_FILE, favs)
    return {
        'ok': True,
        'recipe_id': rid,
        'favorited': added,
        'favorites': favs }


def list_queue():
    rows = _read(QUEUE_FILE, [])
    if isinstance(rows, list):
        return rows


def add_to_queue(recipe_id = None, *, name):
    pass
# WARNING: Decompyle incomplete


def remove_from_queue(recipe_id = None):
    if not recipe_id:
        recipe_id
    rid = ''.strip()
# WARNING: Decompyle incomplete


def get_note(recipe_id = None):
    notes = _read(NOTES_FILE, { })
    if not isinstance(notes, dict):
        return ''
    if not notes.get(recipe_id):
        notes.get(recipe_id)
    return str('')


def save_note(recipe_id = None, text = None):
    if not recipe_id:
        recipe_id
    rid = ''.strip()
    if not rid:
        return {
            'ok': False,
            'message': 'recipe_id required' }
    notes = None(NOTES_FILE, { })
    if not isinstance(notes, dict):
        notes = { }
    if not text:
        text
    text = ''.strip()
    if text:
        notes[rid] = text
    else:
        notes.pop(rid, None)
    _write(NOTES_FILE, notes)
    return {
        'ok': True,
        'recipe_id': rid,
        'note': text }


def user_state():
    if NOTES_FILE.is_file():
        return {
            'materials': list_materials(),
            'inventory': list_inventory_items(),
            'favorites': list_favorites(),
            'queue': list_queue(),
            'notes_count': len(_read(NOTES_FILE, { })) }
    return {
        'materials': list_materials(),
        'inventory': list_inventory_items(),
        'favorites': list_favorites(),
        'queue': list_queue(),
        'notes_count': None(len) }

