# Integrations Implementation

**Product:** Integrations  
**Architecture term:** External APIs  
**Package:** `jarvis/integrations_product/`  
**Date:** 2026-07-29

---

## Executive summary

Integrations is Aria’s **unified management system** for providers, API keys, secrets lifecycle, connection tests, provider health, unlock matrices, and inbound webhook **visibility**.

“External APIs” names the connector/runtime architecture (`jarvis/intelligence/connectors.py`). Operators interact with **Integrations**.

### Ownership

| Product | Owns |
|---------|------|
| **Integrations** | Credentials, health, tests, unlock matrix, hygiene, redacted usage |
| **Voice** | Cloud Live behavior |
| **Models** | Inference / provider routing |
| **Smart Home** | Home Assistant |
| **Engineering** | Meshy generation |
| **Automation** | Inbound webhook execution |
| **Browser** | Browser agent |

Never duplicate product ownership. Never build a Zapier clone or public API marketplace.

---

## Pipeline

```
Provider → Credentials → Validation → Permission review → Connection test
  → Health → Usage → Diagnostics → Mission Control → Products → Recovery
```

---

## Secret bus

Canonical module: `jarvis/integrations_product/secrets_bus.py`  
Compatibility facade: `jarvis/integration_secrets.py`

| Fact | Detail |
|------|--------|
| Storage | `data/jarvis.env` (plaintext) |
| Encryption | **None today** — communicated honestly in UI |
| Masking | Last-4 preview (`••••abcd`) |
| Ops | read / write / clear / rotate / audit / export / import |
| Permissions | Attempts `chmod 600` on save |

**Never** store secrets in Memory or chat history. Gemini Live keys stay server-side.

---

## Provider matrix

Gemini · OpenAI · Anthropic · OpenRouter · Hugging Face · Meshy · Ollama · LiteLLM · Home Assistant (managed elsewhere) · Inbound Automation Webhook (visibility) · SearXNG · Aria Host API key (LAN)

Each entry includes purpose, owner product, unlocks, status, and Test Connection.

---

## Connector framework (External APIs)

`connectors.py` is the real runtime used by Integrations:

- Registers `aria_local`, `ollama`, and credentialed connectors when keys are present (Gemini, OpenAI, OpenRouter, Meshy, Anthropic, LiteLLM).
- Provides retry, rate limit, and optional GET cache.
- OAuth remains experimental (`oauth_placeholder`).

---

## APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/integrations/product` | Product status |
| GET | `/api/integrations/product/home` | Integrations Home |
| GET | `/api/integrations/product/providers` | Provider matrix |
| POST | `/api/integrations/product/test` | Test one provider |
| POST | `/api/integrations/product/test-all` | Test configured |
| GET/POST | `/api/integrations/product/secrets` | Secret bus |
| POST | `/api/integrations/product/secrets/clear` | Clear |
| POST | `/api/integrations/product/secrets/rotate` | Rotate |
| GET | `/api/integrations/product/hygiene` | Secret hygiene |
| GET | `/api/integrations/product/diagnostics` | Diagnostics |
| GET | `/api/integrations/product/mission` | Mission Control panel |
| GET/POST | `/api/integrations/secrets` | Compat (enhanced) |

---

## Operator guide

1. Open **Integrations** (sidebar or Integrations Home view).  
2. Paste keys → Save (or save from provider detail).  
3. **Test connection** before relying on Cloud Live / Models / Meshy.  
4. Read the security banner (plaintext storage).  
5. Follow unlocks into Voice / Models / Engineering / Smart Home as appropriate.

---

## Developer guide

```python
from jarvis.integrations_product.secrets_bus import get_secret, save_secrets
from jarvis.integrations_product.providers import test_connection

key = get_secret("gemini_api_key")
result = test_connection("gemini")
```

Products must not invent parallel secret files. Consume the secret bus.

---

## Mission Control

Snapshot key: `integrations` — configured counts, plaintext warning, failures, recovery, deep links.

---

## Experimental

OS keychain · encrypted vault · OAuth profiles · Platform SecretsManager merge · async connectors · NL setup suggestions (no auto-save).

---

## Testing

```bash
venv/bin/pytest tests/test_integrations_product.py tests/test_integration_secrets.py -q
```

---

## Roadmap

1. OS keychain / encrypted vault backend  
2. Optional Platform secrets unification with migration  
3. OAuth for future calendar providers  
4. Async connector scheduling  
