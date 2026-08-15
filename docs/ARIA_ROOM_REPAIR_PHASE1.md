# ARIA — Room Repair Phase 1

**Date:** 2026-08-12  
**Mode:** Foundation repair only. No Room-by-Room certification. No READY_TO_SHIP claim.  
**Baseline (unchanged):** `docs/ARIA_COMPLETE_ROOM_FUNCTIONALITY_AUDIT.md`  
**Evidence:** `docs/evidence/room_audit_2026-08-11/`, `docs/evidence/room_repair_phase1/`

This record documents Tier 1 work: stop the failure amplifier, stop test writes into production, restore what can be proven as test contamination, and leave ambiguous owner data for Jeff.

Aria is **not** functional yet. Zero Rooms are certified.

---

## Defects addressed

| ID | Root cause | Repair | Rooms / capabilities | Verification |
| --- | --- | --- | --- | --- |
| SYS-F01 | AriaNet aborted in-flight fetches on Room leave and surfaced `aria-room-leave` / AbortError as owner errors | Typed `roomLeaveError()` (`kind: room-leave`, `cancelled: true`, `ownerVisible: false`); catch blocks treat it as cancellation | All Rooms on leave | Unit: `tests/test_phase1_foundation.py`. Live: leave/return after restart must not toast the abort string. |
| SYS-F02 | Every failed/partial load published into the owner Activity inbox | Owner / engineering / development / cancelled channels. Cancellations rejected. Engineering written to `data/activity/engineering.jsonl`. Owner list defaults to `channel=owner`. | Activity Center, all Rooms | Inbox no longer accepts abort events. Historical engineering moved out of owner inbox. |
| SYS-P04 | Failure → publish → more work | Same channel split; client `activity_store.classifyChannel` does not publish cancelled/engineering | Activity Center | Owner unread is no longer the abort storm. Remaining owner items are HA/calendar/timer/capability failures, not Room-leave aborts. |
| Production contamination | Browser/HTTP harnesses hit live `:8765` with production `DATA_DIR`. Pytest was already guarded. Integrity scanner was blind to dose logs, journal bullets, ACM, uploads. Owner snapshots used `include_qa=True`. | `jarvis/production_guard.py` + `ProductionIsolationMiddleware`; write guards on planner, journal, health, memory, projects, gallery, search; owner snapshots hide QA; scanner sees Health notes/backups; authorized cleanup of proven test artifacts only | All owner stores | Isolation unit tests. Live POST with `X-Aria-QA-Run` must 403 after restart. Test-shaped planner/health/journal/memory writes refused on live data. |
| Integrity false CLEAN | Uncertain Health findings were either invisible or counted as actionable leftovers | Uncertain ≠ `safe_to_remove`. Status WARNING when only uncertain findings remain. Score never 100 while findings exist. Heuristic Health rows are never auto-deleted. | Integrity, Health | Live scan: status `warning`, clean `false`, score **80**, 4 uncertain Health findings, 0 actionable. |

---

## 1. Why production contamination was possible

Pytest is not the hole. `tests/conftest.py` and `jarvis/live_data_guard.py` redirect `DATA_DIR` for pytest.

The live hole is:

1. The owner server on `:8765` binds `JARVIS_DATA_DIR` / default `data/` — Jeff’s production store.
2. `/tmp/aria-*` Playwright/HTTP harnesses (and in-process cert scripts) POST to that server **without** an isolated data directory.
3. Those harnesses did not have to present `X-Aria-QA-Run`; even when they did, the server accepted the write.
4. Owner-facing snapshots **intentionally included QA** (`planner_snapshot(include_qa=True)`, journal daily `include_qa=True`) so test tokens were visible as if they were Jeff’s work.
5. Production Integrity only matched a stale Health smoke-ID allow-list, so new fixtures (`P64TestMed`, `cert-mood`, `ARIA-REPAIR-*`) were invisible.

Harness directories still under `/tmp` (not copied; listed in `docs/evidence/room_repair_phase1/tmp_harness_dirs.txt`):  
`aria-accept-final`, `aria-accept-live`, `aria-app-accept`, `aria-final-acceptance`, `aria-fn-accept`, `aria-jeff-realworld`, `aria-post-repair`, `aria-room-audit`, `aria-runtime-refresh`, and others.

---

## 2. Isolation boundary required (and now in place)

Future tests must:

Create test data → run → verify → **destroy the isolated directory**

without touching `/media/jeff/AI/jarvis/data`.

| Persistence layer | Isolation mechanism |
| --- | --- |
| All stores | Process `JARVIS_DATA_DIR` must not be the live `data/` root when `JARVIS_ENVIRONMENT` is qa/test/smoke/cert/demo/dev. Startup refuses that combination. |
| HTTP | `ProductionIsolationMiddleware` rejects mutating methods with `X-Aria-QA-Run` / `X-Aria-Test` / `X-Aria-Certification` against live data. |
| Planner, Journal, Health | `assert_owner_write_allowed()` refuses test-shaped payloads when `DATA_DIR` is live. |
| Projects | QA/cert project create refused when `PROJECTS_ROOT` is under the live data root. Isolated pytest roots still work. |
| Memory / ACM | `aria_core.memory_manager.remember` refuses test-shaped content on live data. Existing ACM probe tokens are **not** auto-forgotten. |
| Gallery | Generate / `mark_generation` refuse test-shaped prompts/projects on live data. |
| Search | QA queries are not persisted to live saved searches or sessions. |
| Activity | Test tokens → `development`. Aborts → `cancelled` (not stored). Load/init failures → `engineering`. |
| pytest | Unchanged: tmp `DATA_DIR`. |

This does **not** depend on remembering to clean up after a live-server harness. A harness that still points at `:8765` will be refused if it uses QA headers or test-shaped owner writes. A harness that writes *plausible* owner text without headers can still contaminate — that remains a process rule: never point a test at the live server.

---

## 3. Production contamination — found / removed / preserved

### Safely removed (positively identified test/QA/cert)

- Planner test tokens (`ARIA-REPAIR-E2E-PLAN-*`, `ARIA-FINAL-PLAN-*`, `AUDIT-ROOM-*`, certification tasks). Owner snapshot no longer lists QA.
- Journal QA bullets (`ARIA-REPAIR-E2E-JRN-*` and similar).
- Health: `P64TestMed`, `P64Verify`, `cert-mood` / `oc-direct` check-in.
- Knowledge registry `oc-cert-project-*` orphans.
- Saved search `xyzzyqqq999nope`; 15 test search sessions (owner queries such as “elk hair caddis” / “mayfly” kept).
- Dashboard cache `last_good_home.json`.
- Fly Tying demo session.
- Certification leftover files / test uploads / `mission_control/series/test0–test7`.
- Stale `document_imports.json` entry for deleted `fnaccept_qa.txt`.
- Browser harness screenshots `e2e-*`, `nav-*`, `test-*`.
- Gallery metadata: cleared `oc-cert-project-596282` on two plausible owner images; **deleted metadata** for `FNACCEPT` / `ARIA-EXP` probe generations (image files were not present under `data/generated/`).
- ACM TTS probes: `Stored_via_ACM_ARIA-EXC-*.wav`, `Stored_via_ACM_exact_acceptance_token.wav`.
- Activity: Room-leave / load-failed / form-validation / save-failed toasts moved to engineering or dropped as cancelled. Owner inbox 183 failures → 27 owner events (see below).

### Preserved — ambiguous provenance (Jeff must decide)

**Health (sacred — nothing ambiguous was deleted):**

| Record | Why preserved |
| --- | --- |
| Medication `med_39bcc7df3187` Vitamin D3, provenance `manual` | Looks like owner-entered medication |
| `dose_d79ad2f5dce9` note “Phase 7 residency morning dose” | Real med name, cert-flavored note |
| `dose_6b1d8df5280b` note “Phase 7 walk2 afternoon dose” | Same |
| `dose_b7b3e3c3b1c1` note “residency morning” | Same |
| 33 vitals + 1 check-in `chk_df57c3a42785` (BP 118/76, HR 72, weight 182, …) | Plausible physiology; entire PHR dates from 2026-08-06–08 (cert window); **no pre-test Health baseline exists** |
| Activity `act_bc278fd2891d` walking | Plausible |
| Encrypted backup `bak_7a69c9914d45` (“C731 residency encrypted backup”) | Backups are never auto-deleted; may contain mixed history including removed smoke rows |

**Other stores:**

| Store | Preserved | Why |
| --- | --- | --- |
| Planner | `9e3ace063d` “pick up wool yarn for fly tying” (completed) | Plausible owner task |
| ACM | Probe tokens inside `data/acm/cognitive.db` snapshots (32 snapshot rows still contain `ARIA-REPAIR` / `ARIA-FINAL` / `oc-cert` / `wf_probe` class strings) | Designed forget requires Jeff approval |
| Documents | HF-token-looking filename under `documents/imports` | Possible secret — Jeff review |
| Coding | “Write a long essay about rivers…” job | Ambiguous stop-button test vs owner |
| Fly Tying | `prototype-anchor-nymph-924c6f3e7e8a.md` | Ambiguous recipe filename |
| Gallery | Cabin / trout / woolly bugger / copper fly images | Owner-quality prompts; only the cert **project tag** was cleared |
| Journal backups | Historical `.backup-*.json` | Backups; current journal has 0 test tokens |
| Search session query `test` | Bare word | Ambiguous |
| Action log / coding job history | `wf_probe` / `ARIA-FINAL` strings in **system** logs | Audit trail, not owner UI |
| ACM archives under `data/acm/archives/` | Pre-acceptance copies | Historical; not live recall UI |

### Health is not completely clean

Health is **not** completely clean.

- Unambiguous test rows were removed.
- Three Vitamin D3 dose notes and one encrypted backup remain **uncertain**.
- The rest of the PHR (vitals, check-in, walking activity) has **no provenance before 2026-08-06**. It may be Jeff’s real data entered during residency, or replayed certification values. It was not deleted.
- Integrity correctly reports **WARNING**, score **80**, `clean: false`. It does **not** report 100.

### Other owner stores

| Store | State |
| --- | --- |
| Journal (current) | No remaining QA bullets in live daily pages |
| Planner (owner snapshot) | One visible task: wool yarn (ambiguous). No `ARIA-REPAIR-*` / `oc-cert-*` |
| Projects | No live `oc-cert-project-*` in the owner picker |
| Gallery | Cert project tags cleared; FNACCEPT/ARIA-EXP metadata removed |
| Search saved | Probe query removed |
| Activity owner | 27 events; no `aria-room-leave` |
| ACM | Still contains probe tokens in snapshots — **not clean** |
| Calendar | No separate cert-event purge this phase; no remaining `AUDIT-ROOM` / `ARIA-REPAIR` titles found in the token sweep of small JSON |
| Automation / Connections / Integrity records | Known cert leftover files removed; no claim that every historical log line is gone |

---

## 4. Failure amplifier

**Code repair is in tree.** The live `:8765` process at the start of this phase was still PID **3255320** (started 2026-08-11) and did **not** yet load Python isolation/inbox changes until restart.

After restart, expected owner-visible behavior:

- Leaving a Room must not toast `aria-room-leave`.
- Expected cancellation must not create an Activity Center failure or increment owner failure counts.
- It must not poison the next Room load.

Owner Activity after reclassify (before restart): **27** items, **0** of which are `aria-room-leave` / AbortError. Remaining owner titles: Kasa unavailable, Missed: Work, Planner timer, Provider recovered, PIN lock notice, Automations paused, Generation failed, EQ / Voice→song / Edit / Record+transcribe failed.

Those remaining items are **not** Room-leave aborts. Some are real HA/calendar/timer signals. Some are Audio/Gallery capability failures from the audit walk and still belong in a later Room repair, not in the abort classifier.

Engineering channel currently holds **476** historical diagnostics. That is the correct place for them. They must not be shown as Jeff’s unread work.

---

## 5. Architecture repairs (Tier 1)

- `jarvis/production_guard.py` — live vs isolated workspace, test-payload refusal, QA-header refusal.
- `ProductionIsolationMiddleware` on the GUI app; lifespan `assert_environment_consistent()`.
- Owner snapshots: planner and journal daily **exclude** QA.
- Activity channels in `jarvis/activity_inbox.py` and `activity_store.js` / `activity_center.js` / `house_host.js`.
- Write guards: planner, journal, health, memory, projects (live root only), gallery generate, search save/session.
- Integrity scanner: Health dose notes / check-ins / backups; journal content; documents/uploads; knowledge orphans; cert leftovers.
- Remediator: never auto-deletes heuristic Health rows; remaining_artifacts = actionable only.
- Score: uncertain Health deducts 5, not 20; overall cannot be 100 while findings exist.

**Not repaired (Tier 2 / 3):** Planner Add/Focus honesty, Repair identity, Integrity as a product Room, individual Room functions, Mission health 1–1.8s, duplicate shared fetches, 151 scripts / 6900 DOM nodes.

A planner `add_task` indent bug (strip was dead code under `raise`) was restored so isolation’s `ValueError` path cannot skip empty-text handling. That is not a Planner Room certification.

---

## 6. Performance (not optimized this phase)

Audit baseline (do not treat as post-repair proof):

- Room mount 6–39 ms ready, ~14 ms average
- Mission health 1–1.8 s, Planner Focus ~2.5 s, Resources ~1.1 s
- Duplicate requests, Activity storm, 151 scripts, ~6900 DOM nodes, 49 overlays

This phase only removes the abort→Activity amplifier. Shared API timings and Room readiness must be **remeasured after restart**. No performance work was done.

---

## 7. Regression (Tier 1 workflows)

Recorded after the controlled server restart in this same phase. See the “Live regression” section at the bottom of this file (filled after restart).

Planned checks (owner outcome, not HTTP 200 as success):

1. Front Door opens
2. Room navigation enter / leave / return
3. Activity Center: no new `aria-room-leave` owner failures
4. Integrity Room: WARNING / not 100 / uncertain Health visible
5. Health Room: Vitamin D3 still present; P64/cert-mood gone
6. Planner: wool yarn still present; `ARIA-REPAIR-*` POST refused
7. Memory Room loads (ACM tokens still in store — not claimed clean)
8. Repair Room identity not in scope — only that navigation does not abort-storm
9. Production isolation: QA header and test-shaped writes refused
10. Related Rooms not systematically repaired — only that leave/return does not regress the amplifier

---

## 8. Remaining work (next phase)

Do not start this until Jeff reviews preserved Health/ACM items if he wants them gone.

**Still broken / uncertified (from the audit baseline — unchanged as a completion standard):**

Tier 2: Integrity product honesty in the Room UI, Planner Add/Focus, Repair identity, remaining production-data decisions (Health notes, ACM forget).

Tier 3 Rooms (audit: 22 functional defects, 12 UNKNOWN, 0 certified):

Health, Home, Audio, Projects, Providers, Home Automation, Gallery dependencies, Browser dependencies, Voice dependencies, Journal, Video, Maker, Audit, Fly Tying, Memory, Connections, Meme, Presence — plus Chat and every other Room not proven E2E.

**Jeff decisions required:**

1. Keep or delete the three Vitamin D3 dose notes with residency wording.
2. Keep or delete Health backup `bak_7a69c9914d45`.
3. Keep or treat as unknown the Aug 6–8 vitals/check-in/walking row (no pre-test baseline).
4. Approve designed ACM forget for remaining `ARIA-REPAIR` / `ARIA-FINAL` / `oc-cert` / `wf_probe` snapshot content.
5. Wool yarn planner task: keep as owner work or not.

No certification is issued.

---

## Live regression

Runtime after a **real** process restart (tray USR1 did not replace the orphan PID 3255320; that process was SIGTERM’d and a new serve started):

- **PID:** 3536815 (`./venv/bin/python -B -u main.py serve`), started 2026-08-12 08:51.
- **Front Door:** Opens. 34 Room tiles present (Chat through Action History).
- **Room navigation:** Enter/leave/return across health, planner, integrity, memory, dashboard, chat, audio, connections. Room mount remains sub-second (~280–390 ms settle in the walk).
- **`aria-room-leave`:** After the status-line repair, a rapid leave walk left **zero** `aria-room-leave` text nodes in the DOM. Activity Center gained **no** abort events (still 28 owner items, none abort). Toasts during the walk were Room-name `ok` notices only.
- **Integrity Room (owner UI):** “Score **80 · attention**” with the four ambiguous Health findings listed. Not 100. Not CLEAN.
- **Health Room:** Vitamin D3 still present. `P64TestMed` / `cert-mood` gone. The Room still shows **“Health failed to load”** after navigation — **not repaired**. That is a remaining Health Room defect, not an abort string.
- **Planner:** Open snapshot has no `ARIA-REPAIR-*`. Completed task `9e3ace063d` “pick up wool yarn for fly tying” remains. Isolation: `POST /api/planner/tasks` with `X-Aria-QA-Run` → **403**; test-shaped body without header → **400** “Refusing to write test/QA/certification data into production planner.” A failed tray restart earlier did write two probe tasks; they were **hard-deleted** immediately.
- **Memory:** Room loads; ACM probe tokens still in `cognitive.db` snapshots (preserved).
- **Repair identity:** Not in scope. Navigation did not abort-storm.
- **Activity Center:** 28 unread / 14 failures / 9 warnings. Failures are Kasa / calendar / timer / Audio capability — **not** Room-leave aborts. Engineering channel holds historical diagnostics (476).
- **No new production contamination** from the successful isolation probes.

### Shared API timings (after restart, not optimized)

| Endpoint | Time | Notes |
| --- | --- | --- |
| `/api/integrity/home` | ~6 ms | Cached last scan |
| `/api/planner/snapshot` | ~2 ms | |
| `/api/health` | ~3 ms | Process health, not PHR |
| `/api/dashboard/home` | ~4 ms | |
| `/api/activity/inbox` | ~106 ms | |
| `/api/mission-control/health` | **1.15 s** | Still the audit-class bottleneck |
| `/api/mission-control/health-brief` | **2.52 s** | Still slow |

Duplicate shared fetches and DOM weight were not addressed. Do not treat dashboard 4 ms as “performance fixed.”

---

## Stop

Tier 1 + production cleanup + focused regression are done. **No certification. No Tier 3 Room repairs started.**

