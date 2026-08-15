# ARIA — One-Password Owner Experience

**Status:** PROVEN (isol + live empty Owner Vault) — M2 credential migration NOT authorized  
**Date:** 2026-08-12 / live initialize 2026-08-13  
**Foundation:** M1 (`docs/ARIA_OWNER_SECURITY_VAULT_M1.md`) — not redesigned  
**Evidence (isol):** `docs/evidence/exhaustive_functional_verification/one_password_owner_experience.json`  
**Evidence (live):** `docs/evidence/exhaustive_functional_verification/live_owner_vault_initialized.json`  
**Checkpoint preserved:** Journal → More → Import encrypted  

---

## 1. User goal

Jeff enters **one Aria Master Password**. Aria unlocks. The Owner session is house-wide. Authorized Rooms work without more Aria passwords.

The vault is infrastructure underneath that experience. It is not a second password manager Jeff has to operate.

---

## 2. One-password model

| What Jeff does | What Aria does |
| --- | --- |
| First time: create Master Password, confirm, store recovery key | Create empty Owner Vault + Owner session |
| Daily: enter Master Password | `OWNER_UNLOCKED` — house-wide |
| Lock | `OWNER_LOCKED` — protected capabilities stop |
| Unlock | Same Master Password |

There is no Journal password, Health password, Integrations password, or per-Room Aria password.

External services may still have their own keys. Those are vault/host concerns, not extra Aria logins.

---

## 3. Owner session

States remain M1: `OWNER_LOCKED` / `OWNER_UNLOCKED` / `OWNER_STEP_UP` / revoke.

- Process start with a vault → **LOCKED** (enter Master Password).
- No vault yet → Aria works as today; Security Room offers first-time setup. Production is not locked out.
- Session token is the existing `X-Jarvis-Session` house token.
- Rooms do not implement their own login.

---

## 4. Vault role

Invisible in normal use.

Master Password → Argon2id → unwrap Vault Root Key → session.  
The Master Password is never used as an OpenAI key, HA token, Git credential, browser password, or portable export password.

M1 empty vault is unchanged. Live credentials are **not** migrated.

---

## 5. Room integration

- Lock overlay covers the house when the vault exists and is locked.
- `window.AriaOwner.authorize(capability, room)` calls the common Security layer.
- `switchToView` does not navigate while the lock overlay is visible.
- If no vault is provisioned, `authorize()` does not invent a second auth wall (Rooms keep working).

Rooms request capabilities. They do not store passwords.

---

## 6. External credential handling

Still in `data/jarvis.env` until an authorized M2/M3.  
Git remains host-managed. Browser remains browser-managed.  
After future migration, unlock once → vault provides the right secret to the authorized capability.

---

## 7. PIN behavior

Optional convenience only. Not a second daily Aria password.  
Primary unlock is the Master Password.  
PIN may still exist for legacy PIN-lock (when no vault) and M1 soft-unlock/step-up.  
No new PIN prompts were added to Rooms.

---

## 8. Step-up behavior

HIGH/CRITICAL capabilities may still require step-up **after** the house is unlocked.  
Normal Room use (Journal read, Health enter, Fly Tying, Memory, …) does not re-ask the Master Password.  
Step-up is not invented merely because a capability exists.

---

## 9. Lock behavior

Lock Now / Security → Lock Aria → hard lock:

- Vault root dropped from memory
- Sessions revoked
- Capability handles invalidated
- Overlay: “Enter your Aria Master Password”

Pending sensitive work fails closed (M1). Safe UI may remain behind the overlay.

---

## 10. Recovery

Unchanged from M1. Shown **once** at setup. Acknowledged before continuing.  
Not requested during ordinary Room use.  
It is only for “I forgot my Aria Master Password.”

---

## 11. Journal exception (portable exports)

Normal Journal use: **no extra password**.

Portable encrypted export/import still asks for a **file password**, because the file can leave Aria. Prompts now say this is **not** the Aria Master Password. Format `jarvis-journal-v1` is unchanged. Aug 8 exports are still unrecovered.

---

## 12. Performance

| Measurement | Result |
| --- | --- |
| Isol startup to UI | ~773 ms |
| Isol API Master unlock (Argon2id) | 67.6 ms |
| Live setup (approx) | ~125 ms |
| Live lock | <1 ms |
| Live unlock after lock | 48.44 ms |
| Live wrong password | ~89 ms |
| **Live unlock after restart** | **65.37 ms** |
| Authorize (no KDF) | still sub-millisecond in M1 tests |

No KDF on Room navigation. No vault re-init per Room.

---

## 13. Testing

Isolated owner UI (`JARVIS_DATA_DIR=/tmp/aria-onepw-isol`, port 8778), disposable password only.

Proven:

1. First-time setup form  
2. Master Password create + confirm  
3. Recovery key shown + acknowledgement  
4. House-wide session (Journal / Health / Fly Tying — no extra Aria password)  
5. Capability authorize `journal.read` / `health.read`  
6. Lock → Master Password overlay  
7. Wrong password stays locked  
8. Unlock → Rooms again  
9. Process restart → LOCKED overlay  
10. Unlock after restart  
11. Integrity **clean / 100** on live  
12. QA header → 403 on live  
13. Live `jarvis.env` untouched; live empty Owner Vault initialized (owner-attended)  

Automated: `tests/test_owner_security_m1.py` (16 passed) including house lock status and authorize-without-vault.

---

## 14. Security

- Master Password never stored, never logged, never sent to providers  
- Recovery key not written into evidence or ACM  
- Health still rejects LAN API key as owner authenticator  
- Tool subprocess env still denylists secrets  
- Production: no test vault, no test secrets in ACM  

---

## 15. Remaining limitations

1. Live vault is **empty** (`entry_count: 0`). Integrations/HA/LAN secrets remain in `jarvis.env` until authorized M2/M3.  
2. M2/M3 credential migration not done.  
3. Legacy PIN UI remains as optional/legacy.  
4. Uncensored session still separate until M4.  
5. Journal encrypted import still **not proven**; exhaustive verification not resumed.  
6. Step-up is not yet wired to every HIGH Room action (by design this phase — avoid password spam).  
7. Memory model remains best-effort (M1).  
8. Cosmetic: Security status line can still say “Aria unlocked” while the lock overlay is showing.

---

## STOP

LIVE OWNER VAULT: **INITIALIZED** (empty).  
LIVE ONE-PASSWORD EXPERIENCE: **PROVEN**.

Do not start M2. Do not modify `jarvis.env`. Do not change Journal crypto. Do not resume exhaustive Room verification.
