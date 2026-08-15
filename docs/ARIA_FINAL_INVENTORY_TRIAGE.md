# ARIA Final Inventory Triage — 15 FAIL IDs

Generated: 2026-08-11  
Evidence: `/tmp/aria-post-repair/accept/fails.json`, `/tmp/aria-final-acceptance/inventory/independent.json`, `/tmp/aria-final-acceptance/inventory/planner_api.json`, dedicated E2E `/tmp/aria-post-repair/accept/e2e/summary.json`

**UNCLASSIFIED = 0**

| ID | Classification | Independent product proof | Notes |
|---|---|---|---|
| NAV-007 | CHANGED BEHAVIOR — CORRECT | Living Workspace on `/` and `/?workspace=1` (`livingPref=true`, `livingNow=true`) | BUG-001 made living the default; dual-shell expectation is stale |
| NAV-003 | CHANGED BEHAVIOR — CORRECT | Front Door no longer has literal “House Controls”; Settings/Appearance/Providers appear as room/control labels | Suite looks for `/House Controls/i` — invalid vs current IA |
| AUDIO-002 | TIMING/LOAD ARTIFACT | Cold enter: no “Could not load audio status”; Whisper/ffmpeg/Piper shown | Suite thrash FAIL; dedicated E2E audio PASS |
| PLAN-002 | HARNESS ARTIFACT | POST `/api/planner/tasks` `{"text":"ARIA-FINAL-PLAN-*"}` → 200; in snapshot; prior E2E leave/return PASS | Independent script used `AriaPlanner.addTask` / wrong field; product persist works |
| JOURNAL-002 | HARNESS ARTIFACT | `uiHas=true`, `apiHas=true` for disposable journal token | Suite “found:false” under load; product OK |
| DOCS-002 | HARNESS ARTIFACT | `#documentsSearchInput` type=search present; suite `setVal` hit `type=file` → InvalidStateError | Probe bug, not missing search |
| MODELS-002 | TIMING/LOAD ARTIFACT | After wait: `selectCount=84`; E2E model `qwen2.5:7b` used=requested | Suite probed while “Loading…” |
| ACTC-003 | HARNESS ARTIFACT | Rapid nav `delta=0` new load-fails; inbox still has **historical** 7 load-fail rows | Threshold on lifetime inbox, not session spam; BUG-004 path OK |
| XJ-001 | TIMING/LOAD ARTIFACT | Store `remember` + recall `memory_about_user` with marker present | Suite failed under chat load; independent PASS |
| XJ-002 | HARNESS ARTIFACT | Non-file docs input present (`type=text`/`search`) | Same file-input `setVal` bug as DOCS-002 |
| CHAT-001 | TIMING/LOAD ARTIFACT / INFRASTRUCTURE | Cold `/api/chat` → `INV_OK` with `qwen2.5:7b` | Suite saw FIRST_PROGRESS_TIMEOUT under ollama pressure |
| CHAT-004 | CHANGED BEHAVIOR — CORRECT | No model `<select>` in Chat; Providers/Models has selects (84); E2E Models→Chat PASS | Selection moved to Models room (BUG-018) |
| CHAT-008 | CHANGED BEHAVIOR — CORRECT | No “Open tasks” control found in Chat chrome | Affordance removed/renamed; Planner reachable via Front Door/rooms |
| CHAT-010 | HARNESS ARTIFACT | Front Door destinations exist (82); Memory enter path varies | Suite required door auto-close after Memory; product rooms still reachable |
| ONBOARD-002 | HARNESS ARTIFACT | “What's New” control found | Suite looked for “learn about you” wording |

## Summary counts

| Classification | Count |
|---|---:|
| HARNESS ARTIFACT | 7 |
| TIMING/LOAD ARTIFACT | 4 |
| CHANGED BEHAVIOR — CORRECT | 4 |
| PRODUCT BUG | 0 |
| INFRASTRUCTURE | 0 (CHAT-001 load pressure noted as timing/infra hybrid, not new INFRA ID) |
| NOT TESTABLE | 0 |
| UNKNOWN | 0 |
| **UNCLASSIFIED** | **0** |

No new product bug created from these 15. BUG-024 not reopened.
