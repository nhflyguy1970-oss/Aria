"""Persistent memory store with semantic search, namespaces, and relevance."""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from jarvis import config as jarvis_config
from jarvis import llm
from jarvis.config import DATA_DIR
from jarvis.modules.memory_common import (
    DEFAULT_NAMESPACE,
    MEMORY_TYPES,
    normalize_entry,
    parse_remember,
    parse_ts,
    relevance_score,
    search_pool,
    split_remember_facts,
    to_public,
    utc_now,
)
from jarvis.modules.memory_embeddings import EmbeddingSidecar

logger = logging.getLogger("jarvis.memory")


def _memory_json_compact() -> bool:
    return os.getenv("JARVIS_MEMORY_COMPACT", "1").strip().lower() not in ("0", "false", "no")


def _vectors_path_for(data_path: Path) -> Path:
    return data_path.parent / "memory_vectors.db"


def create_embedding_sidecar(vectors_path: Path):
    from jarvis.modules.semantic_memory_adapter_store import wrap_semantic_memory_store
    from jarvis.modules.vector_store import SqliteVectorStore

    legacy = SqliteVectorStore(path=vectors_path)
    return wrap_semantic_memory_store(legacy)


class JsonMemoryStore:
    def __init__(self, path: Path | None = None, embeddings: EmbeddingSidecar | None = None):
        self.path = path or jarvis_config.MEMORY_FILE
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._embeddings = embeddings or EmbeddingSidecar(_vectors_path_for(self.path))
        self._pending_touch_ids: set[str] = set()
        self._data = self._load()
        self._hydrate_embeddings_from_json()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                entries = data.get("entries") or []
                for i, e in enumerate(entries):
                    normalize_entry(e, i)
                data["entries"] = entries
                return data
            except (json.JSONDecodeError, OSError):
                pass
        return {"entries": [], "version": 2}

    def _hydrate_embeddings_from_json(self) -> None:
        dirty = False
        for e in self._data["entries"]:
            emb = e.pop("embedding", None)
            eid = e.get("id")
            if eid and isinstance(emb, list) and emb:
                self._embeddings.set(str(eid), emb)
                dirty = True
        if dirty:
            self._save_metadata_only()

    def _save_metadata_only(self) -> None:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(self.path)
        if _memory_json_compact():
            payload = json.dumps(self._data, ensure_ascii=False, separators=(",", ":"))
        else:
            payload = json.dumps(self._data, indent=2, ensure_ascii=False)
        self.path.write_text(payload, encoding="utf-8")

    def _save(self) -> None:
        self._save_metadata_only()

    def flush(self) -> None:
        self._apply_pending_touches()

    def _apply_pending_touches(self) -> None:
        if not self._pending_touch_ids:
            return
        now = utc_now()
        touched = self._pending_touch_ids
        self._pending_touch_ids = set()
        for e in self._data["entries"]:
            if e.get("id") in touched:
                e["access_count"] = int(e.get("access_count", 0)) + 1
                e["last_accessed"] = now
        self._save()

    def _next_id(self) -> str:
        existing = {e.get("id") for e in self._data["entries"]}
        while True:
            nid = uuid.uuid4().hex[:10]
            if nid not in existing:
                return nid

    @staticmethod
    def to_public(entry: dict) -> dict:
        return to_public(entry)

    def _attach_embedding(self, entry: dict, *, include: bool) -> dict:
        if include:
            entry = dict(entry)
            entry["embedding"] = self._embeddings.get(entry["id"])
        return entry

    def add(
        self,
        entry_type: str,
        content: str,
        tags: list[str] | None = None,
        *,
        namespace: str | None = None,
    ) -> dict:
        content = (content or "").strip()
        if not content:
            raise ValueError("Empty memory content")
        from jarvis.trust_memory import is_trusted_memory_content

        if entry_type not in (
            "failure",
            "strategy",
            "teaching",
            "success",
        ) and not is_trusted_memory_content(content):
            raise ValueError("Refusing to store test-artifact content in live memory")
        entry_type = entry_type if entry_type in MEMORY_TYPES else "fact"
        try:
            from aria_core.acm_bridge import (
                acm_is_authoritative,
                note_legacy_write_while_primary,
                redirect_legacy_write_to_acm,
            )

            try:
                redirected = redirect_legacy_write_to_acm(
                    content, entry_type=entry_type, tags=tags, namespace=namespace
                )
            except Exception as exc:
                if acm_is_authoritative():
                    note_legacy_write_while_primary()
                    raise RuntimeError(
                        f"ACM authoritative: legacy MemoryStore write refused "
                        f"({type(exc).__name__})"
                    ) from exc
                redirected = None
            if redirected is not None:
                return redirected
            if acm_is_authoritative():
                note_legacy_write_while_primary()
                raise RuntimeError(
                    "ACM authoritative: legacy MemoryStore write refused "
                    "(redirect returned no entry)"
                )
        except ImportError:
            pass
        embedding = llm.embed_text(content)
        entry = {
            "id": self._next_id(),
            "type": entry_type,
            "content": content,
            "tags": tags or [],
            "namespace": (namespace or DEFAULT_NAMESPACE).strip() or DEFAULT_NAMESPACE,
            "timestamp": utc_now(),
            "access_count": 0,
            "relevance": 1.0,
        }
        self._data["entries"].append(entry)
        if embedding:
            self._embeddings.set(entry["id"], embedding)
        self._save()
        entry["embedding"] = embedding
        return entry

    def similar_exists(self, content: str, threshold: float = 0.88) -> bool:
        try:
            from aria_core.acm_store_facade import acm_similar_exists

            hit = acm_similar_exists(content, threshold=threshold)
            if hit is not None:
                return hit
        except Exception:
            pass
        norm = content.lower().strip()
        if not norm:
            return True
        for e in self._data["entries"]:
            if e["content"].lower().strip() == norm:
                return True
        emb = llm.embed_text(content)
        if not emb:
            return False
        for e in self._data["entries"]:
            e_emb = self._embeddings.get(e["id"])
            if e_emb and llm.cosine_similarity(emb, e_emb) >= threshold:
                return True
        return False

    def relevance_score(self, entry: dict) -> float:
        return relevance_score(entry)

    def touch(self, entry_id: str) -> None:
        if entry_id:
            self._pending_touch_ids.add(entry_id)

    def list_entries(
        self,
        entry_type: str | None = None,
        *,
        namespace: str | None = None,
        query: str | None = None,
        include_embedding: bool = False,
    ) -> list[dict]:
        try:
            from aria_core.acm_store_facade import acm_list_entries

            projected = acm_list_entries(
                entry_type,
                namespace=namespace,
                query=query,
                include_embedding=include_embedding,
            )
            if projected is not None:
                return projected
        except Exception:
            pass
        entries = list(self._data["entries"])
        if entry_type:
            entries = [e for e in entries if e.get("type") == entry_type]
        if namespace:
            entries = [e for e in entries if e.get("namespace") == namespace]
        if query:
            q = query.lower().strip()
            entries = [
                e
                for e in entries
                if q in e.get("content", "").lower()
                or any(q in t.lower() for t in e.get("tags", []))
                or q in e.get("namespace", "").lower()
            ]
        entries.sort(key=lambda e: (self.relevance_score(e), e.get("timestamp", "")), reverse=True)
        if include_embedding:
            return [self._attach_embedding(e, include=True) for e in entries]
        return [to_public(e) for e in entries]

    def get(self, entry_id: str) -> dict | None:
        try:
            from aria_core.acm_store_facade import acm_get

            projected = acm_get(entry_id)
            if projected is not None:
                return projected
            from aria_core import acm_bridge

            if acm_bridge.acm_is_authoritative():
                return None
        except Exception:
            pass
        for e in self._data["entries"]:
            if e.get("id") == entry_id:
                return to_public(e)
        return None

    def find_index(self, entry_id: str) -> int | None:
        for i, e in enumerate(self._data["entries"]):
            if e.get("id") == entry_id:
                return i
        return None

    def update(
        self,
        entry_id: str,
        *,
        content: str | None = None,
        entry_type: str | None = None,
        tags: list[str] | None = None,
        namespace: str | None = None,
    ) -> bool:
        try:
            from aria_core.acm_bridge import acm_is_authoritative, note_legacy_write_while_primary
            from aria_core.acm_store_facade import acm_update

            try:
                diverted = acm_update(
                    entry_id,
                    content=content,
                    entry_type=entry_type,
                    tags=tags,
                    namespace=namespace,
                )
            except Exception as exc:
                if acm_is_authoritative():
                    note_legacy_write_while_primary()
                    raise RuntimeError(
                        f"ACM authoritative: legacy MemoryStore update refused "
                        f"({type(exc).__name__})"
                    ) from exc
                diverted = None
            if diverted is not None:
                return diverted
            if acm_is_authoritative():
                note_legacy_write_while_primary()
                raise RuntimeError(
                    "ACM authoritative: legacy MemoryStore update refused "
                    "(facade returned no result)"
                )
        except ImportError:
            pass
        for e in self._data["entries"]:
            if e.get("id") != entry_id:
                continue
            if content is not None:
                e["content"] = content.strip()
                self._embeddings.set(entry_id, llm.embed_text(e["content"]))
            if entry_type and entry_type in MEMORY_TYPES:
                e["type"] = entry_type
            if tags is not None:
                e["tags"] = tags
            if namespace is not None:
                e["namespace"] = namespace.strip() or DEFAULT_NAMESPACE
            e["timestamp"] = utc_now()
            self._save()
            return True
        return False

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        namespace: str | None = None,
        user_facing_only: bool = False,
    ) -> list[dict]:
        try:
            from aria_core.acm_store_facade import acm_search

            projected = acm_search(
                query, limit=limit, namespace=namespace, user_facing_only=user_facing_only
            )
            if projected is not None:
                return projected
        except Exception:
            pass
        pool = list(self._data["entries"])

        def _get_emb(e: dict) -> list[float]:
            return self._embeddings.get(e["id"])

        def _set_emb(e: dict, emb: list[float]) -> None:
            self._embeddings.set(e["id"], emb)

        return search_pool(
            pool,
            query,
            limit,
            namespace=namespace,
            get_embedding=_get_emb,
            set_embedding=_set_emb,
            touch=self.touch,
            flush_touches=self._apply_pending_touches,
            user_facing_only=user_facing_only,
        )

    def delete(self, index: int) -> bool:
        entries = self._data["entries"]
        if 0 <= index < len(entries):
            eid = entries[index]["id"]
            del entries[index]
            self._embeddings.delete(eid)
            self._save()
            return True
        return False

    def delete_id(self, entry_id: str) -> bool:
        try:
            from aria_core.acm_bridge import acm_is_authoritative, note_legacy_write_while_primary
            from aria_core.acm_store_facade import acm_delete_id

            try:
                diverted = acm_delete_id(entry_id)
            except Exception as exc:
                if acm_is_authoritative():
                    note_legacy_write_while_primary()
                    raise RuntimeError(
                        f"ACM authoritative: legacy MemoryStore delete refused "
                        f"({type(exc).__name__})"
                    ) from exc
                diverted = None
            if diverted is not None:
                return diverted
            if acm_is_authoritative():
                note_legacy_write_while_primary()
                raise RuntimeError(
                    "ACM authoritative: legacy MemoryStore delete refused "
                    "(facade returned no result)"
                )
        except ImportError:
            pass
        idx = self.find_index(entry_id)
        if idx is None:
            return False
        del self._data["entries"][idx]
        self._embeddings.delete(entry_id)
        self._save()
        return True

    def clear(self, entry_type: str | None = None, namespace: str | None = None) -> int:
        try:
            from aria_core.acm_bridge import acm_is_authoritative

            if acm_is_authoritative():
                return 0
        except ImportError:
            pass
        before = len(self._data["entries"])
        if not entry_type and not namespace:
            ids = [e["id"] for e in self._data["entries"]]
            self._data["entries"] = []
            self._embeddings.delete_many(ids)
            self._save()
            return before
        kept = []
        removed_ids: list[str] = []
        for e in self._data["entries"]:
            drop = False
            if entry_type and namespace:
                drop = e.get("type") == entry_type and e.get("namespace") == namespace
            elif entry_type:
                drop = e.get("type") == entry_type
            elif namespace:
                drop = e.get("namespace") == namespace
            if drop:
                removed_ids.append(e["id"])
            else:
                kept.append(e)
        removed = before - len(kept)
        self._data["entries"] = kept
        if removed_ids:
            self._embeddings.delete_many(removed_ids)
            self._save()
        return removed

    def prune(
        self,
        *,
        max_age_days: int = 120,
        min_score: float = 0.35,
        types: tuple[str, ...] = ("auto",),
    ) -> int:
        try:
            from aria_core.acm_bridge import acm_is_authoritative

            if acm_is_authoritative():
                # Legacy prune must not mutate forensic vault under PRIMARY.
                return 0
        except ImportError:
            pass
        now = datetime.now(UTC)
        kept = []
        removed_ids: list[str] = []
        for e in self._data["entries"]:
            if e.get("type") in types:
                age = (now - parse_ts(e.get("timestamp", ""))).days
                if age >= max_age_days and self.relevance_score(e) < min_score:
                    removed_ids.append(e["id"])
                    continue
            kept.append(e)
        removed = len(removed_ids)
        self._data["entries"] = kept
        if removed:
            self._embeddings.delete_many(removed_ids)
            self._save()
        return removed

    def namespaces(self) -> list[str]:
        ns = sorted({e.get("namespace", DEFAULT_NAMESPACE) for e in self._data["entries"]})
        return ns or [DEFAULT_NAMESPACE]

    def stats(self) -> dict:
        entries = self._data["entries"]
        by_type: dict[str, int] = {}
        for e in entries:
            t = e.get("type", "note")
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "total": len(entries),
            "namespaces": self.namespaces(),
            "by_type": by_type,
            "backend": "json",
            "vectors": self._embeddings.count(),
        }

    def latest_checkpoint(self, namespace: str | None = None) -> dict | None:
        candidates = [e for e in self._data["entries"] if "checkpoint" in (e.get("tags") or [])]
        if namespace:
            candidates = [c for c in candidates if c.get("namespace") == namespace]
        if not candidates:
            return None
        return to_public(max(candidates, key=lambda e: e.get("timestamp", "")))

    def upsert_checkpoint(self, content: str, namespace: str = "default") -> dict:
        ns = (namespace or DEFAULT_NAMESPACE).strip() or DEFAULT_NAMESPACE
        remove_ids = [
            e["id"]
            for e in self._data["entries"]
            if e.get("namespace") == ns and "checkpoint" in (e.get("tags") or [])
        ]
        self._data["entries"] = [e for e in self._data["entries"] if e["id"] not in remove_ids]
        if remove_ids:
            self._embeddings.delete_many(remove_ids)
        return self.add(
            "project",
            content,
            tags=["checkpoint", "project-state"],
            namespace=ns,
        )

    def export_data(self, *, include_embeddings: bool = False) -> dict:
        entries = self._data["entries"]
        if include_embeddings:
            public = [self._attach_embedding(dict(e), include=True) for e in entries]
        else:
            public = [to_public(e) for e in entries]
        return {
            "version": int(self._data.get("version") or 2),
            "exported_at": utc_now(),
            "entries": public,
        }

    def import_data(self, payload: dict, *, merge: bool = True) -> int:
        incoming = payload.get("entries") if isinstance(payload, dict) else None
        if not isinstance(incoming, list):
            raise ValueError("Invalid memory import — expected {entries: [...]}")
        try:
            from aria_core.acm_bridge import acm_is_authoritative

            if acm_is_authoritative():
                # Route through add() so each entry hits ACM; never mutate legacy SoT.
                added = 0
                for raw in incoming:
                    if not isinstance(raw, dict):
                        continue
                    content = str(raw.get("content", "")).strip()
                    if not content:
                        continue
                    entry_type = raw.get("type") if raw.get("type") in MEMORY_TYPES else "fact"
                    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
                    namespace = str(raw.get("namespace") or DEFAULT_NAMESPACE)
                    self.add(entry_type, content, tags=tags, namespace=namespace)
                    added += 1
                return added
        except ImportError:
            pass
        added = 0
        if not merge:
            old_ids = [e["id"] for e in self._data["entries"]]
            self._data["entries"] = []
            self._embeddings.delete_many(old_ids)
        existing_ids = {e.get("id") for e in self._data["entries"]}
        existing_content = {e["content"].lower().strip() for e in self._data["entries"]}
        for raw in incoming:
            if not isinstance(raw, dict):
                continue
            content = str(raw.get("content", "")).strip()
            if not content or content.lower() in existing_content:
                continue
            entry_type = raw.get("type") if raw.get("type") in MEMORY_TYPES else "fact"
            tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
            namespace = str(raw.get("namespace") or DEFAULT_NAMESPACE)
            eid = raw.get("id")
            if eid in existing_ids:
                eid = self._next_id()
            eid = eid or self._next_id()
            emb = (
                raw.get("embedding")
                if isinstance(raw.get("embedding"), list)
                else llm.embed_text(content)
            )
            entry = {
                "id": eid,
                "type": entry_type,
                "content": content,
                "tags": tags,
                "namespace": namespace,
                "timestamp": raw.get("timestamp") or utc_now(),
                "access_count": int(raw.get("access_count") or 0),
                "relevance": float(raw.get("relevance") or 1.0),
            }
            self._data["entries"].append(entry)
            if emb:
                self._embeddings.set(eid, emb)
            existing_ids.add(eid)
            existing_content.add(content.lower())
            added += 1
        if added:
            self._save()
        return added

    parse_remember = staticmethod(parse_remember)
    split_remember_facts = staticmethod(split_remember_facts)

    def find_by_env_key(self, env_key: str) -> dict | None:
        tag = f"env-key:{env_key}"
        for e in self.list_entries(namespace="environment", include_embedding=True):
            if tag in (e.get("tags") or []):
                return e
        return None

    def upsert_by_tag(
        self,
        *,
        tag: str,
        entry_type: str,
        content: str,
        namespace: str,
        extra_tags: list[str] | None = None,
    ) -> dict:
        for e in self.list_entries(namespace=namespace, include_embedding=True):
            if tag in (e.get("tags") or []):
                self.update(e["id"], content=content)
                return self.get(e["id"]) or e
        tags = list(extra_tags or []) + [tag]
        return self.add(entry_type, content, tags=tags, namespace=namespace)

    def upsert_branch_summary(self, branch_id: str, content: str) -> dict:
        from jarvis.memory_context import branch_memory_namespace

        ns = branch_memory_namespace(branch_id)
        return self.upsert_by_tag(
            tag="branch-summary",
            entry_type="note",
            content=content,
            namespace=ns,
            extra_tags=["conversation-roll", "branch-summary"],
        )


def create_memory_store(path: Path | str | None = None):
    """Factory: SQLite (default for new installs) or JSON (tests / legacy)."""
    from jarvis.modules.memory_migrate import migrate_json_to_sqlite
    from jarvis.modules.memory_sqlite import SqliteMemoryStore

    p = Path(path) if path is not None else None
    if p is not None:
        vectors_path = _vectors_path_for(p)
    else:
        vectors_path = jarvis_config.MEMORY_VECTORS_FILE
    embeddings = create_embedding_sidecar(vectors_path)

    if p is not None and p.suffix == ".json":
        store = JsonMemoryStore(path=p, embeddings=embeddings)
        from jarvis.modules.memory_adapter_store import wrap_memory_store

        return wrap_memory_store(store)

    if p is not None and p.suffix in (".db", ".sqlite", ".sqlite3"):
        store = SqliteMemoryStore(path=p, embeddings=embeddings)
        from jarvis.modules.memory_adapter_store import wrap_memory_store

        return wrap_memory_store(store)

    backend = jarvis_config.resolve_memory_backend()
    if backend == "sqlite":
        db_path = jarvis_config.MEMORY_DB_FILE
        if not db_path.exists() and jarvis_config.MEMORY_FILE.exists():
            migrate_json_to_sqlite(embeddings=embeddings)
        store = SqliteMemoryStore(path=db_path, embeddings=embeddings)
    else:
        store = JsonMemoryStore(path=jarvis_config.MEMORY_FILE, embeddings=embeddings)

    from jarvis.modules.memory_adapter_store import wrap_memory_store

    return wrap_memory_store(store)


class MemoryStore:
    """Facade over JSON or SQLite memory backends."""

    def __init__(self, path=None):
        self._impl = create_memory_store(path)

    @property
    def path(self):
        return getattr(self._impl, "path", jarvis_config.MEMORY_FILE)

    @property
    def _data(self):
        return self._impl._data

    def _save(self) -> None:
        self._impl._save()

    def __getattr__(self, name):
        return getattr(self._impl, name)

    @staticmethod
    def to_public(entry: dict) -> dict:
        return to_public(entry)

    @staticmethod
    def parse_remember(text: str) -> tuple[str, str, str | None]:
        return parse_remember(text)

    @staticmethod
    def split_remember_facts(content: str) -> list[str]:
        return split_remember_facts(content)


# Back-compat re-exports
_parse_ts = parse_ts
_utc_now = utc_now


class MemoryEngine:
    def __init__(self):
        self.store = MemoryStore()

    def handle(self, prompt: str) -> bool:
        if prompt.lower() == "exit":
            return False

        if prompt.startswith("add "):
            rest = prompt[4:].strip()
            if ":" in rest:
                entry_type, content = rest.split(":", 1)
                entry_type = entry_type.strip()
                content = content.strip()
            else:
                entry_type, content = "note", rest
            self.store.add(entry_type, content)
            print(f"\nAdded [{entry_type}]: {content}\n")
            return True

        if prompt.startswith("tag "):
            parts = prompt[4:].strip().split(maxsplit=1)
            if len(parts) != 2:
                print("\nUsage: tag <index> <tag>\n")
                return True
            try:
                index = int(parts[0])
                entries = self.store.list_entries(include_embedding=True)
                if 0 <= index < len(entries):
                    entries[index].setdefault("tags", []).append(parts[1])
                    self.store._save()
                    print(f"\nTagged entry {index}.\n")
                else:
                    print("\nInvalid index.\n")
            except ValueError:
                print("\nInvalid index.\n")
            return True

        if prompt.startswith("search "):
            results = self.store.search(prompt[7:].strip())
            if results:
                print("\nMatches:\n")
                for entry in results:
                    tags = ", ".join(entry.get("tags", []))
                    tag_str = f" [{tags}]" if tags else ""
                    print(f"  [{entry['type']}]{tag_str} {entry['content']}")
                print()
            else:
                print("\nNo matches.\n")
            return True

        if prompt == "list":
            entries = self.store.list_entries()
            if entries:
                print("\nAll entries:\n")
                for i, entry in enumerate(entries):
                    tags = ", ".join(entry.get("tags", []))
                    tag_str = f" [{tags}]" if tags else ""
                    print(f"  {i}: [{entry['type']}]{tag_str} {entry['content']}")
                print()
            else:
                print("\nMemory is empty.\n")
            return True

        if prompt.startswith("delete "):
            try:
                index = int(prompt[7:].strip())
                if self.store.delete(index):
                    print(f"\nDeleted entry {index}.\n")
                else:
                    print("\nInvalid index.\n")
            except ValueError:
                print("\nUsage: delete <index>\n")
            return True

        if prompt.startswith("clear"):
            parts = prompt.split(maxsplit=1)
            clear_type = parts[1] if len(parts) > 1 else None
            removed = self.store.clear(entry_type=clear_type)
            print(f"\nRemoved {removed} entries.\n")
            return True

        if prompt.startswith("prune"):
            removed = self.store.prune()
            print(f"\nPruned {removed} stale auto memories.\n")
            return True

        if prompt.startswith("export"):
            print(json.dumps(self.store.export_data(), indent=2))
            return True

        print("\nUnknown command. Type 'help' for usage.\n")
        return True


def main():
    engine = MemoryEngine()
    print("\nJarvis Memory Store")
    print("Type 'exit' to quit.")
    print("Commands:")
    print("  add <type>:<content>   add typed entry (or add <content> for note)")
    print("  list                   list all entries")
    print("  search <text>          search entries")
    print("  tag <index> <tag>      tag an entry")
    print("  delete <index>         delete entry")
    print("  clear [type]           clear all or by type")
    print("  prune                  drop stale auto memories")
    print("  export                 dump JSON\n")

    while True:
        try:
            prompt = input("Memory > ")
            if not engine.handle(prompt):
                break
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")
