# Data Migration Plan — INTO ACM Only

**Status:** M2 IMPLEMENTED — operator harvest live; nothing migrates automatically  
**Direction:** Historical Aria memory → ACM Experiences/Concepts/Associations/Identity (Supremacy Rule 5)  
**Operator entry:** `python scripts/acm_harvest.py` · `aria_core.acm_harvest.harvest_into_acm` — never background auto-migrate.

---

## Objectives

1. Import user autobiography into ACM without silent loss.  
2. Preserve supersede/history via Experiences + provenance (`legacy_import`).  
3. Never invent lineage.  
4. Never leave a second cognitive SoT after M4.

---

## Source inventories

| Source | Location (typical under `JARVIS_DATA_DIR`) | Target ACM artifacts | Priority |
|--------|--------------------------------------------|----------------------|----------|
| MemoryStore entries | `memory.db` or `memory.json` | Experience (+ Concept residue) | P0 |
| Profile / preferences | ns `profile`, type preference | Identity attrs + Concepts | P0 |
| Facts / notes / auto | typed entries | Experiences | P0 |
| Superseded entries | tag `superseded` | Prior Experiences (cool/inactive) + revise lineage | P0 |
| Journal cognitive residue | journal-remembered + `journal-learned` ns | Experience + `journal` tags | P1 |
| Project checkpoints | checkpoint upserts / project ns | Goals + Experiences | P1 |
| Experience patterns | ns `experience` | Experiences + skill Concepts | P1 |
| Relationship facts | ns `relationships` (+ graph edges as Associations) | Concepts + Associations | P1 |
| Teaching / corrections / observed / workflows | respective ns | Experiences + provenance | P1 |
| Trust / strategies (cognitive) | strategy entries | Concepts (not spoken-by-default) | P2 |
| Learning distilled profile facts | consolidation outputs | encode + provenance `learned` | P2 |
| Personalization JSON cognitive fields | only if autobiographical | Concepts / encode | P2 audit |
| DualWrite platform copy | AI-Platform local_json | **Do not dual-import** — Aria store is source of truth for harvest | Skip |
| Embeddings DB | `memory_vectors.db` | **Do not import as memory** — rebuild Activation priors later if needed | Skip |
| Knowledge / RAG corpora | documents | Citation wall — explicit encode only later | Skip |
| Chat transcripts | `chat_branches.json` | Not autobiography SoT — skip unless operator opt-in excerpt encode | Skip default |
| Telemetry / tool-outcome | tagged telemetry | Skip (KEEP-HOST) | Skip |

---

## Schema map (legacy entry → encode)

| Legacy field | ACM mapping |
|--------------|-------------|
| `id` | provenance / meta `legacy_id` (idempotency key) |
| `content` | `encode(text=content)` |
| `type` | `kind` map: preference→`preference`; identity-ish→`identity`; else `experience` + meta `legacy_type` |
| `namespace` | `context_tags` += `ns:<namespace>` |
| `tags` | `context_tags` + Concept cues |
| `timestamp` | `t_start` (and meta `legacy_timestamp`) |
| `relevance` / `access_count` | meta only (do not fake Confidence) |
| `meta` | filtered into provenance attributes (no prompts) |
| superseded-of relation | encode older first; newer via `revise_experience` / `revises_id` |
| journal marker | `context_tags` += `journal` |

Idempotency: before encode, if Experience with `legacy_id=X` exists → skip (or reconcile) — safe re-run.

---

## Import strategy (batch, offline-capable)

1. **Preflight:** checksum legacy DB; ACM `backup` / empty or known snapshot.  
2. **Freeze writes** on legacy (or Shadow-only). Record freeze clock.  
3. Export legacy dump (ids, text, tags, timestamps, namespaces, supersede links).  
4. Sort: non-superseded parents, then supersede chains oldest→newest.  
5. For each entry: `encode(...)` with `provenance_origin=legacy_import` (façade/meta).  
6. Replay corrections via `revise_experience` when parent known.  
7. Build Goal Space from active checkpoints (`open_goal` + encode).  
8. Identity high-impact attributes: encode then **assent** per Policy Gate.  
9. Optional Association pass from relationship graph edges (non-authoritative if incomplete).  
10. Emit **Migration Report**: counts in/out, skips, conflicts, unresolved supersedes.  
11. Run Reconciliation samples on contested topics.  
12. Operator sign-off before M3.

**Batch sizing (design defaults):** 500 entries/batch; snapshot ACM between batches; abort batch on integrity failure → restore ACM snapshot (legacy untouched).

No automatic background migration without operator command.

---

## Validation / verification

| Check | Method | Pass criterion (design) |
|-------|--------|-------------------------|
| Completeness | Entry count vs Experiences with `legacy_id` | ≥ 99.5% of P0 rows (documented skips listed) |
| Identity continuity | `who_am_i` covers critical profile keys | Manual checklist 100% of keyed items |
| Preference spot-check | Human UAT list (N≥20) | ≥ 95% agree |
| Journal presence | Experiences tagged journal | ≥ expected remember count |
| Provenance | Every imported Experience | provenance present; fabricated=false |
| No dual-write drift | Legacy freeze hash vs post-harvest dump | Hash match |
| Idempotent re-run | Second harvest | Zero duplicate `legacy_id`s |

---

## Recovery during migration

- Keep immutable legacy DB backups (`*.pre_acm_harvest`).  
- ACM durable snapshots before/after each batch (`export_snapshot` / `backup`).  
- Failed batch → `restore` ACM snapshot; legacy untouched.  
- Partial harvest resumes via `legacy_id` skip.

---

## Rollback of data migration

See [`ROLLBACK_PLAN.md`](ROLLBACK_PLAN.md): reattach legacy SoT; ACM harvest retained as non-authoritative archive until cleared by policy. Harvest does **not** delete legacy until M4 vault decision.
