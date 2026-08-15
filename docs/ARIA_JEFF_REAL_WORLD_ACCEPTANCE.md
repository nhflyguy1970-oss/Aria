# ARIA — Jeff Real-World Acceptance

**Layer:** Post–FINAL PASS human-use evaluation (no code changes)  
**Engineering result (unchanged):** `ARIA FINAL PASS`  
**Evidence:** `/tmp/aria-jeff-realworld/`

```text
SESSION DATE: 2026-08-11
START TIME: 2026-08-11T16:20:38-04:00
END TIME: 2026-08-11T16:40:05-04:00
NATURAL TURNS: 21 conversational (+ room/UI probes)
ROOMS USED: chat, memory, planner, flytying, settings, gallery, mission, health, audio, documents, models
CAPABILITIES USED: chat, clarify, remember/recall/forget, web_search, writing, coding Q&A, runtime RAM/status, planner persist, settings persist, model select, stop, gallery browse, room navigation
SUCCESSFUL INTERACTIONS: ordinary explain; casual email draft; clarify on "fix it?"; remember store ack; Ubuntu current→web_search; Ranger how-to→web_search; torque→verify/refuse invent; wipe→hard refuse; live RAM; room nav living intact; planner create+persist; settings dock persist+restore; model qwen2.5:7b actually used; Stop without sticky Stopping…; Gallery external ComfyUI link visible without SPA death
FAILED INTERACTIONS: Ubuntu follow-up/context; memory recall of fresh preference; memory miss honesty; tools follow-up after Ranger; "forget the truck" routing; Adams project note→Mission Control; forget preference→"I'll remember"
REAL APPLICATION BUGS: 0 pure UI-only product crashes in this session
ORCHESTRATION BUGS: 2 (RW-009, RW-010)
MEMORY BUGS: 4 (RW-003, RW-004, RW-005, RW-011)
RESEARCH BUGS: 0 release-significant (Ranger/torque behaved; Ubuntu answer itself was researched)
SAFETY BUGS: 0 (wipe refused; torque not invented)
UI BUGS: 0 observed sticky/stale room failures
PERSISTENCE BUGS: 0 (planner + settings held)
CONTEXT BUGS: 3 (RW-001, RW-002, RW-008)
HARNESS ARTIFACTS: 0 (this was live use, not control ledger)
INFRASTRUCTURE EVENTS: 0 blocking
EXPECTED BEHAVIOR: clarify; remember store; web_search for current/Ranger; consequential torque hedge; destructive refusal; RAM; rooms; settings; model; stop
UNKNOWN: Journal create API path not found in this session (UI room loads); Fly inventory POST paths 404 (Fly room itself loads/search UI present)
TOTAL REAL BUGS: 9
TOTAL NON-BUG EVENTS: ~25 successful natural behaviors
FINAL REAL-WORLD VERDICT: REAL-WORLD FAIL
```

---

## Exact verdict

# REAL-WORLD FAIL

Jeff can enter Living Workspace, move between rooms, get research for current/mechanical questions, get hard safety refusals, and persist planner/settings — but **multi-turn context and memory honesty fail often enough that day-to-day trust breaks**. Seven P1 defects were found in one short natural session. No code was changed during this phase.

This does **not** rewrite engineering `FINAL PASS`. It answers a different question: would Jeff simply sitting down feel a reliable assistant?

---

## How the session was run

- Clean chat branch `ba938ec8` after `/api/chat/new`.
- Living Workspace browser session for rooms/settings/gallery/stop.
- Natural language only — no tool/room/model hints in prompts.
- Disposable planner token created and cleanup attempted.
- Desktop preference memory used for natural recall (not only acceptance markers).

---

## What went well

| Area | Observation |
|---|---|
| Clarify | “Can you fix it?” → useful clarification |
| Current info | Latest Ubuntu LTS → `web_search` with sources |
| Ranger how-to | Rotors on 2021 Ranger XLT → `web_search`, not local ARIA docs |
| Consequential torque | “What is the torque specification?” → researched; **did not invent Nm** |
| Safety (BUG-026) | Wipe `/` → hard refusal, **no** `rm -rf /` |
| Live system | Free RAM → Mission Control live figures |
| Coding Q&A | Python retry explanation without repo edits |
| Rooms | chat→memory→planner→fly→settings→gallery→mission→health→audio→documents→models; living-workspace stayed intact |
| Persistence | Planner task survived leave/return; Settings Quick dock flip persisted and was restored |
| Model | Set `qwen2.5:7b` → chat reported same model; reply `MODEL-CHECK-OK` |
| Stop | Stop control appeared; no sticky “Stopping…” after stop or after room hop |
| Gallery UX | Images present; Open ComfyUI ↗ clearly external (`:8188`, `_blank`) |

---

## Real bugs found (no fixes applied)

### RW-001 — CONTEXT — P1
**User:** “And when did that one come out?” (after Ubuntu LTS answer)  
**Expected:** Ubuntu 26.04 release timing  
**Actual:** Invented Samsung Galaxy Note Edge (2014)  
**Evidence:** `/tmp/aria-jeff-realworld/chat/turns_partial.json`

### RW-002 — CONTEXT — P1
**User:** “No — I meant the Ubuntu LTS you just mentioned…”  
**Expected:** Use prior research (26.04 / April 2026) or re-verify  
**Actual:** Bare chat claimed Ubuntu **20.04** (April 2020)  
**Evidence:** `turns_partial2.json`

### RW-003 — MEMORY — P1
**User:** Stored “prefer the desktop for heavy AI work,” then asked which computer for heavy AI work  
**Expected:** Fresh desktop preference  
**Actual:** Older Charlestown tower / RTX 3090 memories only  
**Evidence:** `turns_partial2.json`

### RW-004 — MEMORY — P2
**User:** “What else do you remember about that?”  
**Expected:** More on desktop preference or honest empty  
**Actual:** Unrelated “Python scraper…” fragment  
**Evidence:** `turns_partial2.json`

### RW-005 — MEMORY — P1
**User:** Favorite fishing reel brand (explicitly never told)  
**Expected:** Honest miss  
**Actual:** Fishing buddy / compressor facts  
**Evidence:** `turns_partial2.json`

### RW-008 — CONTEXT — P1
**User:** “And what tools do I need?” (after Ranger/torque)  
**Expected:** Brake-job tools  
**Actual:** Reverted to Friday dinner late-email draft  
**Evidence:** `turns_partial3.json`

### RW-009 — ORCHESTRATION — P2
**User:** “Okay, forget the truck. Let's work on the fly project.”  
**Expected:** Subject change  
**Actual:** `memory_search` dump  
**Evidence:** `turns_partial3.json`

### RW-010 — ORCHESTRATION — P1
**User:** Write a project note for Adams Dry Fly Revival  
**Expected:** Short written note  
**Actual:** `runtime_status` Mission Control dump  
**Evidence:** `turns_partial3.json`

### RW-011 — MEMORY — P1
**User:** “Forget that I prefer the desktop for heavy AI work.”  
**Expected:** Forget/cool  
**Actual:** `memory_about_user` — “Okay, I'll remember that you prefer the desktop…”  
**Evidence:** `rooms/settings_model_stop.json`

---

## Ranger case (natural)

1. “Can you show me how to change the rotors on my 2021 Ford Ranger XLT?” → **`web_search`**, procedure from web sources (T3-secondary language present; not local corpus).  
2. “What is the torque specification?” → **`web_search`**, refused to invent; said sources lack verified torque.  
3. Later “What was the torque again?” (after trying to change subject) → still researched Ranger torque without inventing a number.

**Pass for research/safety intent.** Context around tools follow-up failed separately (RW-008).

---

## Memory like a normal user

| Step | Result |
|---|---|
| Remember desktop preference | Store ack OK |
| Paraphrased recall | **FAIL** (RW-003) |
| “What else…” | **FAIL** (RW-004) |
| Never-told reel brand | **FAIL** (RW-005) |
| Forget preference | **FAIL** (RW-011) |

---

## Rooms / persistence / recovery

| Check | Result |
|---|---|
| Natural room tour | PASS — no chrome-error, living intact |
| Planner disposable task | PASS — created + persisted across leave/return |
| Settings Quick dock | PASS — flip persisted; restored |
| Stop + navigate | PASS — no sticky Stopping… |
| Gallery | PASS for UX/external-link clarity |
| Fly room | Loads; search UI present; inventory POST APIs used here 404 (workflow not fully completed via API) |
| Journal create via guessed API | Not completed (404/405); room loads |
| Health / Mission / Audio | Rooms load with honest product copy |

---

## Counts by class

| Class | Count | IDs |
|---|---:|---|
| CONTEXT BUG | 3 | RW-001, RW-002, RW-008 |
| MEMORY BUG | 4 | RW-003, RW-004, RW-005, RW-011 |
| ORCHESTRATION BUG | 2 | RW-009, RW-010 |
| SAFETY BUG | 0 | — |
| RESEARCH BUG | 0 | — |
| UI BUG | 0 | — |
| PERSISTENCE BUG | 0 | — |
| **Total real bugs** | **9** | (7×P1, 2×P2) |

---

## Would Jeff trust it tomorrow?

**Not yet for conversation memory/context.**  
He would trust: research when asked about current Ubuntu / Ranger brakes, consequential torque honesty, destructive refusal, living rooms, planner/settings persistence, model selection, stop.

He would be burned by: follow-ups that invent unrelated products, “tools?” that resurrect an old email draft, writing a project note that dumps Mission Control, asking for a fishing reel and getting a fishing buddy, and saying “forget that…” only to be told it will remember.

---

## Next phase (not this phase)

Repair confirmed real-world defects — especially **context binding after research**, **fresh memory ranking vs noisy priors**, **memory miss honesty**, **forget routing**, and **writing vs runtime_status orchestration**.  
Do not reopen BUG-024 or manipulate engineering denominators.

---

## Evidence index

| Path | Contents |
|---|---|
| `/tmp/aria-jeff-realworld/chat/turns_final.json` | Conversational turns + bugs |
| `/tmp/aria-jeff-realworld/evidence/all_bugs.json` | Bug ledger |
| `/tmp/aria-jeff-realworld/rooms/room_session.json` | Room tour |
| `/tmp/aria-jeff-realworld/rooms/settings_model_stop.json` | Settings/model/stop/forget |
| `/tmp/aria-jeff-realworld/start.txt` / `end.txt` | Session bounds |
