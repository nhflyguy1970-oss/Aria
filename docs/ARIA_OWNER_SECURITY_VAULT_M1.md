# ARIA — Owner Security Vault M1

**Status:** M1 COMPLETE — EMPTY VAULT + OWNER SESSION FOUNDATION  
**Date:** 2026-08-12  
**Authorization:** Owner Security Vault M1 Authorization (Jeff)  
**Architecture:** `docs/ARIA_OWNER_SECURITY_VAULT_ARCHITECTURE.md`  
**Review:** `docs/ARIA_OWNER_SECURITY_VAULT_ARCHITECTURE_REVIEW.md`  

**Not in M1:** credential migration, `jarvis.env` changes, Journal crypto, ACM storage changes, exhaustive verification resume.

---

## 1. Implementation scope

| Delivered | Not delivered |
| --- | --- |
| Empty Owner Vault (`aria-owner-vault-v1`) | M2/M3 secret migration |
| Argon2id → wrap Vault Root Key → AES-GCM entries | Live Integrations/HA/LAN secrets in vault |
| Generated recovery key (shown once) | Production vault setup for Jeff (later: live empty vault, 2026-08-13) |
| Owner session: LOCKED / UNLOCKED / STEP_UP / REVOKED | Full UI lock screen redesign |
| PIN hybrid: soft unlock + step-up only | PIN as vault-root equivalent (forbidden) |
| Capability catalog + authorize() | Per-Room wiring of every API |
| Subprocess env allowlist/denylist | Moving secrets out of env |
| ACM boundary helpers | ACM code rewrite |
| Health step-up: remove LAN API key authenticator | Full Health auth migration |
| HTTP API under `/api/owner-security/*` | Journal portable export UX (M5) |
| Isolated tests + perf measurements | Exhaustive verification resume |

---

## 2. Cryptographic choices (pinned)

| Layer | Choice |
| --- | --- |
| KDF | **Argon2id** via `argon2-cffi` (`hash_secret_raw`, `Type.ID`) |
| Parameters | `t=3`, `m=65536` KiB (64 MiB), `p=4`, `hash_len=32`, `salt_len=16` |
| Fallbacks | **None** — no PBKDF2 fallback |
| Vault Root Key | 32-byte `os.urandom`, independent of password |
| Wrap | AES-GCM (cryptography) under unlock key derived from master or recovery |
| Entries | AES-GCM per entry, AAD = entry id |
| Format | `aria-owner-vault-v1` |
| Master password | Never stored; never used as entry key directly |
| Recovery key | 32-byte random; formatted hex groups; plaintext not retained after setup response |

KDF executes only at: setup, unlock, step-up (master path), password change, recovery.

Module: `jarvis/security/owner/crypto.py`

---

## 3. Owner state model

| State | Meaning |
| --- | --- |
| `OWNER_LOCKED` | No authorized session; protected ops denied |
| `OWNER_UNLOCKED` | House-wide session; normal capabilities per catalog |
| `OWNER_STEP_UP` | Short elevation for HIGH/CRITICAL |
| `OWNER_REVOKED` | Transient during hard lock — sessions/handles cleared |

Restart / process death → always locked (root not persisted in memory).

---

## 4. Session state machine

```
[no vault] --setup(master)--> UNLOCKED (+ recovery key once)
UNLOCKED --lock(hard)--> LOCKED (root wiped)
UNLOCKED --lock(soft)--> LOCKED soft (root stays in memory)
LOCKED soft --PIN--> UNLOCKED   (PIN never reads vault file)
LOCKED hard --master--> UNLOCKED (Argon2id + unwrap)
LOCKED --recovery key + new master--> UNLOCKED (re-wrap)
UNLOCKED --step-up--> STEP_UP (ttl)
any lock/revoke --> capability handles invalidated
```

Session tokens stored as **SHA-256 verifiers** in `data/security/owner/sessions.json` (production path when used). Failed auth: temporary backoff only — **no permanent lockout**.

---

## 5. Recovery model

1. At vault init: generate recovery key; return once in setup response.  
2. Jeff must `POST /api/owner-security/recovery/acknowledge` with `stored: true`.  
3. At rest: only recovery-wrapped root (Argon2id + AES-GCM) — not plaintext recovery key.  
4. Recovery: unwrap root with recovery key → re-wrap under new master → unlock.  
5. Entries remain intact (root unchanged).  
6. Recovery is **not** “anyone local can open Aria.”

---

## 6. PIN model

| Role | Behavior |
| --- | --- |
| Master password | Only credential that unwraps vault root from disk |
| PIN | Soft unlock after soft lock (root still in memory); step-up when unlocked |
| Missing PIN | Soft unlock unavailable; Lock Now via owner API still works; unlock with master |
| Lost PIN | Master + recovery still work |

Existing `pin_lock.py` unchanged for legacy PIN UI; owner soft-unlock calls `verify_pin`.

---

## 7. Capability catalog

Normative list in `jarvis/security/owner/capabilities.py` (versioned in code).

Rooms are **not** superusers. Example: `journal` may request `journal.export`; may not request `health.delete`.

Risk → policy: LOW/MEDIUM when unlocked; HIGH/CRITICAL need step-up (with catalog exceptions for auth boundary ops).

---

## 8. ACM boundary

- Helpers: `assert_safe_for_acm`, `safe_metadata_only`  
- Forbidden: master password, recovery key, vault root, API keys, tokens, passwords  
- M1 does not modify ACM storage modules; establishes the boundary API for later wiring  

---

## 9. Performance measurements

Evidence: `docs/evidence/exhaustive_functional_verification/owner_security_m1_perf.json`

| Operation | Measured (isol) |
| --- | --- |
| Vault setup (2× Argon2id wraps) | ~120 ms |
| Unlock (1× Argon2id) | ~50–60 ms |
| Soft/hard lock | < 1 ms |
| Authorize (no KDF) | < 0.1 ms |
| Step-up (master verify KDF) | ~48 ms |
| Status | < 1 ms |

No KDF on Room navigation or authorize for LOW capabilities. Local only — no network.

---

## 10. Tests

`tests/test_owner_security_m1.py` — **13 passed** (disposable `tmp_path` only).

Coverage: setup, unlock, wrong password, lock, recovery + entry intact, revocation, capability denial, step-up, PIN soft vs hard, restart locked, empty vault, ACM boundary, env denylist, Health rejects LAN API key, crypto params.

Regression: `tests/test_health_phase4.py`, `tests/test_p4_security.py` — passed.

---

## 11. Security results

| Check | Result |
| --- | --- |
| Master never stored plaintext | Pass |
| Recovery plaintext not on disk | Pass (wrapped root only) |
| PIN ≠ vault root from disk | Pass |
| LAN API key Health step-up removed | Pass |
| Tool subprocess env strips secrets | Pass (`build_subprocess_env`) |
| Capability handles cleared on lock | Pass |
| Temporary auth backoff, no permanent lockout | Pass |

---

## 12. Isolation results

| Check | Result |
| --- | --- |
| Tests use `tmp_path` / disposable dirs | Pass |
| Live `data/jarvis.env` not modified by M1 | Pass |
| Live `data/security/owner/vault.json` not created by tests | Pass |
| No Jeff credentials in tests | Pass |
| Integrity scan after M1 | **clean / 100** |

---

## 13. Integrity result

`POST /api/integrity/scan?trigger=owner-security-m1` → **clean / 100** (total 0 findings).

---

## 14. Health step-up correction (M1-safe)

`jarvis/health_product/gate.py`:

- Removed LAN `JARVIS_API_KEY` as step-up authenticator  
- Accepts PIN and, when vault exists, Owner Master Password (KDF at step-up boundary)  
- Full Health grant unification deferred to M4  

---

## 15. Subprocess environment boundary

`jarvis/security/owner/env_boundary.py` + wired into:

- `jarvis/tools/runner.py`
- `jarvis/tools/registry.py`

Replaces blind `os.environ.copy()` for tool children. Secrets remain in process env for Aria itself until M2/M3; children no longer inherit them by default.

---

## 16. API surface (M1)

| Method | Path |
| --- | --- |
| GET | `/api/owner-security/status` |
| GET | `/api/owner-security/capabilities` |
| POST | `/api/owner-security/setup` |
| POST | `/api/owner-security/recovery/acknowledge` |
| POST | `/api/owner-security/unlock` |
| POST | `/api/owner-security/unlock/pin` |
| POST | `/api/owner-security/lock` |
| POST | `/api/owner-security/recover` |
| POST | `/api/owner-security/password/change` |
| POST | `/api/owner-security/step-up` |
| POST | `/api/owner-security/authorize` |
| GET | `/api/owner-security/vault/meta` |
| GET | `/api/owner-security/timings` |

---

## 17. Known limitations

1. No full Security Room UI for master setup yet — API + library only.  
2. Production vault not initialized for Jeff (empty foundation; Jeff-attended setup is a later attended step).  
3. Legacy PIN sessions still separate until M4 unify.  
4. Uncensored sessions still separate until M4.  
5. `jarvis.env` still plaintext source of truth for live secrets.  
6. Memory model is best-effort (`bytearray` wipe on lock) — process death is the hard boundary.  
7. Soft lock keeps root in memory by design for PIN convenience.  
8. Journal encrypted import checkpoint **unchanged / not proven**.  

---

## 18. Exhaustive verification checkpoint

**Unchanged:** Journal → More → Import encrypted  
File: `docs/evidence/exhaustive_functional_verification/EXHAUSTIVE_CHECKPOINT.json`  
Do not resume until later phases authorized.

---

## 19. Next phases (not authorized)

- **M2** — Integrations credential migration (dual-read)  
- **M3** — HA / LAN / remaining secrets  
- **M4** — Unified revocation + finish Health grants  
- **M5** — Journal security UX  
- **M6** — Stop plaintext writes  

---

## 20. STOP

M1 foundation is implemented and proven in isolation.  
**No live credential migration. No jarvis.env edits. No Journal crypto changes. Exhaustive verification not resumed.**
