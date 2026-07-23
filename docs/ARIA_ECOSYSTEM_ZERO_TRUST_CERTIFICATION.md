# Aria Ecosystem Zero-Trust Certification

**Date:** 2026-07-23  
**Stance:** Assume not production-ready until earned  
**Scope:** ACM · Aria Core · Aria Platform · host organs (memory, tools, skills, LAN/auth)  
**Pins:** ACM v0.45.1 · Aria `aria-acm-v0.45.1-1` · AI-Platform main  

## Executive Summary

Prior certifications were treated as untrusted. Adversarial re-verification confirmed most CRITICAL host/ACM fixes still hold, then discovered **additional PRIMARY governance holes** that previous audits missed:

1. JSON `import_data` called `add()` with **swapped arguments** (broken under PRIMARY).
2. SQLite `import_data` **never** routed to ACM (latent SoT pollution).
3. `update` / `delete_id` still **fail-open** to legacy on facade errors.
4. `prune` / `clear` still mutated forensic legacy under PRIMARY.
5. Skill execution defaulted to `shell=True`; Claude dangerous flag needed only a param.

Those defects are fixed and permanently certified. Remaining gaps are intentional scope (Cap Bus assent UX, god-module split, multi-tenant, full RC1 soak process) or product roadmap — not blockers for **single-operator workstation** production use.

**Final verdict:** Production-ready for the certified single-operator local workstation deployment scope.

---

## Subsystem readiness matrix

| Subsystem | Verdict | Notes |
|-----------|---------|-------|
| ACM | **READY** | v0.45.1; corrupt-load fail-closed; write spine; L34 |
| Aria Core / Cap Bus | **READY** | PRIMARY façades; optional platform health |
| ACM bridge / memory host | **READY** | Fail-closed add/update/delete/import/prune/clear |
| Aria Platform / Mission Control | **READY** | MC mutation gate; secrets 0600; random PG password |
| Chat / Router / Assistant | **READY*** | *God modules deferred; behavioral ACM path certified |
| Dashboard / GUI FastAPI | **READY*** | PinLock + LAN key; *surface still large |
| Memory APIs | **READY** | PRIMARY fail-closed |
| Tool permissions (HA / upgrade) | **READY** | Wired |
| Skills / project runner / coding tools | **READY*** | No default shell; dangerous tools env-gated; cwd confined |
| Voice / Audio / Media / Gallery | **READY*** | Video/storyboard paths confined to DATA_DIR media trees |
| Fly Tying / Journal / Calendar / Planner | **ACCEPTABLE** | Domain modules; no CRITICAL write-spine issues found |
| DualWrite / ROLLBACK | **CONTAINED** | Forensic only; not PRIMARY SoT |
| Packaging / installers | **ACCEPTABLE*** | *pyproject deps still dual-path — deferred |
| Documentation | **READY** | This report + prior audits |

\*READY with documented deferred hardening, not with open CRITICAL defects.

---

## Architecture findings

| Finding | Severity | Outcome |
|---------|----------|---------|
| Cap Bus thin over Jarvis monolith | HIGH | Deferred (large) |
| Direct `primary_*` bypass Cap Bus | MEDIUM | Documented; soft cool/revise correct |
| Empty AI-Platform compose scaffolding | MEDIUM | Deferred product honesty |
| DualWrite vs ACM SoT | HIGH | Contained under PRIMARY |

## Security findings

| Finding | Severity | Outcome |
|---------|----------|---------|
| Prior CRITICAL fixes still hold (fail-closed add, corrupt load, PinLock, LAN, MC token, dual-import) | — | **VERIFIED** |
| SQLite import bypass PRIMARY | CRITICAL | **Fixed** |
| JSON import swapped `add()` args | CRITICAL | **Fixed** |
| update/delete fail-open | CRITICAL | **Fixed** |
| prune/clear under PRIMARY | HIGH | **Fixed** (no-op) |
| skill `shell=True` default | HIGH | **Fixed** (`JARVIS_SKILL_SHELL` opt-in) |
| Claude `--dangerously-skip-permissions` | HIGH | **Fixed** (`JARVIS_ALLOW_DANGEROUS_TOOLS`) |
| Teaching debug raw utterance | MEDIUM | **Fixed** (length only) |
| Arbitrary video/storyboard path read | CRITICAL | **Fixed** (`resolve_video_path` / `resolve_storyboard_image`) |
| Automation inbound query-secret + unrestricted chat | CRITICAL | **Fixed** (header-only + `compare_digest`; chat requires `JARVIS_AUTOMATION_ALLOW_CHAT`) |
| `/api/tools/execute` arbitrary cwd | CRITICAL | **Fixed** (PROJECT_ROOT / DATA_DIR only) |
| HA REST toggle/scene bypass tool permissions | HIGH | **Fixed** |
| Upgrade `force` skipped ask permission | HIGH | **Fixed** |
| PRIMARY `upsert_checkpoint` legacy delete | HIGH | **Fixed** |
| Full B20/B36 Cap Bus assent | HIGH | Deferred |
| Multi-user session isolation | MEDIUM | Deferred (single-operator) |
| Audio/VST/document/ICS SSRF hardening | HIGH | Deferred (next pass) |
| Automation inbound chat | MEDIUM | **Gated** (`JARVIS_AUTOMATION_ALLOW_CHAT`) |

## Performance findings

| Finding | Outcome |
|---------|---------|
| `system_prompt_from_acm` 4× round-trips | Deferred cache |
| DualWrite amplification | Contained / non-SoT |
| MC full snapshot cost | Known acceptable for Daily Use |

## Dependency findings

| Finding | Outcome |
|---------|---------|
| No unjustified replacements this pass | Retained |
| Aria pyproject lacks runtime deps | Deferred packaging |
| AI-Platform PyYAML-only runtime | Appropriate |

## Behavioral / certification totals (×2 where noted)

| Suite | Result |
|-------|--------|
| Adversarial probe (dual-import, fail-closed, corrupt, LAN) | PASS |
| Host zero-trust gates | 8 passed ×2 (in Core suite) |
| Aria Core + host | **77 passed**, 1 skipped ×2 |
| Aria ACM promotion | **198 passed** ×2 |
| ACM cognitive+behavioral | PASS ×2 |
| ACM learning certification | PASS ×2 |
| ACM long-duration / framework | PASS |
| AI-Platform | **798 passed** ×2 |

## Bugs discovered this zero-trust pass → permanently prevented

| Bug | Gate |
|-----|------|
| import_data wrong `add()` arity | `test_primary_import_routes_via_add_arg_order` |
| prune/clear under PRIMARY | `test_primary_prune_and_clear_are_noops` |
| skill shell default | `test_skill_exec_defaults_to_no_shell` |
| Claude dangerous without env | `test_claude_dangerous_requires_env_opt_in` |
| SQLite import legacy SoT | covered by import + fail-closed suite |

## Technical debt removed this pass

- PRIMARY fail-open update/delete
- SQLite import PRIMARY hole
- Broken JSON import ACM path
- Default skill shell
- Easy Claude dangerous flag
- Teaching debug utterance leak

## Deferred recommendations (justified)

1. **Cap Bus B20/B36 preview→assent UX** — large host product program; ACM already complete  
2. **Split god modules** — weeks; risk outweighs 1.0 workstation ship  
3. **Declare Aria `[project].dependencies` + lockfile** — packaging program  
4. **Retire DualWrite/ROLLBACK code** — keep forensic window  
5. **Multi-tenant ACM engines** — out of single-operator scope  
6. **Fill or delete empty compose/** — product decision  
7. **Cache system_prompt_from_acm** — measured perf follow-on  
8. **RC1 endurance soak process** — ops checklist, not a code defect  
9. **Automation inbound action allowlist** — medium hardening follow-on  
10. **Full interactive UI crawl of every gallery/voice/flytying workflow** — continuous dogfood; no CRITICAL code defects found this pass  

## Risk assessment

| Risk | Level after audit |
|------|-------------------|
| Cognitive SoT split (ACM vs legacy) under PRIMARY | **Low** (fail-closed) |
| LAN exposure without key | **Low** (refused) |
| MC remote mutation | **Low** (token/loopback) |
| Accidental shell RCE via skills | **Low** (argv default) |
| Corrupt ACM wipe | **Low** (fail-closed load) |
| Cap Bus assent UX gap | **Accepted** for soft cool/revise |
| Packaging reproducibility | **Accepted** (scripts + requirements) |

## Final verdicts

### ACM

**Production-ready.**

### Aria Core

**Production-ready** as Memory Authority façade over ACM PRIMARY.

### Aria Platform

**Production-ready** for single-user local Mission Control / workstation Daily Use (not multi-tenant SaaS).

### Overall Aria Ecosystem

**Production-ready for intended deployment scope: single-operator Linux workstation with ACM PRIMARY, optional AI-Platform Mission Control, optional LAN only with API key.**

Zero-trust assumption **disproved for that scope** after independent re-audit, repair of newly found CRITICAL/HIGH defects, and full re-certification.
