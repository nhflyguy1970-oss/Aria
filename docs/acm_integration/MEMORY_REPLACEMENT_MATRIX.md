# Memory Replacement Matrix — Aria ↔ ACM

**Status:** DESIGN ONLY  
**Policy:** ACM SUPREMACY RULES (`ARIA_ACM_ARCHITECTURE.md`)  
**Legend — Disposition:** `MIGRATE` (into ACM) · `INTERFACE` (host→ACM) · `RETIRE` (approved) · `KEEP-HOST` (non-cognitive)

No row may imply permanent dual cognition or legacy override after cutover.

---

## A. Core cognitive surfaces

| Capability | Current Aria implementation | ACM organ / API | Strategy | Compatibility | Validation | Tests | Rollback |
|------------|----------------------------|-----------------|----------|---------------|------------|-------|----------|
| User identity (profile) | ns `profile` via questionnaire / MemoryStore | Identity `who_am_i`, Policy Gate, encode kind=identity | MIGRATE | Assent high-impact | Identity snapshot parity | Identity encode/assent | Restore profile export |
| Agent identity (config) | `aria_core/identity.py`, prompts | KEEP-HOST agent config | KEEP-HOST | Not autobiographical SoT | Config unchanged | Unit | N/A |
| Preferences (cognitive) | `type=preference` entries | Concepts + preference explanation | MIGRATE | Prefer Concept attrs | Preference recall | Preference lineage | Re-import dump |
| Preferences (usage telemetry) | `personalization/preferences.json` | KEEP-HOST telemetry | KEEP-HOST | Must not be cognitive SoT | No autobiography drift | Unit | N/A |
| Facts | `type=fact` | Experiences + Concepts | MIGRATE | Encode; Concept residue | Fact Q → ACM remember | Fact encode/recall | Legacy reattach |
| Notes | `type=note` | Experiences | MIGRATE | Immutable | List/search | Note suite | Snapshot |
| Episodic experiences | ns `experience`, success/failure | Experience organ | MIGRATE | No silent overwrite | `what_happened` | Immutability | Snapshot |
| Strategies | `type=strategy` / trust_memory | Concepts (cognitive) or host policy | MIGRATE cognitive; KEEP-HOST pure policy | Strategies not spoken recall by default | Policy vs Concept split signed | Strategy class tests | Legacy tags |
| Telemetry / tool-outcome | tagged auto/telemetry | KEEP-HOST diagnostics **or** cool Experiences with telemetry tags | KEEP-HOST preferred | Not Daily Use recall | Excluded from about-me | Filter tests | N/A |
| Learning from reflection | Learning managers + consolidate | Learning organ + Reflective Experiences | MIGRATE (host coordinator only) | propose→assent via ACM | Adaptation records | Learn/assent/rollback | Legacy proposals archive |
| Offline consolidation | `memory_consolidation` | Offline Cognition `sleep` | MIGRATE | LLM = proposer only | Sleep never births false history | Sleep gated | Disable sleep |
| Memory search | `search_memory` / hierarchical_search | Remembering + Activation | INTERFACE→ACM | Not vector-as-memory | Ranking classes | Search regression | Legacy search |
| Recall / spoken answer | MemoryEngine.recall / about_user | `what_do_i_remember` | INTERFACE→ACM | Reconstruction answers | Speech Daily Use | Recall harness | Legacy recall |
| Updates / corrections | update / memory_correct / supersede | `revise_experience` + Reconciliation | MIGRATE | No silent history rewrite | Lineage + reconcile | Correction tests | Legacy supersede |
| Deletes / forget | forget / memory_forget | `cool_memory` (+ rare Policy erase) | MIGRATE | Soft accessibility first | Cool ≠ delete | Forget behavioral | Restore accessibility |
| Conversation memory injection | prepare_context / memory_context | Working Buffer + remember + ContextFrame | INTERFACE→ACM | Prompt packaging Aria | No CoT leak | Context injection | Legacy prepare_context |
| Conversation transcripts | `chat_branches.json` | KEEP-HOST packaging | KEEP-HOST | Not SoT | Branch IO | Branch tests | N/A |
| Working / short-term | hierarchy `working` layer | WorkingBuffer | MIGRATE | Capacity-limited | Displace observables | Buffer tests | N/A |
| Runtime / session scratch | `session.py` | KEEP-HOST / ContextFrame tags | KEEP-HOST | Not autobiographical | No SoT leakage | Unit | N/A |
| Goal / project memory | project_checkpoint / resume | Goal Space + Experiences | MIGRATE | Goals peer system | Checkpoint ↔ goal | Project resume | Legacy checkpoints |
| Predictive recall | Limited | Prediction `what_is_likely` | MIGRATE (optional product expose) | Not planning; not history | API works | Prediction suite | Hide UI |
| Hypothetical futures | Limited | Simulation | MIGRATE (optional expose) | Never Experience history | Reality wall | Simulation suite | Hide UI |
| Analogies / blends | Limited | Analogy / Recombination | MIGRATE (optional expose) | Non-historical | Observables | Suites | Hide UI |
| Conflict / contested facts | supersede tags | Reconciliation + Confidence | MIGRATE | Competing lineage retained | Status lineage | Reconciliation | Legacy tags |
| Confidence / uncertainty | Sparse scores | Confidence organ | MIGRATE | Explainable evolution | `how_certain_am_i` | Confidence tests | Hide MC |
| Provenance / source | Weak tags | Provenance model | MIGRATE | Non-fabricated | `provenance_of` | Provenance cert | — |
| Accessibility | prune / dormant | Forgetting organ | MIGRATE | Soft cool | cool/reactivate | Forgetting suite | — |
| Attention / priority | Retrieval ranking | Attention organ | MIGRATE | Ranking → attention classes | allocate | Attention suite | — |
| Cheatsheets | cheatsheet store/API | KEEP-HOST UI; encode if taught | KEEP-HOST | Citation wall | No silent SoT | — | — |
| Knowledge / RAG corpora | documents / KNOWLEDGE | KEEP-HOST knowledge | KEEP-HOST | Adopt via explicit encode | Citation wall | — | — |

---

## B. MEMORY_RETRIEVAL_BEHAVIOR classes (explicit coverage)

| Class (retrieval doc) | Disposition | Notes |
|-----------------------|-------------|-------|
| User facts | MIGRATE | |
| Preferences | MIGRATE | cognitive only |
| Profile | MIGRATE | into Identity + Concepts |
| Notes | MIGRATE | |
| Journal | MIGRATE encode path; ranking INTERFACE | Journal files KEEP-HOST |
| Strategies | MIGRATE / KEEP-HOST split | see §A |
| Telemetry / tool-outcome | KEEP-HOST (preferred) | exclude from about-me |
| Conversation Trace | INTERFACE observability | not memory SoT |
| Superseded | MIGRATE as inactive Experiences | revise lineage |

---

## C. Conversational behavior actions

| Action | Current | ACM mapping | Disposition |
|--------|---------|-------------|-------------|
| `remember` | → store.add | `encode` | INTERFACE→ACM |
| `recall` | MemoryEngine.recall | `what_do_i_remember` | INTERFACE→ACM |
| `memory_search` | hierarchical_search | remember + neighborhood | INTERFACE→ACM |
| `memory_forget` | topic delete/supersede | `cool_memory` / Policy erase | INTERFACE→ACM |
| `memory_correct` | supersede update | `revise_experience` (+ reconcile) | INTERFACE→ACM |
| `memory_prune` | prune entries | Forgetting cool proposals | INTERFACE→ACM |
| `memory_consolidate` | nightly distill | `sleep` (+ host LLM propose) | INTERFACE→ACM |
| `memory_hierarchy` | layer listing | stage / accessibility views | INTERFACE→ACM |
| `memory_summarize` | summaries | Identity + Concepts + remember | INTERFACE→ACM |
| `memory_namespace` | namespace CRUD | Context tags / roles | MIGRATE tags INTO ACM |
| `memory_about_user` | profile summary | `who_am_i` + remember | INTERFACE→ACM |
| `project_checkpoint` | upsert checkpoint | Goal + encode | INTERFACE→ACM |
| `project_resume` | read checkpoint | Goals + remember | INTERFACE→ACM |
| `remember_image` | image + entry | encode + multimodal envelope | INTERFACE→ACM |
| `journal_remember` | journal entry | encode + `journal` tags | INTERFACE→ACM |
| `auto_remember` | silent writes | encode under Attention | INTERFACE→ACM (visible) |
| `prepare_context` | prompt injection | remember + Aria assembler | INTERFACE (assembler KEEP-HOST) |
| `cheatsheet_*` | cheatsheet files | KEEP-HOST | KEEP-HOST |

---

## D. Core / Cap Bus / storage / APIs

| Capability | Current | ACM | Strategy |
|------------|---------|-----|----------|
| Cap Bus remember/recall | → memory_manager | Façade → encode/remember | INTERFACE→ACM |
| aria_core.memory_* APIs | memory_manager | Thin façade → CognitiveEngine | INTERFACE→ACM |
| REST `/api/memory*` | extensions/memory/api.py | Façade | INTERFACE→ACM |
| jarvis.modules.memory JSON/SQLite | Persistence SoT | ACM DurableCognitiveStore | MIGRATE then RETIRE |
| DualWrite platform adapter | AI-Platform CRUD mirror | Retire authority; optional ACM projection | RETIRE / INTERFACE |
| Embedding sidecar | semantic_memory / vectors | Activation prior **plugin** only | INTERFACE plugin |
| Graph store relationships | relationship_graph.db | Concepts + Associations | MIGRATE facts; graph not SoT |
| Event bus Memory* | content-free events | Map encode/remember/sleep/… | INTERFACE |

---

## E. Specialized domain memory modules

| Module | Current path | ACM | Strategy |
|--------|--------------|-----|----------|
| `experience_memory` | success/failure patterns | Experiences + Concepts | MIGRATE then remove parallel |
| `relationship_memory` | relationship facts | Concepts + Associations | MIGRATE then remove parallel |
| `trust_memory` | strategy rules | Concepts / host policy | MIGRATE cognitive; KEEP-HOST policy |
| `brain_memory` | brain-mode toggles | KEEP-HOST flags → `sleep` | INTERFACE |
| `memory_consolidation` | LLM distill SoT writes | Propose Reflective → Learning/`sleep` | INTERFACE |
| `*_learning` (document/journal/observation/correction/workflow/explicit) | direct memory.add | `encode` + provenance | MIGRATE writers to ACM |
| `profile_questionnaire` | profile ns writes | encode / identity assent | INTERFACE→ACM |
| `platform_memory` / dual-write | AI-Platform CRUD | RETIRE as SoT | RETIRE |

---

## F. Bullet Journal

| Capability | Current | ACM | Strategy |
|------------|---------|-----|----------|
| Journal remember | journal + memory tags | Experience encode + `journal` tags | MIGRATE INTO ACM |
| Journal learning | journal_learning → memory.add | encode + provenance | MIGRATE |
| Journal megablob demotion | Ranking heuristics | Accessibility + Attention + façade policy | INTERFACE |
| Journal export/UI / weather / presets | journal_* | KEEP-HOST UI | Non-cognitive |

Journal is **not** a second memory system after cutover (Rule 1).

---

## G. Observability & host surfaces

| Capability | Current | ACM | Strategy |
|------------|---------|-----|----------|
| Mission Control Memory panel | mission_control_panel | ValidationHarness + Trace observables | INTERFACE — no redesign |
| Conversation Trace organs.memory | read/write flags | ACM verb classes, confidence, provenance | INTERFACE |
| Retrieval diagnostics | ranking decision | Activation / attention why-codes | INTERFACE |
| MCP memory tools | none today | None required | N/A |

---

## H. Intentionally non-ACM (KEEP-HOST)

| Capability | Why |
|------------|-----|
| Cap Bus orchestration policy | Host |
| Router NLU | Host |
| Mission Control chrome / tabs | Host presentation |
| Speech / TTS / sensors | IO |
| Planning / Decision / Executive | Not ACM (deferred separately) |
| Pure knowledge corpora without encode | Knowledge ≠ Memory |
| Chat transcript packaging | Conversation ≠ Memory SoT |
| `ml_memory.py` GPU/RAM | Unrelated naming |

---

## I. Approved intentional retirements (Rule 2)

| Capability | Approval | User-visible note |
|------------|----------|-------------------|
| Hard-delete-as-default forget | Blueprint A001 | Forget cools memory; rare erase gated |
| Namespace-as-separate-DB | A001 | Tags/roles replace parallel DBs |
| DualWrite CRUD as cognitive authority | A001 | Platform may receive projections only |
| Silent LLM distill as SoT | A001 | Distill proposes; ACM owns commit |

New ACM organs (Prediction / Simulation / Analogy) are **kept capabilities**, not replacements of lost Aria features — product may hide UI until Daily Use ready; memory correctness still tested.

---

## Unmapped check

Inventory sources covered:

- `docs/MEMORY_RETRIEVAL_BEHAVIOR.md` classes  
- `aria_core.memory` / `memory_manager` APIs  
- Cap Bus remember/recall  
- MemoryBehavior actions  
- REST memory/journal/profile/cheatsheet routes  
- Specialized `*_memory` / `*_learning` modules  
- Journal, MC, Trace, DualWrite, embeddings, graph, personalization, chat transcripts  

**No capability left unmapped. No dual-SoT end-state dispositions.** Temporary Shadow is migration phase only.
