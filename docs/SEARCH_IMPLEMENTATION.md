# Search Implementation

Aria **Search** is a first-class product: one shared federated retrieval engine with Search Home, ranking, history, saved searches, diagnostics, and Mission Control health.

## Product identity

| | |
|--|--|
| Operator name | **Search** |
| Architecture term | Federated Retrieval |
| Pipeline | `shared_search_pipeline` |
| Package | `jarvis/search_product/` |

### Owns

Search Home, federated search, sessions, ranking, result presentation, history, saved searches, diagnostics, health, APIs, SearchResult contract, intent classification, parallel retrieval, open-in-context.

### Does not own

Documents, Memory, Knowledge Graph, Projects, Gallery, Smart Home, Voice, Vision, Browser, Coding, Planner, Calendar, Automation, Chat synthesis, web search **backend** (SearXNG/DDG — Chat synthesizes answers).

Products own their data. Search retrieves.

## Mental model

| Surface | Role |
|---------|------|
| Sidebar | Filter **navigation** only |
| Ctrl+K | Commands + quick federated search |
| Search Home | Browse everything (facets, previews, history) |
| Chat | Answer + synthesis (including web) |
| Voice | Spoken search → same engine |
| Product views | Scoped search; products own corpora |

## One pipeline

```
Query → Intent → Corpus selection → Parallel retrieval → Ranking →
Dedup → SearchResult contract → Presentation → Open in context →
History → Diagnostics
```

Every entry point is a client of this pipeline:

Search Home · Ctrl+K · Sidebar handoff · Chat `unified_search` · Voice · Agents · `/api/search/product/*` · `/api/knowledge/search` (compat) · Mission Control · product-scoped boxes (local UX only)

## SearchResult contract

Every hit exposes:

`id`, `source`, `source_label`, `title`, `summary`, `preview`, `location`, `score`, `confidence`, `strategy`, `open`, `metadata`, `highlights`, `icon`

See `jarvis/search_product/contract.py`.

## Facets

`everything`, `documents`, `memory`, `projects`, `journal`, `code`, `graph`, `connections`, `audio`, `web`, `planner`, `calendar`, `gallery` (opt-in), `home_assistant` (opt-in), `flytying`, `automation`, `learned`

Code facet supports `code_mode`: `auto` | `semantic` | `grep`.

Web facet returns sources and hands off to Chat for synthesis — Search does **not** duplicate web answer generation.

## Ranking

`jarvis/search_product/ranking.py` fuses:

semantic/base score · keyword overlap · intent match · view context · project hint · history frequency · soft recency

## APIs

| Path | Role |
|------|------|
| `GET /api/search/product` | Status |
| `GET /api/search/product/home` | Search Home payload |
| `GET/POST /api/search/product/query` | Federated query |
| `GET /api/search/product/facets` | Facet matrix |
| `GET/DELETE /api/search/product/history` | History |
| `GET/POST/DELETE /api/search/product/saved` | Saved searches |
| `GET /api/search/product/diagnostics` | Diagnostics |
| `GET /api/search/product/mission` | Mission Control panel |
| `GET/POST /api/search/product/settings` | Opt-in corpora, code mode |
| `GET /api/knowledge/search` | Compat client (legacy hits + contract) |

## Mission Control

Snapshot key: `search` via `search_mission_panel()`.

Shows state, corpora count, latency, web backend, registry/index readiness, recovery, deep links to Search Home and diagnostics.

## Developer guide

```python
from jarvis.search_product import run_search

out = run_search("warranty", facets=["documents"], limit=12)
for r in out["results"]:
    print(r["source"], r["title"], r["open"])
```

Do **not** invent a second search stack. Add a retriever in `retrievers.py` that calls the product-owned API and returns `make_result(...)`.

## Operator guide

1. Open **Search** from Workspaces or the Search tab.
2. Type a query; use facets to narrow.
3. Use **Open in context** / **Open with query** to land in the owning product with the query preserved.
4. For web answers, use the Web facet then **Synthesize in Chat**.
5. Enable Gallery / Home Assistant under Privacy opt-in if desired.
6. Ctrl+K remains the fast launcher; sidebar remains navigation filter.

## Censored / uncensored

One Search engine. Modes may only differ in presentation/policy filters — never duplicate retrieval or ranking.

## Do not build

- A second Search engine
- Duplicate web/Chat/Voice search stacks
- Elastic/Solr for single-user workstation
- Replacing palette or Chat

## Tests

```bash
pytest tests/test_search_product.py tests/test_web_search_auto.py tests/test_product_cross_system_search.py -q
```

## Roadmap (shipped in this delivery)

- Search Home + mental model copy
- Expanded federation (graph, audio, planner, calendar, web, flytying, automation; gallery/HA opt-in)
- Rich results + deep links
- Shared contract + ranking
- Mission Control card
- History / saved searches
- Intent + parallel retrieval
- Unified code facet modes
- Documentation + tests
