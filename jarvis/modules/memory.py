"""Persistent memory store with semantic search, namespaces, and relevance."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone

from jarvis import llm
from jarvis.config import DATA_DIR, MEMORY_FILE

MEMORY_TYPES = ("fact", "auto", "note", "preference", "project", "failure", "strategy")
DEFAULT_NAMESPACE = "default"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


class MemoryStore:
    def __init__(self, path=None):
        self.path = path or MEMORY_FILE
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                entries = data.get("entries") or []
                for i, e in enumerate(entries):
                    self._normalize_entry(e, i)
                data["entries"] = entries
                return data
            except (json.JSONDecodeError, OSError):
                pass
        return {"entries": [], "version": 2}

    def _normalize_entry(self, entry: dict, index: int) -> dict:
        entry.setdefault("id", f"m{index}")
        entry.setdefault("namespace", DEFAULT_NAMESPACE)
        entry.setdefault("tags", [])
        entry.setdefault("access_count", 0)
        entry.setdefault("relevance", 1.0)
        entry.setdefault("timestamp", _utc_now())
        if entry.get("type") not in MEMORY_TYPES:
            entry["type"] = "note"
        return entry

    def _save(self) -> None:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(self.path)
        self.path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _next_id(self) -> str:
        existing = {e.get("id") for e in self._data["entries"]}
        while True:
            nid = uuid.uuid4().hex[:10]
            if nid not in existing:
                return nid

    @staticmethod
    def to_public(entry: dict) -> dict:
        out = {k: v for k, v in entry.items() if k != "embedding"}
        return out

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

        if entry_type not in ("failure", "strategy") and not is_trusted_memory_content(content):
            raise ValueError("Refusing to store test-artifact content in live memory")
        entry_type = entry_type if entry_type in MEMORY_TYPES else "fact"
        embedding = llm.embed_text(content)
        entry = {
            "id": self._next_id(),
            "type": entry_type,
            "content": content,
            "tags": tags or [],
            "namespace": (namespace or DEFAULT_NAMESPACE).strip() or DEFAULT_NAMESPACE,
            "timestamp": _utc_now(),
            "access_count": 0,
            "relevance": 1.0,
            "embedding": embedding,
        }
        self._data["entries"].append(entry)
        self._save()
        return entry

    def similar_exists(self, content: str, threshold: float = 0.88) -> bool:
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
            e_emb = e.get("embedding") or []
            if e_emb and llm.cosine_similarity(emb, e_emb) >= threshold:
                return True
        return False

    def relevance_score(self, entry: dict) -> float:
        base = float(entry.get("relevance", 1.0))
        age_days = max(0, (datetime.now(timezone.utc) - _parse_ts(entry.get("timestamp", ""))).days)
        decay = max(0.25, 1.0 - age_days * 0.008)
        access_boost = min(0.4, int(entry.get("access_count", 0)) * 0.04)
        type_penalty = 0.85 if entry.get("type") == "auto" else 1.0
        return (base * decay + access_boost) * type_penalty

    def touch(self, entry_id: str) -> None:
        for e in self._data["entries"]:
            if e.get("id") == entry_id:
                e["access_count"] = int(e.get("access_count", 0)) + 1
                e["last_accessed"] = _utc_now()
                self._save()
                return

    def list_entries(
        self,
        entry_type: str | None = None,
        *,
        namespace: str | None = None,
        query: str | None = None,
        include_embedding: bool = False,
    ) -> list[dict]:
        entries = list(self._data["entries"])
        if entry_type:
            entries = [e for e in entries if e.get("type") == entry_type]
        if namespace:
            entries = [e for e in entries if e.get("namespace") == namespace]
        if query:
            q = query.lower().strip()
            entries = [
                e for e in entries
                if q in e.get("content", "").lower()
                or any(q in t.lower() for t in e.get("tags", []))
                or q in e.get("namespace", "").lower()
            ]
        entries.sort(key=lambda e: (self.relevance_score(e), e.get("timestamp", "")), reverse=True)
        if include_embedding:
            return entries
        return [self.to_public(e) for e in entries]

    def get(self, entry_id: str) -> dict | None:
        for e in self._data["entries"]:
            if e.get("id") == entry_id:
                return self.to_public(e)
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
        for e in self._data["entries"]:
            if e.get("id") != entry_id:
                continue
            if content is not None:
                e["content"] = content.strip()
                e["embedding"] = llm.embed_text(e["content"])
            if entry_type and entry_type in MEMORY_TYPES:
                e["type"] = entry_type
            if tags is not None:
                e["tags"] = tags
            if namespace is not None:
                e["namespace"] = namespace.strip() or DEFAULT_NAMESPACE
            e["timestamp"] = _utc_now()
            self._save()
            return True
        return False

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        namespace: str | None = None,
    ) -> list[dict]:
        query_lower = query.lower().strip()
        pool = self._data["entries"]
        if namespace:
            pool = [e for e in pool if e.get("namespace") == namespace]

        keyword_matches = [
            e for e in pool
            if query_lower in e["content"].lower()
            or any(query_lower in t.lower() for t in e.get("tags", []))
        ]
        if keyword_matches:
            for e in keyword_matches:
                self.touch(e["id"])
            return [self.to_public(e) for e in keyword_matches[-limit:]]

        if not llm.embed_available():
            return []

        query_emb = llm.embed_text(query)
        if not query_emb:
            return []

        scored = []
        for e in pool:
            emb = e.get("embedding") or []
            if not emb:
                emb = llm.embed_text(e["content"])
                e["embedding"] = emb
            sim = llm.cosine_similarity(query_emb, emb)
            if sim > 0.3:
                scored.append((sim * self.relevance_score(e), e))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [e for _, e in scored[:limit]]
        for e in results:
            self.touch(e["id"])
        return [self.to_public(e) for e in results]

    def delete(self, index: int) -> bool:
        entries = self._data["entries"]
        if 0 <= index < len(entries):
            del entries[index]
            self._save()
            return True
        return False

    def delete_id(self, entry_id: str) -> bool:
        idx = self.find_index(entry_id)
        if idx is None:
            return False
        del self._data["entries"][idx]
        self._save()
        return True

    def clear(self, entry_type: str | None = None, namespace: str | None = None) -> int:
        before = len(self._data["entries"])
        if not entry_type and not namespace:
            self._data["entries"] = []
            self._save()
            return before
        kept = []
        for e in self._data["entries"]:
            drop = False
            if entry_type and namespace:
                drop = e.get("type") == entry_type and e.get("namespace") == namespace
            elif entry_type:
                drop = e.get("type") == entry_type
            elif namespace:
                drop = e.get("namespace") == namespace
            if not drop:
                kept.append(e)
        removed = before - len(kept)
        self._data["entries"] = kept
        self._save()
        return removed

    def prune(
        self,
        *,
        max_age_days: int = 120,
        min_score: float = 0.35,
        types: tuple[str, ...] = ("auto",),
    ) -> int:
        now = datetime.now(timezone.utc)
        kept = []
        removed = 0
        for e in self._data["entries"]:
            if e.get("type") in types:
                age = (now - _parse_ts(e.get("timestamp", ""))).days
                if age >= max_age_days and self.relevance_score(e) < min_score:
                    removed += 1
                    continue
            kept.append(e)
        self._data["entries"] = kept
        if removed:
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
        }

    def latest_checkpoint(self, namespace: str | None = None) -> dict | None:
        candidates = [
            e for e in self._data["entries"]
            if "checkpoint" in (e.get("tags") or [])
        ]
        if namespace:
            candidates = [c for c in candidates if c.get("namespace") == namespace]
        if not candidates:
            return None
        return self.to_public(max(candidates, key=lambda e: e.get("timestamp", "")))

    def upsert_checkpoint(self, content: str, namespace: str = "default") -> dict:
        """Replace prior checkpoint for this namespace with a fresh project state."""
        ns = (namespace or DEFAULT_NAMESPACE).strip() or DEFAULT_NAMESPACE
        self._data["entries"] = [
            e for e in self._data["entries"]
            if not (e.get("namespace") == ns and "checkpoint" in (e.get("tags") or []))
        ]
        return self.add(
            "project",
            content,
            tags=["checkpoint", "project-state"],
            namespace=ns,
        )
        return {
            "version": 2,
            "exported_at": _utc_now(),
            "entries": [self.to_public(e) for e in self._data["entries"]],
        }

    def import_data(self, payload: dict, *, merge: bool = True) -> int:
        incoming = payload.get("entries") if isinstance(payload, dict) else None
        if not isinstance(incoming, list):
            raise ValueError("Invalid memory import — expected {entries: [...]}")
        added = 0
        if not merge:
            self._data["entries"] = []
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
            entry = {
                "id": eid or self._next_id(),
                "type": entry_type,
                "content": content,
                "tags": tags,
                "namespace": namespace,
                "timestamp": raw.get("timestamp") or _utc_now(),
                "access_count": int(raw.get("access_count") or 0),
                "relevance": float(raw.get("relevance") or 1.0),
                "embedding": llm.embed_text(content),
            }
            self._data["entries"].append(entry)
            existing_ids.add(entry["id"])
            existing_content.add(content.lower())
            added += 1
        if added:
            self._save()
        return added

    @staticmethod
    def parse_remember(text: str) -> tuple[str, str, str | None]:
        """Return (content, entry_type, namespace) from natural language."""
        text = (text or "").replace("\r\n", "\n").strip()
        lower = text.lower()
        namespace = None
        if m := re.search(r"\b(?:in|for)\s+(?:namespace|project)\s+[`'\"]?(\w[\w-]*)[`'\"]?", lower):
            namespace = m.group(1)
            text = re.sub(
                r"\b(?:in|for)\s+(?:namespace|project)\s+[`'\"]?\w[\w-]*[`'\"]?\s*",
                "",
                text,
                flags=re.I,
            )
        for prefix in (
            r"^(please\s+)?(remember|don't forget|note that|keep in mind)\s*(that\s+)?",
            r"^(these|the following)\s+facts?\s*:?\s*",
            r"^facts?\s*:?\s*",
        ):
            text = re.sub(prefix, "", text, flags=re.I).strip()
        entry_type = "fact"
        if re.search(r"\b(preference|prefer)\b", lower):
            entry_type = "preference"
        elif re.search(r"\b(project|codename)\b", lower):
            entry_type = "project"
        return text.strip(), entry_type, namespace

    @staticmethod
    def split_remember_facts(content: str) -> list[str]:
        """Split multi-line remember payloads into separate facts."""
        text = (content or "").replace("\r\n", "\n").strip()
        if not text:
            return []
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        skip = re.compile(
            r"^(do not summarize|just reply|reply with|no summary|stored\.?)\b",
            re.I,
        )
        lines = [ln for ln in lines if not skip.search(ln)]
        if len(lines) >= 2:
            return lines
        return [text] if text else []


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
