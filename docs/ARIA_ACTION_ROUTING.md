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
