# ARIA — Room Repair Phase 2 (Tier 2)

**Date:** 2026-08-12  
**Mode:** Authorized owner-data cleanup + foundation honesty. No Room-by-Room certification. No READY_TO_SHIP claim.  
**Baseline (unchanged):** `docs/ARIA_COMPLETE_ROOM_FUNCTIONALITY_AUDIT.md`  
**Prior phase (unchanged):** `docs/ARIA_ROOM_REPAIR_PHASE1.md`  
**Evidence:** `docs/evidence/room_repair_phase2/`

Aria remains **not** functional. Zero Rooms are certified. Tier 3 Room-by-Room repair was **not** started.

Live serve after Tier 2: PID **3696375** (`main.py serve` on `:8765`).

---

## Scope completed

1. Jeff’s five authorized deletions (executed; not re-asked)
2. Integrity Room tells the truth from actual findings / deductions
3. Planner Add → success path + Daily Focus honesty
4. Repair Room identity distinct from Mission Control
5. Production-isolation regression (guard not weakened)
6. Activity Center channel split preserved
7. Focused regression; **STOP** (no Tier 3)

---

## 1. What was deleted

### 1) Three Vitamin D3 dose notes (medication kept)

| ID | Notes | Result |
| --- | --- | --- |
| `dose_d79ad2f5dce9` | Phase 7 residency morning dose | Deleted |
| `dose_6b1d8df5280b` | Phase 7 walk2 afternoon dose | Deleted |
| `dose_b7b3e3c3b1c1` | residency morning | Deleted |

**Kept:** medication `med_39bcc7df3187` Vitamin D3 (`provenance: manual`).

### 2) Encrypted Health backup

| Item | Result |
| --- | --- |
| Row `bak_7a69c9914d45` (“C731 residency encrypted backup”) | Deleted |
| File `data/health_product/backups/aria-health-20260808-092139.json` | Deleted |
| Backup timeline event `evt_ff518279fead` | Deleted |

No backup rows or backup files remain under `data/health_product/backups/`.

### 3) Aug 6–8 Health vitals / check-in / walking (+ associated events)

| Item | Result |
| --- | --- |
| Check-in `chk_df57c3a42785` | Deleted |
| Activity `act_bc278fd2891d` (walking) | Deleted |
| All 33 vitals dated 2026-08-06–07 (entire PHR vital set) | Deleted |
| Associated `events` for vitals / doses / check-ins / activity / backup / dose restore | Deleted |
| Kept event | `evt_279120bdd995` `medications_upsert` Vitamin D3 |

Remaining Health counts: medications **1**, dose_logs **0**, vitals **0**, checkins **0**, activities **0**, backups **0**, events **1**.

### 4) ACM probe / certification snapshot content

Tokens removed from the live owner store (`data/acm/cognitive.db`):

- `ARIA-REPAIR`
- `ARIA-FINAL`
- `oc-cert`
- `wf_probe`

| Metric | Before | After |
| --- | --- | --- |
| Experiences | 878 | 834 (−44 probe) |
| Concepts | 271 | 234 (−37 probe) |
| Associations | 2143 | 2009 (−4 token + 130 dangling cleaned) |
| Snapshot rows with tokens | 32 / 32 | **0** |
| Latest snapshot token hits | 85 | **0** |

Old contaminated snapshots were pruned after writing `kind=tier2_probe_cleanup`. Archives under `data/acm/archives/` were **not** rewritten (historical copies; owner-facing recall uses `cognitive.db`).

Legitimate memories remain (e.g. Jeff / Charlestown / fly tying profile content still present in `/api/memory/all`).

### 5) Planner wool yarn task

| ID | Text | Result |
| --- | --- | --- |
| `9e3ace063d` | pick up wool yarn for fly tying (completed) | Hard-deleted |
| Soft-deleted duplicates `64165768f9`, `a449d226ee`, `43e4d3f799`, `44fdbbaab8` | same text | Hard-deleted |

Owner snapshot / Daily Focus: **0** wool yarn rows.

Deletion log: `docs/evidence/room_repair_phase2/deletion_log.json`  
Pre-delete DB copies: `docs/evidence/room_repair_phase2/pre_delete/`

---

## 2. Confirmation each deletion is gone

| Authorized item | Store | API / UI | Notes |
| --- | --- | --- | --- |
| Three dose notes | SQLite 0 dose_logs | `/api/health/home`, medications, timeline, vitals — no residency/dose IDs | Medication remains |
| Backup `bak_7a69c9914d45` | 0 backup rows; backup dir empty | `/api/health/backups` empty | No broken refs |
| Aug 6–8 vitals/check-in/walking | 0 rows | home / vitals / checkins / activities / timeline clean of those IDs | Not a broad Health purge beyond that set |
| ACM probes | 0 token snapshots | `/api/memory/home`, `/api/memory/all`, `/api/memory/all?q=…`, conflicts — no tokens; Memory Room text has no tokens | Underlying store cleaned, not UI-hidden |
| Wool yarn | 0 rows | snapshot + focus + UI | Hard delete |

Verification tasks used during owner UI proof (`Tier2 planner honesty…`, `buy coffee filters`) were **hard-deleted** after restart proof so they do not remain as production contamination.

---

## 3. Integrity result

| Field | Tier 1 end | Tier 2 end |
| --- | --- | --- |
| status | warning | **clean** |
| clean | false | **true** |
| score | 80 | **100** |
| findings | 4 uncertain Health | **0** |
| deductions | 4 (−5 each) | **[]** |

Score **100** is derived from **zero findings** after the authorized deletions — not a cosmetic override.

Integrity Room repairs:

- Cache no longer paints “No deductions on record.” while findings exist
- Cache stores `items` from deductions **or** `last_scan.findings`
- `/api/integrity/home` exposes top-level `findings`
- Owner UI after wait: **Score 100 · ready** + **No deductions on record.** (accurate)

---

## 4. Planner result

### Add / Focus honesty

**Root causes addressed:**

1. Add used `ariaMutate` without verifying the task in a snapshot, and did not refresh Daily Focus after success.
2. Failed/aborted HTTP paths could toast failure even when the store already had the task, or leave Focus stale.

**Repair:** Add uses `p0Fetch` POST, then reads `/api/planner` and only toasts **Task added** / clears the input when the created id or exact text is present in the snapshot; then `loadPlanner()` + `refreshFocus()`. Empty text still toasts **Task text required** (verified). Failed Add (empty / isolation refusal) does not clear the input as success.

**Owner UI proof:**

- Enter `buy coffee filters` → Add → toast **Task added** → input cleared → task in list → Daily Focus **1 tasks** and Top 3 shows the task
- Leave → return → task + Focus still agree
- Restart → snapshot + Focus still had the task (then hard-deleted as verification cleanup)

### Wool yarn

Gone from snapshot, Focus, and SQLite.

---

## 5. Repair Room identity result

| Check | Result |
| --- | --- |
| Registry `repair.viewId` | `repair` (was `workstation`) |
| Furnish map | no longer maps repair → workstation; native Repair Room used |
| Front Door → Repair | hash `#repair`, `dataset.room=repair`, native `#repairRoom`, place **Restoration bench**, workstation **not** visible |
| Front Door → Mission Control | hash `#workstation`, `dataset.room=mission`, workstation visible with MC toolbar |
| Repair ≠ Mission | Confirmed reverse path |

Guided Repair tool entry now targets the Repair Room (`viewId: repair`), not Mission Control.

---

## 6. Production-isolation result

Against live `:8765` after restart:

| Probe | Result |
| --- | --- |
| `POST /api/planner/tasks` + `X-Aria-QA-Run` | **403** production_isolation |
| Test-shaped body `ARIA-REPAIR-E2E-PLAN-PHASE2` | **400** refuse write into production planner |

Guard **not** weakened. Unit coverage in `tests/test_phase2_tier2.py` + Phase 1 foundation tests: **28 passed**.

---

## 7. Activity Center result

- Owner inbox: **28** unread; titles unchanged family (HA / timer / audio / gallery capability noise) — **no** `aria-room-leave` / AbortError
- Rapid leave/return walk: no owner-visible room-leave abort text
- Channel split retained (`owner` / `engineering` / `cancelled`); Room-leave remains `kind: room-leave`, `ownerVisible: false`

---

## 8. Regressions / measurements

| Area | Note |
| --- | --- |
| Performance | **Not fixed.** Sample after Tier 2: `/api/mission-control/health` ~**1.38 s**, `/api/mission-control/health-brief` ~**1.78 s**, `/api/planner/focus` ~**1.56 s**. See `perf_sample.json`. |
| Health Room load UX | Still out of scope (Tier 3). Cleanup only. |
| ACM archives | Historical archive copies under `data/acm/archives/` may still contain old probe strings; live recall store is clean. |
| Soft-deleted planner QA history | Soft-deleted old QA rows remain in DB as `deleted=1` (Tier 1 already removed owner-visible ones). Not expanded this phase. |

---

## 9. Remaining Tier 3 defects (unchanged inventory posture)

From the authoritative audit, still true:

- **34 Rooms**
- **0 Certified Functional**
- **22** functional-defect Rooms
- **12** UNKNOWN Rooms

Do **not** treat Integrity CLEAN / score 100 as Room certification.

Still queued for later Room repair (non-exhaustive): Health functionality, Audio, Projects, Fly Tying, Gallery, Browser, Voice, Journal, Video, Maker, Home Automation, Mission Control latency, shared init weight, etc.

---

## Code touched (foundation only)

- `jarvis/gui/static/workspace/registry.js` — Repair `viewId`
- `jarvis/gui/static/workspace/rooms/furnish.js` — stop Repair→workstation hijack
- `jarvis/gui/static/view_router.js` — repair/integrity native identity
- `jarvis/gui/static/workspace/tools.js` — Guided Repair → Repair Room
- `jarvis/gui/static/workspace/rooms/priority3_rooms.js` — Integrity truth / cache items
- `jarvis/gui/static/workspace/rooms/house_host.js` — Integrity warm cache includes items
- `jarvis/gui/static/planner.js` — Add verify + Focus refresh
- `jarvis/gui/static/planner_live.js` — open task count honesty
- `jarvis/integrity_product/scanner.py` — home `findings` field
- `jarvis/gui/static/index.html` — cache-bust versions
- `tests/test_phase2_tier2.py` — Tier 2 regression

---

## STOP

Tier 2 complete. **Do not proceed to Tier 3 automatically.**
