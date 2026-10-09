# Phase 6 sandbox and approval guarantees

Current measurements and limits are in [final certification](ARIA_PHASE6_RECOVERY.md). The old nested Codex/bubblewrap architecture is replaced; there is no automatic fallback to weaker isolation.

## Trusted controller and untrusted execution

Trusted: ARIA approval/state/controller code, local Docker daemon, installed kernel/container runtime, pinned local image, read-only toolchain installations and subscription CONNECT broker. Untrusted: every coding CLI, its model output, shell commands, descendants, edited code, tests and repository content.

Live CLI execution uses `aria-oci-external-v1`:

- Local `unix:///var/run/docker.sock` only; no remote Docker context or socket inside the container.
- Image `sha256:509fdf54e23bd50d87af646cb51c0a7a203d6a83cc4d6695b3b08c5be1c62c0a` from the already cached image; `--pull never`. No image download.
- Read-only root; private mount/PID/IPC/network namespaces; UID/GID 1000; `--cap-drop ALL`; no-new-privileges; explicit AppArmor `docker-default`; default seccomp; no privileged/unconfined/host-PID/host-IPC option.
- 6 GiB memory and equal total memory/swap cap, four CPU equivalents, 512 processes; tmpfs `/tmp` 512 MiB and `/run` 16 MiB.
- Exact approved disposable workspace is read-only for review/diagnosis and writable for an approved edit. Workspace Git metadata is read-only.
- Trusted executable roots and worker module directory are read-only. Writable private authentication and output stores are per-run. Production roots, home histories, credentials, datasets, owner config, host service sockets and host process tree are absent.
- Required daemon policy is inspected before start; failed create/inspect refuses the run. Container identity, policy, approval and immutable image are durably receipted before launch.

Codex runs installed `codex app-server` and uses the vendor's **explicit externalSandbox protocol** with approval policy never. The required external boundary is already established by the container; native nested bubblewrap is not attempted. Unsupported protocol/account/installation fails closed. Claude and agy retain their normal native permission/tool modes inside the same external container, but both adapters are currently disabled. There are no dangerous permission-bypass flags.

Discovery is also untrusted execution: version/help/auth probes use private-root bubblewrap, no network, bounded output, timeout/tree termination and private copied auth. It never invokes an unconfined vendor CLI as a fallback.

## Authentication and subscription network

Only named login artifacts are copied into mode-0600 files inside mode-0700 per-run directories. Codex `auth.json`; Claude credential store plus minimized onboarding/OAuth account fields; agy named OAuth/account files including `antigravity-cli/antigravity-oauth-token` if available. Owner histories, MCP/hook settings and session stores are not shared. Token redaction rejects symlinked state paths and uses bounded scans of private copies. Raw credential data is never documentation evidence.

Container network is `none`. A local loopback bridge talks to a mode-0600 Unix socket in a mode-0700 controller directory. The trusted broker allows CONNECT/TLS443 only:

| Adapter | Authorities |
|---|---|
| Codex | `chatgpt.com`, `auth.openai.com` |
| Claude Code | `api.anthropic.com`, `claude.ai` |
| Antigravity | `cloudcode-pa.googleapis.com`, `oauth2.googleapis.com` |

Every resolved address must be public. The broker connects to that IP directly, checks bounded TLS ClientHello and exact SNI against CONNECT authority, and rejects plaintext, missing/mismatched SNI and ECH. Unknown domains, IP authorities, non-443 ports, redirects to unapproved destinations and private/loopback targets are denied. This restricts endpoints; it does not inspect encrypted model payloads or claim content-level DLP. Coding prompts and approved workspace content may reach the signed-in subscription provider.

Host network decision logs are outside all agent mounts and contain authority/reason, not auth headers or TLS payloads. Container subprocesses cannot access API keys, SSH agent or host Docker/DBus sockets. Codex must report ChatGPT authentication before a model turn. Quota/auth/transport failures persist adapter unavailability. Live boundary verdicts immediately persist quarantine; eligibility independently checks durable violation IDs and fails closed on unreviewed or unreadable history. A crash before certificate update cannot silently permit reselection. Cloud inference and paid API fallback remain disabled.

## Approval and promotion

Plan approval and promotion approval are different nonces. Each is owner-only, expires in 30 minutes, binds the reviewed object (including canonical project path, protection, test command and allowed agents for a run) and cannot be replayed for a second execution/application. Safe-mode/capability/autonomy guards apply again at execution, regardless of router or caller. One cross-process run reservation is allowed. Scope is checked before approval, before consumption and immediately before cloning; older approvals without a scope snapshot are preserved but cannot execute.

An agent approval permits only its disposable clone. Promotion requires a separately reviewable diff, destination HEAD/branch, manifest hashes, test evidence and owner approval. It rejects protected data/credentials/symlinks/submodules and touched dirty files; unrelated dirty files remain intact. Destination locks and conflict checks precede recovery snapshots/apply. Verification failure rolls back. Explicit rollback refuses intervening owner edits. Interrupted promotion restores its snapshot; it never auto-retries a production change. Git push, service restart/deployment, migration execution and production approval are absent from agent automation.

Untrusted workspace Git collection/capture runs under hidden-root, no-network bubblewrap, with explicit provenance classification even if workspace-root settings later change. Hooks/fsmonitor are disabled, external diff/textconv are disabled, and optional locks prevent owner index refreshes. Symlink output paths cannot redirect controller reads/log writes.

## Termination, restart and evidence

Cancellation/timeouts remove only the receipt's run-labeled OCI container, killing detached descendants. A worker PID1 watchdog independently enforces wall time. Cleanup failure keeps the concurrency slot reserved and records an error. Restart recovery removes recorded dead-owner containers; it does not kill another live supervisor or repeat a run. New work requires a new plan and approval.

Run streams are bounded, redacted and flushed incrementally to controller-private logs. SQLite receipts retain requested/attempted/changed/tested/verified/unverified distinctions, protected fingerprints, approval, policy/container identity and terminal error class. Claims remain claims; Git/test evidence establishes verification. Coding history/continuity does not write ACM.

Kernel and trusted-controller vulnerabilities are outside the evidence's claim; this is measured process/filesystem/network containment on this host, not proof against an unknown kernel exploit. Current [adversarial outcomes](evidence/phase6_certification/adversarial_outcomes.json) test syscall/subprocess paths, not only canaries. Native safety tests must not be skipped for deployment.
