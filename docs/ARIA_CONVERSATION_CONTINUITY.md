# ARIA conversation continuity (Phase 2)

How ARIA remembers what was discussed, decided, rejected, corrected and left
unfinished — across context pruning, restarts and model backends — without a
second memory engine.

## Layers

| Layer | Holds | Authority |
| --- | --- | --- |
| `data/conversation_archive/<branch>.jsonl` (Phase 1) | Every user/assistant turn, verbatim, append-only, written before context pruning | What was said |
| `data/continuity.db` (`jarvis/continuity/store.py`) | Index of archived turns (FTS5) plus derived records: ideas, decisions, rejections, corrections, tasks, suggestions, outcomes — each citing its source turns | Rebuildable view; asserts nothing on its own |
| ACM (`data/acm/cognitive.db`) | User statements that carry continuity, encoded with `user_statement` / `user_correction` provenance and an `episode:<id>` tag | ARIA's cognitive memory, unchanged |

ACM's ingestion policy (D046) admits only the user's own statements. Assistant
suggestions, tool reports and mission outcomes therefore stay in the continuity
store, labelled by actor (`user`, `assistant`, `tool`, `mission`). A tool
saying it finished something is a *reported* outcome, never a verified one.

## Flow

1. A turn is archived (Phase 1). The active project is stamped on it.
2. `continuity.ingest.sync_archives` reads new archive lines by byte offset.
   Episode ids are archive event ids, so re-reading cannot duplicate.
3. Each turn is classified lexically (no model load). User decisions and
   rejections settle the assistant suggestion they answer; corrections
   supersede what they correct; "done" closes the matching open task.
4. Qualifying user statements spoken live (not seeded or imported history,
   not test artifacts, not health content) enter an outbox and are encoded
   into ACM. Before encoding, ACM is checked for the episode tag, so a crash
   between encode and acknowledgement cannot double-encode. Failures stay
   queued and are visible in `continuity_status` and `/api/continuity/status`.
5. Missions mirror in as open work or outcomes.

A background thread runs steps 2–5 every few seconds; shutdown runs a final
sync. Retrieval also syncs first, so the latest turn is always visible.

## Retrieval

Continuity questions are recognised without trigger words ("where did we
leave off?", "what did we decide about ARIA?", "remember that fishing app
idea?", "what were we talking about yesterday?"). Direct recall questions are
routed to `continuity_recall` and answered deterministically from the record
with sources. "Continue the project we were discussing" stays a conversation
turn and receives the same retrieved context.

Results are typed: `HITS`, `NO_RECORD`, `UNAVAILABLE`, `PARTIAL`. No record is
said plainly; a failed search is never reported as no record.

## Model backends and privacy

Every backend receives one context block rendered from the retrieval result —
never the database. The block is bounded (~3.5 KB), carries only retrieved,
relevant items, redacts credential-shaped strings, and withholds health
content unless the question is about health. Topic-less questions are scoped
to the active branch, because branches are how the user separates threads.

## Deletion (designed, not exercised on production data)

`continuity.erase.plan_erasure(...)` is read-only and lists every place the
selected turns live: archive lines, index rows, derived records, outbox
entries and linked ACM experiences. It returns a token fingerprinting that
plan. `apply_erasure(plan, confirm=token)` re-plans, refuses if anything
changed, then blanks archive content atomically (recording only *which* ids
were erased), blanks index rows and records derived solely from them, and
soft-forgets linked ACM experiences through ACM's own forget path.

Limitation: ACM's Memory Authority rule (P17) keeps experience bodies;
`legal_erase` audits and cools but does not physically purge. A true purge of
ACM-held text needs an ACM-level change and was out of scope.

## Older history

`continuity.history_import.dry_run(backup_dir)` inventories a backup's
`chat_branches.json` read-only against the live store and the index:
provenance per turn, duplicates (including fork copies), suspected test
artifacts, and the records each turn would yield. `apply_import` requires the
manifest token, writes only a new `import-<backup>.jsonl` archive, marks turns
as imported with approximate (branch-level) dates, and never encodes them into
ACM automatically.
