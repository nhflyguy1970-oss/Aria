# Aria Security Hardening RC-S1 Report

**Date:** 2026-07-23  
**Codename:** RC-S1 — Final Host & Platform Security Certification  
**Baseline:** Locked post-audit validation checkpoint (`48d028d` era)  
**Pins:** ACM v0.45.1 / `aria-acm-v0.45.1-1` @ `b720cbb`

## Executive Summary

RC-S1 closed the remaining deferred CRITICAL/HIGH host security surfaces without feature work or architecture redesign. Shared **path confinement** and **SSRF URL guards** now protect media, documents, calendar, browser, and flytying fetches. Authentication paths use constant-time compares; PIN bootstrap and uncensored reset require stronger authorization; trusted-device bypass requires IP binding.

**Final security verdict:** PRODUCTION READY FOR THE CERTIFIED DEPLOYMENT SCOPE

---

## Attack surface review

| Surface | Status |
|---------|--------|
| Filesystem (media/docs/gallery/journal) | **Hardened** |
| Network fetch (ICS/docs/browser/flytying) | **Hardened** |
| Browser navigation policy | **Hardened** |
| Auth (PIN / API key / trusted device / uncensored) | **Hardened** |
| Tool sandbox (skills/cwd/dangerous) | Retained prior locks |
| Memory Authority / PRIMARY | Retained prior locks |
| Mission Control mutations | Retained + `compare_digest` |

---

## Filesystem review

| Issue | Severity | Fix |
|-------|----------|-----|
| Audio/VST/whisper `$HOME` via `fs.resolve_path` | CRITICAL/HIGH | `resolve_audio_library_path()` on AudioEngine + VST process + detect-language |
| Document learn absolute path | CRITICAL | `resolve_document_library_path()` — library/uploads only |
| Gallery GET symlink escape | HIGH | `generated not in path.parents` after resolve |
| Journal photo serve | HIGH | basename + `resolve_named_under` |
| Audio GET/delete `startswith` prefix bypass | HIGH | `relative_to` / parents check |
| Image upscale unconfined | HIGH | `resolve_image_library_path()` |
| VST plugin register arbitrary path | HIGH | Confine to `DATA_DIR/audio/vst_plugins` |

**Deferred (justified):** `fs.resolve_path` still allows `$HOME` for **coding/LSP/MCP tools only** — intentional single-operator project workflow. HTTP media routes no longer call it.

---

## Network / SSRF review

| Issue | Severity | Fix |
|-------|----------|-----|
| Document `fetch_web_page` / learn URL | CRITICAL | `assert_safe_fetch_url` + post-redirect re-check |
| ICS validate/save/scheduled fetch | CRITICAL | Shared URL guard |
| Flytying video discover fetch | CRITICAL | Shared URL guard |
| Browser `allow_risky` skipped all checks | HIGH | Scheme/private blocks **always**; risky only skips checkout heuristics |

Blocks: loopback, RFC1918, link-local, metadata, non-http(s), credentialed URLs, DNS-resolved private IPs.

---

## Authentication review

| Issue | Severity | Fix |
|-------|----------|-----|
| Unauthenticated uncensored reset | CRITICAL | `confirm=true` + API key when enabled + PIN session when lock on |
| Unauthenticated PIN setup race | CRITICAL | API key when enabled; overwrite requires `current_pin` |
| PIN verify timing | HIGH | `hmac.compare_digest` |
| Uncensored password min length 4 | HIGH | Minimum **12** |
| Trusted-device empty-IP match | HIGH | Require device id **and** matching stored IP; `compare_digest` on ids; unlock can register trust |
| API key `==` | MEDIUM | `hmac.compare_digest` |
| MC token `!=` | MEDIUM | `hmac.compare_digest` (AI-Platform) |

**Deferred (justified):** Full signed device-token redesign — incomplete feature now fail-closed without IP; adequate for single-operator LAN.

---

## Authorization / tool sandbox

Prior RC gates retained: skill argv default, dangerous Claude flag env-gated, tools cwd under PROJECT_ROOT/DATA_DIR, HA permissions, automation chat opt-in.

---

## Prompt injection / persistence / dependencies

| Area | Assessment |
|------|------------|
| Prompt injection | ACM teaching/provenance + Cap Bus assent retained; no new host injection sinks opened |
| Persistence | ACM corrupt-load fail-closed retained (v0.45.1) |
| Dependencies | No replacements this RC — prior packaging deferral stands; no CVE-driven swaps required for this pass |

---

## Red-team results (material)

Adversarial probes against deferred surfaces found and fixed: `/etc/passwd` via audio/docs/VST/upscale; SSRF to `127.0.0.1` / `169.254.169.254`; `file://` / `javascript:` browser; uncensored reset without auth; PIN setup race; trusted-device spoof without IP; journal wipe without confirm.

No remaining CRITICAL/HIGH without explicit deferral justification.

---

## Tests added

`tests/test_aria_host_production_audit.py` (now **18** gates), including:

- SSRF private/metadata/file blocks  
- Audio/document/image path confinement  
- Browser file/private/javascript blocks  
- PIN `compare_digest` presence  
- Uncensored min length 12  
- Trusted-device IP binding  

Locked into `scripts/ci_check.py`.

---

## Certification totals (×2)

| Suite | Result |
|-------|--------|
| Host security | **18 passed** ×2 |
| Aria Core + host | **79 passed** ×2 |
| Aria ACM promotion | **198 passed** ×2 |
| Aria CI (`ci_check.py all`) | **681 passed**, 1 skipped ×2 |
| ACM full | **596 passed** ×2 |
| ACM learning cert | **PASS** ×2 |
| AI-Platform | **798 passed** ×2 |

---

## Performance impact

Negligible: path `relative_to` checks and URL DNS resolution on outbound fetches only.

## Compatibility impact

- Uncensored passwords must be ≥12 characters on new setup.  
- VST plugins must live under `data/audio/vst_plugins/`.  
- Journal non-merge import requires `confirm_wipe=true`.  
- ICS/document URLs to private hosts are rejected (use public HTTPS feeds).  
- Trusted LAN devices must register with IP at unlock.

---

## Remaining deferred items (explicit)

1. **Coding-tool `$HOME` via `fs.resolve_path`** — intentional for LSP/MCP; HTTP isolated.  
2. **Signed trusted-device tokens** — fail-closed IP binding sufficient for certified scope.  
3. **MC GET auth if bound beyond loopback** — default bind loopback; document.  
4. **Full-tree stale pytest backlog** — outside shipped CI; not SoT security.  
5. **God-module split / Cap Bus assent UX / packaging lockfile** — not security RC scope.

---

## Risk matrix (after RC-S1)

| Risk | Level |
|------|-------|
| Arbitrary file read via media/docs HTTP | **Low** |
| SSRF to LAN/metadata | **Low** |
| Browser local/private navigation | **Low** |
| Auth bypass (PIN/uncensored/API key) | **Low** |
| Trusted-device spoof | **Low** |
| Memory Authority bypass | **Low** (prior) |

---

## Final security verdict

**PRODUCTION READY FOR THE CERTIFIED DEPLOYMENT SCOPE**
