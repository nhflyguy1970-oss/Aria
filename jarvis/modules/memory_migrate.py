# Source Generated with Decompyle++
# File: memory_migrate.cpython-312.pyc (Python 3.12)

'''Migrate JSON memory store to SQLite + embedding sidecar.'''
from __future__ import annotations
import json
import logging
from pathlib import Path
from jarvis.config import MEMORY_DB_FILE, MEMORY_FILE
from jarvis.modules.memory_embeddings import EmbeddingSidecar
from jarvis.modules.memory_sqlite import SqliteMemoryStore
logger = logging.getLogger('jarvis.memory')

def migrate_json_to_sqlite(json_path = None, db_path = None, *, embeddings):
    '''Import memory.json into memory.db. Returns entry count.'''
    if not json_path:
        json_path
    src = MEMORY_FILE
    if not src.exists():
        return 0
    
    try:
        payload = json.loads(src.read_text(encoding = 'utf-8'))
        if not payload.get('entries'):
            payload.get('entries')
        entries = []
        if not entries:
            return 0
        if not db_path:
            db_path
        store = SqliteMemoryStore(path = MEMORY_DB_FILE, embeddings = embeddings)
        added = store.import_data(payload, merge = False)
        if not embeddings:
            embeddings
        sidecar = EmbeddingSidecar()
        for raw in entries:
            if not isinstance(raw, dict):
                continue
            eid = raw.get('id')
            emb = raw.get('embedding')
            if not eid:
                continue
            if not isinstance(emb, list):
                continue
            if not emb:
                continue
            sidecar.set(str(eid), emb)
        logger.info('Migrated %d memories from %s to SQLite', added, src)
        return added
    except (json.JSONDecodeError, OSError):
        exc = None
        logger.warning('JSON memory migration skipped: %s', exc)
        exc = None
        del exc
        return 0
        exc = None
        del exc



def strip_json_embeddings(json_path = None):
    '''Move inline embeddings from memory.json to sidecar; strip from file.'''
    EmbeddingSidecar = EmbeddingSidecar
    import jarvis.modules.memory_embeddings
    if not json_path:
        json_path
    src = MEMORY_FILE
    if not src.exists():
        return 0
    
    try:
        data = json.loads(src.read_text(encoding = 'utf-8'))
        if not data.get('entries'):
            data.get('entries')
        entries = []
        sidecar = EmbeddingSidecar()
        moved = 0
        for e in entries:
            emb = e.pop('embedding', None)
            eid = e.get('id')
            if not eid:
                continue
            if not isinstance(emb, list):
                continue
            if not emb:
                continue
            sidecar.set(str(eid), emb)
            moved += 1
        if moved:
            src.write_text(json.dumps(data, ensure_ascii = False, separators = (',', ':')), encoding = 'utf-8')
        return moved
    except (json.JSONDecodeError, OSError):
        return 0


