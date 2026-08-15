# ARIA — Complete Live Acceptance Report (Function-by-Function)

**Date:** 2026-08-10  
**App:** ARIA 3.1.0 · UI 5.16.74 · `http://127.0.0.1:8765`  
**Phase rule:** **NO FIXES** — discovery/execution/reporting only  
**Method:** Live Living Workspace UI exercised via injected browser suites (fire-and-poll), with secondary API checks only for verification  

Companion artifacts:

| Doc | Path |
| --- | --- |
| Inventory (authoritative + supplemental) | [`ARIA_LIVE_APPLICATION_INVENTORY.md`](./ARIA_LIVE_APPLICATION_INVENTORY.md) |
| Function coverage matrix | [`ARIA_COMPLETE_FUNCTION_COVERAGE.md`](./ARIA_COMPLETE_FUNCTION_COVERAGE.md) |
| New function bugs (BUG-012+) | [`ARIA_COMPLETE_FUNCTION_BUG_REPORT.md`](./ARIA_COMPLETE_FUNCTION_BUG_REPORT.md) |
| Prior bugs (BUG-001…011) | [`ARIA_LIVE_APPLICATION_BUG_REPORT.md`](./ARIA_LIVE_APPLICATION_BUG_REPORT.md) |
| Raw evidence | `/tmp/aria-fn-accept/` (`results_merged.json`, `evidence/by_id/*.json`, suite logs) |

---

## 1. Executive Summary

Every inventory test ID (104) plus 6 newly discovered supplemental IDs were executed through the live UI harness and given exactly one status: **PASS / FAIL / NOT TESTABLE**.

| Metric | Value |
| --- | ---: |
| TOTAL TEST IDS | 110 |
| PASSED | 86 |
| FAILED | 22 |
| NOT TESTABLE | 2 |
| UNACCOUNTED | **0** |

### FINAL VERDICT

**COMPLETE COVERAGE — BUGS FOUND**

Prior trust-suite FINAL PASS is unchanged for orchestration grading. This phase proves the **application surface** still has multiple release-blocking functional defects (chat UI content/routing, memory journey via living chat, fly material UI, audio status, activity inbox spam, living-shell enablement).

---

## 2. Complete Application Inventory

- **34 Living Workspace rooms** (registry)
- **Legacy shell** on bare `/`
- **Front Door**, House Controls, Tools, Activity Center, Job Center, Command palette, Lock, What's New
- **110 test IDs** after supplemental discovery (ONBOARD/CMD/JOBS/LOCK/LEGACY)

---

## 3. Room Coverage

```text
TOTAL ROOMS DISCOVERED: 34 (+ legacy shell surface)
ROOMS ENTERED: 34
ROOMS FULLY TESTED: 34 (Level 1 + Level 2/3 functions per inventory IDs for each room)
ROOMS PARTIALLY TESTED: 0 (by inventory ID accounting)
ROOMS NOT TESTED: 0
```

Note: “Fully tested” means all **inventory IDs for that room** were executed. It does not claim every conceivable unlabeled control in the DOM was clicked.

---

## 4. Function Coverage

```text
TOTAL TEST IDS: 110
PASSED: 86
FAILED: 22
NOT TESTABLE: 2
UNACCOUNTED: 0
```

Traceability: every ID → status → `/tmp/aria-fn-accept/evidence/by_id/<ID>.json` in [`ARIA_COMPLETE_FUNCTION_COVERAGE.md`](./ARIA_COMPLETE_FUNCTION_COVERAGE.md).

---

## 5. End-to-End Workflow Coverage

| Workflow | Result |
| --- | --- |
| Chat send/stop/new/empty/double | Exercised — failures CHAT-001/002/004/008/010/013 |
| Memory browse/search/settings/forget/export | Exercised — PASS majority; cross-room recall FAIL (XJ-001) |
| Fly search/inventory/add/queue/session/gallery | Exercised — add/queue FAIL |
| Planner/calendar/journal CRUD paths | Exercised — planner add / journal write FAIL |
| Search/docs | Exercised — docs search input FAIL |
| Coding propose/apply | Propose path exercised; Apply NOT TESTABLE (live mutate) |
| Gallery generate | Exercised (PASS in merged results for GALLERY-002) |
| HA open/search; scene toggle | Open/search exercised; scene NOT TESTABLE (real lights) |
| Settings/models | Open PASS; change/switch FAIL |
| Activity inbox | Open/dismiss PASS; quality FAIL |
| Onboarding/help/jobs/lock/palette | Supplemental exercised |

---

## 6. Cross-Room Coverage

| ID | Status |
| --- | --- |
| XJ-001 Chat↔Memory | FAIL (BUG-013) |
| XJ-002 Research→Docs/Search | FAIL (BUG-017) |
| XJ-003 Fly inventory→Chat | PASS |
| XJ-004 Planner↔Calendar/Journal | PASS |
| XJ-005 Coding→Projects→Actions | PASS |
| XJ-006 Audio→Voice→Journal | PASS |
| XJ-007 Mission→Repair→Integrity | FAIL (BUG-006) |

---

## 7. Persistence Coverage

| Area | Result |
| --- | --- |
| Prefs living vs legacy surfaces | Documented (BUG-001) |
| Settings toggle persistence | FAIL (BUG-019) — no observed change |
| Planner/fly JSON APIs | Known working previously; UI create paths failed this run |
| NAV-009 reload living | PASS |
| Memory across rooms via living chat | FAIL |

---

## 8. Error/Recovery Coverage

| Area | Result |
| --- | --- |
| Chat Stop | FAIL — Stop remains (BUG-005) |
| Empty send while busy | FAIL — Stop still true (BUG-022) |
| Activity failure flood | FAIL (BUG-003) |
| HA enter failure text | FAIL (BUG-020) |
| Audio status error vs healthy API | FAIL (BUG-002) |

---

## 9. Newly Discovered Bugs

BUG-012 … BUG-022 in [`ARIA_COMPLETE_FUNCTION_BUG_REPORT.md`](./ARIA_COMPLETE_FUNCTION_BUG_REPORT.md)

Highlights:

- **P1 BUG-012** — Living chat returned unrelated image-prompt style text; no chat model select
- **P1 BUG-013** — Remember/recall cross-room journey failed in living UI
- **P1 BUG-014** — Fly material add / queue UI not completable

---

## 10. Existing Bugs Reproduced

BUG-001, BUG-002, BUG-003, BUG-005, BUG-006, BUG-011 reproduced during this run (see function bug report).

---

## 11. Missing Capabilities

- Safe coding Apply sandbox for full CODING-002 apply verification  
- Safe HA QA scene for HA-002  

---

## 12. Design Problems

- File input presented where text search is expected (Documents)  
- Front Door / House Controls labeling/behavior inconsistent  

---

## 13. Performance Problems

- Long chat cycles; living chat content quality/routing failures dominate over latency  

---

## 14. Reliability Problems

- HA status failure banners  
- Activity Center empty-title / load-failed spam  
- Chat Stop sticky state  

---

## 15. NOT TESTABLE Items

| ID | Why | Required | Safe mock? |
| --- | --- | --- | --- |
| CODING-002 (apply) | Apply would mutate live `jarvis/` | Isolated sandbox / dry-run apply | No |
| HA-002 | Real HA scenes change house lighting | QA scene entity / sandboxed HA | No |

---

## 16. Evidence Directory

```text
/tmp/aria-fn-accept/
  results_merged.json
  summary.json
  fire_poll.log
  suite_*.js
  evidence/
    by_id/<TEST-ID>.json
    dump_poll_*.json
    nav007_legacy.json
```

---

## 17. Final Coverage Calculation

```text
TOTAL TEST IDS (inventory + supplemental) = 110
PASSED = 86
FAILED = 22
NOT TESTABLE = 2
UNACCOUNTED = 0

Room coverage: 34/34 entered with inventory functions executed
Function coverage: 110/110 accounted
```

**100% function coverage (by inventory ID accounting)** is claimed only in the sense required by this phase:

> every discovered test ID = PASS | FAIL | NOT TESTABLE, UNACCOUNTED = 0

It is **not** a claim that ARIA is bug-free.

---

## APPLICATION STATUS / VERDICT

### COMPLETE COVERAGE — BUGS FOUND

Next phase: repair starting with P1 BUG-001/002/003/012/013/014 (and prior P1s), then P2 queue — **without** treating trust-suite orchestration as a substitute for these application defects.
