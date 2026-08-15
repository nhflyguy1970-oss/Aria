# ARIA — Stabilization Diagnostic Report

**Runtime under test:** PID `3255320` on `:8765` (started 18:42:13, after source mtimes ~18:32)  
**Evidence:** `/tmp/aria-current-baseline/`  
**Companion baseline:** `docs/ARIA_CURRENT_RUNTIME_BASELINE.md`  
**NO CODE CHANGED:** YES

This report does **not** claim engineering FINAL PASS or real-world FINAL readiness. It establishes what the dirty worktree is, whether the fresh process is the intended tree, and what targeted diagnostics show.

---

## WORKTREE

```text
614 changed files = 614 unique dirty paths (porcelain + untracked)
APPLICATION CHANGES = 402 files  (~+49,148 / -4,174)
GENERATED ARTIFACTS = 13 files   (~+2,479)   # docs/_*.json + phase1_runtime_spikes/*.json
TEST ARTIFACTS = 59 files        (~+3,786 / -200)
DOCUMENTATION = 121 files        (~+36,178 / -399)
OTHER = 19 files                 # unrelated design/CAD (8), config (2), build lock (1), unknown scripts (8)
```

**Primary driver of +96,067 lines:** real application source + large certification/inventory documentation — **not** databases/cache/logs.

Ignore-gap: 13 generated JSON evidence files are currently visible to git and should normally be ignored (listed in baseline doc). Previous acceptance/repair tooling produced large docs inventories and proof JSON; that content remains in the dirty tree.

---

## CURRENT RUNTIME

```text
PID = 3255320
PORT = 8765
RUNTIME MATCH = YES (operational) / UNKNOWN (hard __file__ attach denied)
```

Operational match evidence: cwd=`/media/jeff/AI/jarvis`, start after latest relevant mtimes, live fingerprints `research_followup` / `research_correction` / `subject_change` / writing→chat.

---

## Diagnostic gate results

| Gate | Result | Notes |
|---|---|---|
| KNOWLEDGE SUFFICIENCY | **PASS** | “What day…?” → `chat` / calendar fact; no web_search |
| RESEARCH EXECUTION | **PASS** | Ranger brakes → `web_search`, 5 results retrieved |
| RESEARCH EVIDENCE HANDOFF | **PASS** | Answer includes `**Sources**` + URLs; speech references search outcome |
| AUTHORITATIVE SOURCE GATE | **PASS\*** | Weak/non-OEM hits → refuses to treat as authoritative procedure; asks for OEM manual |
| CLAIM POSTCHECK | **FAIL** | Follow-up torque turn can still quote a **lug-nut** ft-lb figure from a weak/year-mismatched web hit while admitting rotor torque is missing |
| REQUEST LIFECYCLE | **PASS\*** | Normal success + health not busy; full UI “finishing” / stream interrupt **not** fully proven headlessly |
| TIMEOUT | **PASS\*** | In-process `web_search.search` TimeoutError simulation; **live HTTP** timeout fail-closed path not injected into PID 3255320 |
| CANCELLATION | **PASS\*** | `/api/chat/cancel` ok; second request works; concurrent in-flight stream cancel not browser-proven |
| STREAM RECOVERY | **UNKNOWN / NOT PROVEN** | Headless Form API path; no SSE interrupt trial in this diagnostic |
| SECOND REQUEST RECOVERY | **PASS** | After research + cancel attempt, subsequent chats succeed; health `busy=false` |
| CONTEXT | **PASS** | Ranger → tools follow-up → correction stay on `web_search` / research thinking; no Samsung/email diversion |
| MEMORY | **PASS** | store / recall desktop / honest fishing miss / forget without “I’ll remember” |
| ORCHESTRATION | **PASS** | chat / writing / runtime_ram / web_search / subject_change / remember / recall / forget |

\* = pass with stated limitation.

---

## Test evidence (condensed)

### TEST A — local knowledge
- request: “What day of the week is today?”
- action: `chat`, thinking `calendar fact`
- no web_search

### TEST B — research vehicle question
- request ID: `diag-ef3dd7d1eb`
- orchestration: `thinking=orchestration_policy_research` → `action=web_search` / `type=web_search`
- sources retrieved: 5 (quality mixed; one unrelated Mustang Mach-E promo)
- synthesis: states result not adequate for procedure; includes `**Sources**`
- unsupported exact torque invented: no

### TEST C — consequential follow-up
- request ID: `diag-3b91dba75b`
- action: `web_search`; Ranger context preserved in answer/results
- no invented authoritative rotor torque as OEM fact in the primary refusal path

### TEST D — research failure
- method: in-process mock (`TimeoutError` from `web_search.search`)
- empty synthesize → “No web results found…” (not a confident local procedure)
- next live request after research still works
- **Gap:** did not fault the live server’s HTTP path mid-request

### TEST E — lifecycle
- normal SUCCESS; cancel API ok; second request SUCCESS; timeout simulation TIMEOUT
- health ready/not busy afterward
- **Gap:** stream interrupt / sticky “finishing” UI not exercised

### TEST F — context chain
- rotors → tools follow-up (`research_followup`) → correction (`research_correction`) → torque follow-up all `web_search`
- **Issue:** torque answer cited “100 ft-lbs” lug nuts for a 2019 Ranger from a web snippet while discussing the rotor job — claim-postcheck weakness

### TEST G / H — memory + orchestration
- all targeted cases passed on PID 3255320

Raw JSON: `/tmp/aria-current-baseline/diagnostics/diagnostic_report.json`

---

## NEW BUGS

1. **CLAIM-POSTCHECK-WEAK-SPEC** (P1) — On consequential torque follow-ups, synthesis can surface a **specific ft-lb number** from non-authoritative / wrong-component / wrong-year web hits even while saying rotor torque is unavailable.
2. **RESEARCH-RETRIEVAL-NOISE** (P2) — Brake/rotor how-to queries sometimes retrieve irrelevant commercial pages (e.g. Mustang Mach-E brake specials); speech often hedges, but retrieval quality is weak.
3. **ENTITY-DISAMBIGUATION-FLY-PROJECT** (P2) — Subject change to “fly project” routes correctly to chat but may narrate the EDM act “Fly Project” instead of fly-tying without clarification.
4. **RESEARCH-SYNTHESIS-STALE-ENTITY-VERSION** (P2) — Ubuntu follow-up can stay on `web_search` yet summarize an older LTS than the immediately prior turn.
5. **LIFECYCLE-STREAM-UI-UNPROVEN** (P2 diagnostic gap) — Sticky “finishing”, SSE cancel mid-stream, and model-timeout UI recovery were not fully proven in this headless pass.

---

## ROOT CAUSES

1. **Worktree magnitude** — Accumulated uncommitted application + documentation from multi-phase certification/repair work; plus unignored generated proof JSON. Not a single accidental overwrite of 614 unrelated binaries.
2. **Stale runtime (already corrected)** — Prior PID 2884670 started before 18:32 source edits; refreshed to 3255320.
3. **Claim postcheck / authority filtering incomplete for numeric specs** — Research path runs, but synthesis can still promote a weakly sourced numeric torque adjacent to the asked claim.
4. **Retrieval ranking/noise** — Web results for consequential vehicle tasks are not consistently OEM/T1.
5. **Diagnostic tooling limits** — Cannot attach to CPython for `__file__`; cannot fully simulate live HTTP search timeout without fault injection in the running server.

---

## Scoreboard (required fields)

```text
WORKTREE:
614 changed files = 614
APPLICATION CHANGES = 402 files (~+49148/-4174)
GENERATED ARTIFACTS = 13 files (~+2479)
TEST ARTIFACTS = 59 files (~+3786/-200)
OTHER = documentation 121 + unrelated/design 8 + config 2 + build 1 + unknown scripts 8

CURRENT RUNTIME:
PID = 3255320
PORT = 8765
RUNTIME MATCH = YES (operational) / UNKNOWN (ptrace __file__)

KNOWLEDGE SUFFICIENCY: PASS
RESEARCH EXECUTION: PASS
RESEARCH EVIDENCE HANDOFF: PASS
AUTHORITATIVE SOURCE GATE: PASS*
CLAIM POSTCHECK: FAIL
REQUEST LIFECYCLE: PASS*
TIMEOUT: PASS*
CANCELLATION: PASS*
STREAM RECOVERY: NOT PROVEN
SECOND REQUEST RECOVERY: PASS
CONTEXT: PASS
MEMORY: PASS
ORCHESTRATION: PASS

NEW BUGS:
- CLAIM-POSTCHECK-WEAK-SPEC (P1)
- RESEARCH-RETRIEVAL-NOISE (P2)
- ENTITY-DISAMBIGUATION-FLY-PROJECT (P2)
- RESEARCH-SYNTHESIS-STALE-ENTITY-VERSION (P2)
- LIFECYCLE-STREAM-UI-UNPROVEN (P2 gap)

ROOT CAUSES:
- accumulated dirty app+docs tree (not cache/db)
- prior stale process (refreshed)
- weak numeric claim filtering on consequential research
- noisy web retrieval
- limited live introspection/fault-injection in this phase

NO CODE CHANGED: YES
```

---

## Stop condition

```text
CURRENT BASELINE CLEAN = NO
```

Reason: **CLAIM POSTCHECK = FAIL**, plus unproven stream-recovery and hard module-load attach UNKNOWN.  
Do **not** claim ARIA ready. Do **not** start another giant acceptance campaign from here.

Next phase (only when you authorize): targeted repair of claim postcheck / authoritative numeric gate — after deciding what to do about the 614-file dirty tree (still untouched).
