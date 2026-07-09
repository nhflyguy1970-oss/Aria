# Knowledge Registry & Unified Search

Aria tracks every knowledge source on the workstation and searches them as one.

## Commands (chat or API)

- **Knowledge registry:** `knowledge_registry` — what exists, health, indexing status
- **Sync registry:** `knowledge_sync` — refresh from live workstation state
- **Unified search:** `unified_search` or "search everything: LiteLLM"

## CLI / API

```bash
curl 'http://127.0.0.1:8765/api/knowledge/registry?refresh=1'
curl 'http://127.0.0.1:8765/api/knowledge/search?q=Docker+Compose'
```

## Source types

Document library, code index, projects, git repos, journal, conversation memory, learned URLs, datasets, YouTube transcripts, archives, and project docs.

Registry file: `data/knowledge/registry.json`
