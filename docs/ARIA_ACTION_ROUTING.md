# ARIA action routing (Phase 5)

## What was wrong

The structural NLU stage answers `chat` for many plain commands, and when it
does, orchestration policy could turn the request into `web_search`. Nothing
after that ran — the quick route was consulted only for an allow-list of
coding/media actions, and the 444-action LLM router (a ~7,200-token prompt)
was never reached. Measured on a labelled corpus: 60/100 correct, 3/17
correct arguments, 5 side-effecting misroutes, 0 clarifications.

The three confirmed misroutes and their causes:

| Request | Was | Cause |
| --- | --- | --- |
| "Wake me at 5:30" | chat / web_search | NLU chat default → policy web_search |
| "Add X to my to-do list" | planner_today | natural-intent rule matched "to-do list" before "add" |
| "12-minute timer" | chat | NLU chat default; "12-minute" not parsed |

Other defects found and fixed on the way:

- "edit the image to add falling snow" became an inpaint with no region (now `edit_image`).
- "what's the status of mission X" went to `runtime_status`, and "what's my CPU load" to `runtime_gpu`.
- Any message *containing* "do it" or "go ahead" routed to `apply_proposal`. Examples: "I don't know how to do it", "do it again". Bare confirmations now apply only a proposal this conversation holds; an explicit "apply …" is unchanged.

## What routing does now (`jarvis/action_routing.py`)

Before the natural-intent stage and NLU, in order:

1. **Follow-ups** bound to the previous turn's action, held in the session's `last_action`. The binding lasts 15 minutes and survives a session restore. Examples:
   - "actually make it 15" after a timer;
   - "and on Sunday?" after a forecast;
   - "one more: wax the line" after adding a task.
   - "Run it again" repeats an info action, but a side-effecting one needs a yes/no first.
2. **Deictic clarification**: "delete it", "turn it off" or "move it to tomorrow" with nothing for "it" to mean gets a question, not a guess.
3. **Rules**: high-precision patterns with argument extraction.
   - Covered: timers, reminders, alarms, tasks, calendar events, missions (cancel, pause, status, list), song, play, draw, inpaint, transcribe, home switches, CPU/RAM, document search, "fix X in file.py", planner review, and coding-agent requests.
   - A missing essential (no time, no duration, no file) produces a clarifying question.

Every intent from these stages carries a `routing_receipt` with the method, the stage, and the candidates/model/tokens when the model was involved.

**Shortlist + small model (off by default).** Where NLU fell back to chat, a BM25 ranking over registry metadata, curated aliases and the router training samples picks at most 6 candidates. The router-role model then chooses among them plus `chat` and `clarify`. A side-effecting choice becomes a yes/no confirmation. To enable: `JARVIS_ROUTER_SHORTLIST_MODEL=1`.

It is off because it did not help:

| Configuration | Original corpus | Held-out | Model calls | Worst latency |
| --- | --- | --- | --- | --- |
| Off (production) | 99/100 | 58/66 | 0 | 0.4 s |
| qwen3:1.7b | 98/100 | 57/66 | 31 | 65 s (cold load) |
| ministral-3:3b | 98/100 | 58/66 | 34 | 57 s (cold load) |

The chooser on its own, scored on 154 shortlisted cases (`scripts/routing_model_eval.py`, each model pinned):

| Model | Accuracy | Wrong action | Wrong side-effect | p50 |
| --- | --- | --- | --- | --- |
| qwen3:1.7b | 49.4% | 11.7% | 14 | 41 ms |
| ministral-3:3b | 68.2% | 11.7% | 10 | 52 ms |
| qwen3:4b-instruct | 66.9% | 23.4% | 26 | 82 ms |
| gemma3:4b | 70.8% | 21.4% | 25 | 150 ms |
| qwen3:8b | 77.9% | 14.9% | 15 | 115 ms |
| granite4.2:3b, llama3.2:3b, qwen2.5:3b, nemotron-3-nano:4b | 54–60% | 19–30% | 16–30 | 58–194 ms |

The shortlist held an acceptable action in only 70 of 154 cases. Every model picked a wrong side-effecting action at least 10 times. The router model assignment was therefore not changed (it remains qwen3:1.7b).

> Pitfall: ARIA's execution policy answers every `router` call with the configured router model, whatever model was requested. Benchmarks must pin with `JARVIS_EXECUTION_MODEL`; the eval script records the model that actually served each row.

## Results

`scripts/routing_benchmark.py` runs the corpora through the real `route()`:

- `tests/fixtures/routing_corpus.py`: 100 cases, assembled while the failures were being studied.
- `tests/fixtures/routing_corpus_heldout.py`: 66 cases, labelled before scoring and not used for tuning.

| | Baseline | Phase 5 |
| --- | --- | --- |
| Original corpus | 60/100 | 99/100 |
| Held-out (frozen first run) | 34/66 | 58/66 |
| Held-out (final) | 34/66 | 59/66 |
| Correct arguments | 4/30 | 30/30 |
| Side-effecting misroutes | 10 | 2 |
| Model calls | 0 | 0 |

The final held-out score includes one fix made after seeing it ("move it to tomorrow").

Remaining held-out failures:

| Request | Result |
| --- | --- |
| "do deep research overnight on bushcraft" | `web_search` (policy) |
| "start my truck" | `web_search` (policy) |
| "Describe this image." / "Summarize this document." | `chat` without an attachment |
| "Promote an actionable Journal note into a Planner task" | `planner_today` (planner-review rule too broad) |
| "what is a to-do list app called…" | `planner_today` (old natural-intent rule) |
| "cancel it" | the reflex layer's "Stopped." |

## Permissions

Routing only picks an action; nothing runs at routing time. Phase 1 policy and per-action guards apply at execution whichever stage produced the intent. Tests cover a rule-routed mission action under safe mode, and `coding_agent_execute` reached by any route without the owner's approval token.

---

# Phase 6

## Fixed

| Request | Phase 5 | Phase 6 |
|---|---|---|
| "Do deep research overnight on bushcraft" | `web_search` | `research_create` (mission-backed research job) |
| "Start my truck" (and booking, paying, messaging, social posting, merchant orders) | `web_search` / chat that could pretend | chat with a fixed, honest "no integration is connected" reply; policy override can no longer rewrite it |
| "Describe this image" / "Summarize this document" with nothing attached | chat | asks which image/document; uses the session's last image/document when there is one |
| "Promote an actionable Journal note into a Planner task" | `planner_today` | asks which note (planner-review rule narrowed) |
| "What is a to-do list app called…" | `planner_today` | chat (the old natural-intent rule now skips conceptual questions) |
| "Cancel it" with nothing running | "Stopped." | names the real cancellables (timers, alarms, agent runs, missions) as choices, or says nothing is running; a reply in flight is still stopped |
| "the image of the river in my head is vivid" | **`generate_image`** | chat ("image of" must be a request) |
| "what's your favourite dubbing?" | `memory_search` | chat (preference rule requires *my*) |

## Timer and alarm follow-ups

- "set a timer for 10 minutes" … "actually make it 15" → `planner_update_timer` changes **that** timer (now 15 minutes from now) and says no second timer was started. Alarms work the same way (`planner_update_alarm`).
- The timer is identified by the label the previous turn created. If it has finished, ARIA says so and creates nothing. If several timers match, it asks which.
- After a restart, a follow-up that would change something asks for confirmation first. `last_action_restored` is set on session restore and is never persisted.

## Results

All deterministic, 0 model calls, p50 about 1 ms:

| Corpus | Phase 5 (production) | Phase 6 |
|---|---|---|
| Original (100) | 99 | **100** |
| First held-out (66; contains the seven failures to fix) | 59 | **66** |
| New held-out (60; labelled before scoring), frozen first run | 45 | 55 |
| New held-out, after fixing the misses it found | 45 | **58** |
| Side-effecting misroutes (all three) | 7 | **0** |

Three Phase 5 labels were widened: "actually make it 15" / "make it 8" / "actually make it 6:30" now also accept `planner_update_*`, which is the behaviour Phase 6 was asked for.

Remaining corpus disagreements:
- Two first-person statements ("I ordered waders from Orvis last week", "I like how BlackFly handles retries") go to the memory layer, by Phase 2's ACM teaching policy.


## Recovery verification — 2026-10-09

The final worktree independently measured 100/100, 66/66 and 58/60 with all 40 checked arguments correct, zero side-effecting misroutes, zero model calls, zero fallback calls and zero errors. Automatic classifier benchmarking and network access were disabled for this check. See [Phase 6 recovery assessment](ARIA_PHASE6_RECOVERY.md) for evidence, fixture-label changes, remaining misses, test totals and deployment blockers.

## Final certification repairs

Imperative requests to investigate, diagnose, debug, trace or inspect software failures now use the engineering investigation route even without a named file. The handler asks for missing file/context rather than inventing a target. Six phrasing variants verify the general rule. Timer/alarm/planner/project/research/cancellation behavior remains covered by regressions.

Final scores are **100/100, 66/66, 58/60**, arguments **40/40**, false side effects **zero**, model/fallback calls **zero**. The two remaining first-person purchase/preference statements retain ACM teaching-policy routing; original chat labels are not silently changed. No model classifier benchmark was rerun or claimed improved. [Final deterministic measurements](evidence/phase6_certification/routing_results.json).

A real two-process restart probe writes 400 turns with model context capped at eight, reopens every archived turn in a new process, and checks restored timer follow-up requires confirmation. Pruning and durable storage are separate. See [final certification](ARIA_PHASE6_RECOVERY.md) for exact tests and readiness.
