# ARIA Repair Changelog

## 2026-08-24 — BACKGROUND JOB ROUTING (false "server restart" on Deep Research)

```text
DATE: 2026-08-24
PHASE: Frontend job routing only — Deep Research / Learn topic reported as lost
SYMPTOM:
  Chat showed "Lost track of this job after a server restart. Check Gallery for
  your image." ~8s after a Learn topic / Deep Research request.
ROOT CAUSE (forensic, not job persistence):
  The ARIA server never restarted. chat_done.js routed ANY response carrying
  pending=true to pollMediaJob(). _enqueue_background() returns
  type="background_job", pending=true, and background_job had no frontend
  handler, so Learn topic fell through to the media poller and queried
  /api/media/job/<id>. Background jobs live in the coding registry and are only
  readable at /api/coding/job/<id>, so the media endpoint 404s immediately and
  permanently. media_jobs.js then assumed 404 == server restart and said so.
  The research job kept running and completed normally, unseen.
CODE:
  - jarvis/gui/static/chat_done.js — resolveJobKind(); job *type* selects the
    poller (coding_job | background_job | media_job); `pending` demoted to a
    legacy fallback for untyped image/video producers only
  - jarvis/gui/static/coding_jobs.js — one poller now serves coding and
    background kinds over the shared /api/coding/job/<id> endpoint;
    jarvisPollBackgroundJob exported
  - jarvis/gui/static/media_jobs.js — 404 no longer claims a server restart
TESTS:
  - tests/test_chat_job_routing.py (21 checks)
  - tests/js/job_routing_harness.mjs — loads the real static JS under node and
    records fetched endpoints; verified to FAIL against pre-fix code
VERIFY:
  - Live production, real incident job ids:
      /api/coding/job/d59ed9810986 -> 200 (label "Learn topic", result present)
      /api/media/job/d59ed9810986  -> 404 (the old, broken route)
  - Full suite: 3152 tests
  - Production PID 1765 unchanged, systemd NRestarts=0 (no restart performed)
NOT TOUCHED: coding_jobs/background_jobs registries, Deep Research engine, web
  search, LLM routing, systemd config, restart policy, checkpoint/resume
FOLLOW-UP (separate milestone): durable checkpoint/resume for background jobs —
  they persist metadata but carry no resume payload, so a genuinely interrupted
  research job still cannot be resumed.
```

## 2026-08-11 — RELEASE BLOCKERS FIXED (BUG-026 / BUG-025 / GALLERY INFRA)

```text
DATE: 2026-08-11
PHASE: Fix only BUG-026 P0, BUG-025 P1, clear 45 gallery chrome INFRA
CODE:
  - jarvis/orchestration_policy.py — destructive system refusal + marker memory cues
  - jarvis/behaviors/conversation.py — policy_fixed_reply + wipe integrity gate
  - jarvis/nlu/mapping.py — remember vs recall intent (BUG-025 A)
  - jarvis/behaviors/memory/engine.py + memory/retrieval_diagnostics.py — marker ranking
  - aria_core/acm_bridge.py — host_forgotten hide after soft forget
TESTS:
  - tests/test_destructive_system_refusal.py
  - tests/test_memory_intent_routing.py (extended)
VERIFY:
  - Orchestration 14/14 PASS (/tmp/aria-final-closure/orchestration/)
  - Living Workspace memory E2E PASS
  - Gallery 45 isolated: chrome unresolved=0
DOCS:
  - docs/ARIA_BUG_025_026_REPAIR_REPORT.md
  - docs/ARIA_GALLERY_INFRA_FINAL_REPORT.md
  - docs/ARIA_FINAL_ACCEPTANCE_REPORT.md (updated)
NOT TOUCHED: BUG-024, inventory classifications, denominators, research architecture
VERDICT: FINAL PASS
EVIDENCE: /tmp/aria-final-closure/
```

## 2026-08-11 — FINAL ACCEPTANCE CLOSURE (no product code changes)

```text
DATE: 2026-08-11
PHASE: Final acceptance gap closure — classify-first, no app code edits
DOCUMENTS:
  - docs/ARIA_FINAL_ACCEPTANCE_RECONCILIATION.md
  - docs/ARIA_FINAL_INVENTORY_TRIAGE.md
  - docs/ARIA_FULL_EXECUTION_REGRESSION.md
  - docs/ARIA_FINAL_ORCHESTRATION_ACCEPTANCE.md
  - docs/ARIA_FINAL_E2E_ACCEPTANCE.md
  - docs/ARIA_FINAL_ACCEPTANCE_REPORT.md
WHAT RAN:
  - Reconciled states(111 PASS) vs embedded WF failures
  - Classified all 15 inventory FAILs (UNCLASSIFIED=0; 0 product bugs)
  - Full 2188 ledger post-repair (EXECUTED=ALL, UNTESTED=0, UNACCOUNTED=0)
  - Pre/post regression compare (0 non-INFRA/non-024 product regressions)
  - Gallery INFRA retest 75 → 45 still chrome-crash
  - Orchestration memory/refusal/research probes
NEW BUGS (evidence only; not fixed this phase):
  - BUG-026 P0 destructive refusal provides sudo rm -rf /
  - BUG-025 P1 memory recall misroutes to remember / loses unique marker
VERDICT: BLOCKED
EVIDENCE: /tmp/aria-final-acceptance/
```

## 2026-08-11 — POST-REPAIR ACCEPTANCE

```text
DATE: 2026-08-11
PHASE: Clean post-repair acceptance (no further product repairs in this step)
WHAT RAN:
  - Fire-poll inventory suite (110 IDs) → UNTESTED=0 UNACCOUNTED=0
  - Applicable state suite (111) → UNTESTED=0 PASS=111
  - E2E repaired journeys (17) → PASS=17 NOT EXECUTED=0
  - Infra gallery retest → 0 chrome crashes
  - Orchestration/trust probes
  - Historical spot checks for FIXED bugs
REPORT: docs/ARIA_POST_REPAIR_ACCEPTANCE_REPORT.md
EVIDENCE: /tmp/aria-post-repair/accept/
VERDICT: PASS WITH REQUIRED FIXES
NOTES: BUG-024 untouched; inventory still has 15 FAIL (harness/timing/changed surfaces);
  repaired queue journeys re-verified PASS; orchestration memory-recall ranking soft-fail this run.
```

## 2026-08-11 — REPAIR-023 / BUG-023 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-023
BUG: BUG-023
ROOT CAUSE: Health Doctor visit / Emergency / print actions used window.open or <a href> to /api/health/report?kind=…, which could replace the Living Workspace with a raw HTML API response (especially emergency).
FILES CHANGED:
  - jarvis/gui/static/health.js
  - jarvis/gui/static/index.html (health.js cache bust)
WHAT CHANGED: openHealthReport() fetches report HTML and displays it in an in-SPA modal with Print/Close; intercept print buttons and /api/health/report anchors.
WHY: Emergency/doctor reports must stay inside Living Workspace.
TARGETED TEST: PASS — Emergency click → modal+frame content; URL stays on SPA; not ejected
E2E TEST: PASS — mission apiAnchors=0; living stage remains; close works
REGRESSION: PASS — report API still 200 HTML; health info accessible in modal
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug023/
```

## 2026-08-11 — REPAIR-022 / BUG-022 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-022
BUG: BUG-022
ROOT CAUSE: Health document <input type=file> lived only inside the Documents tab body, so the Health room appeared to have no upload control. Empty-send busy was largely a sticky-Stop/label false positive (BUG-005 family) when the wrong button was probed.
FILES CHANGED:
  - jarvis/gui/static/index.html
  - jarvis/gui/static/health.js
WHAT CHANGED: Persistent Health header Upload + #healthUploadInput; upload posts to /api/health/documents and opens Documents tab. Verified empty #sendBtn does not show Stop.
WHY: Health upload must be discoverable; empty send must be a no-op.
TARGETED TEST: PASS — hasHealthFile=true; emptySendBusy=false; helpOpened=true
E2E TEST: PASS — Health enter shows upload; chat empty send idle
REGRESSION: PASS — healthy Connected HA / health disclaimer still visible
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug022/
```

## 2026-08-11 — REPAIR-020 / BUG-020 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-020
BUG: BUG-020
ROOT CAUSE: Home Automation enter raced AriaNet room-leave aborts. ha_extras/smarthome loaders painted "Could not load entities: error" / "Could not load presets" while HA was Connected and APIs returned 200 when settled.
FILES CHANGED:
  - jarvis/gui/static/ha_extras.js
  - jarvis/gui/static/smarthome.js
  - jarvis/gui/static/index.html (cache busts)
WHAT CHANGED: isRoomAbort + absorbAbort retry for entity/preset/Kasa loads; stop hard-failure UI on navigation abort; Kasa optional unavailability is quiet status (not toast spam).
WHY: Enter Home Automation must not show false load failures when Connected.
TARGETED TEST: PASS — triage /failed|Could not load/ false; entities list populated
E2E TEST: PASS — chat→HA thrash settle with Connected and no Could not load
REGRESSION: PASS — /api/homeassistant/entities and /api/scenes/presets 200
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug020/
```

## 2026-08-11 — REPAIR-010 / BUG-010 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-010
BUG: BUG-010
ROOT CAUSE: specialists/routes.py used from __future__ import annotations with Request imported only inside register_specialist_routes, so OpenAPI schema generation hit unresolved ForwardRef('Request') → HTTP 500.
FILES CHANGED:
  - jarvis/specialists/routes.py
WHAT CHANGED: Import Request/JSONResponse at module top; drop future annotations in this routes module.
WHY: /openapi.json must return a valid schema without exposing internals.
TARGETED TEST: PASS — GET /openapi.json → 200, openapi 3.1.0, 1217 paths
E2E TEST: PASS — /api/health ready; SPA still served
REGRESSION: PASS — schema JSON parses
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug010/
```

## 2026-08-11 — REPAIR-004 / BUG-004 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-004
BUG: BUG-004
ROOT CAUSE: Rapid Room navigation aborts in-flight fetches; Chromium often surfaces those as Failed to fetch / empty-message Errors (not AbortError). Loaders toasted "X load failed" and activity_center durable-inboxed them, inflating unread failures while home APIs were healthy.
FILES CHANGED:
  - jarvis/gui/static/workspace/rooms/house_host.js
  - jarvis/gui/static/activity_center.js
  - jarvis/gui/static/index.html (cache busts)
WHAT CHANGED: AriaNet.isRoomAbort absorb-window for empty/Failed to fetch/load-failed shapes; toast hook swallows load-failed/checklist/work-schedule thrash toasts (no inbox) within 2.5s of abortRoomTraffic; real failures outside the window still inbox.
WHY: Rapid nav must not create false Activity "load failed" debt.
TARGETED TEST: PASS — aggressive + triage rapid nav → newFailCount 0
E2E TEST: PASS — original BUG-004 room loop afterFails not increased
REGRESSION: PASS — synthetic "Synthetic real load failed" still reaches inbox when lastAbortAt=0
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug004/
```

## 2026-08-11 — REPAIR-019 / BUG-019 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-019
BUG: BUG-019
ROOT CAUSE: Appearance controls wrote AriaUiPrefs only after await appearance API; category-filter loadHome→renderAppearance could race and overwrite select values. bind() used one-shot per-element listeners that could miss controls. Result: theme/density looked unchanged (changed=false / theme stayed dark).
FILES CHANGED:
  - jarvis/gui/static/settings_home.js
  - jarvis/gui/static/index.html (settings_home.js cache bust 1.0.3)
WHAT CHANGED: Local-first theme/density apply; delegated change handling on settingsHomeRoot; renderAppearance prefers AriaUiPrefs over stale API payload.
WHY: Settings change → leave → return → reload must keep safe appearance prefs.
TARGETED TEST: PASS — theme+density survive category race, chat/settings nav
E2E TEST: PASS — hard reload keeps prefs+selects; original triage changed=true midTheme flips
REGRESSION: PASS — restored dark/comfortable after probes
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug019/
```

## 2026-08-11 — REPAIR-018 / BUG-018 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-018
BUG: BUG-018
ROOT CAUSE: Models room Overview had no model <select>; triage tab loop ended on Overview → selectCount=0. Conversation role changes did not update /api/chat/model until Save(+confirm). Policy silently downgraded/fallback-swapped explicit UI/session models (VRAM/latency/unavailable/cloud) so Chat could run a different model than selected.
FILES CHANGED:
  - jarvis/gui/static/models_home.js
  - jarvis/gui/static/index.html (models_home.js cache bust 1.0.1)
  - jarvis/model_policy.py
  - jarvis/capability_routing.py
WHAT CHANGED: Default tab=roles; Overview Chat model select; conversation select change → POST /api/chat/model; Save also applies session; gate VRAM/latency/cloud/unavailable silent swaps when explicit override; pass session override through apply_gateway_model.
WHY: Providers/Models → select → Chat must use the chosen model.
TARGETED TEST: PASS — triage selectCount>0 on Overview; conversation change updates chat_model
E2E TEST: PASS — qwen2.5:7b and dolphin-mistral:latest each used=requested on /api/chat
REGRESSION: PASS — explicit deepseek-r1:14b kept under latency=fast policy
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug018/
```

## 2026-08-11 — REPAIR-016 / BUG-016 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-016
BUG: BUG-016
ROOT CAUSE: (1) Journal primary capture was not first: first textarea was morning reflection and /save|add|create|log/ matched Voice log before rapid-log Add, so triage "add" never persisted. (2) /api/journal/daily used daily_get() which stripped timestamped disposable labels (ARIA-*-{epoch}) via looks_like_dev_label, so a correct rapid-log save disappeared on refresh/leave→return (same class as BUG-015).
FILES CHANGED:
  - jarvis/modules/journal.py
  - jarvis/gui/extra_routes.py
  - jarvis/gui/static/index.html
  - jarvis/gui/static/journal.js
WHAT CHANGED: daily_get(include_qa=…) + UI /api/journal/daily uses include_qa=True; digests keep filtered default. Rapid log moved above daily content; "Add to journal" / "Voice draft" / "Add gratitude" labels; rapidLogInput aria-label.
WHY: Journal add → leave → return must show the entry Jeff just logged.
TARGETED TEST: PASS — triage path hits rapidLogInput + Add to journal; foundImmediate+foundReturn+apiHas
E2E TEST: PASS — add → planner → journal → chat → journal; hard reload still shows entry+API
REGRESSION: PASS — daily_get(include_qa=False) still hides QA labels; disposable ARIA-REPAIR-J* cleaned
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug016/
```

## 2026-08-11 — REPAIR-015 / BUG-015 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-015
BUG: BUG-015
ROOT CAUSE: /api/planner snapshot called list_tasks() which filtered timestamped disposable labels (ARIA-REPAIR-*-{epoch}) via looks_like_dev_label. UI Add succeeded (toast + DB insert) but leave→return and /api/planner omitted the task, looking like a persistence failure.
FILES CHANGED:
  - jarvis/planner_store.py
WHAT CHANGED: planner_snapshot() uses list_tasks(include_qa=True) and events_for_day(include_qa=True). Digests may still call filtered list_tasks(); Integrity still flags QA labels for Guided Repair.
WHY: Planner create → leave → return must show the task Jeff just added.
TARGETED TEST: PASS — in_snap True for ARIA-REPAIR-PLAN-{epoch}; filtered list_tasks still hides for digests
E2E TEST: PASS — UI add → chat → planner found; hard reload → still found + API
REGRESSION: PASS — Integrity/purge_qa_planner still detect QA labels; normal tasks unchanged
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug015/
```

## 2026-08-11 — REPAIR-014 / BUG-009 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-014
BUG: BUG-009
ROOT CAUSE: Native Integrity room exit left painted Truth/Score content in a parked #integrityRoom; stage restore did not mark the native panel inert/hidden itself, so leave→chat still looked like a live Integrity mount to DOM probes.
FILES CHANGED:
  - jarvis/gui/static/workspace/rooms/room_kit.js
  - jarvis/gui/static/workspace/rooms/stage.js
  - jarvis/gui/static/index.html
WHAT CHANGED: On native exit, hide+aria-hidden+inert and clear data-nr-body; rebuild body structure on re-enter; AriaStage restore/mount toggles the same flags for native panels.
WHY: Integrity must mount with score when entered and must not remain a live Truth surface after leaving.
TARGETED TEST: PASS — enter has Score/Truth; after leave stale=false (no Truth/Score in integrityRoom innerText); re-enter paints again
E2E TEST: PASS — Integrity → Chat → Integrity (triage NOT REPRODUCIBLE / pass=true)
REGRESSION: PASS — hold still parks natives; a11y excluded while parked
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug009/
```

## 2026-08-11 — REPAIR-013 / BUG-008 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-013
BUG: BUG-008
ROOT CAUSE: parse_remember kept QA framing ("for testing:") and confirmational tails ("Confirm you stored it.") inside stored ACM facts; NLU remember params mirrored the dirty text.
FILES CHANGED:
  - jarvis/modules/memory_common.py
  - jarvis/nlu/mapping.py
  - tests/test_memory_intent_routing.py
WHAT CHANGED: Strip testing/QA prefixes and confirmational trailing clauses in parse_remember; normalize remember params via parse_remember in resolve_memory_route.
WHY: Memory must store clean autobiographical propositions, not test instructions.
TARGETED TEST: PASS — unit scrub; live remember stores "my acceptance token is MARKER" with dirty=false
E2E TEST: PASS — Chat remember with confirm tail → Memory/API content clean (no Confirm you stored)
REGRESSION: PASS — plain remember / preference / exactly: paths still parse
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug008/
```

## 2026-08-11 — REPAIR-012 / BUG-006 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-012
BUG: BUG-006
ROOT CAUSE: needs_attention used sentinel "All clear" and health_brief copied every attention string into critical_issues, so degraded health listed "All clear" beside real warnings (e.g. Long-run stability warning).
FILES CHANGED:
  - jarvis/mission_control_ops/health_brief.py
  - aiplatform/mission_control/aggregator.py (AI-Platform)
  - tests/test_mission_control_ops.py
WHAT CHANGED: Filter clear sentinels from critical_issues; return empty needs_attention when nothing needs attention (UI renders All clear); unit test for dishonest combo.
WHY: Mission health must not claim All clear while overall is degraded.
TARGETED TEST: PASS — pytest test_health_brief_strips_all_clear_sentinel; API critical_issues=['Long-run stability warning'] without All clear
E2E TEST: PASS — Mission room + /api/mission-control/health honest (no All clear + degraded combo)
REGRESSION: PASS — healthy brief still healthy when attention empty
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug006/
```

## 2026-08-11 — REPAIR-011 / BUG-005 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-011
BUG: BUG-005
ROOT CAUSE: Stop control stayed in the DOM with aria-label="Stop responding" while CSS-hidden after cancel, so cancellation looked incomplete; stopChat also could leave "Stopping…" if stream cleanup stalled.
FILES CHANGED:
  - jarvis/gui/static/chat_progress.js
  - jarvis/gui/static/index.html
WHAT CHANGED: setChatBusy only exposes aria-label/operable Stop while busy (hidden+aria-hidden+no label when idle); clears sticky Stopping/Thinking status on release; stopChat adds 2s settle watchdog to finishSendUi if busy sticks.
WHY: After Stop, Jeff must return to a listening Send state with no operable Stop / sticky Stopping…
TARGETED TEST: PASS — Stop appears while streaming; after Stop, querySelector(aria-label Stop responding) is absent; sticky false; busy false
E2E TEST: PASS — Chat send → Stop → recovery (Send available, Listening/Ready, no Stopping…)
REGRESSION: PASS — idle stop has no aria-label; cancel API path unchanged
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug005/
```

## 2026-08-11 — REPAIR-006 / BUG-014 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-006
BUG: BUG-014
ROOT CAUSE: Furnished Living Workspace Fly Tying inventory add was wired, but the room exposed two identical "Add" buttons (video before inventory) and the inventory What field lacked what/material labeling. Open inventory → fill → Add therefore hit Add video / search, never POST /api/flytying/materials/add. Queue control labeled "+ Queue" also mismatched the empty-state "Add to queue" copy.
FILES CHANGED:
  - jarvis/gui/static/index.html
  - jarvis/gui/static/flytying.js
  - jarvis/gui/static/flytying_home.js
WHAT CHANGED: Rename inventory control to "Add material", video control to "Add video"; label What field (placeholder/aria-label/name); Open inventory scrolls inventory into view; recipe queue button "Add to queue".
WHY: Jeff must complete Fly → inventory add → persist → return → queue/planner from visible Living Workspace controls without ambiguous Add targets.
TARGETED TEST: PASS — triage path Open inventory → What → Add material stores via API and shows in UI
E2E TEST: PASS — search Adams → add material → leave/return still present → Add to queue → planner task with marker
REGRESSION: PASS — materials/add API unchanged; correct ManualAdd path still works; disposable ARIA-* materials cleaned after verification
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug014/
```

## 2026-08-11 — REPAIR-005 / BUG-013 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-005
BUG: BUG-013
ROOT CAUSE: Chat→Memory failed for stacked reasons: (1) stream path waited on chat-model GPU load for remember/recall/forget; (2) stale NLU clarification demoted remember→chat (LLM lied about storage); (3) "remember exactly: TOKEN" stored "exactly: TOKEN" attaching a shared prune_eligible concept that hid experiences from /api/memory/all; (4) list filter used any() archived concept; (5) forget token-AND cooled shared concepts; (6) Memory search UI lived in closed <details> so hits were invisible to Living Workspace checks; (7) Running <action> SSE status did not count as stream progress.
FILES CHANGED:
  - jarvis/gui/server.py
  - jarvis/router.py
  - jarvis/modules/memory_common.py
  - jarvis/nlu/mapping.py
  - aria_core/acm_bridge.py
  - jarvis/gui/static/memory_browser.js
  - jarvis/gui/static/chat_send.js
  - jarvis/gui/static/index.html
WHAT CHANGED: Skip chat-model ensure for deterministic memory actions; memory verbs escape pending clarification; strip exactly:/literally: from remember text; list experiences unless ALL linked concepts are forgotten; tighten forget matching; open Browse details on search; load memory list before secondary panels; count "Running …" as stream progress.
WHY: Living Workspace Chat→Memory→Recall must durably store and surface facts end-to-end
TARGETED TEST: PASS — stream remember ~4s Stored via ACM (no loading chat model); list finds exp+concept; recall includes marker; forget clears
E2E TEST: PASS — UI store→Memory search (details open)→leave/return→recall; UI forget cools (left=[]) ; API chain store/list/recall/forget
REGRESSION: PASS — legacy clarification non-memory still → chat; direct POST /api/memory still works
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug013/
```

## 2026-08-11 — REPAIR-012 / BUG-001 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-012
BUG: BUG-001
ROOT CAUSE: prefsEnabled() and prepaint boot ignored livingWorkspace:true unless ?workspace=1 / Electron / app markers were present
FILES CHANGED:
  - jarvis/gui/static/workspace/workspace.js
  - jarvis/gui/static/index.html
WHAT CHANGED: Bare `/` enables Living Workspace when prefs.livingWorkspace !== false (default true). Legacy remains via ?workspace=0 or livingWorkspace:false. Prepaint reads localStorage so legacy shell does not flash.
WHY: Browser users with Living Workspace preferred were silently dropped into the legacy shell
TARGETED TEST: PASS — cold `/` living=true; refresh living; nav chat/memory/planner/settings; Front Door open/close
E2E TEST: PASS — `/` → Living Workspace; legacy escape ?workspace=0; pref false → legacy
REGRESSION: PASS — living restored after pref toggle
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug001/
```

## 2026-08-11 — REPAIR-010 / BUG-002 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-010
BUG: BUG-002
ROOT CAUSE: loadAudioStatus() threw on non-string device fields (e.g. input_source/output_sink objects or non-array output_sinks), collapsing healthy API payloads into "Could not load audio status."; status bar also used a module-load DOM reference
FILES CHANGED:
  - jarvis/gui/static/audio.js
  - jarvis/gui/static/index.html (cache bust)
WHAT CHANGED: Coerce device labels safely; resolve #audioStatusBar at call time; distinguish HTTP/API failure (show real message) from render crashes; keep music status optional
WHY: Audio room appeared broken despite healthy /api/audio/status
TARGETED TEST: PASS — healthy Whisper/ffmpeg/TTS bar; bad_types still renders; API failure shows "device bus offline" (not hidden)
E2E TEST: PASS — enter Audio room status readable
REGRESSION: PASS — restored healthy after injected failure modes
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug002/
```

## 2026-08-11 — REPAIR-001 / BUG-003 — FIXED

```text
DATE: 2026-08-11
REPAIR ID: REPAIR-001
BUG: BUG-003
ROOT CAUSE: Empty title/body events persisted as durable unread (source=api); room-navigation AbortError toasts were published as "X load failed" inbox errors
FILES CHANGED:
  - jarvis/activity_inbox.py
  - jarvis/gui/static/activity_center.js
  - jarvis/gui/static/planner.js
  - jarvis/gui/static/dashboard_home.js
  - jarvis/gui/static/calendar.js
  - jarvis/gui/static/capabilities_home.js
  - jarvis/gui/static/integrations_home.js
WHAT CHANGED: Reject/prune empty inbox noise; list_items returns unread; toast hook skips abort/cancel; planner/home/calendar/capabilities/integrations skip AbortError toasts
WHY: Activity Center was untrustworthy — empty spam + false load failures buried real events
TARGETED TEST: PASS — empty publish rejected; empty count 122→0; thrash new_load_delta=0; real error toast still persists
E2E TEST: PASS — rapid room navigation does not inflate load-failed inbox
REGRESSION: PASS — meaningful ARIA-REPAIR-TEST events still appear
RESULT: FIXED
EVIDENCE: /tmp/aria-post-repair/bug003/
```
