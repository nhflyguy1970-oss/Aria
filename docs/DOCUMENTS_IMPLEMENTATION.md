# Documents & RAG Implementation

## Executive Summary

Documents is Aria’s **Personal Document Intelligence Layer** — local files,
grounded search, cited answers, and Memory **candidates**. It is not Google Drive,
SharePoint, Notion, or an enterprise DMS.

This delivery transforms the thin library browser into a **Documents Home**
workspace that matches the strength of the existing parse/index/RAG engine.

## Product philosophy

| Layer | Meaning |
|-------|---------|
| **Documents** | Personal document library (files you own on disk) |
| **Knowledge** | Extracted / researched knowledge (briefs, registry, git) |
| **Memory** | Autobiographical cognition (ACM) — adopt only |
| **Search index** | Retrieval engine over the library (formerly “RAG” in UI) |

**Answers:** “I know I have this document somewhere.”  
**Does not answer:** “I need another cloud drive.”

## Documents Home

Sections: library overview · index health · recent files/searches/imports ·
Memory candidates · project retrieval pack · preview/metadata · quick actions.

UI: `jarvis/gui/static/documents.js` + `#documentsView`.

## Search

- `/api/documents/search` → `search_library` with **citations** (`doc-N`)
- Actionable hits: Preview, Summarize, Ask Aria, Learn, Open Folder
- Esc / Clear exits search; `/` focuses search

## Upload

- Drag & drop + file picker → `POST /api/documents/upload`
- Folder import → `POST /api/documents/import-folder`
- Smart import classification suggests type; **never** auto-creates memories
- Recent imports tracked in `data/document_imports.json`

## Hybrid RAG

- Library index: `documents_index.json` (extension parity with pipeline)
- Keyword fallback when embeds offline
- `intelligence/hybrid_rag` available for Ask-with-sources
- Rebuild via **Rebuild Search Index** (not “Reindex RAG”)

## Project retrieval

`GET /api/documents/project-pack` scopes library + git docs + knowledge namespace
for the active project. Chat: “ask my documents” / project search.

## Memory candidates

**Learn never writes autobiography.**

`stage_learn_candidates` / `learn_from_*` (default) → `propose_candidate`  
User adopts in Memory → ACM encodes.

`encode=True` remains only for explicit adopt/legacy paths.

## Knowledge integration

Registry, unified search, git indexes, and topic briefs remain separate.
Documents stay documents; Knowledge stays knowledge.

## Chat citations

- `documents_rag.context_for_query` returns `(context, warnings, citations)`
- KnowledgeEngine injects a **visible sources block** (never silent)
- `document_search` / `document_ask_library` return citation payloads
- Routed: search, learn, ingest, recall, briefing, ask library

## Accessibility & keyboard

| Key | Action |
|-----|--------|
| `/` | Search |
| `N` | Upload |
| `Esc` | Clear search / close dialogs |
| `?` | Help |
| Arrows | Navigate list |

Documents included in Ctrl+Tab `VIEW_ORDER`.

## Performance

- Index rebuild is explicit or mtime-triggered
- Hybrid search does not rebuild on query
- Upload reindexes after import (acceptable for personal libraries)

## Testing

```bash
./venv/bin/pytest tests/test_documents_workspace.py tests/test_document_learning.py -q
```

Coverage: health/rebuild/upload, citations, candidates-only learn, home/project pack,
context citations, smart classify, UI wiring (no ICS / no “Reindex RAG”).

## Future roadmap

- Incremental per-file indexing
- Cross-encoder rerank
- Richer page-level preview
- Eval set for citation quality
- Optional vector DB only if library scale demands it

## Design gate

1. Does this help users find information?  
2. Is retrieval trustworthy with visible citations?  
3. Are Documents / Knowledge / Memory boundaries clear?  
4. Is ACM constitution respected (candidates only)?  
5. Is ownership local-first — not a cloud DMS?  

If not — redesign it.
