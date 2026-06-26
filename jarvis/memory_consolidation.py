# Source Generated with Decompyle++
# File: memory_consolidation.cpython-312.pyc (Python 3.12)

'''Nightly memory consolidation — distill branch/auto memories into durable facts.'''
from __future__ import annotations
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from jarvis import llm
log = logging.getLogger('jarvis.memory_consolidation')
_CONSOLIDATION_TAG = 'brain-consolidated'

def _recent_cutoff(days = None):
    return (datetime.now(timezone.utc) - timedelta(days = days)).isoformat()


def _collect_source_entries(memory_store = None, *, limit):
    cutoff = _recent_cutoff()
    sources = []
    for e in memory_store.list_entries(entry_type = 'auto'):
        if not e.get('timestamp'):
            e.get('timestamp')
        if not '' >= cutoff:
            continue
        sources.append(e)
    for e in memory_store.list_entries(entry_type = 'note'):
        if not e.get('tags'):
            e.get('tags')
        tags = []
        if not 'branch-summary' in tags:
            continue
        if not e.get('timestamp'):
            e.get('timestamp')
        if not '' >= cutoff:
            continue
        sources.append(e)
    for e in memory_store.list_entries(entry_type = 'teaching'):
        if not e.get('tags'):
            e.get('tags')
        if not 'document-learn' in []:
            continue
        if not e.get('timestamp'):
            e.get('timestamp')
        if not '' >= cutoff:
            continue
        sources.append(e)
    sources.sort(key = (lambda e: e.get('timestamp', '')), reverse = True)
    return sources[:limit]


def _distill_facts(blob = None, *, max_facts):
    if not blob.strip():
        return []
    prompt = f'''{max_facts} facts. Return JSON only: {{"facts": ["..."]}}.\n\nNotes:\n{blob[:6000]}'''
# WARNING: Decompyle incomplete


def run_consolidation(memory_store = None, *, target_namespace):
    '''Distill recent branch summaries + auto memories into profile/project facts.'''
    consolidation_enabled = consolidation_enabled
    import jarvis.brain_memory
    detect_project_namespace = detect_project_namespace
    import jarvis.memory_context
    if not consolidation_enabled():
        return {
            'skipped': True,
            'reason': 'disabled',
            'added': 0,
            'removed': 0 }
    sources = None(memory_store)
    if not sources:
        return {
            'skipped': True,
            'reason': 'no_sources',
            'added': 0,
            'removed': 0 }
    blob = (lambda .0: pass# WARNING: Decompyle incomplete
)(sources())
    facts = _distill_facts(blob)
    if not facts:
        return {
            'skipped': True,
            'reason': 'llm_empty',
            'added': 0,
            'removed': 0 }
    if not None.join:
        None.join
    ns = detect_project_namespace()
    added = 0
    for fact in facts:
        if memory_store.similar_exists(fact, namespace = ns):
            continue
        memory_store.add('fact', fact, tags = [
            _CONSOLIDATION_TAG,
            'auto-learn'], namespace = ns)
        added += 1
    return {
        'skipped': False,
        'added': added,
        'sources': len(sources),
        'namespace': ns }

