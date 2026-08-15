> **Superseded (2026-07-31):** Historical certification report, not current engineering authority. Use [`Architecture Bible`](architecture/ARCHITECTURE_BIBLE.md) and [`Engineering Roadmap`](architecture/ENGINEERING_ROADMAP.md) as the governing docs.

# Aria Cross-System Consistency Certification — 2026-07-31

**Mandate:** One truth. Every subsystem that represents the same fact must agree — immediately after mutate, after reload, and after restart. Disagreement = FAIL.

**Probe:** `data/certification/onetruth_probe_2026-07-31.json`  
**Prior local consistency:** `docs/ARIA_CONSISTENCY_AUDIT_2026-07-31.md`, `docs/ARIA_TRUTH_VALIDATION_2026-07-31.md`

---

## Dependency map (audited)

| Object | Create | Modify/Delete | Displays | Cache | Index/Search | Links | Activity | History/Meta |
|---|---|---|---|---|---|---|---|---|
| Image | Chat / Gallery generate → `data/generated/` | Soft-delete → trash; restore; purge | Gallery, Chat embeds, Lightbox, Jobs | `cache_state` gallery | Federated `gallery` (+ now default-on) | Chat markdown `/api/gallery/{name}` | gallery outbox | `gallery_product/metadata.json`, prompt history |
| Chat msg | `/api/chat` | Clear / scrub on media delete | Chat UI, branch list | in-memory BranchManager | Federated **`chat`** (new) | — | client activity | `chat_branches.json` |
| Planner task/event | `/api/planner/*` | complete/delete | Planner, Calendar | — | `planner` | Calendar ids | planner_live / outbox slot | `planner.db` |
| Journal bullet | `/api/journal/daily` | edit/delete | Journal, Calendar | — | `journal` | Calendar `journal-note:` | — | `journal/bullet_journal.json` |
| Project | `/api/projects` | PATCH title; archive/restore | Projects home | — | `projects` | Coding active project | — | `projects/{slug}/meta.json` |
| Appearance | POST appearance + localStorage | theme/accent | All chrome | localStorage | `settings` corpus | — | — | `settings_product/appearance.json` |

---

## Verdict

**Audited cross-system create → delete → restore → search → calendar → projects → settings: PASS after repairs.**

Initial one-truth probe: **23 PASS / 1 FAIL** (diagnostics omitted `chat` facet label). Facet registry fixed; re-check **DIAG_FACETS_OK**. Live paths for Gallery↔Search, Chat↔Search, Restore↔Chat/Jobs/Activity already **PASS** in the same run.

---

## Inconsistencies (each repaired)

### 1. Restore left Chat + Jobs lying

| | |
|---|---|
| **Subsystem A** | Gallery trash restore |
| **Subsystem B** | Chat history / Job Center |
| **Expected truth** | Restored file ⇒ Chat embed live again; Jobs not `asset_missing` |
| **Observed** | Restore moved file + invalidated cache only; Chat kept `*[Image removed…]*`; Jobs stayed failed |
| **Root cause** | `soft_delete.restore()` never called consistency helpers (delete path did) |
| **Repair** | `on_gallery_asset_restored` → `restore_chat_gallery_refs` + `clear_asset_missing`; emit `gallery_restore` activity |
| **Regression** | `tests/test_onetruth_restore_search.py::test_restore_chat_gallery_refs_roundtrip` |
| **Final verification** | Probe Restore↔Chat / Jobs / Search / Activity **PASS** |

### 2. Search could not see Gallery (default) or Chat at all

| | |
|---|---|
| **Subsystem A** | Gallery / Chat |
| **Subsystem B** | Federated Search |
| **Expected truth** | Created images and conversation text findable when searchable |
| **Observed** | Gallery opt-in default **off**; no chat/conversations retriever |
| **Root cause** | Privacy-era `OPT_IN_DEFAULT_OFF` included gallery; no `retrieve_chat` / FACETS entry |
| **Repair** | Gallery + **chat** in `DEFAULT_ENABLED`; ignore stale opt-out for graduated corpora; `retrieve_chat` over `chat_branches.json`; FACETS + diagnostics owner |
| **Regression** | `tests/test_onetruth_restore_search.py::test_search_default_includes_gallery_and_chat` |
| **Final verification** | Gallery↔Search, Chat↔Search, Projects↔Search, Planner/Journal↔Search **PASS** |

### 3. Multi-tab Settings diverged

| | |
|---|---|
| **Subsystem A** | Tab 1 theme/accent |
| **Subsystem B** | Tab 2 chrome |
| **Expected truth** | Same origin tabs show the same theme/accent without full reload |
| **Observed** | Write to localStorage + POST; no `storage` / BroadcastChannel listener |
| **Root cause** | `theme.js` only applied theme in the writing tab |
| **Repair** | `storage` event + `BroadcastChannel("aria-settings-sync")` for theme/accent |
| **Regression** | Code review + cache-bust `theme.js?v=1.1.1-onetruth` |
| **Final verification** | Settings↔Disk API **PASS**; multi-tab sync wired (browser peer channel) |

### 4. Search diagnostics disagreed with runtime corpora (probe FAIL)

| | |
|---|---|
| **Subsystem A** | Search FACETS / diagnostics UI |
| **Subsystem B** | Live `enabled_corpora_set` + RETRIEVERS |
| **Expected truth** | Diagnostics lists every default corpus including `chat` |
| **Observed** | Chat searchable but absent from FACETS matrix → probe thought corpora missing |
| **Root cause** | New retriever not registered in `terminology.FACETS` |
| **Repair** | Add `chat` to FACETS + diagnostics owner map |
| **Final verification** | `/api/search/product/facets` includes chat+gallery enabled → **PASS** |

---

## Probe matrix (one-truth run)

| Relationship | Result |
|---|---|
| Image ↔ FS / Gallery / Chat | PASS |
| Gallery ↔ Search / Chat ↔ Search | PASS |
| Delete ↔ Gallery / Chat / Search / Jobs | PASS |
| Restore ↔ FS / Gallery / Chat / Jobs / Search / Activity | PASS |
| Planner ↔ Calendar / Search | PASS |
| Journal ↔ Calendar / Search | PASS |
| Projects ↔ Create / Search / Archive | PASS |
| Settings ↔ Disk | PASS |

---

## Residual debt (not claimed PASS)

1. **Notifications dismiss** — still client `localStorage` only; no server dismiss API → multi-device dismiss can disagree.  
2. **Activity dual path** — server gallery outbox + client producers can duplicate “image ready” style events.  
3. **Long multi-hour interleaved session** — not soak-tested in this pass (restart + full mutate cycle covered).  
4. **Lightbox open from pre-restore DOM without reload** — Chat messages repaired on server; open tab must reload branch to see restored embed.  
5. **Home Assistant corpus** — remains opt-in (intentional privacy).

---

## Code touchpoints

- `jarvis/gallery_product/consistency.py` — restore chat embeds  
- `jarvis/gallery_product/soft_delete.py` — restore hooks + activity  
- `jarvis/media_jobs.py` — `clear_asset_missing`  
- `jarvis/search_product/settings.py` — gallery+chat default-on  
- `jarvis/search_product/retrievers.py` — `retrieve_chat`  
- `jarvis/search_product/terminology.py` / `diagnostics.py` — FACETS  
- `jarvis/gui/static/theme.js` — cross-tab sync  
- `tests/test_onetruth_restore_search.py`

---

## Certification statement

For the relationships exercised above, Aria now maintains **one shared reality** across Gallery, Chat, Jobs, Search, Calendar, Planner, Journal, Projects, Settings disk, and Gallery activity on restore. Any future change that updates one representation without the others is a **FAIL** under this standard.
