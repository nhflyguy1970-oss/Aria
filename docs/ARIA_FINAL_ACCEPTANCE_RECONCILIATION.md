# ARIA Final Acceptance Reconciliation

Generated: 2026-08-11  
Evidence: `/tmp/aria-post-repair/accept/states/summary.json`, `raw.json`, `/tmp/aria-execution-closure/execute_states_wf.js`

## Core distinction (resolves the contradiction)

The post-repair states harness stores **two separate bags**:

1. **`states`** — 111 applicable UI-state IDs (`STATE-*`)
2. **`workflows`** — a small set of embedded cross-cutting workflow probes (`WF-*`) executed in the same script (`execute_states_wf.js`)

The summary line:

```text
STATES: 111 applicable · PASS=111 · FAIL=0 · UNTESTED=0
```

counts **only the `states` bag**.

It does **not** claim that every `WF-*` workflow also passed.

The post-repair acceptance report incorrectly implied a contradiction by listing workflow FAILs under the same mental bucket as “states.” Those are **not state IDs**.

---

## TEST: State bag vs workflow bag

```text
TEST
  Post-repair run_states.py → summary.json counts vs workflows object

RESULT
  states: 111/111 PASS
  workflows: WF-CHAT-MEMORY PASS, WF-NAV-LIVING PASS,
             WF-BUG-023 FAIL, WF-KEYBOARD FAIL, WF-SETTINGS-PERSIST FAIL

RAW EVIDENCE
  /tmp/aria-post-repair/accept/states/summary.json
  /tmp/aria-post-repair/accept/states/raw.json
  Counter on raw.states statuses = {PASS: 111}

WHY SUMMARY DIFFERS
  summary.counts tallies Object.values(states) only.
  summary.workflows is a separate dictionary and is not folded into counts.PASS/FAIL.

ACTUAL PRODUCT STATUS
  Applicable UI states: all exercised and PASS in that run.
  Three workflow probes failed their harness expectations (see below).

FINAL CLASSIFICATION
  DOCUMENTATION / HARNESS ACCOUNTING — not a hidden state failure.
  Correct reporting form:
    STATES: 111 PASS / 0 FAIL / UNTESTED=0
    EMBEDDED WORKFLOWS (same script): 2 PASS / 3 FAIL
```

---

## TEST: WF-BUG-023 (raw `/api/` anchors on Mission)

```text
TEST
  execute_states_wf.js WF-BUG-023:
    enter mission → query a[href*='/api/health/report'], a[href*='/api/']
    FAIL if any such <a> exists (records first href)

RESULT
  FAIL — actual.href = http://127.0.0.1:8765/api/integrity/score (count=5)

RAW EVIDENCE
  /tmp/aria-post-repair/accept/states/summary.json → workflows.WF-BUG-023
  execute_states_wf.js lines ~189–194

WHY SUMMARY DIFFERS FROM DEDICATED BUG-023 E2E
  Dedicated BUG-023 / E2E-BUG-023 tested Health Emergency/Doctor report
  openHealthReport() modal stay-in-app — PASS.
  WF-BUG-023 is a different probe: presence of ANY raw /api/ <a> on Mission,
  and the first hit was /api/integrity/score — not Health Emergency.

ACTUAL PRODUCT STATUS
  Health report SPA stay: FIXED (BUG-023).
  Mission (and possibly Integrity) still exposes raw /api/ anchors — separate residual;
  classified in integrity navigation review (not silently folded into BUG-023).

FINAL CLASSIFICATION
  HARNESS OVER-SCOPE vs BUG-023 title + possible PRODUCT residual for integrity link
  (see ARIA_FINAL_ORCHESTRATION / integrity section in final report).
```

---

## TEST: WF-KEYBOARD (Ctrl+K palette)

```text
TEST
  Synthetic KeyboardEvent ctrl+k; look for #commandPalette / .command-palette / body text

RESULT
  FAIL — open=false

RAW EVIDENCE
  states/summary.json → workflows.WF-KEYBOARD
  execute_states_wf.js WF-KEYBOARD

WHY SUMMARY DIFFERS / WHY NOT A STATE FAIL
  Not a STATE-* ID. Synthetic keydown often does not trigger the same path as a real
  user chord (focus/capture). Inventory CMD-001 may differ.

ACTUAL PRODUCT STATUS
  Requires independent live verification with real key delivery or UI button equivalent.
  Not evidence that Living Workspace states failed.

FINAL CLASSIFICATION
  HARNESS ARTIFACT (synthetic key) pending independent proof — see inventory/E2E follow-up.
```

---

## TEST: WF-SETTINGS-PERSIST

```text
TEST
  Enter settings → panel()?.querySelector("select") with options>1 → flip → leave → return

RESULT
  FAIL — actual.noSelect=true (harness found no usable select in panel())

RAW EVIDENCE
  states/summary.json → workflows.WF-SETTINGS-PERSIST
  Dedicated E2E-SETTINGS PASS (/tmp/aria-post-repair/accept/e2e/summary.json)

WHY SUMMARY DIFFERS FROM DEDICATED E2E
  Workflow uses a narrow panel()?.querySelector("select") before Appearance controls
  are rendered / category selected. Dedicated E2E used broader settings selects and
  AriaUiPrefs — PASS.

ACTUAL PRODUCT STATUS
  Settings persistence product behavior: PASS (dedicated E2E + BUG-019 repair evidence).

FINAL CLASSIFICATION
  HARNESS ARTIFACT — invalid probe relative to proven product behavior.
```

---

## Corrected acceptance language (authoritative)

```text
APPLICABLE STATES (STATE-*):
  111 tested · PASS=111 · FAIL=0 · UNTESTED=0

EMBEDDED WORKFLOWS (WF-* in same states script — NOT states):
  PASS: WF-CHAT-MEMORY, WF-NAV-LIVING
  FAIL: WF-BUG-023 (raw /api/integrity/score anchor presence),
        WF-KEYBOARD (synthetic Ctrl+K),
        WF-SETTINGS-PERSIST (noSelect harness)

DEDICATED PRODUCT E2E (authoritative for repaired journeys):
  BUG-023 Health Emergency modal: PASS
  Settings persist: PASS
```

Do **not** claim “111/111 states PASS” and “state failures exist” as the same thing.
Workflow failures are **workflow** failures.
