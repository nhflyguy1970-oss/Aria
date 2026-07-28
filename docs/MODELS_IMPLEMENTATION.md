# Models Implementation

## Philosophy

**Models** is the AI Model Configuration and Routing Center for the Aria AI Operating System.

| Models owns | Mission Control owns |
|-------------|----------------------|
| Role assignments | Provider / inference health |
| Model registry | VRAM health console |
| Provider configuration | Warm / unload ops |
| Routing configuration | Recovery |
| Presets / catalog / recommendations | Runtime diagnostics |
| Model selection | |

**Models configures. Mission Control monitors.**

Never silent auto-switch. Never auto-download large models. Never replace Ollama.

## Architecture

```
UI: Models Home (models_home.js) + sidebar quick editor + chat override
        ↓
Authoritative API: POST /api/models/switch
        ↓
jarvis/models_product/
  home.py catalog.py switch.py recommender.py providers.py
  vram_advisor.py policy.py packs.py pull_manager.py
  activity_bridge.py task_coach.py
        ↓
jarvis/model_store.py (persistent role map)
jarvis/inference/gateway.py (runtime routing)
```

Mission Control `switch_model` **delegates** to `/api/models/switch` (`role_default`). Warm/unload remain health ops and do not mutate the registry.

## Switch contract

| Scope | Meaning |
|-------|---------|
| `role_default` | Persist role→model in registry |
| `chat_override` | Session-only chat model |
| `make_default` | Promote chat model → conversation default |
| `ops_temporary` | Rejected — use MC warm/unload |

## Roles

**Primary:** conversation, coding, vision, image, embedding  

**Advanced:** reasoning, planning, review, fast_chat, router, tool_calling, summarization, document, web_research, reflection, learning  

Legacy aliases (`general`/`coder`/`embed`) kept in sync for compatibility.

## Catalog & cards

Cards expose friendly name, tag, provider, capabilities, VRAM/RAM estimates, context, license, installed/running, fits-hardware, conflicts, recommended uses.

## Provider wizard

Validates Ollama, LiteLLM, OpenAI, Gemini, OpenRouter, Hugging Face (connectivity / key presence). Cloud keys still saved via Integrations.

## Recommendations

Stack recommender (Fast / Balanced / Quality / Coding / Vision / Reasoning) — **suggest only**, confirm to apply.

Task coach suggests coding/vision/reasoning — confirm required.

## Activity

Events: model_switched, role_changed, pull_*, oom, vram_warning, provider_offline — with Fix links to Models Home or MC Inference.

## Policy packs (experimental)

Optional `policy.json` can gate switch / pull / unload / edit_defaults for future multi-user.

## Shortcuts

- **Ctrl+Shift+.** — Models Home  
- **Ctrl+Shift+M** — Mission Control  

## Testing

`tests/test_model_store.py` — registry, switch, cards, VRAM, recommender, providers, policy, home, packs, MC switch delegation.

## Migration

- Sidebar “Model settings” → Models Home + quick editor  
- MC switch no longer writes `preferred_model.txt`  
- Palette opens Models Home  

## Roadmap

Richer Platform registry metadata, resumable pulls where Ollama supports, multi-user policy UX.
