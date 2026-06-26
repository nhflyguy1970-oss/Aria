# Source Generated with Decompyle++
# File: memory_sqlite.cpython-312.pyc (Python 3.12)

'''SQLite memory backend with embedding sidecar.'''
from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from jarvis import llm
from jarvis import config as jarvis_config
from jarvis.config import DATA_DIR
from jarvis.modules.memory_common import DEFAULT_NAMESPACE, MEMORY_TYPES, embedding_upsert, normalize_entry, parse_remember, parse_ts, relevance_score, search_pool, split_remember_facts, to_public, utc_now
from jarvis.modules.memory_embeddings import EmbeddingSidecar

class SqliteMemoryStore:
    
    def __init__(self = None, path = None, embeddings = None):
        if not path:
            path
        self.path = jarvis_config.MEMORY_DB_FILE
        DATA_DIR.mkdir(parents = True, exist_ok = True)
        if not embeddings:
            embeddings
        self._embeddings = EmbeddingSidecar()
        self._pending_touch_ids = set()
        self._conn = sqlite3.connect(str(self.path), check_same_thread = False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute('PRAGMA journal_mode=WAL')
        self._init_schema()

    
    def _init_schema(self = None):
        self._conn.executescript("\n            CREATE TABLE IF NOT EXISTS memories (\n                id TEXT PRIMARY KEY,\n                type TEXT NOT NULL,\n                content TEXT NOT NULL,\n                namespace TEXT NOT NULL DEFAULT 'default',\n                timestamp TEXT NOT NULL,\n                access_count INTEGER NOT NULL DEFAULT 0,\n                relevance REAL NOT NULL DEFAULT 1.0,\n                tags TEXT NOT NULL DEFAULT '[]',\n                last_accessed TEXT\n            );\n            CREATE INDEX IF NOT EXISTS idx_memories_ns ON memories(namespace);\n            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);\n            CREATE INDEX IF NOT EXISTS idx_memories_ts ON memories(timestamp);\n            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);\n            ")
        self._conn.commit()

    
    def close(self = None):
        self._conn.close()
        self._embeddings.close()

    
    def _row_to_entry(self = None, row = None, *, include_embedding):
        tags = row['tags']
        if isinstance(tags, str):
            
            try:
                tags = json.loads(tags)
                if not row['access_count']:
                    row['access_count']
                if not row['relevance']:
                    row['relevance']
                entry = {
                    'id': row['id'],
                    'type': row['type'],
                    'content': row['content'],
                    'namespace': row['namespace'],
                    'timestamp': row['timestamp'],
                    'access_count': int(0),
                    'relevance': float(1),
                    'tags': tags }
                if row['last_accessed']:
                    entry['last_accessed'] = row['last_accessed']
                if include_embedding:
                    entry['embedding'] = self._embeddings.get(entry['id'])
                return normalize_entry(entry)
            except json.JSONDecodeError:
                tags = []
                continue


    
    def _all_rows(self = None):
        return list(self._conn.execute('SELECT * FROM memories ORDER BY timestamp'))

    
    def _iter_entries(self = None, *, include_embedding):
        pass
    # WARNING: Decompyle incomplete

    _data = (lambda self = None: {
'entries': self._iter_entries(include_embedding = True),
'version': 2 })()
    
    def _save(self = None):
        self.flush()

    
    def flush(self = None):
        self._apply_pending_touches()

    
    def _apply_pending_touches(self = None):
        if not self._pending_touch_ids:
            return None
        now = utc_now()
        touched = list(self._pending_touch_ids)
        self._pending_touch_ids.clear()
        placeholders = ','.join('?' * len(touched))
        None(self._conn.execute, f'''\n            UPDATE memories\n            SET access_count = access_count + 1, last_accessed = ?\n            WHERE id IN ({placeholders})\n            ''')
        self._conn.commit()

    
    def _next_id(self = None):
        nid = uuid.uuid4().hex[:10]
        row = self._conn.execute('SELECT 1 FROM memories WHERE id = ?', (nid,)).fetchone()
        if not row:
            return nid

    to_public = (lambda entry = None: to_public(entry))()
    
    def add(self = None, entry_type = None, content = None, tags = None, *, namespace):
        if not content:
            content
        content = ''.strip()
        if not content:
            raise ValueError('Empty memory content')
        is_trusted_memory_content = is_trusted_memory_content
        import jarvis.trust_memory
        if not entry_type not in ('failure', 'success', 'strategy', 'teaching') and is_trusted_memory_content(content):
            raise ValueError('Refusing to store test-artifact content in live memory')
        entry_type = entry_type if entry_type in MEMORY_TYPES else 'fact'
        eid = self._next_id()
        embedding = llm.embed_text(content)
        if not tags:
            tags
        if not namespace:
            namespace
        if not DEFAULT_NAMESPACE.strip():
            DEFAULT_NAMESPACE.strip()
        entry = {
            'id': eid,
            'type': entry_type,
            'content': content,
            'tags': [],
            'namespace': DEFAULT_NAMESPACE,
            'timestamp': utc_now(),
            'access_count': 0,
            'relevance': 1 }
        self._conn.execute('\n            INSERT INTO memories(id, type, content, namespace, timestamp, access_count, relevance, tags)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            ', (eid, entry['type'], entry['content'], entry['namespace'], entry['timestamp'], 0, 1, json.dumps(entry['tags'])))
        self._conn.commit()
        if embedding:
            embedding_upsert(self._embeddings, eid, embedding, entry)
        entry['embedding'] = embedding
        return entry

    
    def add_batch(self = None, items = None, *, embed):
        is_trusted_memory_content = is_trusted_memory_content
        import jarvis.trust_memory
        created = []
        for raw in items:
            if not raw.get('type'):
                raw.get('type')
            entry_type = 'fact'.strip()
            if not raw.get('content'):
                raw.get('content')
            content = ''.strip()
            if not content:
                continue
            if not entry_type not in ('failure', 'success', 'strategy', 'teaching') and is_trusted_memory_content(content):
                raise ValueError('Refusing to store test-artifact content in live memory')
            entry_type = entry_type if entry_type in MEMORY_TYPES else 'fact'
            eid = self._next_id()
            embedding = llm.embed_text(content) if embed else None
            if not raw.get('tags'):
                raw.get('tags')
            if not raw.get('namespace'):
                raw.get('namespace')
            if not DEFAULT_NAMESPACE.strip():
                DEFAULT_NAMESPACE.strip()
            entry = {
                'id': eid,
                'type': entry_type,
                'content': content,
                'tags': [],
                'namespace': DEFAULT_NAMESPACE,
                'timestamp': utc_now(),
                'access_count': 0,
                'relevance': 1 }
            self._conn.execute('\n                INSERT INTO memories(id, type, content, namespace, timestamp, access_count, relevance, tags)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n                ', (eid, entry['type'], entry['content'], entry['namespace'], entry['timestamp'], 0, 1, json.dumps(entry['tags'])))
            if embedding:
                embedding_upsert(self._embeddings, eid, embedding, entry)
            entry['embedding'] = embedding
            created.append(entry)
        if created:
            self._conn.commit()
        return created

    _entry_matches_scope = (lambda entry = None, *, entry_type: pass# WARNING: Decompyle incomplete
)()
    
    def similar_exists(self = None, content = None, threshold = None, *, entry_type, namespace, tags_include):
        norm = content.lower().strip()
        if not norm:
            return True
        sql = 'SELECT * FROM memories WHERE lower(trim(content)) = ?'
        params = [
            norm]
        if entry_type:
            sql += ' AND type = ?'
            params.append(entry_type)
        if namespace:
            sql += ' AND namespace = ?'
            params.append(namespace)
        row = self._conn.execute(sql, params).fetchone()
        if row:
            entry = self._row_to_entry(row)
            if self._entry_matches_scope(entry, entry_type = entry_type, namespace = namespace, tags_include = tags_include):
                return True
        emb = llm.embed_text(content)
        if not emb:
            return False
        if hasattr(self._embeddings, 'search'):
            hits = self._embeddings.search(emb, limit = 24, min_score = threshold, namespace = namespace)
            for mid, _score in hits:
                row = self._conn.execute('SELECT * FROM memories WHERE id = ?', (mid,)).fetchone()
                if not row:
                    continue
                entry = self._row_to_entry(row)
                if not self._entry_matches_scope(entry, entry_type = entry_type, namespace = namespace, tags_include = tags_include):
                    continue
                hits
                return True
            return False
        for r in self._all_rows():
            entry = self._row_to_entry(r)
            if not self._entry_matches_scope(entry, entry_type = entry_type, namespace = namespace, tags_include = tags_include):
                continue
            e_emb = self._embeddings.get(r['id'])
            if not e_emb:
                continue
            if not llm.cosine_similarity(emb, e_emb) >= threshold:
                continue
            self._all_rows()
            return True
        return False

    
    def relevance_score(self = None, entry = None):
        return relevance_score(entry)

    
    def touch(self = None, entry_id = None):
        if entry_id:
            self._pending_touch_ids.add(entry_id)
            return None

    
    def list_entries(self = None, entry_type = None, *, namespace, query, include_embedding):
        pass
    # WARNING: Decompyle incomplete

    
    def get(self = None, entry_id = None):
        row = self._conn.execute('SELECT * FROM memories WHERE id = ?', (entry_id,)).fetchone()
        if not row:
            return None
        return to_public(self._row_to_entry(row))

    
    def find_index(self = None, entry_id = None):
        rows = self._all_rows()
        for i, r in enumerate(rows):
            if not r['id'] == entry_id:
                continue
            
            return enumerate(rows), i

    
    def update(self = None, entry_id = None, *, content, entry_type, tags, namespace):
        row = self._conn.execute('SELECT * FROM memories WHERE id = ?', (entry_id,)).fetchone()
        if not row:
            return False
    # WARNING: Decompyle incomplete

    
    def search(self = None, query = None, limit = None, *, namespace):
        pass
    # WARNING: Decompyle incomplete

    
    def delete(self = None, index = None):
        rows = self._all_rows()
        if not  <= 0, index or 0, index < len(rows):
            return False
            return False
        return self.delete_id(eid)

    
    def delete_id(self = None, entry_id = None):
        cur = self._conn.execute('DELETE FROM memories WHERE id = ?', (entry_id,))
        self._conn.commit()
        if cur.rowcount:
            self._embeddings.delete(entry_id)
            return True
        return False

    
    def clear(self = None, entry_type = None, namespace = None):
        pass
    # WARNING: Decompyle incomplete

    
    def prune(self = None, *, max_age_days, min_score, types):
        now = datetime.now(timezone.utc)
        remove_ids = []
        for r in self._all_rows():
            entry = self._row_to_entry(r)
            if entry.get('type') not in types:
                continue
            age = (now - parse_ts(entry.get('timestamp', ''))).days
            if not age >= max_age_days:
                continue
            if not self.relevance_score(entry) < min_score:
                continue
            remove_ids.append(entry['id'])
        if not remove_ids:
            return 0
        placeholders = ','.join('?' * len(remove_ids))
        self._conn.execute(f'''DELETE FROM memories WHERE id IN ({placeholders})''', remove_ids)
        self._conn.commit()
        self._embeddings.delete_many(remove_ids)
        return len(remove_ids)

    
    def namespaces(self = None):
        rows = self._conn.execute('SELECT DISTINCT namespace FROM memories ORDER BY namespace').fetchall()
    # WARNING: Decompyle incomplete

    
    def stats(self = None):
        by_type = { }
        for r in self._conn.execute('SELECT type, COUNT(*) FROM memories GROUP BY type'):
            by_type[str(r[0])] = int(r[1])
        by_namespace = { }
        for r in self._conn.execute('SELECT namespace, COUNT(*) FROM memories GROUP BY namespace'):
            by_namespace[str(r[0])] = int(r[1])
        total = sum(by_type.values())
        return {
            'total': total,
            'namespaces': self.namespaces(),
            'by_type': by_type,
            'by_namespace': by_namespace,
            'backend': 'sqlite',
            'vector_backend': getattr(self._embeddings, 'backend', 'sqlite'),
            'vectors': self._embeddings.count() }

    
    def latest_checkpoint(self = None, namespace = None):
        sql = "SELECT * FROM memories WHERE tags LIKE '%checkpoint%'"
        params = []
        if namespace:
            sql += ' AND namespace = ?'
            params.append(namespace)
        rows = self._conn.execute(sql, params).fetchall()
        if not rows:
            return None
        best = max(rows, key = (lambda r: if not r['timestamp']:
r['timestamp']''))
        return to_public(self._row_to_entry(best))

    
    def upsert_checkpoint(self = None, content = None, namespace = None):
        if not namespace:
            namespace
        if not DEFAULT_NAMESPACE.strip():
            DEFAULT_NAMESPACE.strip()
        ns = DEFAULT_NAMESPACE
        rows = self._conn.execute("SELECT id FROM memories WHERE namespace = ? AND tags LIKE '%checkpoint%'", (ns,)).fetchall()
    # WARNING: Decompyle incomplete

    
    def export_data(self = None, *, include_embeddings):
        entries = self._iter_entries(include_embedding = include_embeddings)
    # WARNING: Decompyle incomplete

    
    def import_data(self = None, payload = None, *, merge):
        incoming = payload.get('entries') if isinstance(payload, dict) else None
        if not isinstance(incoming, list):
            raise ValueError('Invalid memory import — expected {entries: [...]}')
        if not merge:
            self.clear()
    # WARNING: Decompyle incomplete

    parse_remember = staticmethod(parse_remember)
    split_remember_facts = staticmethod(split_remember_facts)
    
    def find_by_env_key(self = None, env_key = None):
        tag = f'''env-key:{env_key}'''
        for e in self.list_entries(namespace = 'environment', include_embedding = True):
            if not e.get('tags'):
                e.get('tags')
            if not tag in []:
                continue
            
            return self.list_entries(namespace = 'environment', include_embedding = True), e

    
    def upsert_by_tag(self = None, *, tag, entry_type, content, namespace, extra_tags):
        for e in self.list_entries(namespace = namespace, include_embedding = True):
            if not e.get('tags'):
                e.get('tags')
            if not tag in []:
                continue
            self.update(e['id'], content = content)
            if not self.get(e['id']):
                self.get(e['id'])
            
            return self.list_entries(namespace = namespace, include_embedding = True), e
        if not extra_tags:
            extra_tags
        return self.add(entry_type, content, tags = tags, namespace = namespace)

    
    def upsert_branch_summary(self = None, branch_id = None, content = None):
        branch_memory_namespace = branch_memory_namespace
        import jarvis.memory_context
        ns = branch_memory_namespace(branch_id)
        return self.upsert_by_tag(tag = 'branch-summary', entry_type = 'note', content = content, namespace = ns, extra_tags = [
            'conversation-roll',
            'branch-summary'])


