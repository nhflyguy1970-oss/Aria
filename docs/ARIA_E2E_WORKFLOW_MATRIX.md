# ARIA E2E Workflow Matrix

Generated: 2026-08-11T03:46:21.612160+00:00

Every meaningful cross-room workflow is **EXECUTED**, **NOT TESTABLE**, or **NOT APPLICABLE**. None remain bare NOT EXECUTED.

| Workflow | Rooms | Executed? | Result | Bug | Evidence |
|---|---|---|---|---|---|
| Chat → research → answer | chat | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-CHAT-RESEARCH |
| Chat → memory → recall | chat, memory | yes | FAIL | BUG-013 | /tmp/aria-triage/triage_raw.json::BUG-013 |
| Chat → clarification → follow-up | chat | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-CHAT-CLARIFY |
| Chat → cancellation → recovery | chat | yes | FAIL | BUG-005 | /tmp/aria-triage/triage_raw.json::BUG-005 |
| Chat → model selection → response | providers, chat | yes | FAIL | BUG-018 | /tmp/aria-triage/triage_raw.json::E2E-MODELS-CHAT |
| Research weak-source refusal | chat | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-RESEARCH-WEAK |
| Documents search | documents | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-DOCS-SEARCH |
| Documents import/search reopen | documents | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-DOCS-IMPORT-PATH |
| Fly search | flytying | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-FLY-SEARCH |
| Fly search → inventory → planner | flytying, planner | yes | FAIL | BUG-014 | /tmp/aria-triage/triage_raw.json::E2E-FLY-INVENTORY-PLANNER |
| Gallery generate affordance | gallery | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-GALLERY-OPEN |
| Image generate UI (no full GPU wait) | gallery | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-IMAGE-GENERATE-UI |
| Audio status | audio | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-AUDIO-STATUS |
| Audio record UI → journal handoff | audio, journal | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-AUDIO-RECORD-UI |
| Mission health honesty | mission | yes | FAIL | BUG-006 | /tmp/aria-triage/triage_raw.json::E2E-MISSION-HONESTY |
| HA read-only status/search | home_automation | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-HA-READONLY |
| HA device toggle | home_automation | NOT TESTABLE | NOT TESTABLE | — | No safe QA entity/device |
| Coding propose without apply | coding | yes | NOT TESTABLE | — | /tmp/aria-triage/triage_raw.json::E2E-CODING-PROPOSE |
| Coding apply to live jarvis | coding | NOT TESTABLE | NOT TESTABLE | — | Would mutate live production tree |
| Command palette Ctrl+K | shell | yes | FAIL | — | /tmp/aria-triage/triage_raw.json::E2E-KEYBOARD-PALETTE |
| Planner create → leave → return | planner, chat | yes | FAIL | BUG-015 | /tmp/aria-triage/triage_raw.json::E2E-PLANNER-PERSIST |
| Settings persist | settings | yes | PASS | — | Prior WF-SETTINGS-PERSIST PASS in execution closure |
| Living workspace entry | shell | yes | FAIL | BUG-001 | /tmp/aria-triage/triage_raw.json::BUG-001 |
| Integrity mount | integrity | yes | FAIL | BUG-009 | /tmp/aria-triage/triage_raw.json::BUG-009 |
| Journal add entry | journal | yes | FAIL | BUG-016 | /tmp/aria-triage/triage_raw.json::BUG-016 |
| Memory store quality | chat, memory | yes | FAIL | BUG-008 | /tmp/aria-triage/triage_raw.json::BUG-008 |
| Front Door enter/close | front_door, chat | yes | PASS | BUG-021 | /tmp/aria-triage/triage_raw.json::BUG-021 |
| Fly inventory add | flytying | yes | FAIL | BUG-014 | /tmp/aria-triage/triage_raw.json::BUG-014 |
| Calendar create real appointment | calendar | NOT TESTABLE | NOT TESTABLE | — | Avoid mutating live calendar without disposable fixture path confirmed |
| Automation create → inspect | automation | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-AUTOMATION-CREATE |
| Browser → capture affordance | browser, documents | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-BROWSER-CAPTURE |
| Video room affordances | video | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-VIDEO-UI |
| Voice room affordances | voice | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-VOICE-UI |
| Repair guided/restoration enter | repair | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-REPAIR-GUIDED |
| Projects → coding | projects, coding | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-PROJECTS-CODING |
| Job Center inspect (no cancel foreign jobs) | mission, shell | yes | PASS | — | /tmp/aria-triage/triage_raw.json::E2E-JOBCENTER |
| Job Center cancel/retry foreign jobs | mission | NOT TESTABLE | NOT TESTABLE | — | No disposable job fixture; canceling live jobs unsafe |
| Health upload PHR | health | NOT TESTABLE | NOT TESTABLE | — | Production Integrity — live PHR writes forbidden |
| Activity Center load quality | activity, shell | yes | FAIL | BUG-003 | /tmp/aria-triage/triage_raw.json::BUG-003 |
| SPA raw /api navigation (BUG-023) | mission, health | yes | CHANGED BEHAVIOR | BUG-023 | /tmp/aria-triage/triage_raw.json::BUG-023 |
| Full image GPU lifecycle to gallery asset | gallery | NOT TESTABLE | NOT TESTABLE | — | Long GPU job; UI path covered by E2E-IMAGE-GENERATE-UI |
| Full audio record→transcribe durable artifact delete cycle | audio | NOT TESTABLE | NOT TESTABLE | — | Would create/delete real media without dedicated sandbox store |

## Result counts

- PASS: 20
- FAIL: 13
- NOT TESTABLE: 8
- CHANGED BEHAVIOR: 1

## Notes

- GPU/full media lifecycles and live HA/PHR/coding-apply/job-cancel paths are NOT TESTABLE with stated safety reasons.
- FAIL rows map to historical bugs (planner persist, models, mission honesty, keyboard, fly inventory).

