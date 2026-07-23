# Aria Complete Platform Production Audit

**Status:** Production-ready for single-operator workstation (with documented follow-ons)  
**Date:** 2026-07-23  
**ACM pin:** v0.45.1 / `aria-acm-v0.45.1-1` @ `b720cbb`  
**Aria:** jarvis host + `aria_core`  
**Aria Platform:** AI-Platform 0.1.0 (Alpha / RC1 Daily Use)

ACM remains complete — this program did not add ACM cognitive capabilities.
Fixes that touched ACM were **fail-closed durable load** only (data-loss bug).

## Architecture findings

| Finding | Severity | Action |
|---------|----------|--------|
| Silent legacy SoT write when ACM redirect fails under PRIMARY | CRITICAL | **Fixed** — fail closed + counter |
| Memory `import_data` bypassed ACM under PRIMARY | CRITICAL | **Fixed** — routes via `add()` → ACM |
| Corrupt ACM snapshot treated as empty → wipe risk | CRITICAL | **Fixed** (ACM 0.45.1) |
| Cap Bus / Core is thin façade over Jarvis monolith | HIGH | Documented; god-module split deferred |
| AI-Platform DualWrite vs ACM SoT tension | HIGH | Documented; DualWrite non-authoritative under PRIMARY |
| Ownership docs still claimed legacy memory SoT | MEDIUM | **Fixed** `ownership.py` + phase7 test |
| Cap Bus health false-negative without aiplatform | MEDIUM | **Fixed** — platform caps optional |
| Boundary test scanned wrong path | HIGH | **Fixed** — allowlisted soft jarvis imports |

## Security & governance findings

| Finding | Severity | Action |
|---------|----------|--------|
| PinLockMiddleware never registered | HIGH | **Fixed** |
| LAN bind without API key | HIGH | **Fixed** — refuse unless override |
| Mission Control POST unauthenticated off-loopback | CRITICAL | **Fixed** — loopback-only or `AIPLATFORM_MC_TOKEN` |
| Secrets file world-readable risk | HIGH | **Fixed** — `chmod 0600` |
| Default Postgres password `postgres` | HIGH | **Fixed** — empty default; random on generate |
| Tool permissions dead for HA / upgrade_apply | HIGH | **Fixed** — gates wired |
| Auto-memory stamped as TEACHING | HIGH | **Fixed** — STATEMENT for auto tags |
| Full B20/B36 Cap Bus assent UX | HIGH | **Deferred** (large host program) |
| Multi-user session isolation | MEDIUM | **Deferred** — single-operator product |

## Performance findings

| Finding | Action |
|---------|--------|
| `system_prompt_from_acm` 4× cognitive round-trips | Deferred (cache) — not blocking |
| DualWrite write amplification | Deferred / ACM projection path |
| MC full snapshot cost | Known; lazy tabs already |

## Dependency findings

| Finding | Action |
|---------|--------|
| Aria `pyproject.toml` has no runtime deps | Deferred packaging hardening |
| AI-Platform runtime = PyYAML only | Appropriate for local-first |
| Empty compose/config scaffolding | Documented; not implemented as deploy stack |

## Behavioral / certification

| Suite | ×2 | Result |
|-------|----|--------|
| Aria Core + host audit | ×2 | **73 passed**, 1 skipped |
| Aria ACM promotion | ×2 | **198 passed** |
| AI-Platform tests | ×2 | **798 passed** |
| ACM corrupt-load + prior audit | — | PASS |

## Technical debt removed / improvements shipped

- Fail-closed PRIMARY memory writes (JSON + SQLite)
- ACM import path under PRIMARY
- Corrupt durable load fail-closed (ACM 0.45.1)
- ACM flush on GUI shutdown
- PinLock middleware registration
- LAN API-key requirement
- Tool permission gates (HA control, upgrade apply)
- Auto-memory provenance = STATEMENT
- Cap Bus optional platform health
- Ownership SoT truth
- MC mutation auth
- Secrets file permissions
- Random Postgres password on env generate
- Honest workstation boundary test

## Recommendations intentionally deferred

1. **Cap Bus B20/B36 preview→assent UX** — ACM complete; host conversational surface is a separate program  
2. **God-module split** (`router.py`, `assistant.py`, `gui/server.py`) — weeks of refactor  
3. **Declare Aria `[project] dependencies` / lockfile** — packaging program  
4. **Retire DualWrite / ROLLBACK code** — keep forensic window with loud gates  
5. **Multi-tenant engines / session isolation** — out of single-operator scope  
6. **Fill empty AI-Platform compose/** — or delete scaffolding (product decision)  
7. **Cache `system_prompt_from_acm`** — measured perf follow-on  
8. **Full RC1 soak checklist** — process gate, not code defect  

## Bugs permanently prevented

| Bug | Permanent gate |
|-----|----------------|
| PRIMARY → legacy write on encode failure | `test_primary_memory_add_fail_closed_on_redirect_error` |
| Auto teaching stamp | `test_auto_memory_uses_statement_provenance` |
| PinLock not registered | `test_pin_lock_middleware_registered_in_server_source` |
| LAN without key | `test_lan_bind_requires_api_key` |
| Corrupt snapshot wipe | ACM `test_corrupt_snapshot_fail_closed` |
| Boundary test always green | AI-Platform `test_workstation_boundary` |

## Final assessment

### Aria Core
**Production-ready** as the sovereign Cap Bus / memory façade over ACM PRIMARY, with fail-closed governance on the critical write spine.

### Aria Platform (AI-Platform)
**Production-ready for single-user local workstation / Mission Control Daily Use**, not multi-tenant SaaS. Control-plane mutations gated; secrets hardened; test boundary truthful. Empty compose and DualWrite/ACM product alignment remain documented follow-ons.

### Combined verdict
**Yes — Aria Core + Aria Platform are production-ready to the ACM standard for the certified single-operator workstation scope**, with the deferred host UX and packaging items listed above.
