# Aria Complete Platform Production Audit

**Status:** Production-ready for single-operator workstation (with documented follow-ons)  
**Checkpoint:** Security Hardening RC-S1 complete (2026-07-23)  
**ACM pin:** v0.45.1 / `aria-acm-v0.45.1-1` @ `b720cbb`  
**Aria:** jarvis host + `aria_core`  
**Aria Platform:** AI-Platform 0.1.0 (Alpha / RC1 Daily Use)

ACM remains complete — this program did not add ACM cognitive capabilities.
Fixes that touched ACM were **fail-closed durable load** only (data-loss bug).

Companion reports: [`ARIA_ECOSYSTEM_ZERO_TRUST_CERTIFICATION.md`](ARIA_ECOSYSTEM_ZERO_TRUST_CERTIFICATION.md) · [`ARIA_SECURITY_HARDENING_RC_S1.md`](ARIA_SECURITY_HARDENING_RC_S1.md) · ACM `docs/PRODUCTION_READINESS_AUDIT.md`

---

## Architecture findings

| Finding | Severity | Action |
|---------|----------|--------|
| Silent legacy SoT write when ACM redirect fails under PRIMARY | CRITICAL | **Fixed** — fail closed + counter |
| Memory `import_data` bypassed ACM under PRIMARY (JSON + SQLite) | CRITICAL | **Fixed** — routes via `add()` → ACM |
| JSON `import_data` swapped `add()` argument order | CRITICAL | **Fixed** |
| `update` / `delete_id` fail-open to legacy on facade errors | CRITICAL | **Fixed** |
| `prune` / `clear` mutated forensic legacy under PRIMARY | HIGH | **Fixed** (no-op) |
| `upsert_checkpoint` deleted legacy rows under PRIMARY | HIGH | **Fixed** — add-only under PRIMARY |
| JSON `delete(index)` bypassed ACM gate | HIGH | **Fixed** — routes via `delete_id` |
| Corrupt ACM snapshot treated as empty → wipe risk | CRITICAL | **Fixed** (ACM 0.45.1) |
| Cap Bus / Core is thin façade over Jarvis monolith | HIGH | Documented; god-module split deferred |
| AI-Platform DualWrite vs ACM SoT tension | HIGH | Documented; DualWrite non-authoritative under PRIMARY |
| Ownership docs still claimed legacy memory SoT | MEDIUM | **Fixed** `ownership.py` + phase7 test |
| Cap Bus health false-negative without aiplatform | MEDIUM | **Fixed** — platform caps optional |
| Boundary test scanned wrong path | HIGH | **Fixed** — allowlisted soft jarvis imports |

### Engineering rationale (architecture)

Under `ARIA_ACM_PRIMARY`, legacy JSON/SQLite stores are forensic vaults, not SoT. Any path that still mutated them on encode/import/delete/checkpoint failure created split-brain cognition and silent data loss. Fail-closed + ACM routing preserves Memory Authority.

---

## Security & governance findings

| Finding | Severity | Action |
|---------|----------|--------|
| PinLockMiddleware never registered | HIGH | **Fixed** |
| LAN bind without API key | HIGH | **Fixed** — refuse unless override |
| Mission Control POST unauthenticated off-loopback | CRITICAL | **Fixed** — loopback-only or `AIPLATFORM_MC_TOKEN` |
| Secrets file world-readable risk | HIGH | **Fixed** — `chmod 0600` |
| Default Postgres password `postgres` | HIGH | **Fixed** — empty default; random on generate |
| Tool permissions dead for HA / upgrade_apply | HIGH | **Fixed** — gates wired |
| HA REST homeassistant toggle/scene bypassed tool permissions | HIGH | **Fixed** — `ha_control` ask/never |
| `ha_scene` behavior ungated | HIGH | **Fixed** |
| Upgrade `force` skipped ask permission | HIGH | **Fixed** — confirm still required |
| Auto-memory stamped as TEACHING | HIGH | **Fixed** — STATEMENT for auto tags |
| Skill exec defaulted to `shell=True` | HIGH | **Fixed** — argv default; `JARVIS_SKILL_SHELL` opt-in |
| Claude `--dangerously-skip-permissions` via param only | HIGH | **Fixed** — requires `JARVIS_ALLOW_DANGEROUS_TOOLS` |
| Arbitrary video/storyboard filesystem paths | CRITICAL | **Fixed** — `resolve_video_path` / `resolve_storyboard_image` |
| Automation inbound accepted query-string secret | CRITICAL | **Fixed** — header-only + `hmac.compare_digest` |
| Automation inbound `action=chat` → full `assistant.process` | CRITICAL | **Fixed** — requires `JARVIS_AUTOMATION_ALLOW_CHAT=1` |
| `/api/tools/execute` arbitrary `cwd` | CRITICAL | **Fixed** — PROJECT_ROOT / DATA_DIR only |
| Full B20/B36 Cap Bus assent UX | HIGH | **Deferred** (large host program) |
| Multi-user session isolation | MEDIUM | **Deferred** — single-operator product |
| Audio/VST/document path + ICS/URL SSRF hardening | HIGH | **Fixed** (RC-S1) |
| Browser `allow_risky` / trusted-device / PIN timing | HIGH | **Fixed** (RC-S1) |
| Uncensored reset auth + password policy | CRITICAL/HIGH | **Fixed** (RC-S1) |
| PIN setup race | CRITICAL | **Fixed** (RC-S1) |
| Journal wipe without confirm | HIGH | **Fixed** (RC-S1) |

### Security rationale

Media APIs that `resolve()` any readable path are arbitrary file read/process when LAN + API key (or localhost) is available. Automation webhooks that accept secrets in query strings leak via HA history/Referer/logs; unrestricted chat equates a leaked webhook secret to host RCE via coding tools. Tool cwd and dangerous flags must not expand operator blast radius beyond the project/data trees.

### Production impact

- Video studio / storyboard only ingest files under `DATA_DIR` media trees.
- HA automations must send `X-Jarvis-Automation-Secret` (no `?secret=`).
- Full chat via automation is off unless explicitly enabled.
- External coding tools cannot be pointed at arbitrary directories.
- HA GUI toggles respect the same permission model as chat `ha_control`.

---

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

---

## Behavioral / certification (post-audit validation checkpoint)

| Suite | ×2 | Result |
|-------|----|--------|
| Aria Core + host security gates | ×2 | **79 passed** |
| Aria ACM promotion (`tests/test_aria_acm_*.py`) | ×2 | **198 passed** |
| Aria shipped CI (`scripts/ci_check.py all`) | ×2 | **681 passed**, 1 skipped |
| Host security regression (`test_aria_host_production_audit`) | ×2 | **18 passed** |
| ACM full (`tests/`) | ×2 | **596 passed** |
| ACM learning certification script | ×2 | **PASS** (exit 0) |
| ACM cognitive + behavioral + performance | — | **PASS** |
| AI-Platform (`tests/`) | ×2 | **798 passed** |
| Vendor pin / no ACM drift | — | **VERIFIED** (`b720cbb` / `aria-acm-v0.45.1-1`) |
| Security Hardening RC-S1 | — | **COMPLETE** — see `ARIA_SECURITY_HARDENING_RC_S1.md` |

### Full-tree inventory note

A naïve `pytest tests/` over the entire Aria tree reports **~78 failed / 9 errors / 97 skipped** alongside ~984 passes. Those failures are **pre-existing** (largely dating to the 2026-06-26 recovery alignment commit), outside `scripts/ci_check.py` maintained paths, and **not regressions** from this audit’s security fixes (e.g. missing `jarvis/skill_defaults/`, stale backlog/API stubs, optional PySide6).

**Shipped production suite** = `scripts/ci_check.py all` (ruff + format-check + ACM supremacy + scoped pytest). Host production-audit and dual-import gates are now included in that suite.

---

## Technical debt removed / improvements shipped

- Fail-closed PRIMARY memory writes (JSON + SQLite add/update/delete/import/prune/clear/checkpoint)
- Corrupt durable load fail-closed (ACM 0.45.1)
- ACM flush on GUI shutdown
- PinLock middleware registration
- LAN API-key requirement
- Tool permission gates (HA control/scene, upgrade apply; force cannot skip ask)
- Auto-memory provenance = STATEMENT
- Cap Bus optional platform health
- Ownership SoT truth
- MC mutation auth
- Secrets file permissions
- Random Postgres password on env generate
- Honest workstation boundary test
- Skill argv default / dangerous-tools env gate
- Video/storyboard path confinement
- Automation inbound header-only secret + chat gate
- Tools execute cwd confinement
- Host security gates locked into CI

## Recommendations intentionally deferred

1. **Cap Bus B20/B36 preview→assent UX** — ACM complete; host conversational surface is a separate program  
2. **God-module split** (`router.py`, `assistant.py`, `gui/server.py`) — weeks of refactor  
3. **Declare Aria `[project] dependencies` / lockfile** — packaging program  
4. **Retire DualWrite / ROLLBACK code** — keep forensic window with loud gates  
5. **Multi-tenant engines / session isolation** — out of single-operator scope  
6. **Fill empty AI-Platform compose/** — or delete scaffolding (product decision)  
7. **Cache `system_prompt_from_acm`** — measured perf follow-on  
8. **Full RC1 soak checklist** — process gate, not code defect  
9. **Audio/VST/document path confinement + ICS/document SSRF** — **Done (RC-S1)**  
10. **Browser `allow_risky` / trusted-device / PIN compare_digest** — **Done (RC-S1)**  
11. **Recover stale full-tree pytest backlog** — separate test-hygiene program (not a production SoT blocker)  
12. **Coding-tool `$HOME` via `fs.resolve_path`** — intentional single-operator workflow; HTTP isolated  
13. **Signed trusted-device tokens** — IP-bound registration sufficient for certified scope  

## Bugs permanently prevented

| Bug | Permanent gate |
|-----|----------------|
| PRIMARY → legacy write on encode failure | `test_primary_memory_add_fail_closed_on_redirect_error` |
| import_data wrong `add()` arity | `test_primary_import_routes_via_add_arg_order` |
| prune/clear under PRIMARY | `test_primary_prune_and_clear_are_noops` |
| upsert_checkpoint legacy delete under PRIMARY | `test_upsert_checkpoint_primary_does_not_delete_legacy` |
| Auto teaching stamp | `test_auto_memory_uses_statement_provenance` |
| PinLock not registered | `test_pin_lock_middleware_registered_in_server_source` |
| LAN without key | `test_lan_bind_requires_api_key` |
| skill shell default | `test_skill_exec_defaults_to_no_shell` |
| Claude dangerous without env | `test_claude_dangerous_requires_env_opt_in` |
| Unconfined video/storyboard paths | `test_video_paths_are_confined` |
| Automation query-string secret | `test_automation_secret_rejects_query_only` |
| Tools arbitrary cwd | `test_tools_cwd_must_be_under_project_or_data` |
| SSRF private/metadata | `test_ssrf_guard_blocks_private_and_metadata` |
| Audio/doc/image path escape | `test_audio_document_image_paths_confined` |
| Browser file/private schemes | `test_browser_blocks_file_and_private_even_with_allow_risky` |
| PIN timing compare | `test_pin_verify_uses_compare_digest` |
| Weak uncensored password | `test_uncensored_password_min_length_12` |
| Trusted-device IP spoof | `test_trusted_device_requires_ip_binding` |
| Corrupt snapshot wipe | ACM `test_corrupt_snapshot_fail_closed` |
| Boundary test always green | AI-Platform `test_workstation_boundary` |

---

## Final assessment

### Aria Core

**Production-ready** as the sovereign Cap Bus / memory façade over ACM PRIMARY, with fail-closed governance on the critical write spine and hardened host media/automation/tool surfaces from the zero-trust follow-up.

### Aria Platform (AI-Platform)

**Production-ready for single-user local workstation / Mission Control Daily Use**, not multi-tenant SaaS. Control-plane mutations gated; secrets hardened; test boundary truthful. Empty compose and DualWrite/ACM product alignment remain documented follow-ons.

### Combined verdict

**Yes — Aria Core + Aria Platform remain production-ready for the certified single-operator workstation scope.** Security Hardening RC-S1 closed deferred CRITICAL/HIGH host surfaces (path confinement, SSRF, browser, auth). Remaining deferred items are explicitly justified (coding-tool HOME, signed device tokens, packaging, Cap Bus UX) and do not block the certified deployment scope.
