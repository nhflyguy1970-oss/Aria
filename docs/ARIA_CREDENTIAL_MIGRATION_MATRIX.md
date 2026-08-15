# ARIA — Credential Migration Matrix (M2 + M3)

**Date:** 2026-08-13  
**Inventory:** `docs/evidence/credential_migration_m2/inventory.json`, `docs/evidence/credential_migration_m3/inventory.json`  
**Precedence:** **VAULT FIRST**. Legacy `data/jarvis.env` fallback **only if that credential is not yet migrated**. Migrated + locked → fail closed (no env fallback).  
**Rollback:** keep `jarvis.env`; do not delete plaintext copies in this phase.

`jarvis.env` is **not rewritten or emptied**. Git, Browser, Journal, Health credentials, Cloud Live, Automation, Connections, OAuth, and Postgres remain **DEFERRED**.

---

## Authorized now — Integration / Provider API credentials

| Credential | Current Store | Consumer | Target Vault Entry | Risk | Migration | Verification | Rollback |
|------------|---------------|----------|--------------------|------|-----------|--------------|----------|
| `OPENAI_API_KEY` | `data/jarvis.env` | Integrations `secrets_bus` → `test_connection(openai)`; Models wizard; connectors; LiteLLM/env leftover | `provider.openai.api_key` | Medium — live cloud spend | **AUTHORIZED NOW** — configured | Integrations Test Connection (models list) | Keep env; ignore vault entry |
| `GEMINI_API_KEY` | `data/jarvis.env` | Integrations `secrets_bus` → `test_connection(gemini)`; Models wizard; connectors | `provider.gemini.api_key` | Medium — live cloud spend | **AUTHORIZED NOW** — configured | Integrations Test Connection (models list) | Keep env; ignore vault entry |
| `GOOGLE_API_KEY` | not in env file | Alias of Gemini | `provider.gemini.api_key` | — | **AUTHORIZED NOW** — not configured (skip) | — | — |
| `HF_TOKEN` | `data/jarvis.env` | Integrations; `audio_diarize.hf_token()`; Models wizard | `provider.huggingface.token` | Medium — hub auth | **AUTHORIZED NOW** — configured | Hugging Face whoami | Keep env; ignore vault entry |
| `HUGGING_FACE_HUB_TOKEN` / `HUGGINGFACE_TOKEN` | not in env file | Aliases of HF | `provider.huggingface.token` | — | **AUTHORIZED NOW** — not configured (skip) | — | — |
| `ANTHROPIC_API_KEY` | not in env file | Integrations / connectors | `provider.anthropic.api_key` | Medium | **AUTHORIZED NOW** — not configured (skip) | — | — |
| `OPENROUTER_API_KEY` | not in env file | Integrations / Models | `provider.openrouter.api_key` | Medium | **AUTHORIZED NOW** — not configured (skip) | — | — |
| `JARVIS_MESHY_API_KEY` / `MESHY_API_KEY` | not in env file | Engineering `meshy_client` | `provider.meshy.api_key` | Medium | **AUTHORIZED NOW** — not configured (skip) | — | — |

---

## M3 — Home Assistant + LAN API (PROVEN)

| Credential | Current Store | Consumer | Target Vault Entry | Risk | Migration | Verification | Rollback |
|------------|---------------|----------|--------------------|------|-----------|--------------|----------|
| `JARVIS_HA_TOKEN` | vault `ha.token` (env copy retained) | `ha_token()` → Smart Home / HA HTTP Bearer | `ha.token` | High | **MIGRATED / PROVEN** | `GET /api/homeassistant/status` → HA `GET /api/` (no device toggle); lock fail-closed; restart | Keep env |
| `JARVIS_API_KEY` | vault `lan.api_key` (env copy retained) | `get_api_key()` / `APIKeyMiddleware` — LAN API auth only | `lan.api_key` | High | **MIGRATED / PROVEN** | LAN IP 401 without key / 200 with key; lock → 401 even with correct key; must not unlock Owner or Health | Keep env |

LAN API key authenticates the LAN API. The Aria Master Password authenticates Jeff. These remain different boundaries.

---

## Deferred — do not migrate in M3

| Credential | Current Store | Consumer | Target Vault Entry | Risk | Migration | Verification | Rollback |
|------------|---------------|----------|--------------------|------|-----------|--------------|----------|
| `JARVIS_AUTOMATION_SECRET` | `data/jarvis.env` | Automation webhook | `automation.webhook` (later) | High | **DEFERRED** | — | env remains |
| `POSTGRES_PASSWORD` | `data/jarvis.env` | Postgres | `postgres` (later) | High | **DEFERRED** | — | env remains |
| `PGVECTOR_DATABASE_URL` | `data/jarvis.env` | pgvector (URL may embed password) | `postgres` (later) | High | **DEFERRED** | — | env remains |
| Journal portable export password | not stored | Journal More → Export/Import encrypted | *not a vault secret* | High | **DEFERRED** | Exhaustive checkpoint | — |
| Health backup password | ephemeral | Health backups | *portable file password (class B)* | High | **NOT A VAULT SECRET** — M4 kept distinct from Master Password | — | — |
| Health step-up | Owner Security | Health gate | Owner session + class A step-up | High | **M4 PROVEN** | Health home no extra password; export class A; LAN/HA rejected | — |
| Cloud Live | reuses Gemini/OpenAI **via `os.getenv`** | `cloud_live_voice.py`, `gemini_live_bridge.py` | same provider entries later | Medium | **DEFERRED** as a consumer path | — | env still feeds Cloud Live |
| Git / `gh` | host | Coding shell | host-managed | High | **DEFERRED** | — | — |
| Browser profile | Chromium profile | Browser Room | browser-managed | Medium | **DEFERRED** | — | — |
| OAuth | — | — | — | High | **DEFERRED** | — | — |
| Connections | Integrations bus | Rooms | vault-backed later | Medium | **DEFERRED** | — | — |
| PIN / Uncensored hashes | PIN not configured live; leftover `uncensored_auth.json` unused when vault exists | Lock / Uncensored | Owner Security | High | **M4 PROVEN relationship** | PIN convenience only (not vault root); Uncensored is `uncensored.enable` class A | leftover hash file not deleted |

---

## Not credentials

~150 other `data/jarvis.env` keys are **config flags** (models, audio devices, feature toggles, URLs). They are listed in the inventory JSON and are **not** vault entries.

---

## Dual-read design (authorized fields)

```
CURRENT:  jarvis.env → os.environ → secrets_bus.get_secret() → consumer
TARGET:   Owner Vault  → Security.authorize(vault.secret.use)
                       → AES-GCM get (cached; no Argon2id per request)
                       → consumer receives only that credential
          If vault entry missing → legacy env
          If vault entry present and owner locked → empty (fail closed)
```

The consumer never receives the Owner Master Password.

---

## STOP

Do not migrate another category in this document’s authorization beyond the proven M2 provider batch and M3 HA+LAN. M4 unified Health/Uncensored with Owner Security and did **not** migrate further credentials.
