# Aria Core Known Limitations

**Date:** 2026-07-24  
**Applies to:** Certified single-operator workstation deployment of `aria_core`

These are intentional scope boundaries or deferred enhancements — **not** open material defects blocking Core certification.

## Architectural

1. **Not a standalone OS runtime.** Core is a sovereign API / coordination layer. Organs live in `jarvis` and optionally `aiplatform`. Callers outside Aria host must embed those organs or accept soft-unavailable capabilities.
2. **Phase 2 golden rule.** Thin delegation; organ moves are explicitly out of Core’s current charter.
3. **Cap Bus is thin over host handlers.** Registry `permission_requirements` are **metadata for Mission Control**, not Cap Bus ACL enforcement. Tool/HA/shell permission checks remain in host registries — Core `execute_tool` trusts the in-process caller.
4. **No Core plugin system.** Extension loading is a host concern (`jarvis.extensions`). Core has no third-party plugin isolation/sandbox.
5. **In-process Event Bus only.** No durable queue, no cross-process IPC, no exactly-once delivery. Ring buffer is observability/replay-of-ring, not a message broker.
6. **Learning commits immediately.** Phase 5 contract is propose → commit → apply; human assent UX for Cap Bus is deferred ecosystem work.
7. **God-module debt stays in host.** Splitting `jarvis.assistant` / router is deferred; Core Cognition does not absorb that split.

## Security / tenancy

8. **Single-operator trust model.** No multi-user session isolation inside Core.
9. **No network listeners in Core.** AuthN/AuthZ for HTTP/LAN/API keys is host GUI/server responsibility.
10. **Secrets.** Core does not own secret storage; do not place tokens in Event Bus payloads.
11. **Direct `acm_bridge.primary_*` callers.** Cap Bus is preferred; soft cool/revise paths remain for host memory façades (documented ecosystem MEDIUM).

## Reliability / performance

12. **Synchronous event handlers.** A slow/blocking subscriber delays publishers on that process.
13. **No formal Core shutdown protocol.** State is process-lifetime; tests use `reset_for_tests()`.
14. **ACM prompt assembly cost.** Multi-round retrieval for system prompt caching is deferred.
15. **Compose organ coverage.** `orchestrate_compose` executors today emphasize reference/runtime/memory; other organs may return soft “no executor” parts by design of current plan filters.

## Testing / packaging

16. **Long soak / chaos.** Core concurrency stress covers threaded Cap Bus use; multi-hour soak remains an Aria host/ACM operational concern.
17. **Packaging.** Publishing Core as an independent PyPI runtime with full organ deps is deferred.

## Future enhancements (non-blocking)

- Durable event transport (optional)
- Explicit Cap Bus permission policy objects
- Learning assent / delayed commit mode
- Broader compose organ executors
- Standalone Core packaging profile
