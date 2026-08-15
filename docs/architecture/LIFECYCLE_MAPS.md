# Aria Lifecycle Maps

Companion to [ARCHITECTURE_BIBLE.md](./ARCHITECTURE_BIBLE.md).  
Each map is the **one lifecycle** that subsystem should obey. Divergent paths are debt.

---

## 1. Request lifecycle (HTTP → response)

```
Client (SPA / MCP / webhook)
  → Middleware (NetworkGuard → RateLimit → APIKey → PinLock)
  → FastAPI route (server | extra_routes | extension | product)
  → [Chat] asyncio.to_thread / stream_sync_iter
       → JarvisAssistant.process[_stream]
            → acquire _request_lock
            → route() → intent
            → handlers/registry or queue submit or _chat
            → persist branch / emit jobs / activity
  → JSON | SSE
```

**Failure modes:** auth bypass on LAN; silent missing product routes; lock timeout (stream only); event-loop blocked by sync route.

---

## 2. Conversation lifecycle

```
New Chat / switch branch
  → BranchManager create/switch (chat_branches.json)
  → optional chat_sessions.db row (weak link)
  → Conversation messages [system, …]
  → user message → route → action/chat
  → assistant message appended
  → Clear: clear_branch_messages → verify GET messages empty
  → Delete branch (not main) → session row may orphan
```

**SoT:** `chat_branches.json` messages.  
**Forbidden:** Clear success without verify; dual transcript stores without integrity.

---

## 3. Inference lifecycle

```
action/capability
  → capability_routing (capability → role)
  → model_policy.select_model_for_role
  → (again) execution_policy.apply_policy_to_route
  → inference.policy.select_route (ollama | litellm)
  → gateway.chat_with_usage / stream_chat
       litellm error → ollama fallback
  → usage + execution_* fields
```

**Debt:** 2–3 policy passes; ask_stream Ollama bypasses gateway.

---

## 4. LLM routing lifecycle (intent)

```
message (+ attachment)
  → pending clarification?
  → skills / automation / specialists / workflows
  → reflex / cognition compose
  → memory NLU / NLU pipeline (weather/calendar fast paths)
  → _quick_route (router_table + inline duplicates)
  → llm.route_with_tools / ROUTER_PROMPT JSON
  → runtime_priority
  → _finalize_intent → action
```

**Dead paths:** `try_local_route`, `try_functiongemma_route` (unreachable).

---

## 5. Model / provider selection

```
User/UI Models home or auto
  → model_store role binding
  → model_policy (benchmark, VRAM, installed)
  → providers via integrations_product / ollama_*
  → provider_health publish
```

**SoT:** `model_settings.json` (legacy) + models_product façade.

---

## 6. Memory lifecycle

```
Utterance / explicit remember / auto_remember
  → MemoryEngine / modules.memory / ACM bridge
  → write cognitive record (ACM primary — declared)
  → optional vector / graph / hierarchy mirrors
  → context assembly in ConversationEngine.build_context_prefix
  → retrieval at chat time (policy-gated sources)
```

**Multi-truth risk:** memory.db / memory.json / vectors / graph / ACM / platform dual_write theater.

---

## 7. Search lifecycle

```
POST /api/search/product/query
  → intent / facets
  → retrievers × N corpora (enabled settings)
  → ranking / contract
  → history/sessions optional
```

**SoT:** none (federation). Each corpus must agree with its owner SoT.

---

## 8. Planner lifecycle

```
Create task/timer/alarm (API or NL)
  → planner_store (planner.db)
  → Calendar day view federates tasks
  → Search may retrieve
  → Focus start → timer + optional HA scene (ha_ok independent)
  → complete/delete → store update → UI refreshCalendar/loadPlanner
```

---

## 9. Calendar lifecycle

```
Day/week request
  → calendar_schedule aggregates:
       planner tasks | journal notes | ICS | work schedule
  → UI calendar.js
  → NL schedule → confirm → refresh (must verify item identity)
```

**Owns almost no data** — facade.

---

## 10. Journal lifecycle

```
Bullet create/edit (journal UI / API)
  → modules.journal → bullet_journal.json
  → Calendar federation
  → Search corpus
  → photo attach/delete (must check DELETE status)
```

---

## 11. Coding lifecycle

```
Chat coding_* or Coding UI
  → propose (pending_proposals)
  → review / apply / undo
  → coding_jobs worker
  → verify / tests optional
  → code_index.json context (huge)
  → Activity may claim “patch applied” too early
```

---

## 12. Browser lifecycle

```
Navigate / run agent
  → browser_product.session (_PAGE)
  → Playwright
  → history/screenshots/downloads under data/
  → legacy browser_agent may still exist
```

**Triple stack:** legacy + product + extension.

---

## 13. Voice lifecycle

```
Mic / wakeword / Cloud live
  → STT (Whisper / RealtimeSTT)
  → intent_router / speech_policy
  → assistant.process
  → TTS
```

**Dual-write settings:** `voice_product/settings.json` + `voice_settings.json`.

---

## 14. Vision lifecycle

```
Webcam / attach / import
  → vision_product.engine analyze/OCR
  → model via vision role
  → history.jsonl
  → may feed coding/browser bridges
```

---

## 15. Gallery / media lifecycle

```
generate image/video (chat or Gallery UI)
  → media_jobs queue
  → ComfyUI / generators
  → file in data/generated[/videos]
  → gallery list + chat durable markdown embed
  → jobs_center row
  → search hit
  → soft-delete → trash + scrub chat embeds
  → restore → file + repair embeds (+ clear asset_missing)
```

**Truth rule:** Complete only when file exists AND surfaces agree.

---

## 16. Notification / Activity lifecycle

```
Producer (job done, HA, calendar, client producer…)
  → often activity_outbox.jsonl OR client publish
  → notifications pipeline / preferences
  → Activity Center UI (localStorage log)
  → dismiss/read (client only today)
```

**Broken one-truth:** server outbox ≠ client store.

---

## 17. Settings lifecycle

```
UI toggle (theme, product setting)
  → local apply + localStorage / BroadcastChannel
  → POST settings_product or product-owned JSON
  → other tabs storage event
```

**Must:** remote persist failure → warn, not silent success.

---

## 18. Projects lifecycle

```
Create project → data/projects/{slug}/meta.json
  → activate → namespace sync
  → archive → remove from active search
  → assets under project dirs
```

---

## 19. Automation lifecycle

```
Rule/DAG create
  → automation_product / legacy user_automations
  → engine schedule / webhook inbound
  → execution history
  → pause/resume (must verify API ok)
```

---

## 20. Mission Control / Dashboard lifecycle

```
Dashboard home → aggregate products + last_good cache
Mission Control → aiplatform aggregator + enrich → UI
```

---

## 21. Job lifecycle (unified view)

```
submit(coding|media|background)
  → queue.Queue + worker thread
  → state JSON
  → events / notifications
  → jobs_center sanitize (asset_missing)
  → cancel / timeout / recover_stale on boot
```

---

## 22. Certification lifecycle

```
POST /api/certification/run[/sync]  (sync must off-event-loop)
  → create run dir under data/certification/runs/{id}
  → suites assert expected vs observed + API traces + files
  → mutation check (must FAIL injected)
  → false-pass resample
  → gate: READY_TO_SHIP | SMOKE_PASS | DO_NOT_SHIP
  → dashboard home/detail + evidence package
```

**Rule:** skip_image ⇒ cannot READY_TO_SHIP.

---

## Cross-cutting consistency rule

For any created object O:

```
UI representation ≡ API representation ≡ Disk/DB ≡ Search (if indexed)
  ≡ Jobs/History (if applicable) ≡ Notifications (if emitted)
after reload (and restart when claimed)
```

Disagreement = defect, not “eventual.”
