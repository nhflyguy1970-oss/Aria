# Source Generated with Decompyle++
# File: memory_embeddings.cpython-312.pyc (Python 3.12)

'''Embedding sidecar — re-exports vector store (sqlite / chroma / qdrant / weaviate).'''
from __future__ import annotations
from jarvis.modules.vector_store import SqliteVectorStore, create_vector_store, migrate_sqlite_vectors_to, resolve_vector_backend
EmbeddingSidecar = SqliteVectorStore
__all__ = [
    'EmbeddingSidecar',
    'SqliteVectorStore',
    'create_vector_store',
    'migrate_sqlite_vectors_to',
    'resolve_vector_backend']
