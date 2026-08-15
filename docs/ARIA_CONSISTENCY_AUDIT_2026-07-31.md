# Aria Consistency Audit — 2026-07-31

**Purpose:** Prove every representation of the same fact agrees (Chat ↔ Gallery ↔ Jobs ↔ FS ↔ Calendar ↔ Planner ↔ Journal ↔ Settings), including after reload and restart. Toasts/HTTP/`Complete` alone are not evidence.

**Probe artifacts:**
- `data/certification/consistency_probe_2026-07-31.json` (initial: 19 PASS / 4 FAIL)
- `data/certification/consistency_probe_reverify.json` (after repair: 9 PASS / 0 FAIL on focused suite)
- Restart suite: `RESTART_CONSISTENCY_PASS`

---

## Executive verdict

Initial audit found **4 real cross-view disagreements**. Each was root-caused and repaired. Focused create/delete/federation/restart re-verification then passed. Broader product surfaces (Search index opt-in, Settings multi-tab, Projects rename matrix) remain **open debt** — not claimed PASS in this report.

Overall for audited surfaces after repair: **PASS** (with residual debt listed below).

---

## Inconsistencies found → repaired

### 1. Image — Job Center Complete with missing file

| Field | Detail |
|---|---|
| **Feature** | Image / Job Center |
| **Operation** | Historical meme job + soft-delete of generated image |
| **Expected** | Job Center must not show `result_ok` / Complete when the asset file is gone |
| **Observed** | `bc54680ec9b3` Complete → `meme_20260730_174832.png` missing; after delete, job still pointed at deleted path with `result_ok` |
| **Views that disagreed** | Jobs vs filesystem vs Gallery |
| **Root cause** | `_sanitize_job` trusted `result.ok`; soft-delete never updated media job records |
| **Repair** | `jobs_center._sanitize_job` marks `asset_missing` when path absent; `media_jobs.mark_asset_missing`; `gallery_product.consistency.on_gallery_asset_removed` on soft/permanent delete |
| **Regression** | `tests/test_consistency_surfaces.py::test_jobs_center_marks_missing_assets` |
| **Final verification** | Re-probe + restart: no `result_ok` rows with missing files → **PASS** |

### 2. Image delete — Chat still embeds deleted Gallery URL

| Field | Detail |
|---|---|
| **Feature** | Gallery delete ↔ Chat history |
| **Operation** | Soft-delete image after Chat durable `![generated](/api/gallery/…)` |
| **Expected** | Gone everywhere — Chat must not keep a live gallery URL |
| **Observed** | Gallery list empty / trash has file; Chat messages still contained `/api/gallery/{name}` |
| **Views that disagreed** | Chat vs Gallery vs FS |
| **Root cause** | Soft-delete moved file only; never scrubbed branch messages (live or disk) |
| **Repair** | `gallery_product/consistency.scrub_chat_gallery_refs` via live `get_assistant().branches` + persist; hooked from `soft_delete` and permanent DELETE |
| **Regression** | Covered by live consistency re-probe |
| **Final verification** | After delete: Chat shows `*[Image removed from Gallery: …]*`; no `/api/gallery/{name}`; survives restart → **PASS** |

### 3. Journal note missing from Calendar day

| Field | Detail |
|---|---|
| **Feature** | Journal ↔ Calendar |
| **Operation** | `POST /api/journal/daily` with `bullet_type=note` |
| **Expected** | Same day Calendar schedule includes the note |
| **Observed** | Journal readback had note; Calendar `counts.journal` ignored it (`_journal_items` only emitted event/task) |
| **Views that disagreed** | Journal vs Calendar |
| **Root cause** | `calendar_schedule._journal_items` filtered out `note` |
| **Repair** | Federate notes (and other non-event/task bullets) as `kind=note`; Journal `postDaily` + Planner `loadPlanner` call `window.refreshCalendar` so open Calendar DOM updates |
| **Regression** | `tests/test_consistency_surfaces.py::test_journal_notes_federate_to_calendar` |
| **Final verification** | New note appears on `/api/calendar/day`; prior `CONSIS_JOURNAL_*` visible after restart → **PASS** |

### 4. Planner ↔ Calendar data (pre-existing OK) / UI refresh gap

| Field | Detail |
|---|---|
| **Feature** | Planner ↔ Calendar |
| **Operation** | Create task/event via Planner API |
| **Expected** | Calendar day includes items; open Calendar UI refreshes |
| **Observed** | API already agreed (PASS in probe). UI could stay stale until view re-entry |
| **Repair** | Expose `window.refreshCalendar`; call from `loadPlanner` and journal `postDaily` |
| **Final verification** | API federation PASS; UI refresh wired → **PASS** (API proven; UI wiring reviewed) |

---

## Surfaces verified consistent (create path)

| Surface | Checks | Result |
|---|---|---|
| Image create | File, Gallery list, Gallery open, metadata, Chat persist, branch count, Job Center same asset | **PASS** |
| Planner task/event | Snapshot + Calendar day | **PASS** |
| Journal create | Readback | **PASS** (federation fixed) |
| Settings appearance | API + `data/settings_product/appearance.json` | **PASS** |
| Chat clear | Messages empty + branch list | **PASS** |
| Restart | Journal/cal, scrubbed chat, gallery absence, jobs truth, planner/cal | **PASS** |

---

## Residual consistency debt (not PASS)

These were **not** fully exercised end-to-end in this audit; treat as open:

1. **Search** — Chat transcripts not in federated search; Gallery search is live scan (opt-in). Deleted/created items vs Search not proven.
2. **Settings multi-tab / other pages** — appearance disk/API agree; other tabs may hold stale `localStorage` until reload.
3. **Projects** create/rename/delete matrix across Search — not run.
4. **Notifications / Activity feed** after planner ticks — not cross-checked against planner.db.
5. **Lightbox / thumbnail** after soft-delete — Chat scrubbed; open lightbox from old DOM without reload not browser-proven.
6. **Restore from trash** — Chat remains “removed from Gallery” (honest about delete; restore does not rewrite embed back).

---

## Code touchpoints

- `jarvis/gallery_product/consistency.py` (new)
- `jarvis/gallery_product/soft_delete.py`
- `jarvis/gui/extra_routes.py` (permanent delete hook)
- `jarvis/media_jobs.py` (`mark_asset_missing`)
- `jarvis/jobs_center.py` (missing-asset sanitize)
- `jarvis/calendar_schedule.py` (journal notes)
- `jarvis/gui/static/planner.js`, `calendar.js`, `journal.js` (sibling refresh)
- `tests/test_consistency_surfaces.py`

---

## Rule for future audits

A feature is **PASS** only when every related representation agrees **and** reload/restart still agree **and** delete (if applicable) leaves no phantom references. Anything less is FAIL.
