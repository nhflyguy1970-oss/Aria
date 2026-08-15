# ARIA Phase 7.3 — Credential-Gated Workflow Revalidation

**Date:** 2026-08-08  
**Nature:** Validation-gap audit only — no feature work, no refactoring.  
**Basis:** Phase 7.2 Owner Residency Certification + residency artifacts under `/tmp/aria-residency/` + Living Workspace product surfaces.

---

## Executive finding

Phase 7.2 certified the house for **normal owner use** with strong evidence for Rooms, Tools, House Controls, coding, soaks, and contamination.

It did **not** fully close credential-gated end-to-end workflows. Several paths were entered (Room loaded, control clicked, password **prompt cancelled**) without completing authenticate → work → persist → return → verify.

That is a **validation gap**, not a known product defect.

---

## 1. Credential Inventory

Every Jeff-reachable workflow that requires a secret, PIN, token, password, API key, or external login.

| ID | Feature | Room / surface | Auth method | Depends on |
|----|---------|----------------|-------------|------------|
| C01 | Journal encrypted export | Journal | Owner-chosen export password (`ariaPrompt`) | Local encrypted file |
| C02 | Journal encrypted import | Journal | Same password as export (`ariaPrompt`) | Encrypted export file |
| C03 | Health step-up | Health | Aria PIN (`ariaPrompt` / form) | PIN configured + `JARVIS_PIN_LOCK` / health gate |
| C04 | Health encrypted backup create | Health · Backups | Backup password (form) | Local backup store |
| C05 | Health encrypted backup restore | Health · Backups | Backup password + confirm | Existing backup |
| C06 | Security PIN setup | Security | New PIN (form) | Owner chooses PIN |
| C07 | Security lock / unlock | Security / lock screen | PIN | `pin_configured` + lock enabled |
| C08 | Trusted device enroll / revoke | Security | Prior PIN unlock (+ optional face) | PIN session |
| C09 | Uncensored mode set password | Uncensored / House Control | New password (≥12) | Local uncensored vault |
| C10 | Uncensored mode unlock | Uncensored | Password | Prior password set |
| C11 | Uncensored clear password | Uncensored | Confirm + reset | Existing password |
| C12 | LAN API key gate | Any (non-localhost) | Jarvis API key modal | `api_key_required` + not localhost-exempt |
| C13 | Integrations secrets (Gemini / OpenAI / Anthropic / OpenRouter / HF / Meshy) | Integrations / Providers | Paste API keys · save · test | External providers |
| C14 | Cloud Live / Gemini Live | Voice | Gemini (or related) key usable | C13 |
| C15 | Home Assistant token | Smart Home / HA panel | Long-lived access token | HA URL + token |
| C16 | Git remote auth (push/PR via `gh`) | Coding / Git tool | `gh auth` / SSH / credential helper | GitHub account |
| C17 | Browser site logins | Browser Room | Site username/password / SSO cookies | Jeff’s sites |
| C18 | Experimental OAuth profiles | Integrations (experimental) | OAuth (placeholder / future) | External IdP |

**Out of scope as “credentials” (but owner confirms):** Restart Server, Coding Apply, theme, Free VRAM warnings, activity high-stakes confirms. These were exercised with `ariaConfirm` (often cancel). They are **not** credential gaps.

---

## 2. Coverage Matrix

Evidence codes:
- **Cert** = `docs/ARIA_PHASE7_OWNER_RESIDENCY_CERTIFICATION.md`
- **EXPORT59** = residency console / `EXPORT59.json` (journal enc prompt + cancel; Health Print/Export UI)
- **OV53** = House Controls click (uncensored, security) without password completion
- **A/B*** = Room entered (security, etc.) without auth completion
- **Live API** = `GET /api/security/lock/status` (2026-08-08): `pin_configured=false`, `pin_lock_enabled=false`, `lock_capable=false`
- **Live API** = `/api/live`: `api_key_required=true`, `api_key_localhost_exempt=true` (residency used `127.0.0.1`)

| ID | Fully validated | Partially validated | Deferred / skipped | Evidence | Why incomplete |
|----|-----------------|---------------------|--------------------|----------|----------------|
| C01 Journal enc export | | **Partial** | | Cert claims “encrypted journal export ariaPrompt **cancel**”; EXPORT59: `ariaPrompt:true` then cancel | Prompt UI only — **no** password submitted, **no** file produced, **no** reopen |
| C02 Journal enc import | | | **Needs rerun** | No residency artifact shows import with password | Never run to completion |
| C03 Health step-up | | | **Needs rerun** | Health Room entered (LIFE51, A/B); Live API `pin_configured=false` | Cannot complete step-up without PIN; no PIN entry evidence |
| C04 Health backup create | | **Partial** | | EXPORT59: Print/Export UI opened | UI reached; no backup password submitted / file verified |
| C05 Health backup restore | | | **Needs rerun** | No restore-with-password evidence | Never completed |
| C06 Security PIN setup | | **Partial** | | Security Room + `ctrl:security` entered (A50, OV53, AB*) | Panel loaded; Live API shows PIN **not** configured — setup never completed |
| C07 Security lock/unlock | | | **Needs rerun** | `lock_capable=false`, `pin_configured=false` | Lock cycle impossible until C06 + env enable |
| C08 Trusted devices | | | **Needs rerun** | Security panel empty-state copy only | No enroll/revoke with PIN session |
| C09 Uncensored set password | | | **Needs rerun** | OV53: `ctrl:uncensored` clicked → providers; DEPTH57: no aria password dialog | Toggle/control reached; password **not** set in residency |
| C10 Uncensored unlock | | | **Needs rerun** | Depends on C09 | No unlock evidence |
| C11 Uncensored clear | | | **Needs rerun** | No clear-password confirm completion | — |
| C12 LAN API key | | | **Needs rerun** (conditional) | Residency on localhost; exempt | **Skipped by environment** — never hit non-localhost LAN gate |
| C13 Integrations secrets | | **Partial** at most | **Needs rerun** | Providers/Integrations surfaces visited; no save+test+persist cycle with owner keys in residency logs | Room/control presence ≠ credential workflow |
| C14 Cloud Live | | | **Needs rerun** | Voice Room entered; no Cloud Live auth success evidence in residency | Needs usable cloud key |
| C15 Home Assistant | | | **Needs rerun** | No HA token paste/save/connect evidence in Phase 7.2 residency artifacts | Token never supplied during residency |
| C16 Git `gh` auth | | | **Needs rerun** (if remotes used) | Coding propose/apply on local files worked **without** remote auth | Local coding ≠ authenticated push/PR |
| C17 Browser site logins | | | **Needs rerun** | Browser navigate/screenshot to public example (earlier #41) | No owner account login on real sites |
| C18 OAuth experimental | | | **Deferred** | Product marks experimental / placeholder | Not required for current owner daily driver unless Jeff uses it |

### Confirmed fully validated (non-secret owner confirms)

| Workflow | Evidence |
|----------|----------|
| Restart Server → ariaConfirm → **Cancel** | OV53 `restart_confirm cancelled-aria` |
| Coding propose → Apply → undo (no external creds) | CODE54, CODE55b |
| Journal **plain** export (no password) | Button exists; not the encrypted path |

---

## 3. Rerun Plan (minimal, complete authenticated coverage)

**Law:** Same Phase 7 residency law — live as Jeff in Living Workspace; no internal API shortcuts for *living* proof. Credentials are supplied by Jeff (or a dedicated owner secrets briefing) at the start of the session.

### Prep (once)

1. Jeff provides (or confirms already set) only what he uses:
   - Aria PIN (or consent to set one for the session)
   - Journal/Health backup test passwords (throwaway OK)
   - Uncensored password (throwaway OK if he uses the feature)
   - Any cloud API keys he actually uses
   - HA token if Smart Home is in daily use
   - `gh auth status` OK if he pushes from Aria
2. Enable PIN lock for the rerun window if C06–C08 are in scope (`JARVIS_PIN_LOCK=1` + set PIN via Security UI as Jeff).
3. For C12: one pass from a LAN URL (not `127.0.0.1`) **or** explicitly mark N/A if Jeff never uses LAN.

### Session shape (single half-day residency block)

| Block | Duration | Workflows | Natural day script |
|-------|----------|-----------|-------------------|
| **A — Vaults** | ~45–60 min | C01→C02, C04→C05 | Morning Journal: encrypted export → leave Room → return → encrypted import (merge + replace once) → verify bullets. Health: create password backup → leave → restore preview → restore merge → verify. Cancel once on each password prompt to prove cancel. |
| **B — House locks** | ~30–45 min | C06→C08, C09→C11 | Security: set PIN → lock → unlock → (optional) trust device → revoke. Uncensored: set password → enable → use one harmless toggle → disable → clear password → set again. Restart mid-unlock attempt once; verify no orphan dialog. |
| **C — Providers Jeff uses** | ~45–90 min | C13, C14, C15, C16 as applicable | Integrations: open each **configured** provider → test connection → leave → return → still configured. Voice Cloud Live only if key present. HA: paste token → save → toggle one light/scene Jeff owns → reopen. Coding: one `gh`-backed action if remotes are used. |
| **D — Edge access** | ~20–30 min | C12, C17 | From phone/LAN hostname: API key modal → enter key → work → refresh. Browser: log into one real site Jeff uses → screenshot → leave Browser → return → session still useful or honest re-login. |
| **E — Gate** | ~20 min | Integrity + A/B smoke | Integrity Score clean; Front Door → each touched Room; no native dialogs; no stale confirms. |

**Skip with written N/A (Jeff signs):** any provider Jeff does not use (e.g. Meshy, Anthropic, OAuth experimental). N/A must be explicit — not silent skip.

### Success criteria (per workflow)

Authentication succeeds; workflow completes; cancel works; retry works; leave/return persistence; restart does not orphan sessions; no browser-native password dialogs; Integrity clean.

---

## 4. Final Recommendation

### After credential-gated workflows are revalidated, can Owner Residency be considered complete with no remaining known validation gaps?

**Not yet — Phase 7.2 certification remains valid for non-credential residency, but a known validation gap remains until Phase 7.3 rerun completes.**

**Why not fully complete today**

Evidence shows **cancel-only** or **Room-enter-only** coverage for secret-bearing paths (especially C01 cancel, C06/C09 enter-without-set, C12 never hit on localhost, C13–C17 not end-to-end with owner secrets). Missing evidence is treated as incomplete validation, not as proof of failure.

**What remains**

Execute the rerun plan above for every workflow Jeff actually uses (minimum: C01–C02, C04–C05 if Health backups matter, C06–C07 if PIN will be enabled, C09–C10 if uncensored is used, plus any of C13–C17 in daily life). Record pass/fail with Living Workspace evidence. Then answer this question again with **Yes** only if every in-scope row is Fully validated or explicit N/A.

**No code changes recommended** from this audit — no engineering defect was demonstrated; the gap is coverage.

---

## Appendix — Artifact cross-check

| Artifact | Credential relevance |
|----------|----------------------|
| `ARIA_PHASE7_OWNER_RESIDENCY_CERTIFICATION.md` | Explicitly “encrypted journal export ariaPrompt **cancel**” |
| EXPORT59 run | Journal enc prompt cancelled; Health export UI; no password submit |
| OV53 | `ctrl:uncensored`, `ctrl:security` navigation only |
| A50 / AB55–57 | Security Room hash OK — not PIN lifecycle |
| CODE54 | Local file coding — no GitHub auth |
| soak45m / soak2h | Room cycling — no credential completion |
| Live `/api/security/lock/status` | PIN not configured on this host at audit time |
| Live `/api/live` | LAN key required but localhost exempt during residency |
