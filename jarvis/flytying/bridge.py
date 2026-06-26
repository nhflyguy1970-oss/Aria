# Source Generated with Decompyle++
# File: bridge.cpython-312.pyc (Python 3.12)

'''Bridge to the Blackfly fly-tying dataset (external project).'''
from __future__ import annotations
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from jarvis.flytying.config import flytying_root, gold_recipes_path, images_root
from jarvis.flytying import index as recipe_index
from jarvis.flytying.media import list_all_videos, recipe_videos, resolve_recipe_images
from jarvis.flytying.export import export_recipe
from jarvis.flytying.hatch import hatch_context, hatch_context_text
from jarvis.flytying.library_health import library_health
from jarvis.flytying.substitutions import substitutions_for_recipe
from jarvis.flytying.search import unified_search
from jarvis.flytying.user_store import get_note
from jarvis.flytying.stats import read_status
from jarvis.flytying.aliases import aliases_for_name
API_VERSION = 3
_blackfly_ready: 'bool | None' = None
_blackfly_checked_at: 'float' = 0
_BLACKFLY_RETRY_SEC = 120

def reset_blackfly_cache():
    global _blackfly_ready, _blackfly_checked_at
    _blackfly_ready = None
    _blackfly_checked_at = 0


def _prepare_blackfly(*, force):
    now = time.monotonic()
# WARNING: Decompyle incomplete


def available():
    return _prepare_blackfly()


def gold_available():
    return gold_recipes_path().is_file()


def status():
    '''Fast status from gold_stats.json — no Blackfly import.'''
    st = read_status()
    st['api_version'] = API_VERSION
    st['blackfly_import'] = _prepare_blackfly()
    if st.get('index_built'):
        st.get('index_built')
    st['semantic_usable'] = bool(_prepare_blackfly())
    if not st.get('index_built') and st.get('semantic_usable'):
        st['index_note'] = 'index on disk; semantic search needs Blackfly import'
    elif st.get('index_built'):
        st['index_note'] = 'keyword + semantic (multi-word queries)'
    else:
        st['index_note'] = 'keyword search only'
    
    try:
        st['library_health'] = library_health()
        
        try:
            pattern_of_the_day = pattern_of_the_day
            import jarvis.flytying.nightly
            st['pattern_of_the_day'] = pattern_of_the_day()
            
            try:
                st['hatch'] = hatch_context()
                return st
                except Exception:
                    continue
                except Exception:
                    continue
            except Exception:
                return st





def build_gold(**kwargs):
    if not _prepare_blackfly():
        return {
            'ok': False,
            'message': 'Blackfly unavailable' }
    DATASET_PATH = DATASET_PATH
    import blackfly_ai
    build_gold_dataset = build_gold_dataset
    gold_path = gold_path
    import blackfly_gold
    import blackfly_rag as br
    if not kwargs.get('source'):
        kwargs.get('source')
    source = DATASET_PATH
    if not kwargs.get('output'):
        kwargs.get('output')
    stats = build_gold_dataset(source, gold_path(), min_quality = float(kwargs.get('min_quality', 70)), min_materials = int(kwargs.get('min_materials', 2)), min_steps = int(kwargs.get('min_steps', 2)))
    index_result = { }
    if kwargs.get('build_index', True):
        index_result = br.GLOBAL_GOLD_INDEX.build()
    recipe_index.invalidate()
    return {
        'ok': True,
        'stats': stats,
        'index': index_result }


def _enrich_search_row(row = None, recipe = None):
    pass
# WARNING: Decompyle incomplete


def _format_recipe_plain(recipe = None):
    name = _recipe_name(recipe)
    if not recipe.get('type'):
        recipe.get('type')
    lines = [
        f'''**{name}** ({'?'})''']
    if recipe.get('hook'):
        lines.append(f'''Hook: {recipe['hook']}''')
    if not recipe.get('materials'):
        recipe.get('materials')
    mats = []
    if mats:
        None('; '.join + (lambda .0: pass# WARNING: Decompyle incomplete
)(mats[:20]()))
    if not recipe.get('steps'):
        recipe.get('steps')
    steps = []
    if steps:
        lines.append('')
        lines.append('Steps:')
        (lambda .0: pass# WARNING: Decompyle incomplete
)(enumerate(steps[:25], 1)())
    return '\n'.join(lines)


def _recipe_name(recipe = None):
    if not recipe.get('fly_name'):
        recipe.get('fly_name')
        if not recipe.get('name'):
            recipe.get('name')
            if not recipe.get('instruction'):
                recipe.get('instruction')
    return str('Unknown')


def search_recipes(query = None, *, fly_type, limit, **kwargs):
    if not kwargs.get('min_quality'):
        kwargs.get('min_quality')
    payload = unified_search(query, fly_type = fly_type, limit = limit, min_quality = float(0), favorites_only = bool(kwargs.get('favorites_only')), hook_size = kwargs.get('hook_size'))
    if not payload.get('results'):
        payload.get('results')
    rows = []
    results = []
    for row in rows:
        if not row.get('recipe_id'):
            row.get('recipe_id')
            if not row.get('name'):
                row.get('name')
        recipe = recipe_index.find_recipe('')
        enriched = _enrich_search_row(row, recipe)
        enriched['search_mode'] = payload.get('search_mode')
        results.append(enriched)
    return results


def get_recipe(name_or_id = None):
    recipe = recipe_index.find_recipe(name_or_id)
    if not recipe:
        return None
    if _prepare_blackfly():
        format_recipe_card = format_recipe_card
        recipe_id = recipe_id
        recipe_name = recipe_name
        import blackfly_rag
        formatted = format_recipe_card(recipe)
        name = recipe_name(recipe)
        if not recipe.get('recipe_id'):
            recipe.get('recipe_id')
        rid = recipe_id(recipe)
    else:
        formatted = _format_recipe_plain(recipe)
        name = _recipe_name(recipe)
        if not recipe.get('recipe_id'):
            recipe.get('recipe_id')
        rid = recipe.get('content_hash')
# WARNING: Decompyle incomplete


def ask_fly_tying(question = None, *, fly_type, limit):
    '''Unified Q&A — always through chat + index RAG.'''
    chat_turn = chat_turn
    import jarvis.flytying.chat
    result = chat_turn([
        {
            'role': 'user',
            'content': question }], fly_type = fly_type)
    if not result.get('recipes'):
        result.get('recipes')
    hits = search_recipes(question, fly_type = fly_type, limit = limit)
    return {
        'ok': result.get('ok', False),
        'message': result.get('message', ''),
        'answer': result.get('answer', ''),
        'recipes': hits,
        'model': result.get('model') }


def export_recipe_markdown(name_or_id = None, *, fmt):
    row = get_recipe(name_or_id)
    if not row:
        return None
    return export_recipe(row, fmt = fmt)


def compare_recipes_by_id(ids = None):
    rows = []
    for rid in ids:
        row = get_recipe(rid)
        if not row:
            continue
        rows.append(row)
    if not rows:
        return {
            'ok': False,
            'message': 'no recipes found' }
    compare_recipes = compare_recipes
    import jarvis.flytying.export
    return {
        'ok': True,
        'count': len(rows),
        'markdown': compare_recipes(rows),
        'recipes': rows }


def seasonal_suggestions(*, month, limit):
    ctx = hatch_context(month = month)
    if not ctx.get('hatches'):
        ctx.get('hatches')
    if not ctx.get('suggest_types'):
        ctx.get('suggest_types')
    terms = [] + []
    seen = set()
    results = []
    for term in terms:
        for hit in search_recipes(str(term), limit = 3):
            if not hit.get('recipe_id'):
                hit.get('recipe_id')
                if not hit.get('name'):
                    hit.get('name')
            rid = str('')
            if rid in seen:
                continue
            seen.add(rid)
            results.append(hit)
            if not len(results) >= limit:
                continue
            search_recipes(str(term), limit = 3)
    if not len(results) >= limit:
        continue
    return {
        'ok': True,
        'hatch': ctx,
        'results': results[:limit] }


def list_recipes(*, q, fly_type, limit):
    cap = max(1, min(limit, 500))
    if not q:
        q
    needle = ''.strip()
    (rows, mode) = recipe_index.search(q, fly_type = fly_type, limit = cap)
    if needle and len(needle.split()) > 1 and _prepare_blackfly():
        
        try:
            hybrid_search = hybrid_search
            bf_rid = recipe_id
            import blackfly_rag
            if not fly_type:
                fly_type
            type_filter = ''.strip().lower()
            semantic_rows = []
            seen = set()
            if not fly_type:
                fly_type
            for recipe in hybrid_search(needle, fly_type = None, limit = cap):
                if not recipe.get('recipe_id'):
                    recipe.get('recipe_id')
                rid = str(bf_rid(recipe))
                if rid in seen:
                    continue
                if not recipe.get('type'):
                    recipe.get('type')
                rtype = str('').lower()
                if type_filter and rtype != type_filter:
                    continue
                seen.add(rid)
                semantic_rows.append(recipe_index._recipe_row(recipe))
            if semantic_rows:
                merged = []
                seen_ids = set()
                for row in semantic_rows + rows:
                    if not row.get('recipe_id'):
                        row.get('recipe_id')
                        if not row.get('name'):
                            row.get('name')
                    rid = str('')
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                    merged.append(row)
                merged.sort(key = (lambda r: if not r.get('quality_score'):
r.get('quality_score')(-float(0), r.get('name', '').lower())))
                return (merged[:cap], 'hybrid')
            return (rows, mode)
            return (rows, mode)
        except Exception:
            return (rows, mode)



def suggest_from_materials(materials = None, *, limit):
    pass
# WARNING: Decompyle incomplete


def list_videos(*, q, limit):
    return list_all_videos(q = q, limit = limit, recipes = recipe_index.recipes())


def resolve_image_file(name = None):
    root = images_root().resolve()
    if name or '..' in name.replace('\\', '/'):
        return None
    candidate = (root / Path(name)).resolve()
    
    try:
        if candidate.is_file() and candidate.is_relative_to(root):
            return candidate
    except ValueError:
        return None


