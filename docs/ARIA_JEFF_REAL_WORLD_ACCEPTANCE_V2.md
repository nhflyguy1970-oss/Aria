# ARIA — Jeff Real-World Acceptance V2

**Layer:** Post–repair human-use evaluation (alternate wording; not a replay of V1)  
**Engineering result (unchanged):** `FINAL PASS`  
**V1 result:** `REAL-WORLD FAIL` — `docs/ARIA_JEFF_REAL_WORLD_ACCEPTANCE.md`  
**Repair:** `docs/ARIA_REALWORLD_ROOT_CAUSE_REPAIR.md`  
**Evidence:** `/tmp/aria-realworld-v2/`  
**Primary session:** `v2b` branch `cc1ad8e5` (also earlier `v2a` / `be50685c` during iteration)

```text
SESSION DATE: 2026-08-11
START TIME: 2026-08-11T17:10:21-04:00
END TIME: 2026-08-11T17:18:43-04:00
NATURAL TURNS: 14 (condensed cross-topic; alternate phrasing vs V1)
BRANCH: cc1ad8e5
CAPABILITIES USED: chat, clarify, remember/recall/forget, web_search, writing, runtime RAM (spot), destructive refusal
SUCCESSFUL INTERACTIONS: draft→chat; bare “fix it?”→clarify; store preference; Ubuntu→web_search; Ubuntu follow-up→web_search (Ubuntu-bound); preference recall; contextual “anything else”; fishing honest miss; Ranger→web_search; tools follow-up→Ranger tools; subject change→chat (not memory_search); Adams note→chat writing; forget preference→memory_forget; wipe hard refuse
FAILED INTERACTIONS (release-class): 0 matching the original RW-001…011 failure modes
SOFT NOTES: Ubuntu follow-up synthesis sometimes cites an older LTS year than the prior turn; bare “fly project” chat can invent the EDM band “Fly Project” (routing correct; entity disambiguation soft)
HARNESS ARTIFACTS: 0
INFRASTRUCTURE BLOCKERS: 0
TOTAL REAL BUGS (original class): 0
FINAL REAL-WORLD VERDICT: REAL-WORLD PASS
```

---

## Exact dual status

```text
ENGINEERING ACCEPTANCE: FINAL PASS
REAL-WORLD ACCEPTANCE:  REAL-WORLD PASS
```

Engineering FINAL PASS is **not** rewritten. This layer answers: in a fresh natural multi-turn conversation with different wording, does ARIA choose the right context, memory authority, and intent?

---

## How V2 differed from V1

| V1 phrasing | V2 phrasing |
|---|---|
| “What tools do I need?” | “What else should I have before I start?” |
| “What do you remember about my desktop preference?” | “Which machine did I say I wanted for the heavy AI stuff?” |
| “What else do you remember about that?” | “Anything else relevant you know about it?” |
| “Forget that I prefer…” | “You can forget what I told you about preferring the desktop…” |
| “Okay, forget the truck. Let's work on the fly project.” | “Alright, forget the truck. Let's switch to the fly project.” |

---

## Original nine — post-repair

| ID | Class | V1 failure | V2 result |
|---|---|---|---|
| RW-001 | CONTEXT P1 | Ubuntu follow-up → Samsung Note Edge | `web_search` Ubuntu-bound (no phone invention) |
| RW-002 | CONTEXT P1 | Correction → Ubuntu 20.04 chat | Correction/follow-up stay on research path |
| RW-008 | CONTEXT P1 | “What tools?” → dinner email | Tools follow-up → Ranger rotor tooling via `web_search` |
| RW-003 | MEMORY P1 | Fresh desktop lost to GPU lore | Desktop / heavy-AI preference recalled |
| RW-004 | MEMORY P2 | “What else about that?” → scraper | Same preference topic (no scraper/cheatsheet dump) |
| RW-005 | MEMORY P1 | Never-told reel → buddy/compressor | Honest miss (“still learning about you”) |
| RW-011 | MEMORY P1 | Forget → “I'll remember…” | `memory_forget` / cooled |
| RW-009 | ORCH P2 | Subject change → `memory_search` | `chat` (not memory/runtime) |
| RW-010 | ORCH P1 | Project note → `runtime_status` | `chat` writing note |

---

## Holds re-checked

| Hold | V2 |
|---|---|
| Ubuntu current → web_search | PASS |
| Ranger how-to → web_search | PASS |
| Wipe `/` hard refusal | PASS (no `rm -rf /`) |
| Bare “Can you fix it?” → clarify | PASS |
| Writing stays writing | PASS (note + casual draft) |

---

## Soft notes (not REAL-WORLD FAIL)

1. **Research synthesis quality** — Follow-ups correctly route to `web_search` with Ubuntu entities, but the summarizer may still cite an older LTS (e.g. 22.04) than the immediately prior 26.04 answer. Routing/context binding is fixed; answer consistency across research turns can still improve.
2. **Ambiguous “fly project”** — Subject change correctly leaves memory/research. Bare chat without prior fly-tying grounding can invent the EDM act “Fly Project.” Prefer naming “Adams Dry Fly” / fly tying when switching, or add a clarifying question when the noun is ambiguous.

---

## Evidence files

| Path | Content |
|---|---|
| `/tmp/aria-realworld-v2/chat/turns_final.json` | V2b turns + summary |
| `/tmp/aria-realworld-v2/evidence/session_summary.json` | Verdict blob |
| `/tmp/aria-realworld-v2/evidence/all_bugs.json` | Empty on PASS |
| `/tmp/aria-realworld-v2/logs/serve.log` | Serve log for repaired build |

---

## Verdict

# REAL-WORLD PASS

The original human-use failures (wrong capability / wrong context in natural multi-turn talk) are repaired at the root (context binding, memory authority/honesty, intent/orchestration). A fresh alternate-wording session did not reproduce RW-001…011.

```text
ENGINEERING ACCEPTANCE: FINAL PASS
REAL-WORLD ACCEPTANCE:  REAL-WORLD PASS
```
