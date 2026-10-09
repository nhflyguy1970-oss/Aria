# Coding agents under ARIA supervision — Phases 5–6

Measured state: [Phase 6 final certification](ARIA_PHASE6_RECOVERY.md). **Codex is verified in disposable development fixtures. Claude Code and Antigravity are disabled.** Production is unchanged. Read [sandbox/approval guarantees](ARIA_PHASE6_SANDBOX.md) before activation.

## Installed interfaces

| Agent | Version verified | Execution interface | Authentication / availability |
|---|---|---|---|
| Codex | 0.161.0 | `codex app-server`, JSON-RPC `thread/start`, `turn/start`, explicit `externalSandbox` | Existing ChatGPT subscription; current-code real task verified |
| Claude Code | 2.1.295 | Shipped native binary, `--print --output-format stream-json`, normal permission/tools modes | claude.ai Pro recognized; actual request returns weekly-quota 429; disabled |
| Google Antigravity (`agy`) | 1.3.2 | `--print --output-format stream-json --mode plan\|accept-edits --sandbox --print-timeout` | Current isolated request enters interactive OAuth and hits 60-second wall timeout; historical violation retained; disabled |

Claude's npm wrapper is broken; discovery uses the native binary already shipped alongside it. Nothing was reinstalled. Version/help/auth probes run in a no-network private-root sandbox; prompts run only inside an approved disposable OCI workspace. Authentication files are privately copied, not shared writable or read out to users. Installed flags are checked; a version/policy/native-binary certificate invalidates on change.

The old `codex exec` native sandbox cannot nest under the required outer boundary on this host. ARIA now uses Codex's external-sandbox protocol and enforces the whole process tree with OCI. There is no bare-process fallback or dangerous bypass flag. This is an explicit adapter architecture, not a silent sandbox downgrade.

Subscription auth does not activate Phase 4's paid adapters. API keys and SSH/Git credentials are absent. Codex checks account type `chatgpt`; Claude overage remains disabled. No paid API purchase or fallback is permitted. There is no IDE/GUI automation, spending-cap claim for subscription plans, or host keychain exposure. Claude's reported quota reset is 2026-10-11 07:00 UTC; eligibility requires a new safe check, not elapsed time alone.

## Contract, approval and supervision

Every run separates:

- **requested**: the approved plan;
- **attempted**: agent events/commands, labelled as its report;
- **changed**: independently collected workspace diff;
- **tests_run**: ARIA's no-network independent verification;
- **verified**: facts those observations establish;
- **unverified**: the agent's claims, with contradictions retained.

`verified` requires actual changes and passing ARIA verification. `completed` is a read-only task with a report; findings remain unverified. Other states include `no_changes`, `changes_unverified`, `tests_failed`, `boundary_violation`, `failed`, `timeout`, `cancelled`, `interrupted` and `refused`. Quota exhaustion is an availability error, not an invented correctness failure. Raw unsuccessful benchmark attempts remain visible.

Chat/API proposes a plan. An owner-only approval nonce, expiry and plan hash authorize one execution. Safe mode, autonomy and mission/coding capabilities are checked again at execution. Cross-process launch reservation allows one run at a time. A project name alone never starts work. The approved hash includes canonical project path, protected paths, verification command and allowed agents. Changed settings or old unbound approvals require a new proposal; they never clone a newly substituted source. All actual commands and descendants run in the approved container; read-only requests have a read-only workspace. Independent tests run under private-root/no-network bubblewrap. There is no push, commit or automatic application into the source project.

Resources are enforced through OCI cgroups: 6 GiB memory/swap, four CPUs, 512 processes, bounded tmpfs and wall time. Logs are redacted, capped at 4 MB and flushed to controller-private paths. Current CPU/RSS telemetry measures the controller client; container limits are separate receipt fields, not claimed measurements of the full agent tree.

Cancellation removes the run-labeled container and its detached descendants. Restart recovery marks dead-owner runs interrupted and removes only their recorded containers; it never silently resumes them. Cleanup failure blocks further execution. A worker watchdog bounds abandoned containers even before ARIA restarts. A resumed task is a new proposal requiring approval.

## Projects and promotion

The development registry contains ARIA (`aria`), FTR (`fly-tying-reference`) and BlackFly (`blackfly`), with distinct namespaces, explicit Git paths, test commands and protected paths. ARIA points at the Phase 6 worktree. Production registration is unchanged. Registration does not index the repository or write ACM. Empty project agent allow-lists add no agent-specific restriction; runtime eligibility remains mandatory.

Projects are resolved from registry records, never guessed from a chat name. Candidate paths can be shown with their evidence if registration is missing. Agents operate in clones of committed HEAD and cannot see other production projects or datasets. Trusted toolchains are read-only; agents cannot authorize a new host mount by replacing a clone symlink.

Approving an agent plan permits only the disposable run. Promotion is a distinct decision:

1. Capture binary diff, base/new hashes and a file manifest using sandboxed untrusted Git.
2. Reject protected data, credentials, env, symlink/submodule and service/venv paths; flag deletions, binary/mode changes and migration risks. Do not execute migrations.
3. Apply to a fresh destination-HEAD clone and run independent tests.
4. Present destination branch/HEAD, files, test evidence, risks and patch hash.
5. Require a separate owner-only, single-use promotion approval.
6. Lock destination and recheck registration, branch/HEAD, touched dirty files, manifest and conflicts.
7. Save exact recovery snapshots, apply without a three-way merge, verify and roll back on failure.
8. Record outcome and rollback. Refuse rollback over later owner edits; restore interrupted applications rather than repeat them.

Tests cover successful, rejected, expired, replayed, conflicting, protected-path, failed-verification and interrupted cases. A real Codex-produced fixture patch was promoted and rolled back in a disposable destination with unrelated dirty content preserved. No production promotion was made.

## Benchmark scoring and selection

| Agent | Standard safety-qualified | Hard safety-qualified |
|---|---:|---:|
| Codex | 16/16 | 12/12 |
| Claude Code | 16/16 | 7/12 |
| Antigravity | 15/16 | 12/12 |

These are preserved live results audited offline, not rerun tasks. Fixture completeness, content correctness, original unsuccessful attempts, capacity errors and historical safety findings remain distinct. Safety-qualified fixture scores do not certify the old sandbox. Two diagnostic reruns are reported separately, not substituted into standard results. See the final report for raw/corrected results, exact fixture hashes and latency.

Selection requires installation, supported mode, subscription authentication, project permission, a current measured execution certificate, available quota and reviewed boundary history. A named request skips ranking, **never safety/compatibility gates**. New history or implementation/CLI changes invalidate qualification. A live boundary verdict immediately quarantines the adapter. Eligibility also reads durable run history, refusing unreviewed violations and unreadable/corrupt history even if a certificate update was interrupted. Missing certificates disable execution.

Eligible candidates rank by task-specific correctness, sample strength (at least two samples for strong evidence), structured reliability/timeouts, latency and available resource measurements. Hard categories contribute to the corresponding base kind. Correctness refreshes cannot erase historical violations or receipt IDs. Currently Codex alone qualifies in development; production has no new runtime certificate. Claude and agy cannot be automatically selected or forced by name.

`--simulate` validates the benchmark harness with a known fixture executable; its offline certificate override is scoped to that executable and cannot qualify real agents. Completed real benchmarks are preserved. Quota signals stop further benchmark attempts rather than manufacturing capability comparisons.

## Durable coding continuity

`jarvis/coding_agents/history.py` builds history from durable execution/promotion receipts: proposed, approved, in progress, completed, independently verified, awaiting promotion, applied, unverified changes, failed/cancelled/interrupted/rejected/rolled back. Owner questions about accomplishments, files changed, pending approvals or interrupted tasks are answered from those records, with agent claims explicitly labelled unverified.

Plans create proposals; runs and promotions create outcomes/checkpoints in the continuity store. ACM remains memory authority and is not written by this subsystem. Context pruning does not delete durable chat history. A two-process probe reopens all 400 recorded turns with bounded context eight and restores timer follow-up confirmation.

Implementation: `jarvis/coding_agents/`; handlers `jarvis/handlers/coding_agent_cli_handlers.py`; API `/api/coding-agents/*`. [Deployment checklist](ARIA_PHASE6_DEPLOYMENT_CHECKLIST.md), [test and skip evidence](evidence/phase6_certification/test_results.json).
