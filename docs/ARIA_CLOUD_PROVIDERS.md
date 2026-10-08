# ARIA cloud providers (Phase 4)

Native adapters for OpenAI (Responses API), Anthropic (Messages API) and
Google Gemini (`generateContent`) behind the existing inference gateway. They
are **installed but inert**: with production settings (cloud disabled, no
authorization, zero budget) no request can leave the machine.

## Using a cloud model — what has to be true

All of these, checked at execution time and again immediately before the
request is transmitted:

1. `JARVIS_CLOUD_INFERENCE=1` and not `JARVIS_OFFLINE=1`.
2. The provider is allowed by `JARVIS_CLOUD_PROVIDERS` (if set).
3. The request is not local-only (health context always is).
4. The provider's API key is in the Owner Vault (or legacy env) and the vault
   is unlocked.
5. An **owner authorization** is active for that provider and the task's role:
   `POST /api/cloud/authorizations` with `provider`, `max_cost_usd`, `roles`,
   `context_classes`, `expires_in_s` (requires the owner unlocked with step-up).
6. The model has a **price** in `data/cloud_budget.json`, and the worst-case
   cost (prompt + full output allowance) fits the authorization's remaining
   cap, the per-task cap, the provider's monthly cap and the monthly total.

Fail any of them and the request is answered by the installed local model; the
routing receipt says which check refused it. Nothing is sent.

Model ids: `openai/<model>`, `anthropic/<model>`, `google/<model>`. No names
are built in — `POST /api/cloud/discover/<provider>` lists what the account can
use (free, but outbound, so it obeys the same cloud-disable/offline/allowlist
rules) and caches capabilities and context windows in `data/cloud_models.json`.

## What a cloud model sees

Default: the current request plus a neutral instruction. Each extra class must
be named in the authorization:

| Class | Content |
| --- | --- |
| `current_turn` | the request (and any tool exchange it started) — always |
| `recent_conversation` | the last few turns of the active branch |
| `continuity` | the retrieved "Conversation history" block (Phase 2) |
| `memory` | ACM fragments, profile, relevant memories |
| `system_prompt` | ARIA's own system prompt |
| `project` | project checkpoint / world state blocks |

Never shared: health context, Owner Vault secrets (a payload containing one is
refused outright), credential-shaped strings (redacted). Every send is
recorded in `data/cloud_ledger.db` → `disclosures`: provider, model, role,
authorization, classes shared and withheld, size, and a SHA-256 of the payload
(not the content).

## Money

`data/cloud_budget.json` (missing = zero budget):

```json
{
  "monthly_total_usd": 5.0,
  "per_task_max_usd": 0.25,
  "providers": {"anthropic": {"monthly_usd": 5.0}},
  "prices": {"anthropic/<model>": {"input_per_mtok": 3.0, "output_per_mtok": 15.0}}
}
```

Prices are the operator's to maintain — providers do not publish them via API.
Usage is recorded per call (`usage` table) from the provider's reported tokens,
and charged against the authorization. A failed or interrupted call is charged
at its worst case when the provider reported no usage.

These adapters always bill the **API account**. A ChatGPT, Claude or Google
subscription does not authorize API inference, and no CLI login is reused.
Subscription-backed coding CLIs (Codex, Claude Code, AGY) are Phase 5.

## Reliability

* Retries (max 2) only before any output, for 429/5xx/network faults,
  honouring `Retry-After` (capped at 30 s). Authentication failures and bad
  requests are not retried.
* A per-provider circuit opens after 3 consecutive failures for 2 minutes.
* Completion is the provider's terminal signal (`response.completed`,
  `message_stop`/`stop_reason`, `finishReason`). A stream without it is an
  interruption; after any streamed text it is never continued by another
  model. `length`/`filtered` endings are noted in the receipt.
* Cancellation stops the stream and closes the connection; no fallback.
* Tool calls are normalised to `{id, name, arguments}`; ARIA executes them only
  from a completed response, so a retried or replaced attempt cannot run a
  tool twice.

## Routing

`provider_routing.choose(role)` ranks candidates by privacy/authorization,
capabilities, measured correctness (`data/model_quality.json`, imported from
the Phase 3 benchmark), availability, context fit, latency, then cost.
Cloud candidates are listed by the operator in `data/cloud_routing.json` and are
considered automatically only when `auto_escalate` is true (default false).
`GET /api/cloud/routing?role=…` shows the decision and why.

## Status

`GET /api/cloud/status` — policy, per-provider credential *presence*,
discovery, circuits, budget, active authorizations, recent disclosures.
`GET /api/inference/receipts` — what recent calls actually did.
