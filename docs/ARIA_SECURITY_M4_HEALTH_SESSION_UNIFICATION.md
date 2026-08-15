# ARIA — M4 Security Unification (Health step-up + Owner session)

**Status:** HEALTH SESSION UNIFIED — LIVE PROVEN — STOP  
**Date:** 2026-08-13  
**Evidence:** `docs/evidence/security_m4/`  
**Checkpoint preserved:** Journal → More → Import encrypted (not resumed)

Jeff continues to have **one Aria Master Password**. Health, Uncensored, HA, LAN, and providers do not get their own Aria passwords. No new credential was migrated. `data/jarvis.env` was not rewritten.

---

## 1. Health authentication inventory

Canonical gate: `jarvis/health_product/gate.py`.

| Path | Gate | Live (unlocked) |
| --- | --- | --- |
| `GET /api/health/home` | `_owner_or_response` — Owner session only | 200, no extra password (~19 ms) |
| `GET /api/health/overview` | `_owner_or_response` | 200 |
| `GET /api/health/product` | `_owner_or_response` | Owner session |
| `GET /api/health/export` | `_gate_or_response(export_record)` | 423 `step_up_required` `prompt_class: A` |
| `POST /api/health/backups` | `_gate_or_response(backup_create, body)` | class A step-up; `body.password` is portable (class B), not Owner auth |
| `POST /api/health/auth/step-up` | Owner `step_up(master_password / PIN)` | LAN key and HA token rejected |

Grant cache is keyed on `X-Jarvis-Session` / `"local"`, **never** `X-API-Key`.

When the Owner Vault exists and the house is locked: Health returns 423 *Unlock Aria with your Master Password to use Health.*

Evidence: `health_ops_inventory.json`, `health_auth_status.json`.

---

## 2. Health risk classification

From actual `SENSITIVE_OPS` wired through `_gate_or_response` — not guessed.

**NORMAL HEALTH ACCESS** (Owner session only; no extra password):

- Home, overview, product, timeline, check-in, ordinary viewing

**SENSITIVE HEALTH OPERATION** (Owner Security step-up, class A):

- `export_record`, `view_full_record`, `emergency_info`
- `edit_medications`, `edit_allergies`, `edit_conditions`, `edit_family_history`, `edit_emergency`
- `delete_record`, `cloud_consult`
- `backup_create`, `backup_restore`

**PORTABLE FILE PASSWORD** (class B, in addition to Owner step-up):

- `backup_create` / `backup_restore` — `body.password` encrypts the file that can leave Aria. It is **not** the Master Password and is **not** used as Owner auth (`PORTABLE_PASSWORD_OPS`).

Ordinary Health viewing does **not** require the Master Password again after house unlock.

---

## 3. Final Health step-up model

```
ONE ARIA MASTER PASSWORD
→ OWNER_UNLOCKED (house session)
→ Health Room (home / overview) — no second Aria password
→ sensitive op → Owner Security step-up (Master Password, or PIN if configured)
→ portable backup/restore also requires a distinct file password
```

- LAN API key is not a Health authenticator.
- HA token is not a Health authenticator.
- No Health-specific Aria password was created.
- Recovery key is not used for routine Health step-up.
- Step-up grants are dropped on Owner lock (`revoke_grants()`).

Live: `GET /api/health/auth/status` → `owner_vault: true`, `owner_unlocked: true`, `pin_convenience: false`, `portable_backup_distinct: true`.

---

## 4. LAN-key authentication regression

Proven live, twice (unlock-after-restart and unlock-after-lock):

- `POST /api/health/auth/step-up` with the LAN API key → `ok: false` “Incorrect Master Password or PIN.”
- Same with the HA token → rejected.
- LAN from `10.0.0.235` still requires `X-API-Key` for the LAN API (401 without / 200 with, when unlocked). That authenticates the **network**, not Jeff.

---

## 5. PIN relationship

M1 decision unchanged: **PIN is convenience / step-up only. PIN is not the vault root.**

Live:

- `data/security/pin.json` does not exist
- `JARVIS_PIN_LOCK` is off
- Owner status `pin_model.vault_root_from_pin: false`
- Health `pin_convenience: false`

If Jeff later sets a PIN, Health and Uncensored step-up may accept it as convenience. It still cannot reconstruct the vault root from disk. There is one PIN system (`jarvis/security/pin_lock.py`), not a Health-specific PIN.

---

## 6. Uncensored relationship

Inventory:

| Concern | Finding |
| --- | --- |
| Authenticate | When Owner Vault exists: Owner session + `uncensored.enable` step-up (Master Password / PIN). Legacy `uncensored_auth.json` password is **not** required. |
| Store | Capability session tokens in `uncensored_sessions.json`. Legacy hash file may still exist; M4 does not write a second Aria password. |
| Lock / revoke | Owner `lock()` calls `invalidate_all_sessions()`. Locked house cannot enable Uncensored. |
| Expire | Session TTL (default 12 h) |
| Duplicate? | Yes, historically. Corrected: Uncensored is a **capability**, not a second Aria password. |
| Live | `auth_mode: owner_security`, `prompt_class: A`. **Not enabled** on production. No test Uncensored state written. |

UI copy: “Confirm with your Aria Master Password. Uncensored is a house capability — not a second Aria password.”

A leftover `data/uncensored_auth.json` may exist from before M4. It is unused while the vault exists. It was not deleted (no silent production deletion).

---

## 7. Owner session relationship

House model:

```
ONE ARIA MASTER PASSWORD
→ UNLOCK
→ OWNER_UNLOCKED
→ Rooms (Health, Journal, Fly Tying, Memory, Coding, Integrations, HA, …)
   do not ask another Aria password merely for entry
→ vault supplies already-migrated service credentials
```

Health `_owner_or_response` is the same Owner session as the rest of the house. Sensitive Health ops and Uncensored enable are Owner Security step-up (class A), not new identity systems.

---

## 8. Revocation model

On hard lock (`POST /api/owner-security/lock` `{"hard": true}`):

1. Owner session → `OWNER_LOCKED`; vault locked (no env fallback for migrated secrets)
2. Health `revoke_grants()` — in-memory step-up grants dropped
3. Uncensored `invalidate_all_sessions()`
4. HA / providers / LAN fail closed (M2/M3 vault-first)

Restart starts `OWNER_LOCKED`. Unlock with the existing Master Password restores capabilities. No credential remains authorized after lock.

---

## 9. Capability authorization

Rooms request; Security authorizes (`jarvis/security/owner/capabilities.py`). Health Room is not a superuser.

| Capability | Room | Risk | Notes |
| --- | --- | --- | --- |
| `health.read` | health | MEDIUM | ordinary viewing after Owner unlock |
| `health.write` / `health.export` / `health.delete` | health | HIGH/CRITICAL | step-up |
| `uncensored.enable` | security, chat | HIGH | step-up |
| `vault.secret.use` | integrations, ha, lan, … | MEDIUM | migrated credentials |
| `ha.actuate` | ha, home | MEDIUM | not used in M4 proof |

Isol: `health.delete` from `flytying` is denied.

---

## 10. Health backup / export distinction

Two different secrets:

| Secret | Class | Purpose |
| --- | --- | --- |
| Aria Master Password | A | Owner identity / Health step-up |
| Portable Health backup password | B | Encrypts a file that can leave Aria |

UI (`health.js`): backup field placeholder *Portable backup password (not Aria Master Password)*. Restore preview asks for the portable password, not the Master Password.

M4 did **not** run live backup create/restore (destructive / file-password). Classification and UI copy are the proof. Journal portable export passwords remain a separate class B (exhaustive checkpoint, not resumed).

---

## 11. Password prompt audit

| Surface | Class | Result |
| --- | --- | --- |
| Owner overlay | A | Jeff-attended unlock |
| Health home | none | 200 |
| Health export | A | 423 step-up; record not dumped |
| Health backup form | B | copy only; not executed |
| Uncensored (vault) | A | policy; not enabled live |
| OpenAI / Gemini / HF | C | vault; no key prompt |
| HA | C | vault; no token prompt |
| LAN `X-API-Key` | C | network credential |
| Journal encrypted import | B | not exercised |

**Defects: none.** No extra Aria-specific password appeared.

Evidence: `password_prompt_audit.json`.

---

## 12. Lock / unlock matrix

| Capability | Unlocked | Locked | Unlock again |
| --- | --- | --- | --- |
| Health home | 200, no extra password | 423 locked | 200 |
| Health export | 423 step-up class A | 423 locked | 423 step-up class A |
| OpenAI | ok | `key_missing` | ok |
| Gemini | ok | `key_missing` | ok |
| Hugging Face | ok | `key_missing` | ok |
| HA | connected | fail-closed | connected |
| LAN (correct key) | 200 | 401 | 200 |
| LAN (no key) | 401 | 401 | 401 |
| Uncensored | `owner_security` class A | denied / sessions revoked | policy restored; not enabled live |

Evidence: `lock_fail_closed.json`, `unlock_after_lock.json`, `providers_unlocked.json`, `lock_unlock_matrix.json`.

---

## 13. Restart matrix

| After restart (before unlock) | After Jeff unlock |
| --- | --- |
| `OWNER_LOCKED` | `OWNER_UNLOCKED` |
| Health home / overview 423 | Health home 200, ~23 ms then ~19 ms |
| Health export 423 locked (after `_gate_or_response` repair) | 423 step-up class A |
| HA locked, not connected | HA connected ~4–9 ms |
| LAN + correct key 401 | LAN + correct key 200 |
| Providers denied | OpenAI / Gemini / HF ok |

First restart had `GET /api/health/export` 500 because `_gate_or_response` was missing; restored; re-restarted; export then 423 fail-closed. Evidence: `restart_locked_matrix.json`, `unlock_after_restart.json`.

Unlock KDF after restart: **50.46 ms**.

---

## 14. Performance

No Argon2id on ordinary Health GET, HA status, LAN auth, or vault credential use. No repeated vault initialization on Room navigation.

| Measurement | Result |
| --- | --- |
| Owner unlock (Argon2id) | 50.46 ms (restart unlock) |
| Health home (unlocked) | 18.9–22.7 ms |
| Health export step-up check | 5.9–16.2 ms |
| HA status (unlocked) | 3.9–8.7 ms |
| LAN authenticated (unlocked) | 3.1–8.6 ms |
| Hard lock | 2.06 ms |
| Integrity scan | 42 ms |
| Provider tests (network) | OpenAI ~0.7–1.9 s; Gemini ~230–249 ms; HF ~168–171 ms |

Health overview ~425 ms is payload work, not KDF.

---

## 15. Secret leak audit

**SECRET LEAK FOUND: no**

Checked 581 files: logs, ACM, Activity, Journal, diagnostics, test artifacts, M4 evidence.  
Skipped (expected stores, not leaks): `data/jarvis.env`, `data/security/owner/vault.json`.

No Master Password, PIN, recovery key, HA token, LAN key, or provider key values in those surfaces. Evidence holds metadata only.

Evidence: `secret_leak_check.json`.

---

## 16. Production isolation

- QA mutating POST with `X-Aria-QA-Run` → **403**
- No synthetic Health records created
- No test credentials written to production
- Uncensored not enabled on live
- Isol tests bind `JARVIS_DATA_DIR` / pytest skip of the live vault
- `data/jarvis.env` retained (mode 0600, size 10616)

---

## 17. Integrity

**clean / 100.** Artifacts: 0.

Evidence: `integrity.json`.

---

## 18. Remaining security work

M4 is unification only. Do **not** treat the following as authorized:

- Automation, Postgres, Git, Browser, Cloud Live, Connections, OAuth
- Journal encryption / encrypted import (checkpoint remains **Journal → More → Import encrypted**)
- Deleting `data/jarvis.env` rollback copies
- Deleting leftover `data/uncensored_auth.json` (Jeff-approved cleanup later, if desired)
- Enabling Uncensored on live
- Configuring a PIN (optional convenience; not required)

Vault still has **5** entries (OpenAI, Gemini, HF, `ha.token`, `lan.api_key`). Cloud Live may still read provider keys via `os.getenv` (deferred consumer).

**Do not start M5 automatically.**

---

## Isol tests

`tests/test_owner_security_m4.py` with M1/M3: **31 passed**. Live vault is never mutated under pytest.

---

## STOP

M4 is complete.

- Health uses unified Owner Security
- LAN key cannot authenticate Health
- Health does not require a separate Aria password
- PIN relationship is correct (convenience only; not configured live)
- Uncensored uses Owner Security, not a second Aria password
- Owner lock revokes Health grants, Uncensored sessions, and migrated credentials
- Restart requires Owner unlock
- Capability authorization remains room-scoped
- Performance remains acceptable
- No secrets leaked
- Production remains isolated
- Integrity is clean / 100

Do not migrate additional credentials.  
Do not delete `data/jarvis.env`.  
Do not resume exhaustive Room verification.
