# ARIA — Credential Migration M2 (Integration / Provider)

**Status:** LIVE PROVIDER BATCH PROVEN — STOP  
**Date:** 2026-08-13  
**Matrix:** `docs/ARIA_CREDENTIAL_MIGRATION_MATRIX.md`  
**Evidence:** `docs/evidence/credential_migration_m2/`  
**Checkpoint preserved:** Journal → More → Import encrypted (not resumed)

---

## 1. Credential inventory

See `docs/evidence/credential_migration_m2/inventory.json` (metadata only).

`data/jarvis.env` has 162 keys (161 configured). Most are config flags.

## 2. Authorized migration scope

Integration / Provider API credentials only.

**VAULT FIRST.** Legacy `jarvis.env` fallback only if that credential is **not** migrated. Migrated + owner locked → fail closed (no env fallback).

`jarvis.env` was **not** rewritten or emptied.

## 3. Migration matrix

`docs/ARIA_CREDENTIAL_MIGRATION_MATRIX.md`

## 4. Credentials migrated

| Env | Vault entry | Live provider op | Evidence |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | `provider.openai.api_key` | authenticated (200) | `openai.json` |
| `GEMINI_API_KEY` | `provider.gemini.api_key` | authenticated (200) | `gemini.json` |
| `HF_TOKEN` | `provider.huggingface.token` | authenticated (200) | `huggingface.json` |

Skipped (authorized category, not configured): Anthropic, OpenRouter, Meshy, `GOOGLE_API_KEY`, HF aliases.

## 5. Credentials deferred

HA token, LAN API key, Automation webhook secret, Postgres/pgvector, Journal portable passwords, Health, Git, Browser, OAuth, Connections, Cloud Live **consumer path** (`os.getenv` in `cloud_live_voice.py` / `gemini_live_bridge.py`).

## 6. Consumer verification

`secrets_bus.get_secret()` → `Security.authorize(vault.secret.use)` → vault AES-GCM get (cached). Consumers never receive the Owner Master Password.

Proven via Integrations Test Connection after each migrate, after lock/unlock, and after restart unlock.

## 7. Lock verification

Hard lock → OpenAI / Gemini / HF Test Connection all `key_missing` while `jarvis.env` still holds copies. Evidence: `lock_fail_closed.json`.

## 8. Restart verification

Process restart → `OWNER_LOCKED`, `entry_count: 3`. Unlock with existing Master Password (no provider keys re-entered). First ops after unlock: all three authenticated. Evidence: `restart_locked.json`, `unlock_after_restart.json`.

## 9. ACM boundary

Allowed metadata: “OpenAI configured”. Secret values refused. ACM text files: no leak.

## 10. Subprocess boundary

`build_subprocess_env()` does not inherit provider keys. `os.environ.copy()` not restored.

## 11. Secret leakage check

**SECRET LEAK FOUND: no**

## 12. Performance

| Measurement | Result |
| --- | --- |
| Unlock after restart (Argon2id) | 50.9 ms |
| Unlock after lock | 55.91 ms |
| Vault put (migrate) | 6.5–7.2 ms |
| First credential get after unlock | 0.05–0.09 ms (no Argon2id) |
| Subsequent get (cache) | ~0.00 ms |
| Lock | 0.19–0.33 ms |
| First OpenAI test after restart unlock | 954 ms (network) |
| First Gemini test after restart unlock | 240 ms |
| First HF test after restart unlock | 172 ms |

Room navigation does not run Argon2id.

## 13. Integrity

**clean / 100.** QA mutating POST → 403.

## 14. Rollback

Still valid: `data/jarvis.env` retained (mode 0600). Fingerprints unchanged from pre-migrate inventory. Delete vault entries or ignore them to fall back to env for unmigrated IDs; migrated IDs stay vault-gated until a later M6 plaintext-removal authorization.

## 15. Remaining legacy credentials

Still plaintext in `jarvis.env`: HA, LAN, Automation, Postgres, and all config flags. Provider keys remain in env **as rollback copies** until an explicit later authorization removes them.

Cloud Live still reads provider keys from process env (deferred consumer).

---

## Failed

None of the configured authorized credentials failed migration. OpenAI had one network timeout during a later probe; vault retrieval had already succeeded.

A hard lock occurred during that later OpenAI timeout. First-after-restart-unlock operations were already proven. Unlock Aria for daily use if the overlay is showing.

---

## STOP

Do not migrate another category. Do not delete `jarvis.env`. Do not migrate Health, HA, LAN, Git, Browser, or Journal. Do not resume exhaustive Room verification.
