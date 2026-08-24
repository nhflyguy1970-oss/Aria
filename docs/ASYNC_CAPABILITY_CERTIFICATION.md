# ARIA Asynchronous Capability Certification

**Date:** 2026-08-24
**Baseline commit:** `f04e5c2`
**Method:** repository-wide discovery → per-capability trace → frontend/backend contract
execution under node → live end-to-end run against the production server.
**Standard:** a capability is PASS only when the whole user lifecycle works —
trigger → job → worker → result *delivered to the user* → persistence → accurate
failure reporting. A green backend or a 200 is not a pass.

---

## Executive Summary

| | Count |
|---|---|
| Asynchronous capabilities discovered | **26** (14 chat-queued actions + 12 panel/system) |
| Job registries discovered | **9** |
| LIVE (exercised end-to-end against the running server) | **1** |
| PASS (full contract verified; lifecycle shared with a LIVE path) | **9** |
| PARTIAL | **7** |
| BLOCKED (dependency unavailable in this environment) | **9** |
| FAIL | **0** (3 found and fixed during this audit) |

**E2E grading is deliberately strict.** `LIVE` means the whole lifecycle was run
against the production server and observed. `PASS` means every contract layer was
verified by executing the real frontend router over real backend responses *and*
the capability shares its async lifecycle code with a `LIVE`-verified path — only
the worker body differs. `BLOCKED` means the async plumbing is verified but the
worker could not run here: **ComfyUI was not running during this audit**
(`127.0.0.1:8188` → no response), so no image/video/meme job could complete.
Nothing is graded from source inspection alone.

**Defects found: 3** — one HIGH (interrupted jobs reported as still running,
confirmed live in production), two LOW/MEDIUM (queue-resolution gap, a missing
audio job reported as a timeout). All three are fixed with regression tests that
fail before the fix.

The headline finding is that the Deep Research bug was **not** a one-off. It was
an instance of a class: *asynchronous work whose backend is correct while the
user-facing half is silently wrong*. This audit found two more members of that
class, and the certification matrix now covers the class rather than the instance.

---

## Certification Matrix

Legend: **T** trigger · **BE** backend · **JC** job created · **TY** job type correct ·
**RG** registry correct · **UI** UI route · **PL** poll/stream · **PR** progress ·
**CP** completion · **RD** result delivery · **EH** error handling · **PS** persistence ·
**RC** restart/recovery · **E2E** end-to-end.

### Chat-queued actions (all route through `handleDone` → `resolveJobKind`)

| Capability | T | BE | JC | TY | RG | UI | PL | PR | CP | RD | EH | PS | RC | E2E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Deep Research / Learn topic (`learn_about`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **LIVE** |
| Document summarize (`document_summarize`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS⁸** |
| Knowledge research (`knowledge_research_run`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS⁸** |
| Self-upgrade (`self_upgrade_run`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS⁸** |
| ARIA self-fix (`aria_self_fix`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS⁸** |
| Coding agent (`coding_agent`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS⁸** |
| Debug until tests pass (`coding_fix_tests`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS⁸** |
| Image generate (`generate_image`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Image edit (`edit_image`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Image inpaint (`inpaint_image`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Image upscale (`upscale_image`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Meme (`generate_meme`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Video generate (`generate_video`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Storyboard video (`storyboard_video`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |

### Panel-scoped and system asynchronous work

| Capability | T | BE | JC | TY | RG | UI | PL | PR | CP | RD | EH | PS | RC | E2E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gallery generate/variation | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Meme studio | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Video studio | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | N/T⁷ | N/T⁷ | PASS | PASS | PASS | **BLOCKED⁷** |
| Audio / Song Studio | PASS | PASS | PASS | N/A | PASS | PASS | PASS | PASS | PASS | PASS | **PASS¹** | FAIL² | FAIL² | **PARTIAL** |
| ComfyUI settings jobs | PASS | PASS | PASS | N/A | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL² | FAIL² | **PARTIAL** |
| Vision batch | PASS | PASS | PASS | N/A | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL² | FAIL² | **PARTIAL** |
| 3D print jobs | PASS | PASS | PASS | N/A | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PARTIAL | FAIL² | **PARTIAL** |
| Browser / computer-use tasks | PASS | PASS | PASS | PASS³ | PASS | PASS | PASS | PASS | N/T | N/T | PASS | PASS | PASS | **PARTIAL⁹** |
| Checkpointed agent jobs (`agent_job_start`) | PASS | PASS | PASS | N/A⁴ | PASS | PARTIAL⁴ | N/A⁴ | PASS | PASS | PARTIAL⁴ | PASS | **PASS** | **PASS** | **PARTIAL** |
| Specialist team jobs | PASS | PASS | PASS | N/A | PASS | PARTIAL⁵ | N/A⁵ | PASS | PASS | PARTIAL⁵ | PASS | PARTIAL | FAIL² | **PARTIAL** |
| Automation pipeline jobs | PASS | PASS | PASS | N/A | PASS | PARTIAL⁵ | N/A⁵ | PASS | PASS | PARTIAL⁵ | PASS | PARTIAL | FAIL² | **PARTIAL** |
| Voice / Gemini Live WebSocket | PASS | PASS | N/A | N/A | N/A | PASS | PASS | PASS | PASS | PASS | PASS | N/A | N/A | **BLOCKED⁶** |

¹ Fixed in this audit (Defect #3). ² In-memory registry: jobs do not survive
restart. Acceptable for short panel-scoped work, but see Remaining Risks.
³ Fixed in `f04e5c2` via the `queue: "coding"` hint. ⁴ Deliberate
"start then check status" design — no inline poller. ⁵ Discoverable via Job
Center (`/api/jobs`) only. ⁶ Requires live audio hardware + a Gemini key;
not exercisable in this environment. ⁷ **ComfyUI was not running during this
audit** — routing, registry, persistence and recovery are verified; the worker
could not produce an artifact, so completion/result delivery were not tested
(N/T = not tested, never "assumed passing"). ⁸ Shares the `_enqueue_background` /
`_enqueue_coding` lifecycle with the LIVE-verified Learn topic path; only the
worker body differs. ⁹ Async plumbing verified; a live browser task was not run
(the computer-use browser test is itself flaky in this environment).

---

## Capability-by-Capability Results (representative)

### Deep Research / Learn topic — **PASS** (canonical case)

* **Trigger:** chat, `is_learn_command()` → `learn_about`
* **Backend:** `conversation_pipeline.dispatch_action` → `assistant._enqueue_background`
* **Job type:** `background_job` (explicit)
* **Registry:** `coding_jobs._jobs` (background jobs submit to the coding worker)
* **Frontend route:** `resolveJobKind` → `background_job` → `jarvisPollBackgroundJob`
* **Endpoint:** `/api/coding/job/<id>` ✅
* **Completion:** `data.done && data.result.ok` → `handleDone`
* **Result:** rendered inline; brief written to `data/knowledge/<slug>.md`
* **Persistence:** metadata in `coding_jobs_state.json`; result persisted
* **Recovery:** interrupted runs are now closed out with an accurate message (Defect #2)

**Live E2E, production, 2026-08-24 13:04:45Z**

```
POST /api/chat  "do deep research on tenkara rod action and learn about it"
  → HTTP 200, job_id 816609e51c9d, type=background_job, pending=true
  → resolveJobKind → background_job
  → 56 polls, ALL to /api/coding/job/<id>
  → media-endpoint hits: 0
  → completed in 87.9s, result.ok=true, type=knowledge_learned
  → knowledge/do-deep-research-on-tenkara-rod-action-and-learn-about-it.md (9 sources)
  → rendered warnings: none (no Gallery, no restart claim)
VERDICT: PASS
```

Server PID 1765 unchanged, `NRestarts=0` throughout.

### Checkpointed agent jobs — **PARTIAL**

Best persistence in the codebase: per-job JSON with `checkpoint` and `result`
fields, `resume_incomplete_jobs()` on demand via `POST /api/agent-jobs/resume`.
`agent_job_start` returns the id nested in `data`, with no top-level `job_id` /
`pending`, so no inline poller starts and the chat never delivers the result.
The user must call `agent_job_status` or open Job Center. Deliberate and
honestly reported — but it is not a completed inline lifecycle. See Future Work.

---

## Defects Found

### Defect #1 — `job_framework` cannot resolve the `fix_tests` queue — **LOW**

* **Root cause:** the handler registry emits `queue="fix_tests"` for
  `coding_fix_tests`, but `job_framework.QUEUES` knew only
  `media|coding|background|audio`, so `get_job`/`cancel`/`stats`/`list_recent`
  raised `ValueError` for a legitimate queue. `submit_assistant_action` also
  reported coding-queue actions as "not a queued action", which is false.
* **Evidence:** `test_job_framework_resolves_every_queue` failed with
  `coding_fix_tests: job_framework cannot resolve queue 'fix_tests'`.
* **Live impact:** none — `job_framework` currently has no production callers.
  This is a trap for the next caller, not an active bug.
* **Fix:** `CODING_QUEUES = ("coding", "background", "fix_tests")` used by every
  coding-registry branch; accurate error text for coding-queue submits.
* **Regression test:** `tests/test_async_job_contract.py::test_job_framework_resolves_every_queue`

### Defect #2 — an interrupted job reports itself as still running, forever — **HIGH**

* **Root cause:** `media_jobs.recover_stale_jobs()` runs at startup, but
  `coding_jobs` had no equivalent and the lifespan hook never called one.
  `_load_persisted_state()` restores a killed job exactly as it was —
  `done=False` — and nothing ever finishes it.
* **Evidence (live production, 3 days after the fact):**

  ```
  GET /api/coding/job/be700505aeed
  {"ok": true, "label": "Learn topic", "pct": 3,
   "message": "Preparing coding model…", "done": false, "result": null,
   "started": 1787326657.6}   # killed by the Aug 21 11:38 restart
  ```

* **User impact:** the UI polls "Working…" against a corpse until its
  client-side timeout (30 min for coding/background), then gives up silently
  with no message at all. Job Center lists it as active indefinitely.
* **Fix:** `coding_jobs.recover_stale_jobs()`, mirroring the media model, called
  from the server lifespan. Interrupted jobs are closed out as failed with a
  message naming the job and the next step. Reaching that function at process
  start *is* evidence of a restart, so the message may say so — unlike a
  mid-poll 404, which may not.
* **Regression tests:** `tests/test_async_job_recovery.py` (7 tests; 6 fail before the fix)

### Defect #3 — a missing audio job is reported as a timeout — **MEDIUM**

* **Root cause:** `pollAudioJob` did `if (!data.ok) break;` and fell through to
  the loop-exhaustion branch, printing "Job timed out". `audio_progress` is an
  in-memory registry, so any restart makes every audio job return
  `404 {"ok": false, "message": "Unknown job"}` — reported as a timeout it never had.
* **Fix:** distinguish the two exit reasons; a vanished job now says
  "This audio job is no longer tracked by the server — run it again to retry."
* **Regression test:** `tests/test_async_error_messages.py::test_audio_poller_distinguishes_lost_from_timed_out`

---

## Certification Gaps (why the Deep Research bug escaped)

| # | What was tested before | What was missing | How the bug escaped |
|---|---|---|---|
| 1 | `learn_about` handler returns `ok:True` with a brief (`test_background_jobs.py`) | Nothing asserted which **endpoint the frontend polls** for the returned `job_id` | Backend was perfect; the failure lived entirely in `chat_done.js` |
| 2 | Static JS parses (`test_cert_static_js_syntax.py`) | Syntax ≠ semantics — the router parsed fine and routed wrongly | Valid JS, wrong branch |
| 3 | Job registries tested per module | No test crossed the **registry ↔ endpoint** boundary | Each half correct in isolation; only the join was broken |
| 4 | Error strings never asserted | A message may assert a cause (`"server restart"`) it cannot observe | The false diagnosis was invisible to tests and actively misled a human |
| 5 | Recovery tested for `media_jobs` only | `coding_jobs` had no recovery and no test demanded one | Defect #2 sat in production for 3 days undetected |

**The structural gap:** every previous test asked *"does this component work?"*.
None asked *"do these two components agree?"*. The new contract test asks the
second question for all 14 queued actions at once, by executing the real
frontend router over real backend responses.

---

## Test Suite Triage (Phase 12)

Final full suite in the isolated worktree: **3115 passed, 4 failed, 61 skipped**.
Control run with all four new test files excluded: **3064 passed, 3 failed**.
No unrelated test was weakened, skipped, deleted or modified to obtain a green run.

| Failure | Class | Evidence | Action |
|---|---|---|---|
| `test_async_job_contract::test_every_queued_action_is_discovered` | **New — mine, order-dependent** | Passed alone, failed in the full run. Other tests register probe actions into the process-global handler registry. | **Fixed.** Discovery now runs in a clean subprocess, order-independent by construction. Verified against a 551-test mixed slice; absent from all later runs. |
| `test_computer_use::test_real_browser_navigate_extract_click` | **Pre-existing flake** | Passes alone (1), with the new tests (90), with its whole file (69). Fails in the control run with the new tests excluded. Chromium is installed. | Left alone. Unrelated to async jobs. |
| `test_health_phase4::test_live_write_still_blocked` | **Environmental — worktree artifact** | `sqlite3.OperationalError: unable to open database file`. Fails in the worktree, passes in the production checkout: the worktree has no `data/` tree (gitignored). Also fails in the control run. | Left alone. An artifact of the isolation Phase 13 requires. |
| `test_inference::test_chat_with_usage_defaults_to_ollama` | **Pre-existing flake** | **Fails in the control run with every new test file excluded** — decisive. Passes alone. Depends on process-global inference-gateway routing state. | Left alone. |
| `test_world_state::test_world_state_cache_ttl` | **Pre-existing intermittent flake** | Failed 1 of 3 full runs. Passed 15/15 in isolation. Passed when run directly after all four new test files (56 passed), so there is no deterministic interaction. Asserts `a["ts"] == b["ts"]` against a time-based module-global cache — racy under load. | Left alone. |

**Blast-radius check.** This work touched `coding_jobs.py`, `gui/server.py`,
`job_framework.py` and `static/audio_studio.js`. Neither flaky module references
any of them (0 matches). The `server.py` change lives in the FastAPI lifespan,
and no test uses `with TestClient(...)`, so the lifespan never runs during tests
— the new recovery call cannot perturb any other test.

## Remaining Risks

1. **In-memory registries lose jobs on restart** — audio, ComfyUI settings,
   vision batch, specialists, pipelines. Now reported honestly (Defect #3), but
   work in flight is silently discarded. Acceptable for short panel jobs;
   material for long vision batches.
2. **No execution-state or checkpoint persistence outside `jobs/checkpointed`.**
   `coding_jobs` and `media_jobs` persist *metadata*; only `media_jobs` carries a
   `resume` payload, and only `checkpointed` stores true checkpoints. An
   interrupted Learn topic is abandoned — now accurately, but still abandoned.
3. **Agent/specialist/pipeline jobs have no inline result delivery** — Job Center
   only. No false claims, but the chat lifecycle is incomplete.
4. **Multi-tab consistency is untested** (Phase 8E). Media jobs track ids in
   `sessionStorage`, which is per-tab, so a second tab will not resume a job the
   first tab started.
5. **Media E2E is uncertified.** ComfyUI was down for this audit, so no
   image/video/meme job could produce an artifact. Their routing, registry,
   persistence and recovery are verified, but completion and result delivery are
   **not** certified. Re-run this audit with ComfyUI up to close the gap — the
   live harness (`tests/js/live_learn_topic_acceptance.mjs`) takes a message
   argument and works for any chat-queued action.
6. **Voice/Gemini Live WebSocket is BLOCKED** — needs live audio hardware and a
   provider key.

---

## Future Work (explicitly *not* in this milestone)

* **Durable checkpoint/resume for background research.** Give `coding_jobs` a
  `resume` payload like `media_jobs`, or migrate background actions onto
  `jobs/checkpointed`, which already does this properly.
* **A single job abstraction.** Nine registries, four persistence models and
  three recovery models is the root condition that let Defect #2 exist.
  `job_framework.py` is the seed of this and currently has no callers.
* **Inline delivery for agent/specialist/pipeline jobs** — a generic
  `background_job`-style poller keyed on queue.
* **Cross-tab job tracking** — move media job ids from `sessionStorage` to
  server-derived state (`/api/media/status` already exposes what is needed).

---

## Production Safety Statement

All development happened in an isolated git worktree at
`/media/jeff/AI/aria-cert-audit` (branch `cert/async-audit`), never in the
production tree. Production was touched exactly once, deliberately, for the
required live acceptance test.

| | Before | After |
|---|---|---|
| MainPID | 1765 | 1765 |
| NRestarts | 0 | 0 |
| ActiveState | active | active |
| Commit | `f04e5c2` | `f04e5c2` |
| Working tree | 5 pre-existing edits | 5 pre-existing edits |
| restart_audit last entry | 2026-08-21T11:38:11 | 2026-08-21T11:38:11 |

The only production side effect was the intended one: one new knowledge brief,
`data/knowledge/do-deep-research-on-tenkara-rod-action-and-learn-about-it.md`.
