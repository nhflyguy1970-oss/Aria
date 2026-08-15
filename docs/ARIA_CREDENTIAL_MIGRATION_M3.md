# ARIA — Credential Migration M3 (Home Assistant + LAN API)

**Status:** HA AND LAN LIVE PROVEN — STOP  
**Date:** 2026-08-13  
**Matrix:** `docs/ARIA_CREDENTIAL_MIGRATION_MATRIX.md`  
**Evidence:** `docs/evidence/credential_migration_m3/`  
**Checkpoint preserved:** Journal → More → Import encrypted (not resumed)

Jeff continues to have **one Aria Master Password**. He was not asked for the HA token or the LAN API key.

---

## 1. Complete HA credential inventory

Canonical getter: `jarvis.home_assistant.ha_token()`.

All runtime HA consumers go through `ha_token()` / `ha_enabled()` / `check_connection()` except Integrations’ configured-flag getenv fallback (boolean presence only).

| File | Room / role | Notes |
| --- | --- | --- |
| `jarvis/home_assistant.py` | Canonical getter, Bearer `_headers()`, `check_connection` | Direct getenv replaced with vault-first dual-read |
| `jarvis/home_assistant_product/{engine,entities,rooms,favorites,mission_bridge}.py` | Smart Home / Mission | via `ha_enabled()` |
| `jarvis/behaviors/smarthome/engine.py` | Chat / Smart Home | via `ha_enabled()` / `save_config` |
| `jarvis/gui/extra_routes.py` | `/api/homeassistant/status`, `config`, `test`, `entities`, `toggle`, `scene` | Toggle/scene **not** used for M3 proof |
| `jarvis/jarvis_mcp.py` | MCP HA tools | via `ha_enabled()` |
| `jarvis/services.py` | Startup health | `check_connection` |
| `jarvis/integrations_product/providers.py` | Integrations | `ha_token()` + getenv configured flag |
| `jarvis/router.py` | Chat token paste | existing save path; not a new prompt |
| `jarvis/device_router.py`, `scene_presets.py`, `sunlight_scene.py`, `security/tools_status.py` | Downstream | via `ha_enabled()` |
| `scripts/enable-home-assistant.sh`, `set-ha-token.sh` | Legacy env writers | not run during M3 |

- Cached: vault get cache after first retrieve (no Argon2id per request)
- Passed to subprocess: no
- Exposed to logs / Activity / ACM: no (metadata “configured” / “locked” only)
- Safe proof op: `GET /api/homeassistant/status` → Home Assistant `GET /api/` (authenticated, **no device toggle**)

Full consumer list: `docs/evidence/credential_migration_m3/inventory.json`.

Legacy metadata (not the secret): length 183, sha256_8 `f76cc236`, prefix_class `jwt`.

---

## 2. Complete LAN credential inventory

Canonical getter: `jarvis.auth.get_api_key()`. `api_key_enabled()` remains true if env or vault entry exists so a locked house does **not** open LAN.

| File | Role | Notes |
| --- | --- | --- |
| `jarvis/auth.py` | `get_api_key` / `check_key` / `APIKeyMiddleware` | Vault-first; empty stored key + configured → fail closed (401) |
| `jarvis/lan.py` | LAN bind policy; `/api/lan` | Bind check uses `api_key_enabled()` |
| `jarvis/gui/server.py` | Bind warning; some `check_key` | |
| `jarvis/extensions/security/api.py` | Owner Security APIs | middleware `check_key` |
| `jarvis/gui/static/lan_access.js` | Remote client sends LAN key | not Owner password |
| `jarvis/integrations_product/providers.py` | `aria_host` configured flag | getenv presence |
| `scripts/enable-lan.sh`, `rotate-api-key.sh` | Legacy env writers | **not run** during M3 |

- Loopback is exempt (`JARVIS_API_KEY_LOCAL` default on)
- LAN + remote require the key when configured
- **Must not** authenticate Owner Security or Health step-up
- Harmless proof: `GET /api/homeassistant/status` from `10.0.0.235` with `X-API-Key`

Legacy metadata: length 30, sha256_8 `cec7e051`.

---

## 3. HA migration

`POST /api/owner-security/migrate-provider` `{field: "ha_token"}` while `OWNER_UNLOCKED`.

- Vault entry: `ha.token`
- Fingerprint match vs env: `f76cc236`
- Jeff entered HA token: **no**
- `data/jarvis.env` retained (size 10616, mode 0600)
- Evidence: `ha_migrate.json`

Precedence: vault first. Env fallback only if `ha.token` does not exist. After migration, lock does **not** fall back to `jarvis.env`.

---

## 4. HA actual-operation proof

Safe op only: authenticated Home Assistant `GET /api/` via Aria status. **No device toggle.**

| Phase | Connected | Owner-visible time |
| --- | --- | --- |
| Pre-migration (env) | yes — “API running.” | 26.23 ms |
| Post-migrate unlocked | yes | 4.06 ms |
| Unlock after lock | yes | 7.68 ms |
| Unlock after restart | yes | 4.01–4.50 ms |

Evidence: `ha_pre_migration.json`, `ha_operation.json`, `ha_unlock_after_lock.json`, `ha_unlock_after_restart.json`.

---

## 5. HA lock failure proof

Hard lock → HA fail-closed while env copy still present (length 183, fp8 unchanged).

Locked message after code load: **“Home Assistant is locked. Unlock Aria with your Master Password.”**  
Jeff is not asked to paste the HA token.

Evidence: `ha_lock_fail_closed.json`.

---

## 6. HA restart proof

Serve recycle → `OWNER_LOCKED`, `entry_count` 4 (then 5 after LAN). Unlock with existing Master Password. HA connected again. Jeff did not re-enter the HA token.

Evidence: `ha_restart_locked.json`, `ha_unlock_after_restart.json`.

---

## 7. LAN migration

Performed only after HA restart-unlock was proven.

`POST /api/owner-security/migrate-provider` `{field: "lan_api_key"}`.

- Vault entry: `lan.api_key`
- Fingerprint match: `cec7e051`
- Jeff entered LAN key: **no**
- Env retained
- Evidence: `lan_migrate.json`

---

## 8. LAN authenticated-operation proof

From `http://10.0.0.235:8765` (LAN zone, not loopback):

| Request | Result |
| --- | --- |
| No `X-API-Key` | 401 Invalid or missing API key |
| Correct key | 200 + HA connected (~4 ms) |
| Loopback without key | 200 (exempt by design) |

Evidence: `lan_operation.json`, `lan_unlock_after_lock.json`, `lan_unlock_after_restart.json`.

---

## 9. LAN lock failure proof

Hard lock, env copy still present:

- LAN IP + **correct** key → **401** (vault credential not retrievable; no env bypass)
- Loopback `/api/live` still 200 (exempt)
- HA still fail-closed

Evidence: `lan_lock_fail_closed.json`.

---

## 10. LAN restart proof

Restart → `OWNER_LOCKED`, `entry_count: 5`. LAN IP + correct key → 401. Unlock with Master Password → LAN 200 + HA connected. Jeff did not re-enter the LAN key.

Evidence: `lan_restart_locked.json`, `lan_unlock_after_restart.json`.

---

## 11. Health authentication regression

LAN API key **must not** authenticate Health owner step-up or Owner Security.

| Test | Result |
| --- | --- |
| `POST /api/owner-security/unlock` with LAN key | `ok: false` Incorrect master password |
| `POST /api/security/unlock` with LAN key | 403 Incorrect master password |
| Session after those attempts | still `OWNER_UNLOCKED` (did not lock Jeff out; did not accept LAN key) |
| `gate._verify_credentials(LAN key)` against live vault | **rejected** |
| `POST /api/health/auth/step-up` with LAN key | Health step-up **not required** (PIN lock off); LAN key was not used as authenticator |
| Isol `test_m3_health_step_up_rejects_lan_api_key` | PIN accepted; LAN key rejected; Master Password accepted for Health step-up |

**lan_key_authenticated_health: false**  
**lan_key_authenticated_owner: false**

Evidence: `health_regression.json`, `lan_operation.json`. Isol: `tests/test_owner_security_m3.py`.

---

## 12. Subprocess environment audit

Blind `os.environ.copy()` on live spawn paths was replaced with `copy_process_env()` (secret denylist, including `JARVIS_HA_TOKEN`, `HOME_ASSISTANT_TOKEN`, `JARVIS_API_KEY`). Tool runners already use `build_subprocess_env()`.

Unrelated children (ComfyUI, Ollama, ffmpeg, Piper, Electron, AnimateDiff install) do not inherit HA or LAN secrets. Aria restart children load `jarvis.env` themselves; spawn env is scrubbed.

Evidence: `subprocess_audit.json`. Isol: `test_m3_subprocess_strips_ha_and_lan`.

---

## 13. ACM boundary

ACM may know “Home Assistant configured” / “LAN API configured”.  
ACM must not know HA token, LAN API key, Master Password, recovery key, or vault root.

`FORBIDDEN_ACM_FIELDS` includes `ha_token` and `lan_api_key`. Isol `test_m3_acm_metadata_only` strips those fields. ACM/journal/activity text scan: no secret values.

---

## 14. Secret leakage check

**SECRET LEAK FOUND: no**

Checked: logs, ACM, Activity, Journal, diagnostics, test artifacts, M3 evidence.  
Skipped (expected stores, not leaks): `data/jarvis.env`, `data/security/owner/vault.json`.

No HA token value, LAN key value, Master Password, or recovery key in those surfaces. Evidence files contain fingerprints only.

Evidence: `secret_leak_check.json`, `boundaries.json`.

---

## 15. Performance

No Argon2id per credential request. No repeated vault initialization on Room navigation.

| Measurement | Result |
| --- | --- |
| Owner unlock (Argon2id) | 49–67 ms (51.2 lock-cycle; 49.4 / 61.7 / 66.9 after later unlocks) |
| HA vault put (migrate) | 6.54 ms |
| LAN vault put (migrate) | 4.74 ms |
| First HA vault get after unlock | 0.06 ms |
| First LAN vault get after unlock | 0.05 ms |
| Subsequent vault get (cache) | ~0.00 ms |
| Hard lock | 0.29–25.5 ms |
| HA owner-visible status (unlocked, includes HA HTTP) | ~4–8 ms (pre-migration 26 ms) |
| LAN authenticated request (unlocked) | ~3.7–4.6 ms |
| LAN fail-closed (locked, correct key) | 0.64 ms |
| Integrity scan | 54 ms |

---

## 16. Integrity

**clean / 100.** Artifacts: 0.  
QA mutating POST with `X-Aria-QA-Run` → **403**.

Evidence: `integrity.json`.

---

## 17. Rollback state

`data/jarvis.env` was **not** deleted or rewritten (mode 0600, size 10616). HA and LAN plaintext copies remain for rollback until a later explicit authorization removes them.

Migrated + locked does **not** use those copies. Unmigrated fields still may.

Vault entries: 5 (OpenAI, Gemini, HF, `ha.token`, `lan.api_key`).

---

## 18. Remaining legacy credentials (plaintext copies still in `jarvis.env`)

Still in env as rollback or unmigrated:

- OpenAI / Gemini / HF (M2 rollback copies)
- HA token (M3 rollback copy)
- LAN API key (M3 rollback copy)
- Automation webhook secret
- Postgres / pgvector
- Config flags (not vault credentials)

Cloud Live still reads provider keys via `os.getenv` (deferred consumer).

---

## 19. Deferred categories (not authorized)

Do **not** migrate:

- Automation
- Postgres
- Journal encryption
- Health credentials
- Git
- Browser
- Cloud Live
- Connections
- OAuth

Do **not** resume exhaustive Room verification. Checkpoint remains **Journal → More → Import encrypted**.

---

## Isol tests

`tests/test_owner_security_m3.py` — 8 passed (plus M1/M2/HA: 39 passed in the combined run). Live vault is never mutated under pytest.

---

## STOP

M3 is complete. HA and LAN are individually migrated and proven.

Do not migrate Automation, Postgres, Cloud Live, Git, Browser, Connections, or OAuth.  
Do not modify Journal encryption.  
Do not delete `data/jarvis.env`.  
Do not resume exhaustive Room verification.
