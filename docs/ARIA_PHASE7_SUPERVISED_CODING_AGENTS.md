# ARIA Phase 7 — Supervised Coding Agents

Phase 6 remains complete. This is the coding-agent phase from the October 8 hybrid roadmap, with the owner's corrected numbering. The implementation extends the existing coding-agent plans, missions, OCI boundary, supervision, project registry and continuity records. It introduces no new orchestration authority.

## Implemented

- Codex app-server uses durable `thread/start` and supported `thread/resume`, with structured progress, session IDs, terminal outcomes, usage and additional-approval denial events. Incoming server requests cannot collide with client RPC IDs. Notifications arriving before a call response are retained. Normal completion closes the app-server gracefully so private history can flush.
- Every task and continuation uses a new scope-hashed, expiring, single-use owner approval. Continuation keeps the same agent, project, permission mode, disposable workspace and private history. Code, session state or project-test changes invalidate the proposal. Empty threads without saved turn history, redirected state, and refused/boundary-violating runs cannot be continued.
- Approval consumption and launch intent commit together. A mission-creation failure is recorded on the run; its approval cannot launch a second attempt. Run reservation remains cross-process serialized and limited to one concurrent agent. Restart never automatically relaunches an interrupted task.
- Cancellation works before launch, during agent execution, during independent verification, and at completion. An accepted cancellation cannot become a successful completion. Existing OCI/process ownership checks remain intact; tests confirm detached process-tree cleanup and unrelated-process protection.
- Independent verification has a remaining-task deadline, cancellation polling, bounded output and private logs. A successful test process that changes the code cannot verify the previous code snapshot.
- Complete binary-capable patches, independent test receipts, verification logs and sanitized agent output are retained in controller-owned artifacts. Each file and the manifest are hashed and read back. The artifact API rejects modified evidence. Agent claims remain separate from observed changes and independently verified tests. Codex exit zero without a successful terminal event fails.
- Private continuation state carries only named authentication/session/history databases. Owner-wide history, hooks, MCP settings and permission configuration are not copied. Refreshed tokens are redacted again before durable logs and artifacts are finalized.
- Execution policy hashing includes the new session and artifact enforcement code. Old certificates fail closed after a policy change; production's existing certificate is preserved.

## Use after guarded activation

The existing chat proposal/Yes/No flow remains. A continuation can specify a run ID and a new task through `coding_agent_resume`. A legacy ephemeral run is explicitly labeled as a new isolated attempt, never presented as a resumed session.

HTTP flow:

1. `POST /api/coding-agents/runs/{run_id}/resume-plan` with `{"task":"the next bounded task","timeout_s":120}`. Owner Vault/`git.write` step-up is required. This creates a proposal and executes nothing.
2. Review agent, project, mode, task, timeout, unchanged workspace/private history scope and lineage.
3. `POST /api/coding-agents/plans/{plan_id}/approve` through the existing owner-authenticated interface. Existing mission/autonomy/security and runtime-certificate gates still apply.
4. Read `/api/coding-agents/runs/{run_id}` for events/results. Read `/api/coding-agents/runs/{run_id}/artifacts` for readback verification of the retained evidence.
5. Existing run cancellation remains available. No task or continuation implicitly commits, merges, promotes or pushes production work.

Do not send credentials or approval nonces in chat. Additional server requests for authority are declined; expanded authority requires another reviewed ARIA plan. No Claude Code or Antigravity qualification is included.

## Focused verification

89 distinct component regression cases passed with zero failures and zero skips, combining the final 88-case supervision/OCI run and the targeted atomic-reservation follow-up. These tests cover owner approval, replay, scope mutation, durable continuation, PID reuse, cancellation, restart reconciliation, bounded verification, changed-code rejection, terminal-event enforcement, artifact tampering and credential redaction. Native tests use the installed Codex in existing OCI isolation, including detached-tree cancellation, timeout, dead-owner reconciliation, and an offline persisted-thread resume.

A separate two-turn disposable native subscription pilot succeeded: Codex repaired only `calc.py`; ARIA ran the unchanged registered test and verified it; a second fresh app-server resumed the same private thread and added one requested comment; ARIA independently verified it again. The original fixture and production files remained untouched. The worker required a ChatGPT account before each turn, and the broker admitted only existing first-party subscription destinations. No separately billed API inference was used.

Focused Ruff F checks and compilation passed for the changed supervision code/tests. The unchanged legacy `extra_routes.py` specialist error handler has pre-existing F841/F821 findings; it was preserved and is outside this phase.

## Operational limits

This candidate is implemented and tested in isolation, not activated in production. The live service and its existing Codex certificate remain unchanged. Ollama is still default; Claude Code and Antigravity remain unavailable; the existing $0 cloud budget and permissions remain unchanged. No merges, pushes, scraper jobs, or production worker activation occurred.

The existing production health endpoint reported `ready=false` because its Ollama generation probe timed out after five seconds. No unrelated repair or restart was attempted. This must be resolved or explained before guarded activation.

The release package includes source overlays, exact preimages, dirty/index preservation evidence, focused test reports, native pilot evidence without private credentials/history, and a policy-bound certificate proposal pending owner approval. Activation requires the existing stopped-state backup procedure and a new owner-approved certificate binding; copying the old certificate or bypassing its source hash is forbidden.

Official Codex protocol reference: https://learn.chatgpt.com/docs/app-server
