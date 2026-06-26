# Source Generated with Decompyle++
# File: vector_store.cpython-312.pyc (Python 3.12)

'''Vector memory backends — sqlite (default), ChromaDB, Qdrant, Weaviate.'''
from __future__ import annotations
import logging
import os
import sqlite3
import struct
from pathlib import Path
from typing import Any, Protocol
from jarvis import config as jarvis_config
from jarvis.config import DATA_DIR
logger = logging.getLogger('jarvis.vector_store')
VECTOR_BACKENDS = ('sqlite', 'chroma', 'qdrant', 'weaviate')
COLLECTION_NAME = 'jarvis_memory'

class VectorMemoryStore(Protocol):
    backend: 'str' = 'VectorMemoryStore'
    
    def get(self = None, memory_id = None):
        pass

    
    def upsert(self = None, memory_id = None, vector = None, *, namespace, entry_type, content):
        pass

    
    def delete(self = None, memory_id = None):
        pass

    
    def delete_many(self = None, memory_ids = None):
        pass

    
    def count(self = None):
        pass

    
    def search(self = None, query_vector = None, limit = None, *, namespace, min_score):
        pass

    
    def close(self = None):
        pass



def resolve_vector_backend():
    explicit = os.getenv('JARVIS_VECTOR_BACKEND', '').strip().lower()
    if explicit in VECTOR_BACKENDS:
        return explicit


def _vector_root(data_dir = None):
    if not data_dir:
        data_dir
    root = DATA_DIR
    custom = os.getenv('JARVIS_VECTOR_PATH', '').strip()
    if custom:
        return Path(custom)


class SqliteVectorStore:
    '''Linear-scan fallback — same file as legacy embedding sidecar.'''
    backend = 'sqlite'
    
    def __init__(self = None, path = None):
        if not path:
            path
        self.path = jarvis_config.MEMORY_VECTORS_FILE
        self.path.parent.mkdir(parents = True, exist_ok = True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread = False)
        self._conn.execute('PRAGMA journal_mode=WAL')
        self._conn.execute("\n            CREATE TABLE IF NOT EXISTS embeddings (\n                memory_id TEXT PRIMARY KEY,\n                dims INTEGER NOT NULL,\n                vector BLOB NOT NULL,\n                namespace TEXT NOT NULL DEFAULT 'default',\n                entry_type TEXT NOT NULL DEFAULT 'fact'\n            )\n            ")
    # WARNING: Decompyle incomplete

    
    def close(self = None):
        self._conn.close()

    _pack = (lambda vector = None: dims = len(vector)# WARNING: Decompyle incomplete
)()
    _unpack = (lambda dims = None, blob = None: list(struct.unpack(f'''{dims}f''', blob)))()
    
    def get(self = None, memory_id = None):
        row = self._conn.execute('SELECT dims, vector FROM embeddings WHERE memory_id = ?', (memory_id,)).fetchone()
        if not row:
            return []
        (dims, blob) = None
        return self._unpack(int(dims), blob)

    
    def upsert(self = None, memory_id = None, vector = None, *, namespace, entry_type, content):
        if not vector:
            self.delete(memory_id)
            return None
        (dims, blob) = self._pack(vector)
        if not namespace:
            namespace
        if not entry_type:
            entry_type
        self._conn.execute('\n            INSERT INTO embeddings(memory_id, dims, vector, namespace, entry_type)\n            VALUES (?, ?, ?, ?, ?)\n            ON CONFLICT(memory_id) DO UPDATE SET\n                dims=excluded.dims,\n                vector=excluded.vector,\n                namespace=excluded.namespace,\n                entry_type=excluded.entry_type\n            ', (memory_id, dims, blob, 'default', 'fact'))
        self._conn.commit()

    
    def set(self = None, memory_id = None, vector = None):
        self.upsert(memory_id, vector)

    
    def delete(self = None, memory_id = None):
        self._conn.execute('DELETE FROM embeddings WHERE memory_id = ?', (memory_id,))
        self._conn.commit()

    
    def delete_many(self = None, memory_ids = None):
        if not memory_ids:
            return None
        placeholders = ','.join('?' * len(memory_ids))
        self._conn.execute(f'''DELETE FROM embeddings WHERE memory_id IN ({placeholders})''', memory_ids)
        self._conn.commit()

    
    def count(self = None):
        row = self._conn.execute('SELECT COUNT(*) FROM embeddings').fetchone()
        if row:
            return int(row[0])

    
    def search(self = None, query_vector = None, limit = None, *, namespace, min_score):
        llm = llm
        import jarvis
        if not query_vector:
            return []
        sql = None
        params = []
        if namespace:
            sql += ' WHERE namespace = ?'
            params.append(namespace)
        rows = self._conn.execute(sql, params).fetchall()
        scored = []
        for memory_id, dims, blob in rows:
            vec = self._unpack(int(dims), blob)
            sim = llm.cosine_similarity(query_vector, vec)
            if not sim >= min_score:
                continue
            scored.append((str(memory_id), sim))
        scored.sort(key = (lambda x: x[1]), reverse = True)
        return scored[:limit]



class ChromaVectorStore:
    '''Embedded ChromaDB — best local default when installed.'''
    backend = 'chroma'
    
    def __init__(self = None, path = None):
        import chromadb
        if not path:
            path
        root = _vector_root() / 'chroma_memory'
        root.mkdir(parents = True, exist_ok = True)
        self.path = root
        self._client = chromadb.PersistentClient(path = str(root))
        self._collection = self._client.get_or_create_collection(name = COLLECTION_NAME, metadata = {
            'hnsw:space': 'cosine' })

    
    def close(self = None):
        pass

    
    def get(self = None, memory_id = None):
        pass
    # WARNING: Decompyle incomplete

    
    def upsert(self = None, memory_id = None, vector = None, *, namespace, entry_type, content):
        if not vector:
            self.delete(memory_id)
            return None
        if not namespace:
            namespace
        if not entry_type:
            entry_type
        if not content:
            content
        self._collection.upsert(ids = [
            memory_id], embeddings = [
            vector], metadatas = [
            {
                'namespace': 'default',
                'type': 'fact' }], documents = [
            ''[:2000]])

    
    def delete(self = None, memory_id = None):
        
        try:
            self._collection.delete(ids = [
                memory_id])
            return None
        except Exception:
            return None


    
    def delete_many(self = None, memory_ids = None):
        if not memory_ids:
            return None
        
        try:
            self._collection.delete(ids = memory_ids)
            return None
        except Exception:
            return None


    
    def count(self = None):
        return int(self._collection.count())

    
    def search(self = None, query_vector = None, limit = None, *, namespace, min_score):
        if not query_vector:
            return []
        kwargs = {
            'query_embeddings': [
                None],
            'n_results': max(limit, 1),
            'include': [
                'distances'] }
        if namespace:
            kwargs['where'] = {
                'namespace': {
                    '$eq': namespace } }
    # WARNING: Decompyle incomplete



class QdrantVectorStore:
    '''Embedded Qdrant — file-backed, no Docker required.'''
    backend = 'qdrant'
    
    def __init__(self = None, path = None):
        QdrantClient = QdrantClient
        import qdrant_client
        Distance = Distance
        VectorParams = VectorParams
        import qdrant_client.models
        if not path:
            path
        root = _vector_root() / 'qdrant_memory'
        root.mkdir(parents = True, exist_ok = True)
        self.path = root
        self._client = QdrantClient(path = str(root))
        self._collection = COLLECTION_NAME
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(collection_name = self._collection, vectors_config = VectorParams(size = 768, distance = Distance.COSINE))
            return None

    
    def close(self = None):
        
        try:
            self._client.close()
            return None
        except Exception:
            return None


    
    def get(self = None, memory_id = None):
        pass
    # WARNING: Decompyle incomplete

    
    def upsert(self = None, memory_id = None, vector = None, *, namespace, entry_type, content):
        PointStruct = PointStruct
        import qdrant_client.models
        if not vector:
            self.delete(memory_id)
            return None
        if not namespace:
            namespace
        if not entry_type:
            entry_type
        if not content:
            content
        self._client.upsert(collection_name = self._collection, points = [
            PointStruct(id = memory_id, vector = vector, payload = {
                'namespace': 'default',
                'type': 'fact',
                'content': ''[:2000] })])

    
    def delete(self = None, memory_id = None):
        
        try:
            self._client.delete(collection_name = self._collection, points_selector = [
                memory_id])
            return None
        except Exception:
            return None


    
    def delete_many(self = None, memory_ids = None):
        if not memory_ids:
            return None
        
        try:
            self._client.delete(collection_name = self._collection, points_selector = memory_ids)
            return None
        except Exception:
            return None


    
    def count(self = None):
        
        try:
            info = self._client.get_collection(self._collection)
            if not info.points_count:
                info.points_count
            return int(0)
        except Exception:
            return 0


    
    def search(self = None, query_vector = None, limit = None, *, namespace, min_score):
        FieldCondition = FieldCondition
        Filter = Filter
        MatchValue = MatchValue
        import qdrant_client.models
        if not query_vector:
            return []
        query_filter = None
        if namespace:
            query_filter = Filter(must = [
                FieldCondition(key = 'namespace', match = MatchValue(value = namespace))])
    # WARNING: Decompyle incomplete



class WeaviateVectorStore:
    '''Weaviate server — set JARVIS_WEAVIATE_URL (default http://localhost:8080).'''
    backend = 'weaviate'
    
    def __init__(self = None, url = None):
        if not url:
            url
        self.url = os.getenv('JARVIS_WEAVIATE_URL', 'http://localhost:8080')
        self._client = self._connect()
        self._class = 'JarvisMemory'
        self._ensure_schema()

    
    def _connect(self):
        
        try:
            import weaviate
            if hasattr(weaviate, 'connect_to_custom'):
                host = self.url.replace('http://', '').replace('https://', '').split(':')[0]
                port = 8080
                secure = self.url.startswith('https')
                if ':' in self.url.split('//')[-1]:
                    port = int(self.url.split(':')[-1].split('/')[0])
                return weaviate.connect_to_custom(http_host = host, http_port = port, http_secure = secure, grpc_host = host, grpc_port = 50051, grpc_secure = secure)
            return None.Client(self.url)
        except Exception:
            exc = None
            raise RuntimeError(f'''Weaviate unavailable at {self.url}: {exc}'''), exc
            exc = None
            del exc


    
    def _ensure_schema(self = None):
        pass
    # WARNING: Decompyle incomplete

    
    def close(self = None):
        
        try:
            if hasattr(self._client, 'close'):
                self._client.close()
                return None
            return None
        except Exception:
            return None


    
    def _uuid_for(self = None, memory_id = None):
        import uuid
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f'''jarvis.memory.{memory_id}'''))

    
    def get(self = None, memory_id = None):
        return []

    
    def upsert(self = None, memory_id = None, vector = None, *, namespace, entry_type, content):
        if not vector:
            self.delete(memory_id)
            return None
        uid = self._uuid_for(memory_id)
        if not namespace:
            namespace
        if not entry_type:
            entry_type
        if not content:
            content
        props = {
            'memory_id': memory_id,
            'namespace': 'default',
            'type': 'fact',
            'content': ''[:2000] }
        
        try:
            if hasattr(self._client, 'collections'):
                col = self._client.collections.get(self._class)
                col.data.insert(properties = props, vector = vector, uuid = uid)
                return None
                
                try:
                    self._client.data_object.create(data_object = props, class_name = self._class, vector = vector, uuid = uid)
                    return None
                except Exception:
                    exc = None
                    logger.warning('Weaviate upsert %s: %s', memory_id, exc)
                    exc = None
                    del exc
                    return None
                    exc = None
                    del exc



    
    def delete(self = None, memory_id = None):
        
        try:
            uid = self._uuid_for(memory_id)
            if hasattr(self._client, 'collections'):
                self._client.collections.get(self._class).data.delete_by_id(uid)
                return None
                
                try:
                    self._client.data_object.delete(uuid = uid, class_name = self._class)
                    return None
                except Exception:
                    return None



    
    def delete_many(self = None, memory_ids = None):
        for mid in memory_ids:
            self.delete(mid)

    
    def count(self = None):
        
        try:
            if hasattr(self._client, 'collections'):
                col = self._client.collections.get(self._class)
                agg = col.aggregate.over_all(total_count = True)
                if not agg.total_count:
                    agg.total_count
                return int(0)
            return 0
        except Exception:
            return 0


    
    def search(self = None, query_vector = None, limit = None, *, namespace, min_score):
        if not query_vector:
            return []
    # WARNING: Decompyle incomplete



def create_vector_store(data_dir = None, *, backend, sqlite_path):
    '''Factory for vector memory backend.'''
    if not backend:
        backend
    name = resolve_vector_backend().lower()
    root = _vector_root(data_dir)
# WARNING: Decompyle incomplete


def migrate_sqlite_vectors_to(target = None, source = None):
    '''One-time import from sqlite sidecar into chroma/qdrant/weaviate.'''
    if target.backend == 'sqlite':
        return 0
    if not source:
        source
    src = SqliteVectorStore()
    if src.count() == 0:
        return 0
    rows = src._conn.execute('SELECT memory_id, dims, vector, namespace, entry_type FROM embeddings').fetchall()
    moved = 0
    for memory_id, dims, blob, namespace, entry_type in rows:
        vec = src._unpack(int(dims), blob)
        if not vec:
            continue
        if not namespace:
            namespace
        if not entry_type:
            entry_type
        target.upsert(str(memory_id), vec, namespace = 'default', entry_type = 'fact')
        moved += 1
    logger.info('Migrated %d vectors sqlite → %s', moved, target.backend)
    return moved

