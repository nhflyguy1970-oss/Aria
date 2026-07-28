# Knowledge Graph / Connections Implementation

## Executive Summary

**Connections** is Aria’s user-facing relationship explorer. The underlying
implementation remains the Knowledge Graph (`graph_store` + helpers).

| Layer | Meaning |
|-------|---------|
| **Documents** | Document Intelligence (files you own) |
| **Knowledge** | Knowledge Briefs (researched topics / registry) |
| **Connections** | Knowledge Graph (entities & relationships) |
| **Memory** | Autobiographical cognition (ACM) |

**ACM remains the only cognitive source of truth.** The graph **mirrors**
adopted or explicitly approved relationships. It never replaces Memory.

This delivery transforms a hidden developer API into a trustworthy Connections
system: inspectable entities, visible provenance, review-before-write imports,
chat grounding with confidence thresholds, and Mission Control health.

## Architecture

```
UI Connections Home / Chat / Documents / MC
        │
        ▼
 /api/connections/*   (+ /api/intelligence/graph/* compatibility)
        │
        ▼
 connections_services  (product layer)
        │
        ├── intelligence.knowledge_graph  (extract / explicit ingest)
        ├── relationship_memory           (teach + ACM record_link)
        └── modules.graph_store           (sqlite default · Bolt optional)
```

Persistence: `{DATA_DIR}/relationship_graph.db` (or `JARVIS_GRAPH_PATH`).  
Backends: `JARVIS_GRAPH_BACKEND=sqlite|memgraph|neo4j`.

## Connections philosophy

- Model, retrieve, and explain **relationships**
- Not a second Memory
- Not Documents / Knowledge Briefs
- Not Neo4j Bloom / Obsidian Graph clone
- Local-first; explicit user control; provenance required

## Relationship lifecycle

```
User
  → Memory candidate (optional)
  → Adopt
  → ACM encode (cognitive SoT)
  → Graph mirror (Connections)

Documents / Import text
  → Extract
  → Review (pending queue)
  → Approve
  → Graph write with provenance
```

**Never:** Graph → Memory (automatic).

## ACM alignment

- `adopt_candidate` calls `mirror_adopted_memory` for relationship-tagged content
- `record_link` encodes ACM then mirrors to graph with `source=memory`
- `sync_memory_entry` auto-extract is **disabled** unless `JARVIS_GRAPH_SYNC_MEMORY=1`

## Namespaces

| Namespace | Role |
|-----------|------|
| `default` | Manual / general |
| `relationships` | ACM relationship mirror |
| `project:<slug>` | Project-scoped subgraph |
| `queries` | **Deprecated** — cleanup only; soft-ingest removed |

## Projects

`project_subgraph(slug)` / `GET /api/connections/project?slug=` scopes nodes and
edges to `project:<slug>`. Unrelated projects are never merged.

## Documents

Documents never auto-write the graph.

Workflow: Analyze / preview → **Add to Connections…** → pending review → Approve
in Connections Home (`POST /api/connections/from-document`).

## Memory mirroring

Associative Memory / Journal surfaces use `jarvis.knowledge_graph.search`
(shim) and label hits as **Connections**, not autobiography.

## Chat grounding

`relationship_context_for_chat` / `chat_grounding_context`:

- Requires confidence ≥ `0.55` (default)
- Requires provenance (`source` not unknown, or `memory_id`)
- Injects a visible “Trusted Connections” block with why/source/confidence
- Actions: `connection_recall`, `connection_lookup`

## Mission Control

Databases tab shows Connections health only:

- Backend, status, node/relationship counts, namespaces
- Last ingest / cleanup, storage path
- Clarifies: not Memory, not Documents

MC “Knowledge” tab is **Knowledge Briefs / retrieval**, not the graph.

## API surface (product)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/connections/home` | Connections Home |
| GET | `/api/connections/health` | MC / status |
| GET | `/api/connections/search` | Entity / relationship search |
| GET | `/api/connections/entity` | Entity page |
| POST | `/api/connections/entity` | Create entity |
| POST | `/api/connections/relationship` | Create relationship (provenance required) |
| POST | `/api/connections/propose` | Stage extract for review |
| POST | `/api/connections/approve` | Persist pending |
| DELETE | `/api/connections/entity` | Delete + undo snapshot |
| DELETE | `/api/connections/relationship` | Delete edge |
| POST | `/api/connections/prune` | Orphan cleanup |
| POST | `/api/connections/cleanup-queries` | Remove queries pollution |
| POST | `/api/connections/undo` | Undo destructive action |
| POST | `/api/connections/merge` | Entity merge |
| GET | `/api/connections/assistant` | Suggestions (no auto-modify) |
| GET | `/api/connections/explain` | Why two entities connect |
| GET | `/api/connections/project` | Project subgraph |
| POST | `/api/connections/from-document` | Doc → pending review |

Intelligence compatibility: `POST /api/intelligence/graph/ingest` now **proposes**
by default; persist only with `approve`/`explicit` true. Query soft-ingest removed
from `intelligent_query`.

## UI

- Sidebar + view tab: **Connections**
- Home: overview, identity legend, namespaces, activity, pending reviews, entity panel
- Search modes: all / entities / relationships / people / places / orgs / concepts / project / document
- Keyboard: `/` search · `N` new · `Delete` delete · `Esc` clear · `?` help · arrows
- Command palette: Open Connections, Search Connections, import/cleanup context

## Performance

- SQLite WAL default; personal-library scale
- No query-time soft ingest
- Bolt optional when configured; falls back to sqlite

## Testing

```bash
./venv/bin/pytest tests/test_connections.py tests/test_intelligence_platform.py::test_knowledge_graph_extract_and_ingest -q
```

Coverage includes: store CRUD/prune, provenance guards, propose/approve,
pollution prevention, ACM mirror, chat grounding, shim search, project
namespaces, assistant, explain, home/health.

## Future roadmap

- Richer entity merge preview UI
- Optional LLM extract behind the same review queue
- Lightweight link diagram only after data quality is trusted
- Citation eval harness for relationship explanations
- Vector DB: **not** planned unless measured scale demands it

## Design gate

1. Is ACM still the only cognitive authority?  
2. Can users see why entities are connected?  
3. Is provenance visible?  
4. Does this reduce graph pollution?  
5. Does this avoid becoming a Neo4j product?  

If not — redesign it.
