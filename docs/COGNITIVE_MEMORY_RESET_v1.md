# Cognitive Memory Reset v1 — Post-D041 Baseline

**Date (UTC):** 2026-07-16  
**Repository:** Aria / Jarvis only  
**Standalone ACM:** not modified  
**Operator tool:** `scripts/acm_cognitive_memory_reset.py`

## Reason

Early autobiographical memories in Aria’s embedded ACM durable store were formed
**before**:

- D038 Memory Authority  
- D039 Cognitive Intent Classification  
- D040 End-to-End Cognitive Dispatch  
- D041 Semantic Extraction  

Those memories contain known incorrect identity data (example: assistant named
“Jeff”; user statement contaminated with “you are aria. please remember that.”).
They are not scientifically valid as a behavioral baseline.

## Scope

**Removed (learned autobiographical memory only):**

| Item | Pre-reset count |
|------|-----------------|
| Experiences | 92 |
| Concepts (learned + schemas) | 41 |
| Associations | 196 |
| Goals | 0 |
| Adaptations | 0 |
| Agent identity attributes | name=Jeff |
| User identity attributes | contaminated statement |
| Project identity attributes | mentioned=projects |

**Retained:**

- ACM architecture and all cognitive organs (vendored `aria_acm/`)  
- Semantic Extraction / Dispatch / Memory Authority / Intent Classification (code)  
- Confidence, provenance, accessibility, attention, consolidation, forgetting, reflection, learning **logic**  
- Configuration, system prompts, documentation, tests, build, releases  
- Aria application functionality  

## Archive (optional)

By default the operator tool **archives** then resets. For production empty start without preserving prior content:

```bash
.venv/bin/python scripts/acm_cognitive_memory_reset.py --no-archive
```

See [`PRODUCTION_ACM_EMPTY_START.md`](PRODUCTION_ACM_EMPTY_START.md).

## Post-reset baseline

| Check | Result |
|-------|--------|
| Experiences | **0** |
| Associations | **0** |
| Goals | **0** |
| Adaptations | **0** |
| Identity attributes (user/agent/project) | **none** |
| Schema concept shells (empty agent/user/project nuclei) | 3 (architecture scaffolding only — not autobiographical content) |
| Durable DB size | ~32 KiB empty store |
| Architecture operational (`classify_request` / `cognitive_respond`) | **yes** |

## Behavioral baseline established

All **future** autobiographical memories in Aria shall be formed under:

1. Memory Authority (D038)  
2. Cognitive Intent Classification (D039)  
3. End-to-End Cognitive Dispatch (D040)  
4. Semantic Extraction (D041) — after explicit promotion into Aria  

Until D041 is promoted into Aria’s vendored copy, new memories still use the
currently vendored ACM revision; the **data** baseline is clean either way.

## Re-validate

```bash
.venv/bin/python scripts/acm_cognitive_memory_reset.py --validate-only
```

## Teaching gate

**Do not teach Aria new autobiographical memories until explicit approval.**
