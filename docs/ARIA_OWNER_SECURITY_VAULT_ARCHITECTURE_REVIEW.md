# ARIA — Owner Security Vault Architecture Review

**Status:** PRE-IMPLEMENTATION REVIEW — NO CODE  
**Date:** 2026-08-12  
**Reviews:** `docs/ARIA_OWNER_SECURITY_VAULT_ARCHITECTURE.md`  
**Checkpoint preserved:** `docs/evidence/exhaustive_functional_verification/EXHAUSTIVE_CHECKPOINT.json`  
**Integrity at review:** clean / 100  

**Scope:** Correctness, security, usability, recoverability, performance, Aria compatibility.  
**Out of scope:** Implementation, migration execution, credential changes, Journal format changes.

---

## 1. Architecture verdict

### CONDITIONAL APPROVE — required changes before M1

The proposed direction is **correct and Aria-compatible**:

- One owner identity and house-wide session
- Vault root key ≠ master password ≠ portable export password
- ACM never holds secrets
- Host-managed Git/browser remain outside the vault by default
- Exhaustive verification checkpoint at Journal encrypted import is preserved
- Aug 8 exports stay sealed and unrecovered

The document is **not yet implementation-ready**. Several decisions are underspecified in ways that would create lockout risk, migration risk, or silent security flaws if coded as written.

**Do not start M1 until the Required Changes (section 2) are answered in an architecture amendment or addendum.**

---

## 2. Required changes (blockers before M1)

| ID | Blocker | Why |
| --- | --- | --- |
| R1 | **Recovery must be an explicit product decision with a concrete mechanism** | §18 currently lists options without choosing. “Forgot master password” cannot be deferred to implementation. |
| R2 | **PIN ↔ Master Password relationship must be chosen (A–F) with strength rules** | Migrating a 4–6 digit PIN into vault-root equivalence would fatally weaken the vault. |
| R3 | **Vault crypto must pin exact primitives (no “Argon2id if available”)** | Ambiguity causes incompatible vault files and review failure. **Required pin:** Argon2id via `argon2-cffi` (or document vendored equivalent) with fixed `m/t/p` + 16-byte random salt stored next to wrapped root; wrap Vault Root Key with Unlock Key; encrypt entries with AES-GCM (preferred) or Fernet with unique nonce per entry; authenticate vault metadata with AEAD or HMAC over sealed blob. PBKDF2 ≥600k only as documented emergency fallback with upgrade-on-unlock path — not an indefinite dual standard. |
| R4 | **`jarvis.env` dependency map must be part of the migration contract** | Including secrets **outside** `secrets_bus.SECRET_FIELDS`, subprocess `os.environ.copy()` paths, and `PGVECTOR_DATABASE_URL`. |
| R5 | **Lock/revocation must define pending-operation semantics** | Tools, HA, Git, Journal export mid-flight need fail-closed rules. |
| R6 | **Secret memory model must be honest** | No false claim of guaranteed zeroization in Python. |
| R7 | **Health LAN-API-key step-up must be scheduled as a hard correction** | Prefer a small pre-vault repair when PIN lock is enabled; must not ship vault while preserving this substitution. |
| R8 | **Migration phase order adjustment** | See §18 — env inheritance / Health step-up / automation secret hardening before or with M2. |
| R9 | **Capability permission catalog must be normative, not illustrative** | M1 needs a versioned permission list. |
| R10 | **Backup/recovery packaging for vault + recovery material** | Ciphertext-only backups without recovery material = Jeff locked out of his own backup. |

Non-blockers (should track, may land in later phases): gallery `?api_key=` leak path, HF wget process-table exposure, `enable-lan.sh` stdout echo, session-file plaintext tokens, Postgres default password.

---

## 3. Security risks

| Risk | Severity | Architecture handling | Review finding |
| --- | --- | --- | --- |
| Plaintext `jarvis.env` theft | High | Migrate to vault | Correct; must not delete env until dual-read verified |
| Health step-up = LAN API key | High (dormant while `JARVIS_PIN_LOCK=0`) | Remove | Must be explicit gate; see §6 |
| Unlimited PIN guessing | High | Mentioned rate-limit | Must port uncensored-style lockout **without** permanent lockout |
| Subprocess inherits full env | Medium–High | Not addressed | **Gap** — vault useless if tools still get `os.environ.copy()` of secrets |
| `JARVIS_AUTOMATION_SECRET` sole gate on exempt route | High | Migrate to vault | Must remain separately audited; not “just another key” |
| Master password used as export password | High | Explicitly forbidden | Keep as invariant + UX tests |
| Permanent lockout | Critical | “Must not” | Recovery design (R1) is the only real mitigation |
| Weak PIN as vault root | Critical | “Strengthen” hand-wave | R2 — must not derive vault root from 4-digit PIN |
| Session token file theft | Medium | Hash verifiers | Keep in M1 design |
| ACM/log secret leakage | High | Forbidden | Add negative tests (R20) |

---

## 4. Recovery design (CRITICAL)

### Product decision required

Jeff must choose **one** of the following **before M1**:

| Option | Usability | Security | Fits Aria? |
| --- | --- | --- | --- |
| **A. Recovery key file** (e.g. `aria-owner-recovery.key`, printed/USB, created at vault init) | High | High if stored offline | **Recommended default** |
| **B. Offline recovery phrase** (BIP39-style) | High if written down | High | Acceptable alternative |
| **C. Encrypted recovery bundle** in backup (unlockable only with recovery key) | Medium | High | Complements A/B |
| **D. Deliberate unrecoverable** (“lose password = lose vault secrets”) | Poor for daily driver | Highest confidentiality | **Only if Jeff explicitly accepts data loss** — conflicts with “don’t permanently lock Jeff out” unless combined with non-vault escape for non-secret Aria use |
| **E. Anyone-local recovery** (no secret) | Highest | **Unacceptable** | Reject |

### Required architecture amendment content

1. Chosen option (A or B recommended; C as backup packaging).  
2. Recovery unlocks **Vault Root Key wrap**, not a backdoor into every external service.  
3. Using recovery **rotates** master password and invalidates old unlock key.  
4. Recovery material shown **once** at vault init; Jeff confirms possession (Jeff-attended).  
5. Aria without recovery material still boots for non-secret Rooms; vault-backed capabilities fail closed with honest UI.  
6. **Portable Journal/Health files are unaffected** by master recovery (still need their own passwords).

**Verdict on “Forgot password = permanently lost Aria”:**  
Must **not** mean Aria is unusable. It may mean **vault secrets are unrecoverable without recovery material**. That distinction must be written into the architecture.

---

## 5. PIN interaction

### Current facts

- PIN: 4–6 digits, PBKDF2 120k, hashed in `pin.json`
- Lock Now = revoke sessions only; **no permanent lockout**
- Unlock has **no** attempt throttling (unlike Uncensored)
- Trusted device can bypass middleware
- Health step-up can accept PIN **or** LAN API key

### Required decision (architecture must pick)

**Recommended: hybrid B + D (not A, not E alone)**

| Role | Mechanism |
| --- | --- |
| **Vault root / master** | Strong master password (≥12, or passphrase) — never the 4–6 digit PIN |
| **Convenience unlock (B)** | After master set, optional PIN may unlock an **already provisioned** device session within policy (short TTL, trusted device) — PIN unwraps a **device-bound wrapped session key**, not the Vault Root Key directly from PIN alone |
| **Step-up (D)** | PIN or master re-entry for high-risk ops once unlocked |
| **Deprecate (E) alone** | Reject — breaks existing Security UX without migration |

**Forbidden:** deriving Vault Root Key solely from a 4–6 digit PIN (equivalent to a weak master).

Uncensored password (≥12) should become a **capability gate / step-up**, not a second house unlock — eventually unified under owner session + step-up catalog.

---

## 6. Health step-up correction

### Why it exists

Docstring: *“reuse Aria PIN/API key/face/trusted device; no redesign.”* Intent was reuse, not a new Health password store.

### Problem

LAN API key is a **machine access** secret already held by any authorized LAN client. Using it as step-up **collapses presence confirmation into network auth** — exactly what step-up was meant to add. Also uses `==` instead of `hmac.compare_digest`.

### Required correction

1. **Remove API key as Health step-up authenticator** when PIN/master is configured.  
2. After vault: Health step-up consumes **Owner Session + step-up re-auth** (master or PIN per policy).  
3. Step-up catalog stays for PHR export/delete/cloud consult/etc.  
4. Prefer a **small pre-M1 or parallel repair** when enabling `JARVIS_PIN_LOCK` — do not wait for full vault if PIN lock is turned on sooner.  
5. Grant model: kill shared `"local"` bucket and over-broad `*` grants as part of M4.

---

## 7. Session / revocation model

Architecture proposes unified revoke. Review requires these states:

| State | Meaning |
| --- | --- |
| `OWNER_LOCKED` | No vault root in memory; protected ops denied |
| `OWNER_UNLOCKED` | Session valid; normal capabilities |
| `OWNER_STEP_UP` | Short elevation for high-risk |
| `OWNER_REVOKED` | Explicit invalidate (Lock / password change / recovery) — stronger than idle lock messaging |

### On Lock / Revoke — required semantics

| Asset | Behavior |
| --- | --- |
| Active Rooms | Stay visible; protected actions fail with “Unlock Aria” |
| Open dialogs | Cancel or disable confirm; no secret-bearing submit |
| Pending Tools | **Fail closed** if they need vault secrets; non-secret tools may finish |
| Background jobs | Checkpoint; do not pull new secrets after revoke |
| Cached secrets | Drop immediately |
| Capability handles | Invalidate; no reuse after revoke |
| External HA/Git calls in flight | Let TCP finish if already sent; no new authenticated calls |
| Browser / Playwright | Leave browser profile; do not inject Aria secrets after lock |
| API tokens in vault | Inaccessible until unlock |
| Uncensored / Health grants | Cleared with unified revoke |

**Gap in original arch:** pending Journal encrypt/import mid-password-prompt — cancel cleanly; do not write partial imports.

---

## 8. Secret memory model

### Honest boundary

Python cannot guarantee secure erasure of all string/bytes copies. Architecture must say:

1. **Security boundary = process + OS user**, not “secrets vanish from RAM.”  
2. Minimize copies; prefer `bytearray` where practical; avoid logging/repr.  
3. On lock: drop references to root key and entry cache; force GC best-effort.  
4. On restart/crash: memory gone with process — vault stays locked at rest.  
5. **Do not** claim military-grade zeroization.

### Lifetime

| Event | Secrets in memory |
| --- | --- |
| Unlock | Root key loaded; entry cache empty |
| Get credential | Decrypt into short-lived buffer; optional TTL cache per entry id |
| Idle / Lock | Clear root + cache |
| Crash / kill | Lost with process |

KDF only at unlock / step-up / password change — **never** per Room nav or per HA poll.

---

## 9. `jarvis.env` dependency map (summary)

Full map evidence from 2026-08-12 read-only review (no values).

### Credential-bearing keys present (examples)

`JARVIS_API_KEY`, `JARVIS_AUTOMATION_SECRET`, `JARVIS_HA_TOKEN`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `HF_TOKEN`, `POSTGRES_PASSWORD`, `PGVECTOR_DATABASE_URL` (password inline).

### Expected by code but often absent

`ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `JARVIS_MESHY_API_KEY`, `JARVIS_JOURNAL_AT_REST_PASSWORD`, `JARVIS_UNCENSORED_PASSWORD`, `JARVIS_GRAPH_PASSWORD`, …

### Critical consumers beyond Integrations UI

| Path | Risk |
| --- | --- |
| `jarvis/auth.py` | LAN/API middleware |
| `jarvis/home_assistant.py` | Bearer HA |
| Automation inbound | Sole secret on exempt route |
| `cloud_live_voice` / bridges | Provider keys |
| `tools/runner.py`, `tools/registry.py` | **`env=os.environ.copy()`** — child gets all secrets |
| `sandbox.py` | Allowlist — good pattern to extend |
| Docker HA/Memgraph | Generally no `-e` secrets (good) |

### Migration prerequisite

Before cutting vault reads:

1. Inventory every `os.getenv` of secret keys (re-run).  
2. Introduce **secret provider API** used by auth, HA, automation, providers, tools.  
3. Stop wholesale `os.environ.copy()` for tool runners (filter or inject only needed keys).  
4. Dual-read: vault if unlocked+present else env.  
5. Never delete `jarvis.env` in M1–M5.

---

## 10. Credential ownership model

| Class | Examples | Vault? |
| --- | --- | --- |
| **ARIA-MANAGED** | Provider API keys, HA token, LAN key, automation secret, graph/postgres passwords, uncensored gate | **Yes** (phased) |
| **HOST-MANAGED** | `gh` / GitHub CLI, OS user, SSH keys | **No** (default) |
| **EXTERNAL-SERVICE-MANAGED** | OAuth provider sessions, Cloud Live ephemeral tokens minted from Aria-managed keys | Ephemeral not stored; source keys Aria-managed |
| **BROWSER-MANAGED** | Site cookies in Playwright profile | **No** |
| **PORTABLE-FILE** | Journal/Health encrypted export passwords | **No** (optional future opt-in store of *export* password is separate product decision) |

Do not force Git or browser cookies into the vault “for completeness.”

---

## 11. Capability authorization

### Required model: **operation-scoped capabilities**, not Room-superuser

Rooms may request multiple capabilities; possessing “enter Health Room” ≠ `health.export_phr`.

### Normative starter catalog (must version)

```
owner.unlock / owner.lock / owner.step_up / owner.recovery
security.modify
vault.meta.read / vault.secret.use / vault.secret.reveal / vault.secret.write / vault.rotate
journal.read / journal.write / journal.export_portable / journal.import_portable
health.read / health.write / health.export / health.delete / health.cloud_consult
integrations.read / integrations.use / integrations.modify
ha.read / ha.actuate / ha.token.reveal
git.read / git.write_destructive
browser.use / browser.profile.export
automation.webhook.invoke / automation.secret.reveal
lan.auth / lan.key.rotate
providers.use / providers.modify
uncensored.enable
```

Authorization checks **capability + risk**, then vault get if needed.

---

## 12. Step-up model

### Risk classes

| Class | Examples | Auth |
| --- | --- | --- |
| **LOW** | Enter unlocked Room; list “configured?” metadata; ordinary generation with already-configured key | Owner unlocked |
| **MEDIUM** | Actuate HA device; run Coding non-destructive; use Browser | Unlocked (policy may tighten) |
| **HIGH** | Reveal secret in UI; rotate key; export encrypted Journal/Health; Git push; disable integration | Step-up |
| **CRITICAL** | Change master password; recovery use; delete PHR; wipe Journal replace-all; disable security; export_bundle with values; destroy vault | Step-up + explicit confirm |

**Usability rule:** step-up TTL (e.g. 2–5 minutes) covers a burst of HIGH ops; not every click.

---

## 13. Portable export separation

**Confirmed correct** in architecture:

- Vault ≠ portable export password  
- Never silent master→export  
- Aug 8 files need original export-time password; unrecovered  

### Future UX (M5)

- Default: Jeff chooses export password; UI states “not stored by Aria”  
- Optional: generate one-time password and **show once** for Jeff to save  
- Optional later: “also store this export password in vault” — explicit checkbox + step-up  

### Journal import checkpoint after vault work

**Correct next tests:**

1. **Isol:** current export → import (known disposable password)  
2. **Owner:** new Export encrypted (Jeff chooses/saves password) → Import encrypted → STOP WAIT FOR JEFF  
3. **Do not** attempt Aug 8 recovery  

Preserve `EXHAUSTIVE_CHECKPOINT.json`; do not restart from Room 1.

---

## 14. ACM boundary

Architecture rule is correct. Review adds enforcement requirements:

| Surface | Must not contain secrets |
| --- | --- |
| ACM memories / search / snapshots / conflicts | Yes |
| Activity Center | Yes |
| Diagnostics / debug_bundle | Yes (already mostly clean) |
| Chat transcripts | Redact pasted keys where detected |
| Integrity findings | Report “secret-shaped material” without printing values |

Negative tests required before M2 cutover.

---

## 15. Backup / recovery

### Required design (pre-M1 amendment)

| Artifact | Protection |
| --- | --- |
| Vault ciphertext DB/file | Included in Aria backup as opaque |
| Recovery key / phrase | **Not** only inside the same unencrypted backup; Jeff holds offline copy; optional encrypted recovery bundle |
| Pre-migration `jarvis.env` snapshot | Encrypted or 0600 offline copy before M2 |
| Restore drill | Isol restore → unlock with recovery → verify one capability |

Ciphertext backup without recovery material ⇒ Jeff cannot use backup after password loss — must be stated in UI at vault init.

---

## 16. Performance

Architecture targets are right. Review adds:

| Op | Rule |
| --- | --- |
| Unlock | One KDF; async so UI doesn’t freeze house chrome |
| Credential get | Memory cache while unlocked; **no KDF** |
| Room enter | No vault I/O unless Room needs a secret immediately |
| Lock | Drop caches; cheap |
| Tools | Must not re-init vault per tool |

Measure later against current baselines (Room entry already repaired once — do not regress).

---

## 17. Failure behavior

| Event | Required behavior |
| --- | --- |
| Explicit lock | Revoke all; clear memory; Rooms stay; secrets unusable |
| Idle lock | Same |
| Browser refresh | Re-bind session cookie/header if still valid **or** locked — pick one and document; prefer short server TTL |
| Room change | No re-auth |
| App/backend restart | **Locked** |
| Frontend crash | Server session may remain until idle; next UI attach respects TTL |
| Duplicate tabs | Shared owner state; lock broadcasts |
| Pending Journal encrypt | Abort without writing live Journal |
| Pending Git/HA/Tool needing secret | Fail closed after revoke |
| Wrong master password | Honest error + throttling |
| Vault corruption | Fail closed; offer backup restore |

---

## 18. Migration ordering

### Original

M0 → M1 empty vault+PIN bridge → M2–M3 env secrets → M4 revoke+Health → M5 Journal UX → M6 cut plaintext → resume exhaustive

### Corrected recommendation

| Phase | Content |
| --- | --- |
| **M0** | Architecture + **this review** + recovery/PIN decisions (Jeff) |
| **M0b** | Optional **small** Health step-up fix (remove API key path) — independent of vault |
| **M1** | Security Service + Owner Session + empty vault + **recovery material UX** + hashed session verifiers + unlock throttling (non-permanent) |
| **M1b** | Secret provider facade; **filter tool subprocess env** (sandbox allowlist pattern) |
| **M2** | Migrate Integrations bus keys (dual-read) |
| **M3** | HA + LAN + automation secret (extra care on automation inbound) |
| **M4** | Unify revoke (PIN/uncensored/health grants); finish Health step-up |
| **M5** | Journal/Health portable UX honesty |
| **M6** | Stop writing migrated plaintext; retain rollback snapshot |
| **Resume** | Exhaustive verification at Journal checkpoint |

**Why reorder:** migrating secrets while children still inherit full `os.environ` and Health accepts LAN key as step-up leaves the largest holes open during “secure” migration theater.

---

## 19. Rollback

Architecture dual-read approach is sound. Review requires:

1. Feature flags per phase  
2. Pre-M2 encrypted snapshot of `jarvis.env`  
3. Ability to force `SECRET_SOURCE=env`  
4. No deletion of old files until Jeff ACK + Integrity clean/100  
5. If verify fails → automatic prefer-old + stop migration  

---

## 20. Testing

Add to architecture test list:

- Recovery key unlock + password rotate  
- PIN cannot unwrap vault root alone (if hybrid)  
- Health step-up rejects LAN API key  
- Tool subprocess env does not contain vault/env secrets (allowlist)  
- Lock invalidates in-flight capability handles  
- ACM ingest rejects secret-shaped payloads  
- Portable export password ≠ master (fuzz UX paths)  
- Migration dual-read / rollback  
- Exhaustive checkpoint file still present and unchanged in meaning  

Disposable secrets only. Never Jeff’s real credentials in CI.

---

## 21. Implementation prerequisites (checklist)

Before any vault code:

- [ ] Jeff accepts recovery model (R1)  
- [ ] Jeff accepts PIN/master split (R2)  
- [ ] Crypto primitives pinned (R3)  
- [ ] `jarvis.env` dependency map filed under evidence (this review §9 + agent map)  
- [ ] Exhaustive checkpoint still points at Journal encrypted import  
- [ ] Integrity clean/100  
- [ ] Explicit written authorization to begin M1  

---

## 22. Owner experience

Target feel remains: **“I unlocked Aria.”**

Avoid:

- Per-Room unlock  
- Master password on every HA click  
- Ambiguous “password” prompts that don’t say *export* vs *unlock* vs *step-up*

Prefer:

- One lock indicator in shell  
- Step-up only on HIGH/CRITICAL  
- Portable export prompts that name **export file password**

---

## 23. STOP

This review does **not** authorize implementation.

**Verdict:** Conditional approve — resolve R1–R10 in an architecture amendment, then Jeff may authorize M1.

**Do not:** implement vault, migrate `jarvis.env`, change Security/Health/ACM/Journal crypto, or resume exhaustive verification past the Journal credential gate without Jeff.

**Preserve:** `EXHAUSTIVE_CHECKPOINT.json` — Journal → More → Import encrypted.

**Aug 8 exports:** unchanged; original password required; not recoverable via vault.
