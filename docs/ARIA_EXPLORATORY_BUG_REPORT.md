# ARIA Exploratory Discovery Bug Report

Generated: 2026-08-10T20:25:25.029760+00:00

Continues from BUG-022. No repairs applied in this phase.

## BUG-023 — P1

| Field | Value |
|---|---|
| SEVERITY | P1 |
| EXPLORATORY TEST ID | EXP-178 |
| ROOM | shell / multiple |
| CONTROL | health emergency report link/navigation |
| FUNCTION | Navigate / open status control |
| STATE | during candidate exploration |
| USER ACTION | Click discovered control during recursive exploration |
| EXPECTED | Remain inside Living Workspace SPA |
| ACTUAL | Top-level navigation to `/api/health/report?kind=emergency`; SPA wiped; exploration interrupted after EXP-177 |
| REPRODUCTION RATE | 1/1 observed during exploratory candidate pass |
| STEPS | 1) Living Workspace 2) Enter rooms and click discovered controls 3) Observe navigation to raw API health report |
| EVIDENCE | `/tmp/aria-exp-accept/by_id/EXP-178.json`; browser href captured mid-run |
| ERROR | Page left application shell |
| LIKELY ROOT CAUSE | Anchor/button exposing raw `/api/...` URL as top-level navigation |
| USER IMPACT | User can be thrown out of Living Workspace into a raw JSON/API report; loses UI context |
| WORKAROUND | Manually return to `/?workspace=1` |
| BLOCKS RELEASE | yes |

## BUG-024 — P2 (class)

| Field | Value |
|---|---|
| SEVERITY | P2 |
| EXPLORATORY TEST ID | multiple EXP-020+ |
| COUNT | 116 FAIL rows tagged BUG-024 |
| ROOM | many (see distribution) |
| CONTROL | label-targeted click after room enter |
| FUNCTION | Activate previously discovered control by visible label |
| STATE | DEFAULT after AriaHouse.enter |
| USER ACTION | Re-find control by label and activate |
| EXPECTED | Control still present and activatable |
| ACTUAL | Control missing / label drift / conditional-only / covered by overlay |
| REPRODUCTION RATE | high within automated label re-click harness |
| STEPS | Discover label in room → leave/re-enter → click by exact label |
| EVIDENCE | `/tmp/aria-exp-accept/by_id/EXP-*.json` with `bug: BUG-024` |
| ERROR | `missing: true` in actual |
| LIKELY ROOT CAUSE | Dynamic labels, tab-scoped controls, Front Door/overlays, or discovery collecting chrome not room-scoped |
| USER IMPACT | Some controls are hard to rediscover or only exist in conditional states; automation/user revisit friction |
| WORKAROUND | Use Front Door / known tabs; open revealers first |
| BLOCKS RELEASE | no (class noise + real conditional gaps mixed; triage in repair phase) |

### BUG-024 distribution by room

- `documents`: 12
- `chat`: 10
- `browser`: 9
- `flytying`: 9
- `home_automation`: 7
- `maker`: 7
- `gallery`: 6
- `meme`: 5
- `mission`: 5
- `planner`: 5
- `home`: 4
- `repair`: 4
- `voice`: 4
- `actions`: 3
- `calendar`: 3
- `coding`: 3
- `memory`: 3
- `security`: 3
- `audio`: 2
- `audit`: 2
- `presence`: 2
- `video`: 2
- `capabilities`: 1
- `connections`: 1
- `integrations`: 1
- `projects`: 1
- `providers`: 1
- `search`: 1

## Prior bugs rechecked

| Bug | Status |
|---|---|
| BUG-001 | STILL FAILING |
| BUG-002 | CHANGED BEHAVIOR |
| BUG-003 | STILL FAILING |
| BUG-004 | NOT CHECKED |
| BUG-005 | STILL FAILING |
| BUG-006 | STILL FAILING |
| BUG-007 | NOT CHECKED |
| BUG-008 | NOT CHECKED |
| BUG-009 | NOT CHECKED |
| BUG-010 | NOT CHECKED |
| BUG-011 | STILL FAILING |
| BUG-012 | CHANGED BEHAVIOR |
| BUG-013 | STILL FAILING |
| BUG-014 | STILL FAILING |
| BUG-015 | STILL FAILING |
| BUG-016 | NOT CHECKED |
| BUG-017 | NOT CHECKED |
| BUG-018 | STILL FAILING |
| BUG-019 | NOT CHECKED |
| BUG-020 | NOT CHECKED |
| BUG-021 | NOT CHECKED |
| BUG-022 | NOT CHECKED |

## Notes

- Raw-label final passes (EXP-FINAL-PASS…3) found hundreds of *data-instance* labels (named flies, automation rules). Those are not new function kinds.
- Function-normalized final gate: EXP-FINAL-PASS-FN found 21 novel verbs; absorbed+tested; EXP-FINAL-PASS-FN-2 found **0**.
- BUG-011: single Front Door enter/close recheck PASSED (EXP-BUG-011); all-destinations sweep still FAIL (EXP-002).
- BUG-002: Audio status PASS on EXP-014, FAIL on EXP-BUG-002 recheck → intermittent.

