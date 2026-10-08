# ARIA inference boundary (Phase 3)

One place decides what a model call may do, and records what it actually did.
No second router was added: `jarvis.inference.gateway` was already the path
every model call takes (`jarvis.llm`, `model_routing.execute`, conversation
streaming); Phase 3 made it the enforcement point and moved the one bypass —
the tool-call router — onto it.

## Layers

| Layer | Decides | Module |
| --- | --- | --- |
| Model selection (unchanged) | which model suits the role: Settings, benchmark policy, capability routing, `model_routing` | `capability_routing`, `inference/execution_policy`, `model_routing` |
| Route | local Ollama, or a cloud model via the configured gateway | `inference/policy.select_route` |
| **Boundary** | whether that route may run *now*, what replaces it if not, what the model can do, and the receipt | `inference/boundary`, `inference/gateway` |
| Provider call | Ollama, or LiteLLM (today's only cloud transport) | `gateway._ollama_*`, `gateway._litellm_*` |

## Rules enforced at execution time

1. **Cloud permission** — a cloud target runs only if `JARVIS_CLOUD_INFERENCE=1`,
   ARIA is not offline (`JARVIS_OFFLINE`), the request is not local-only, and
   the provider is in `JARVIS_CLOUD_PROVIDERS` when that allowlist is set. An
   explicit model choice, or a caller-supplied route, is re-checked; the
   LiteLLM call itself re-checks the global policy before any egress.
2. **Private context stays local** — a request carrying health record context
   is classified local-only automatically; callers can also pass
   `privacy="local_only"`.
3. **Fallback is to installed local models only** — a refused or failed cloud
   target is answered by the model configured for the role, verified as
   installed; a cloud model id can never reach Ollama (hard check in the Ollama
   call). With no installed local model, the call fails honestly.
4. **Local failures are not retried elsewhere**; policy refusals and
   capability mismatches are never "fallen back" around.
5. **Streams**: a provider that fails before producing output may be replaced
   by the local model; once any text has streamed, failure raises
   `StreamInterrupted`. The conversation reports the interruption and never
   saves the partial text as an answer. Cancellation stops the attempt and
   never triggers a fallback.
6. **Capabilities**: tools, images (vision) are checked against what the
   provider reports (Ollama `/api/show`; LiteLLM `/model/info`) before the call.
7. **Tool calls** (`gateway.chat_with_tools`) return normalised tool calls
   from one *completed* attempt. The gateway never executes tools, so a failed
   or replaced attempt cannot have caused a side effect.
8. **Health preflight is route-dependent**: a permitted cloud request does not
   wait on local Ollama health; anything that will run locally does.

## Receipts

Every call returns `usage["receipt"]`: requested model, privacy class, policy
decisions, and each attempt's provider, model, locality, status (`completed`,
`failed`, `interrupted`, `cancelled`), first-token and total latency, output
size and token usage; plus the executed provider/model/locality and whether a
fallback was used. The last 50 are at `GET /api/inference/receipts` with the
current cloud policy. Existing `execution_*` usage keys are preserved.

## Not hardcoded

No cloud model name is built in. Large-context escalation needs an
operator-set `JARVIS_CLOUD_MODEL`; `boundary.discover_cloud_models()` asks the
configured gateway what it serves.

## Phase 4 prerequisites

* Native adapters (OpenAI Responses, Anthropic Messages, Gemini) plug in as
  providers beside LiteLLM and must implement the same contract: the egress
  guard, normalised tool calls, terminal-status checks, usage, and
  pre-output vs. post-output failure classification.
* Credentials from the Owner Vault per provider; per-provider allowlist entries;
  budgets/quotas and a usage ledger keyed by receipt id.
* Account-level capability discovery replacing the LiteLLM `/model/info` read.
* A decision on which memory/project classes may be sent to which provider
  (today only health context is automatically local-only).
