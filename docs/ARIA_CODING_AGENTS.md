# Coding agents under ARIA supervision (Phase 5)

Code: `jarvis/coding_agents/` (discovery, adapters, workspace, contract, runs, projects, supervisor); chat actions in `jarvis/handlers/coding_agent_cli_handlers.py`; API under `/api/coding-agents/*`.

## What is installed (discovered 2026-10-08, read-only)

| Agent | Executable | Headless interface used | Sign-in | Billing |
| --- | --- | --- | --- | --- |
| Codex CLI 0.161.0 | `~/.nvm/.../bin/codex` | `codex exec --json --sandbox … --cd … --ephemeral -o …` | `codex login status`: ChatGPT | ChatGPT subscription |
| Claude Code 2.1.29x (auto-updates) | npm wrapper broken; platform binary `…/claude-code-linux-x64/claude` | `claude --print --output-format stream-json --permission-mode … --tools … --no-session-persistence` | `claude auth status --json`: claude.ai | Claude Pro subscription |
| Antigravity CLI (agy) 1.3.0 | `~/.local/bin/agy` | `agy --print --output-format stream-json --mode plan\|accept-edits --sandbox --print-timeout` | no auth-status command: *unknown* until a run | Google account |

Notes:

- The `claude` command on PATH fails with "claude native binary not installed": the npm postinstall step didn't run, which also breaks the shell's `grep`/`find` wrappers. Discovery falls back to the platform binary npm ships next to the wrapper. Nothing was reinstalled.
- Discovery keeps only an auth *method* and a billing class. Emails, org names and tokens are never read out of auth output, and credential files are never opened.
- Subscriptions are not API keys:
  - Phase 4's paid adapters never use these logins.
  - Agents run with every `*_API_KEY` stripped from their environment, so a CLI cannot silently fall back to API billing.
  - An agent found signed in with an API key is marked not usable.
- Every flag an adapter relies on is checked against the installed `--help`; a missing flag makes the agent unusable.

**Not supported, and not faked:**

- the Antigravity IDE/GUI (no automation);
- agy auth checks and per-run tool allow-lists;
- Claude Code running shell or tests (no Bash tool is granted; ARIA runs tests itself);
- spending caps on subscription plans (`--max-budget-usd` applies to API billing only);
- any `--dangerously-*`, `danger-full-access`, `bypassPermissions` or `--yolo` flag. The adapters refuse to build these.

## The contract

Each run records six separate things:

- **requested**: what the owner approved;
- **attempted**: the agent's own event stream, labelled as its word;
- **changed**: `git diff` of the workspace against the base commit;
- **tests_run**: run by ARIA in a no-network sandbox;
- **verified**: statements ARIA checked;
- **unverified**: the agent's success claims. Claims that ARIA's tests contradict are listed separately.

`success` is true only for:

- **verified**: changes were made and ARIA's test run passed; or
- **completed**: a read-only task finished within bounds and produced a report. Its findings still count as unverified.

Other outcomes:

- An exit code of 0 with no changes is `no_changes`.
- Changes with no test command are `changes_unverified`.
- Failing tests are `tests_failed`.
- Edits during a read-only task, a protected path changing, or the agent rewriting its own config are a `boundary_violation`.
- Other terminal states: `failed`, `timeout`, `cancelled`, `interrupted`.

## Safety model

**Approval**

- Chat produces a plan only. The owner starts it by replying "yes" or through `POST /api/coding-agents/plans/{id}/approve` (owner `git.write` with step-up).
- Approval needs a nonce that only those two paths hold. It is single-use and expires after 30 minutes.
- `runs.plan_id` is UNIQUE, so one approval gives one execution.

**Execution policy**

- Each run is a mission of kind `coding_agent` that needs both the `mission` and `coding` capabilities. Safe mode, or the `assisted` autonomy level, refuses it.
- One run at a time.
- Timeouts are capped by the autonomy level's runtime bound. Output is capped at 4 MB.

**Isolation**

- Each run gets a shallow clone of the project's committed HEAD in `../aria-agent-workspaces/`, outside ARIA's code and data.
- The clone's push URL is `no-push://`. `SSH_AUTH_SOCK` and `GIT_*` credentials are stripped.
- Nothing is applied to the real project.
- The agent runs under bubblewrap:
  - read-only root;
  - writable workspace, run output directory and the agent's own state directory;
  - private `/tmp`.
- As a result, FTR and BlackFly production data are not writable by the agent at all.
- Protected paths are fingerprinted before and after the run.

**Restarts**

- A run that ARIA loses track of becomes `interrupted` and is never re-run.
- "Resume the unfinished task" proposes a new plan, which again needs approval.

**Delegation**

- An agent's recommendation can at most become a *proposal*, at depth 1. A deeper chain is refused.

**Other entry points**

- `tool_execute` refuses `claude_code`, `codex` and `antigravity`, and auto-selection no longer picks `claude_code`.
- The Claude Code health probe no longer sends a prompt: it reports version and sign-in only.

## Projects and continuity

- Projects come only from ARIA's project registry, where a git path must be owner-confirmed.
- ARIA, Fly Tying Reference and BlackFly are recognised *by name*. If one isn't registered, ARIA says so and shows the candidate location with its evidence:
  - FTR: `/media/jeff/C/fly_tying_reference`, from `ftr-backup`'s `APP_DIR`;
  - BlackFly: `/media/jeff/C/fly_fishing_project`, from the `blackfly-scraper` launcher;
  - ARIA: the directory it runs from.
- **None of these are registered.**
- Registration, with an optional test command and protected paths: `POST /api/coding-agents/projects`.
- A project name in conversation never starts or proposes work. Only a request directed at an agent ("Ask Codex to…", "Have Claude review…") or "Continue working on X" / "Resume the unfinished task" produces a proposal.

Continuity (Phase 2 store, never ACM):

- a `suggestion`/proposed record per plan, accepted or rejected by the owner;
- a tool-actor `outcome` per run, marked `verified` only for verified completion, with agent claims labelled "Agent reported (unverified)";
- a `checkpoint` per run.

Reports such as "what did the coding agents accomplish yesterday" are built from the execution receipts.

## Selection and benchmark

`scripts/coding_agent_benchmark.py` builds disposable fixture repos. Each agent goes through the production plan → mission → sandbox → verification path. Every one of the 8 categories has its own check:

| Category | Check |
| --- | --- |
| Comprehension | expected facts appear in the report |
| Diagnosis | the off-by-one is identified, with no edits |
| Repair | ARIA's tests pass |
| Test creation | tests pass, and fail against a mutated function |
| Code review | the SQL injection is flagged |
| Refactor | no old name remains and tests pass |
| Docs | README flags match the CLI |
| Permission compliance | the in-scope fix is made and an out-of-workspace canary is untouched |

`--simulate` validates the harness with the simulated agent: the honest one scored 8/8, a claims-only agent 0/8, and the outside write was blocked.

**Live runs have not been made.** They use the owner's subscriptions and need explicit permission.

The supervisor selects the best *measured* agent per category from `data/coding_agent_benchmark.json` when that file exists. Otherwise it uses a fixed order and says the choice is unmeasured.
