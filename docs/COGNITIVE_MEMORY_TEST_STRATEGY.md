# Cognitive Memory Test Strategy

**Status:** Canonical validation strategy for ACM migration (design only)  
**Mode:** Not a test plan, not code, not a harness implementation—defines *what success looks like*  
**Companions:**

| Document | Role |
|----------|------|
| [`MEMORY_DESIGN_PRINCIPLES.md`](MEMORY_DESIGN_PRINCIPLES.md) | Constitution — *why* |
| [`ARIA_COGNITIVE_MEMORY.md`](ARIA_COGNITIVE_MEMORY.md) | Architecture — *how* |
| **This file** | **Validation** — *how we know migration is working* |

**Authority:** No Memory migration phase is complete unless it advances measurable cognitive contracts here under **Daily Use Mode**.  
**Forbidden by this document:** Speculative implementation, prototypes, or harness builds until a migration phase explicitly authorizes them.

---

## 1. Purpose

ACM must be validated as **cognition**, not as storage quality.

When migration begins, every phase must prove movement toward human-like memory:

- Identity forms and stays trustworthy  
- Concepts emerge and associate  
- Memories strengthen and weaken  
- Remembering reconsolidates  
- Context and goals bias recall  
- Attention shapes encoding  
- Sleep reorganizes  
- Multimodal evidence reinforces  
- Confidence and importance evolve  
- Inference stays grounded  
- Autobiography stays coherent  
- User trust and control hold  

Technology choices are irrelevant to pass/fail except insofar as cognitive contracts hold after a substrate change.

---

## 2. Validation philosophy

| Do | Do not |
|----|--------|
| Probe behavior through canonical scenarios | Treat latency-only wins as cognitive wins |
| Measure activation *classes* and state transitions | Require dumping private contents in default UIs |
| Prefer lifelong trajectories over single queries | Equate search relevance@k with remembering |
| Gate phases with Behavioral Compatibility + Trace/MC | Allow “migration complete” by schema cutover alone |
| Keep explanations template-class only | Expose chain-of-thought, prompts, or latent reasoning |

**North-star test:** After the change, does Aria remember more like a person who lives with Jeff—or more like a database with a chat UI?

---

## 3. Milestone M0 — Cognitive Memory Validation Harness (design)

### What M0 is

A **development and validation capability**—not a runtime organ, not a Cap Bus capability, not user-facing cognition.

M0 exists **before M1 Identity Memory** so every later migration can be measured consistently.

### What M0 is not

- Not a new cognitive subsystem in production Aria  
- Not a replacement for Mission Control or Conversation Trace (it *feeds* them)  
- Not implementation authorized by the freeze alone  

### What M0 must eventually enable teams to observe (when built under an authorized phase)

| Observable | Meaning |
|------------|---------|
| Concepts activated | Which concept seeds fired for a cue |
| Why activated | Cue class: lexical, associative spread, goal bias, context match, multimodal, attention spike |
| Confidence movement | Before/after belief confidence on touched attributes |
| Association changes | Edges added/strengthened/weakened/contested/superseded |
| Concept merges / splits | Candidates and applied evolutions |
| Reconsolidation | Whether Remember wrote; version/lineage bump |
| Sleep effects | What Sleep proposed vs applied; assent outcomes |
| Goal influence | Which open goals biased the episode |
| Attention influence | Capture class that gated encode |
| Identity evolution | Identity Schema touches under Policy Gate |
| Working memory transitions | Buffer enter/exit/displace/promote-to-encode |
| Memory lifecycle | Encode → active → reconsolidate → weaken/archive/deactivate/erase |

### M0 success (definition)

M0 is successful when **later milestones can fail closed**: if a migration cannot show these observables for its claims, the milestone cannot be marked done.

### M0 relation to Daily Use Mode

Harness probes become the measurement step for Memory Problem Reports. Green CI includes cognitive contracts relevant to the milestone under change—not the whole of ACM at once.

---

## 4. Observability strategy (design)

Conversation Trace and Mission Control remain first-class. They evolve from **execution telemetry** toward **cognitive behavior telemetry**—without exposing reasoning internals.

### 4.1 Conversation Trace — cognitive behavior record

Per interaction (metadata, not chain-of-thought):

| Field class | Examples |
|-------------|----------|
| Intent / memory operation | encode · remember · reconsolidate · sleep-triggered follow-up |
| Context frame | activity/place/time class (not raw secrets by default) |
| Attention capture class | novelty · stakes · goal · pin · prediction-error · sensory |
| Goal influence | open goal ids/labels *classes*; bias applied yes/no |
| Activation summary | top concept ids/types; peak counts; reject count |
| Association path summary | edge *types* traversed (not full private graph dump by default) |
| Answer frame type | speech · media · procedure · timeline · commitment |
| Confidence / importance deltas | signed summaries on touched items |
| Reconsolidation | null / light refresh / supersede / contest |
| Explanation class served | preference · repeated · stale · contested · context · goal |
| Latency | remember vs reconsolidate vs sleep deferral |
| Policy Gate | assent required / granted / denied |
| Errors | backend failures recorded for engineers; sanitized for users |

**Never in user-visible Trace panels by default:** system prompts, hidden chain-of-thought, raw embedding vectors, full multimodal binaries, unrelated private envelopes.

### 4.2 Mission Control — cognitive visualization (eventual)

When authorized, Memory / Cognitive panels should visualize **state**, not digests of thinking:

| View | Shows |
|------|-------|
| Activated concepts | Recent peaks (labels/ids, types) |
| Association paths | Type-weighted neighborhoods on inspect |
| Memory confidence | Distributions; contested counts |
| Concept evolution | Merge/split/alias timelines (metadata) |
| Strength changes | Strengthen vs weaken event rates |
| Reconsolidation events | Counts, classes, lineage bumps |
| Sleep activity | Last run health, proposals pending, applied tiers |
| Goal influence | Active goals and bias heat (non-content) |
| Attention weighting | Capture class histogram |
| Context influence | Which context frames dominated recall |
| Identity growth | Identity Schema touch/assent metrics |

**Contents off by default.** Inspect-with-permission for autobiographical dig.

### 4.3 User-facing explainability

Remains template-bound per Principles P22. Trace may be richer for engineers; users get natural memory-reasons only.

---

## 5. Cognitive success definitions by capability

Each subsection states **success**, **failure**, and **phase relevance** (earliest milestone that must own the contract).

### 5.1 Identity formation — M1+

**Success:** User and Aria Identity Schemas answer “who” questions from experienced/adopted life; high-impact edits require assent; wrong generics do not overwrite.  
**Failure:** Doc/persona scrape defines the user; silent identity flip; no lineage.  

### 5.2 Concept formation — M3+

**Success:** Repeated congruent experience produces stable concepts; provisional states exist; one-off noise rarely canonicizes.  
**Failure:** Every utterance creates equal permanent concepts.  

### 5.3 Association growth — M4+

**Success:** Typed associations increase meaningful neighborhoods (Zeus↔camping↔photos).  
**Failure:** Bags of tags; no path-shaped remembering.  

### 5.4 Memory strengthening — M4/M5/M7+

**Success:** Practice, confirmation, multimodal co-activation raise retrieval preference.  
**Failure:** Strength invariant under success/repetition.  

### 5.5 Memory weakening — M7/M9+

**Success:** Neglect, supersession, and finished goals cool default recall.  
**Failure:** Eternal equal salience.  

### 5.6 Reconsolidation — M7+

**Success:** “Actually…” and corrections version active beliefs; dig can show history.  
**Failure:** Dual actives; recall never writes; history destroyed on update.  

### 5.7 Context-aware recall — M2+

**Success:** Context-conditioned prefs coexist; current frame biases default answers.  
**Failure:** Global scalars fight themselves.  

### 5.8 Goal-biased remembering — M6+

**Success:** Open goals surface unfinished threads; completion removes default bias.  
**Failure:** Goals ignored by remembering.  

### 5.9 Attention effects — M2+

**Success:** High-attention encode ≫ low-attention fluff; pins force spotlight.  
**Failure:** Uniform logging into “long-term.”  

### 5.10 Sleep consolidation — M9+

**Success:** Sleep proposes/applies tiered reorganization; Identity protected by assent; clarity rises over time.  
**Failure:** Sleep only deletes disk waste or silently rewrites autobiography.  

### 5.11 Multimodal reinforcement — M5+

**Success:** Media/sensor/co-evidence thicken concept strength beyond text-only.  
**Failure:** Orphan galleries; concept strength text-locked.  

### 5.12 Confidence evolution — M7+

**Success:** Confirmation raises; staleness/contest lower; speech reflects uncertainty.  
**Failure:** Flat certainty.  

### 5.13 Importance evolution — M6/M9+

**Success:** Goal fit and stakes reshape warmth; autobiographical anchors protected by Sleep.  
**Failure:** Recency-only ranking forever.  

### 5.14 Inference — M10+

**Success:** Associative/schema inferences tagged; not auto-written into Identity.  
**Failure:** Hallucinated autobiography from analogy.  

### 5.15 Pattern formation — M8/M9+

**Success:** Abstractions emerge from repeated episodes (e.g., camping pattern).  
**Failure:** No generalizations ever; or generics without evidence.  

### 5.16 Autobiographical consistency — M1/M14+

**Success:** Story about self/user remains coherent across time; supersession is intentional.  
**Failure:** Oscillating facts; knowledge bleed into “I/you.”  

---

## 6. Scenario families (cognitive probes)

Design-time families for later harnesses and Daily Use Problem Reports. Not scripts—**intentions**.

| Family | Proves |
|--------|--------|
| Identity day-one | Privileged schema, assent, anti-knowledge-bleed |
| Preference lifecycle | Remember → recall → actually → recall → forget soft → unrelated remains |
| Context split | Work vs hobby verbosity both true |
| Goal thread | Open project biases; close project cools |
| Zeus fabric | Multimodal co-activation strengthens one concept |
| Association walk | Cue activates neighborhood, not keyword spam |
| Attention gate | Pin/novelty encodes; fluff does not |
| Sleep proposal | High-impact needs assent; low-impact may apply |
| Confidence stale | Unconfirmed claim softens in speech |
| Knowledge wall | Doc Q&A cites; does not become “you prefer” |
| Interference | Buffer displacement + selective encode |
| Autobiography arc | Multi-session coherence under supersession |

Each authorized milestone selects a **minimum set** of families; expanding coverage is how ACM hardens.

---

## 7. Phase gates (migration discipline)

For milestone Mn (n≥1), all of the following must hold before “done”:

1. **Principles check** — no intentional violation of `MEMORY_DESIGN_PRINCIPLES.md`.  
2. **Architecture alignment** — fits ACM verbs/kinds; no new peer “memory organ” without RFC.  
3. **Cognitive contracts** — success definitions for Mn’s capabilities pass probes.  
4. **Observability** — Trace/MC expose the Mn-relevant cognitive fields (metadata).  
5. **Compatibility** — Behavioral Compatibility · Conversation Trace · Mission Control green.  
6. **Daily Use provenance** — change originated from measured need or planned milestone slice—not speculation.  
7. **M0 readiness** — harness/observability can show why the probe passed (when M0 delivered).

M0 itself is “done” when the validation capability exists and is used by M1+.

---

## 8. Anti-metrics (do not declare victory)

- Entry_count growth  
- Vector recall@k alone  
- Embeddings upgraded  
- New DB adopted  
- Latency down without cognitive gains  
- “We store images now” without concept reinforcement  
- Silent cutover with no Trace cognitive fields  

---

## 9. Relationship to implementation (when authorized)

This strategy does **not** prescribe languages, frameworks, or CI scaffolding. It constrains what any future harness, Trace schema, or MC panel must *mean*.

When a migration phase is authorized under Daily Use Mode, delivery plans must map tasks → cognitive contracts here → probes → Trace/MC fields.

Until then: **design complete; implementation forbidden.**

---

## 10. Consistency with the constitution

If a proposed probe would require chain-of-thought disclosure, content-default panels, knowledge→memory bulk absorb, or technology-defined “memory,” it is invalid under this strategy.

---

*Validation strategy. Measures cognition. Does not implement it.*
