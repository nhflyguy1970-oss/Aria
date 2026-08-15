# ARIA — Owner Session Daily-Use Contract

**Status:** PROVEN — STOP  
**Date:** 2026-08-14  
**Campaign:** exhaustive 34-Room verification **STOPPED** (do not resume in this work)  
**Evidence:** `docs/evidence/exhaustive_functional_verification/owner_session_daily_use.json`  
**Not:** Owner Residency · M5 · new credential migration · 34/34 certification

Jeff’s daily model:

```
START ARIA
    → LOCKED
    → Master Password
    → UNLOCKED (use the house; no timeout)
    → Jeff clicks Lock Aria
    → LOCKED
```

`OWNER_UNLOCKED` stays `OWNER_UNLOCKED` until (1) Jeff clicks **Lock Aria**, (2) Aria is restarted or shut down, or (3) a genuine security-critical revoke.

---

## 1. Existing timeout mechanism

Two independent 900-second timers were locking the house during exhaustive work. Neither was required for daily use.

### Frontend (the smoking gun)

`jarvis/gui/static/lock_screen.js` `resetIdle()`:

- Started after unlock and after `click` / `keydown` / `touchstart`.
- Fetched `/api/security/lock/status` and used `d.idle_seconds || 900`, so **even `0` became 900**.
- After that timeout, **POST `/api/security/lock` `{ hard: true }`**, which wipes the in-memory vault root.
- Reading a Room without clicking did **not** reset the timer.
- Survived Room changes (same SPA document). Did **not** survive a full process restart (new JS context).
- Ran during “active work” if that work produced no click/key/touch (Chat wait, Coding wait, reading).

### Backend Owner session idle

`jarvis/security/owner/session.py` `OwnerSessionManager`:

- Config: `JARVIS_OWNER_IDLE_SECONDS` then `JARVIS_LOCK_IDLE` then `JARVIS_LOCK_IDLE_SEC`, previously default `"900"`.
- `session_valid()` / `touch()` revoked the token when `now - last_active > idle_seconds`.
- `last_active` was set at unlock. Normal Room API traffic did **not** call Owner `touch()`.
- Status reported `idle_seconds: 900` on the live house before this change.

### PIN idle (secondary)

`jarvis/security/pin_lock.py` used `lock_idle_seconds()` with `max(60, …)` historically. Jeff uses Owner Vault, not PIN as the house authenticator. PIN idle is now the same flag (0 = off).

### Where it was introduced

Idle lock was a security-session convenience from PIN-era / Owner Vault M1 session design (`docs/ARIA_OWNER_SECURITY_VAULT_ARCHITECTURE.md` originally listed idle as a lock event). It was **not** a residency test harness, but exhaustive Room testing repeatedly hit the 15-minute wall because the campaign did not match how Jeff actually uses the house.

### Configurable

Yes. After this change:

| Env | Meaning |
| --- | --- |
| *(unset)* | **0 — no automatic idle lock** (daily-use default) |
| `JARVIS_OWNER_IDLE_SECONDS` | Sole opt-in timeout (seconds). Unset = off. |
| `JARVIS_LOCK_IDLE` / `JARVIS_LOCK_IDLE_SEC` | **Ignored.** PIN-era leftovers. Live `jarvis.env` still exports `JARVIS_LOCK_IDLE_SEC` (was 900). That file was **not** edited. |

First code-load restart still reported `idle_seconds: 900` because the new default still inherited `JARVIS_LOCK_IDLE_SEC`. Owner session now ignores that PIN-era flag.

---

## 2. Why it was locking

During exhaustive verification Jeff unlocked once, then worked in Rooms. After ~15 minutes of reading or waiting (or of using the house without the specific events that reset the frontend timer), `lock_screen.js` issued a **hard lock**. Vault root was wiped. Overlay appeared. Protected credentials failed closed. That is correct **lock** behavior — it was the **trigger** that was wrong.

The campaign was therefore testing “Aria under a 15-minute idle lock,” not “Aria the way Jeff will actually use it.”

---

## 3. New intended session contract

```
START ARIA                    → OWNER_LOCKED (in-memory vault root empty)
Master Password               → OWNER_UNLOCKED (house-wide session)
Use Rooms / Front Door / Chat → stays OWNER_UNLOCKED
Lock Aria (Front Door)        → OWNER_LOCKED (hard lock: sessions revoked, vault wiped)
Restart / shutdown            → OWNER_LOCKED
Idle time                     → does nothing
Room navigation               → does nothing
Browser back/forward          → does nothing
Credential gate               → does not lock the house
```

One password. One house session. No arbitrary timeout. Manual lock when Jeff wants it.

Security that **remains**:

- Master Password required after startup, restart, and manual Lock.
- Vault locked when Owner Security is locked.
- Migrated credentials fail closed while locked.
- Argon2id remains an unlock / step-up operation only — not on Room navigation.

---

## 4. Automatic timeout behavior

**Default: off.**

`jarvis/p4_flags.py` `lock_idle_seconds()` reads **only** `JARVIS_OWNER_IDLE_SECONDS` (default `"0"`). PIN-era `JARVIS_LOCK_IDLE_SEC` is ignored so the live house is not locked by a leftover 900.

`OwnerSessionManager._idle_expired()` returns `False` when `idle_seconds <= 0`.

Frontend `idleSecondsFromStatus()` treats missing / non-finite / `<= 0` as **0**. `resetIdle()` returns immediately when idle is off. No per-click status fetch. No 900s fallback.

Status now includes `auto_idle_lock: false` when idle is 0. `house_lock_status()` reports Owner idle (not PIN’s old 900 bleed-through) when the vault exists.

Opt-in: set `JARVIS_OWNER_IDLE_SECONDS` to a positive integer. Isolated test proves `idle_seconds=2` still expires. Daily use does not set this.

---

## 5. Manual Lock behavior

`POST /api/security/lock` `{ hard: true }` → `OwnerSecurityService.lock(hard=True)`:

1. `sessions.hard_lock()` — revoke all Owner sessions, bump generation, clear capability handles.
2. `vault.lock()` — wipe in-memory vault root.
3. Health step-up grants revoked.
4. Uncensored sessions revoked.

Frontend `window.jarvisLockHouse({ hard: true })` calls that API, clears `sessionStorage` session, then `jarvisShowLock()`.

This is the same house lock as Security-room **Lock Aria**, not a visual flag.

---

## 6. Front Door Lock control

Visible on the Front Door footer when `lock_capable && locked === false`:

- Control: `#fdLockAria` **Lock Aria**
- Location: Front Door footer next to Return — house-level, not buried in Security / Settings / Capabilities
- Hidden when locked (the overlay is the locked-state UI)
- Click → `jarvisLockHouse({ hard: true })` then close foyer

Command palette **Lock Aria** and Security-room lock buttons also call `jarvisLockHouse`. Catalog item `ctrl:security` is titled **Security** (opens the Security room); it is no longer labeled as the house lock.

Overlay copy when locked:

> Aria is locked. Enter your Aria Master Password to unlock the house.

No second password is created.

---

## 7. Restart behavior

**Unchanged.** New process has no in-memory vault root → `OWNER_LOCKED` → Master Password required.

Isolated: `OwnerSecurityService` reconstructed against the same vault file starts locked.

Live: code-load restart of `main.py serve` leaves `OWNER_LOCKED`. Idle time is not a restart.

---

## 8. Vault behavior

| State | Vault root | Migrated secrets |
| --- | --- | --- |
| `OWNER_UNLOCKED` | In memory | Retrievable for authorized capabilities |
| `OWNER_LOCKED` (manual or restart) | Wiped | Fail closed — no env fallback for migrated entries |

`data/jarvis.env` was not rewritten. No new vault entries. No credential migration.

---

## 9. Capability revocation

On hard lock:

- Owner session tokens invalid
- Capability handles invalid
- `authorize(...)` denied
- HA token path fails closed
- Provider credentials fail closed
- LAN migrated key fails closed (loopback live exempt unchanged)
- Health owner-gated operations return 423 *Unlock Aria with your Master Password to use Health.*

A credential gate (Jeff must supply a real provider key, etc.) must **not** lock the house. Jeff can provide that input while `OWNER_UNLOCKED`.

---

## 10. Performance

Isolated explicit `lock(hard=True)` measured **under 2 seconds** (typically tens of milliseconds; no KDF).

Unlock still pays Argon2id once. Room navigation does not KDF.

Frontend idle-off path does not poll `/api/security/lock/status` on every click.

---

## 11. Long-run owner-use test

**Isolated (proven, no live wait):** unlock, backdate `last_active` by **10_000 seconds**, `session_valid` still True, `house_lock_status.locked` False, `auto_idle_lock` False. Tests used `JARVIS_DATA_DIR=tmp_path`; live `data/security/owner` was not the vault path.

**Live:** after Python load, `/api/security/lock/status` must report `idle_seconds: 0` and `auto_idle_lock: false`. Do **not** wait 15 minutes. Do **not** insert lock/unlock between Rooms.

Navigation that must not lock: Room change, Front Door, browser back/forward, Chat/Coding wait, sitting idle while reading, leave/return.

---

## 12. Manual lock / unlock test

After proving no auto-lock:

1. Front Door → **Lock Aria**
2. `OWNER_LOCKED`, overlay, vault locked, protected paths fail closed
3. Master Password → `OWNER_UNLOCKED`
4. Use multiple Rooms — stays unlocked

Requires Jeff to unlock the live house after the code-load restart. Password is never requested in chat.

---

## 13. Activity behavior

Lock/unlock is Owner Security, not an engineering failure.

- Uncensored “session expired” toast is **Uncensored mode**, not Owner idle — left in place.
- Provider “stream idle timeout” is provider health — left in place.
- Health `log_event("health_access", "owner_locked")` is the Health store audit when a locked caller hits Health — not Activity Center QA.
- No timeout / session-expired / QA messages were added to Activity Center.

---

## 14. Production isolation

The 2026-08-12 Journal wipe used `DATA_DIR` while Aria reads `JARVIS_DATA_DIR` (`jarvis/config.py`).

This work:

- Isolated tests: `monkeypatch.setenv("JARVIS_DATA_DIR", tmp_path)` and `OwnerSecurityService(data_dir=tmp_path)`.
- Asserted the test vault path ≠ live `data/security/owner`.
- No Journal / Health / Planner / ACM writes.
- No `jarvis.env` edits.
- No new vault entries.
- Live serve `JARVIS_DATA_DIR=/media/jeff/AI/jarvis/data` (correct). Tests did not point at it.

---

## 15. Regression results

### Isolated (`venv/bin/python -m pytest`)

`tests/test_owner_session_daily_use.py` + `tests/test_p4_security.py` + `tests/test_owner_security_m1.py`: **31 passed**.

| Check | Result |
| --- | --- |
| Default idle 0 / `auto_idle_lock` false | PASS |
| PIN-era `JARVIS_LOCK_IDLE_SEC=900` does not enable Owner idle | PASS |
| Session survives 10_000s elapsed when idle off | PASS |
| Opt-in idle=2 still expires | PASS |
| Explicit hard lock revokes vault + handles, &lt; 2s | PASS |
| New process starts locked | PASS |
| JS has no `idle_seconds \|\| 900`; has `jarvisLockHouse` + `#fdLockAria` | PASS |
| M1 unlock/lock/restart/env-boundary | PASS |

### Live (after code-load restart)

Serve PID 1513514. `jarvis.env` was **not** edited.

| Check | Result |
| --- | --- |
| Restart → `OWNER_LOCKED` | PASS |
| `idle_seconds` | **0** |
| `auto_idle_lock` | **false** |
| Overlay | `display:flex` · “ARIA locked” · “Aria is locked. Enter your Aria Master Password to unlock the house.” |
| `#fdLockAria` while locked | exists, text “Lock Aria”, **hidden** |
| Health home / overview | 423 fail closed |
| HA | `locked: true`, `connected: false`, Master Password message |
| OpenAI / Gemini test | `key_missing` fail closed |
| Integrity | **clean / 100 / artifacts 0** |
| Activity timeout / QA hits | none |
| Journal POST | none (size 67547 unchanged) |

### Live (after Jeff unlock)

Jeff unlocked after the code-load restart. `idle_seconds` stayed **0**. Overlay `display:none`.

Room hashes `#journal` → `#health` → `#coding` → `#chat`: `OWNER_UNLOCKED` throughout, overlay stayed `none`.

Front Door → Journal: hash `#journal`, house still unlocked (no overlay).

Front Door footer **Lock Aria** visible next to Return (`owner_session_lock_aria_footer.png`). Click:

- `OWNER_LOCKED` immediately
- overlay `display:flex` with Master Password copy (`owner_session_manual_lock_overlay.png`)
- `#fdLockAria` hidden while locked
- Health 423, HA fail-closed, OpenAI/Gemini `key_missing`
- Integrity **clean / 100 / artifacts 0**
- no Activity timeout/QA hits from this lock
- journal size 67547 unchanged; no journal POST

Second Master Password unlock after Front Door **Lock Aria**:

- `OWNER_UNLOCKED`, overlay `none`, `idle_seconds` 0
- Chat / Health / Coding / Journal stayed unlocked
- Health home 200, HA `connected: true` (`API running.`), OpenAI test ok
- Front Door **Lock Aria** visible again (`display:block`)
- Integrity **clean / 100 / artifacts 0**
- journal size 67547; no POST

### Exhaustive campaign

**STOPPED.** Owner Session daily-use is proven. Do **not** resume the 34-Room campaign in this work. When it resumes later: unlock **once**, remain unlocked across Rooms, stop only for genuine Jeff-only gates, lock only when Jeff clicks **Lock Aria**.

---

## Proof checklist (section 21)

| # | Requirement | Isolated | Live |
| --- | --- | --- | --- |
| 1 | Aria starts locked | PASS | PASS (restart) |
| 2 | Jeff unlocks once | — | PASS |
| 3 | Stays unlocked during extended use | PASS (10_000s backdate) | PASS — hashes + Front Door Journal; idle 0 |
| 4 | Room navigation does not lock | contract + idle off | PASS |
| 5 | Normal interaction does not lock | frontend timer off | PASS (Front Door open/close, Journal) |
| 6 | Front Door has Lock Aria | source PASS | PASS — footer next to Return, hidden when locked |
| 7 | Lock Aria actually locks | API PASS | PASS — Front Door click → OWNER_LOCKED |
| 8 | Protected credentials fail closed | M1/M3 model | PASS after restart lock and after Lock Aria |
| 9 | Master Password unlocks again | M1 PASS | PASS after Front Door Lock Aria |
| 10 | Restart still locks | PASS | PASS |
| 11 | Integrity clean / 100 | — | PASS (restart lock; Lock Aria; second unlock) |
| 12 | No production contamination | PASS | journal size 67547; no POST |
| 13 | No secret leakage | tests use fake master | evidence has no secrets |

---

## Do not

- Resume the 34-Room exhaustive campaign
- Start Owner Residency
- Start M5
- Apply Coding proposal `603973e7`
- Execute Guided Repair
- Guess or ask for the Master Password in chat
- Insert artificial lock/unlock cycles between Rooms
