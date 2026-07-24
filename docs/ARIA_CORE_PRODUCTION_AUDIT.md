# Aria Core Production Audit

**Date:** 2026-07-24  
**Stance:** Zero-trust — treat prior ecosystem certifications as untrusted for Aria Core specifically  
**Package:** `aria_core` (`__version__` 2.0.0-phase2 façade + Phase 3–8 organs)  
**Intended deployment scope:** Single-operator local Aria workstation; Core is the sovereign API / Cap Bus / Event Bus / Cognition / Memory / Learning / Reflex / ACM bridge layer over host organs (`jarvis` / optional `aiplatform`)

## Executive Summary

An independent certification pass reviewed every module under `aria_core/` (≈9k LOC), all `tests/test_aria_core*.py` suites, Cap Bus/Event Bus/Cognition/Memory/Learning/Reflex/ACM bridge paths, and concurrency under threaded Cap Bus use.

**Material defect found and fixed this pass:** process-global observability histories and counters in Cognition, Memory Manager, Learning Manager, and Reflex Engine were mutated without locks; ACM `get_engine()` singleton init lacked double-checked locking. These are race conditions under concurrent Cap Bus / reflex / learning traffic.

After fixes + new concurrency stress gates + full Aria Core re-run: **no remaining material Core bugs or Core-owned security holes** within the intended single-operator workstation scope.

## Architecture findings

| Finding | Severity | Outcome |
|---------|----------|---------|
| Core is primarily a sovereign façade (Phase 2 rule: wrap/delegate) | HIGH (scope) | **By design** — see Known Limitations |
| Cap Bus → Cognitive Orchestrator → organs | — | Verified passthrough + compose path |
| Event Bus in-process only (no durable IPC) | MEDIUM | Documented; acceptable for workstation |
| Learning is propose → immediate commit | MEDIUM | Documented Phase 5 contract |
| Thin Cap Bus over Jarvis god-modules | HIGH (debt) | Deferred host split — not a Core correctness defect |
| Platform ops caps optional when AI-Platform absent | — | `health()` marks optional; graceful degrade OK |

## Security findings

| Finding | Severity | Outcome |
|---------|----------|---------|
| ACM PRIMARY fail-closed memory write spine (host + Core manager) | — | Covered by host production audit gates; Core `memory_manager` routes PRIMARY via `acm_bridge` |
| Cap Bus `execute_tool` / `invoke` trust host caller | MEDIUM | In-process API — host auth/permissions remain SoT |
| Event / MC panels: ids/metadata preferred over contents | — | Memory history strips private fields; MC notes visibility-only |
| No plugin sandbox inside Core | HIGH (scope) | Core has no third-party plugin loader; host extensions are out of Core package |
| Secrets / tokens | — | Core does not mint auth tokens; delegates identity/config to host |
| Path / backup hint | LOW | `latest_backup_hint` reads repo `backups/` names only; does not execute scripts |
| Concurrent shared-state races (histories/stats/engine init) | HIGH | **Fixed** this pass |
| Shared ACM `ContextFrame` clobber under concurrent encode | HIGH | **Fixed** (`engine_exclusive`) |
| Cap Bus `permission_requirements` metadata-only | MEDIUM (scope) | Documented — host enforces tool policy |

## Performance findings

| Finding | Severity | Outcome |
|---------|----------|---------|
| Event handler runs synchronous on publisher thread | MEDIUM | By design; slow handlers block publishers — documented |
| Cognition/Learning/Reflex history rings capped | — | Limits enforced under lock |
| ACM `system_prompt_from_acm` multi-round-trip | MEDIUM | Deferred host/ACM cache (ecosystem note) |
| Cap Bus health probes import only | — | Cheap; no side-effect verbs |

## Reliability / recovery findings

| Finding | Severity | Outcome |
|---------|----------|---------|
| Event publish/handler failures swallowed | — | Intentional isolation |
| Nested Cap Bus orchestration depth suppressed | — | `contextvars` depth gate |
| `repair`/`recover` soft-fail when platform missing | — | Returns `{ok: False}` |
| ACM engine cleanup migration fail-open on error | LOW | Retries next start; metrics bumped |
| No explicit Core process shutdown hook | LOW | In-process; process exit clears state |

## Concurrency findings

| Finding | Severity | Outcome |
|---------|----------|---------|
| Unlocked `_HISTORY` / `_STATS` in cognition, memory, learning, reflex | HIGH | **Fixed** (`threading.RLock`) |
| Event bus `rates()` `ring_size` read outside lock | MEDIUM | **Fixed** |
| ACM `get_engine()` double-init race | HIGH | **Fixed** (lock + re-check) |
| Concurrent publish/learn/reflex/health stress | — | New `tests/test_aria_core_concurrency.py` |

## Tests (this certification)

| Suite | Result |
|-------|--------|
| `tests/test_aria_core*.py` (all phases + contract + concurrency) | **PASS** |
| Concurrency stress ×3 | **PASS** |
| Host production audit + cognitive infrastructure + ACM M4 + learning governor (paired) | **PASS** (94 in combined Core-focused run) |

## Fixes implemented this pass

1. Thread-safe histories/stats in `cognitive_orchestrator`, `memory_manager`, `learning_manager`, `reflex_engine`
2. Thread-safe ACM engine singleton + `reset_for_tests`
3. Event bus `rates()` ring size under lock
4. `engine_exclusive()` serializes ACM encode/cool/revise + harvest ContextFrame swaps
5. `tests/test_aria_core_concurrency.py` + CI path registration

## Engineering assessment

Aria Core is **not** a freestanding OS-level runtime with its own auth, sandbox, scheduler, and network stack. It is the **cognitive coordination façade** for Aria. Within that intended scope — Cap Bus verbs, Event Bus, Cognition, Memory/Learning ownership APIs, Reflex, ACM bridge — it is production-capable after this concurrency hardening.

See also: [`ARIA_CORE_CERTIFICATION.md`](ARIA_CORE_CERTIFICATION.md), [`ARIA_CORE_KNOWN_LIMITATIONS.md`](ARIA_CORE_KNOWN_LIMITATIONS.md).
