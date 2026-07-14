# Aria Cognitive Memory

**Status:** **Canonical Cognitive Memory architecture — DESIGN FREEZE (v2.1)**  
**Mode:** Architecture only — no implementation, migration, or prototype authorized by this document  
**Foundation:** Experiences · Concepts · Associations · Goal Space · Remembering · Reconsolidation · Sleep  

**Governance:** Future work proceeds only under **Daily Use Mode** (Problem Reports → measure → minimal change → regressions → Trace/MC). This document is the **north star**, not a build queue.

---

## Final Architectural Review (RFC)

**Review posture:** Final RFC before canonical freeze. Assumptions challenged again.

### Recommendation

**2 — Approve with the final design edits embodied in this v2.1 freeze text.**

Not “unchanged”: v2 was cognitively strong but left several freeze blockers (tech/normative split, procedure ontology, closed-loop feedback, testability, Daily Use binding, trust/policy gate, agent/embodiment extensibility). Those are resolved below. Not “reject”: remaining risks are manageable and do not invalidate the mental model.

### Summary findings

| Lens | Finding |
|------|---------|
| Consistency | Sound after clarifying Procedure⊂Concept, Goal≠Concept, Learning≠store |
| Contradictions | Tech “preferences” had drifted into appearing normative → separated |
| Missing caps | Trust/Policy Gate, act→encode, Working Buffer interference, testability, Daily Use, multi-agent scope |
| Circular deps | Resolved: Control Plane *proposes*; ACM *encodes under policy*; Planning *consumes* Goals |
| Dead ends | High-impact Sleep needs assent; low-impact Sleep may proceed—stated |
| Complexity | Minimum complete set listed; affinity/vectors demoted to optional substrate |
| Scalability / extensibility | Lifelong log + warm set + Sleep GC; agents/embodiment via envelopes + scoped spaces |
| Migration | Feasible as behavior projections; not a big-bang store rewrite |
| Observability / testability | Explicit contracts added |
| Human-like behavior | Associative, contextual, confidence-bearing, reconsolidating, goal-supporting—confirmed |
| Daily Use | Bound as sole implementation process |

### Core loop — complete?

Yes, with explicit feedback and act-outcome (v2.1):

```
      ┌──────────────────────────────────────────────┐
      │         priors (Concept / Goal / Identity)    │
      └──────────────────────┬───────────────────────┘
                             ▼
 Attention × Context × Goals × Prediction-error
                             ▼
                    Encode ◀── Act / Perceive / Dialogue
                             ▼
         Experience Log ↔ Concept Space ↔ Multimodal fabric
                             ▼
                      Remember ──▶ Answer frame
                             │
                             ├──▶ Reconsolidate (awake write)
                             ▼
                    Sleep / Consolidate
                             ▼
              Updated Concept / Goal / Importance / edges
                             │
                             └──▶ Future Attention & Remembering
```

**Nothing foundational missing** from the loop once priors and act→encode are named. Affection/stakes remain Attention inputs, not a separate store.

### Minimum complete foundation

| Component | Foundational? | Note |
|-----------|---------------|------|
| Experiences | Yes | Episodic truth |
| Concepts (+ Associations) | Yes | Semantic fabric |
| Goal Space | Yes | Future-directed memory |
| Working Buffer | Yes | Capacity-limited focus |
| Identity Schemas | Yes | Privileged concepts |
| Remembering Engine | Yes | Activation physics |
| Reconsolidation | Yes | Retrieval-as-write |
| Sleep / Consolidation | Yes | Lifelong organization |
| Attention · Context · Importance · Confidence · Time | Yes | Cross-cutting modulators |
| **Trust / Policy Gate** | Yes (thin) | Who may change Identity/Goals; assent rules |
| Procedure / Skill | **Role of Concept** | Not a parallel ontology |
| Diagnostic residue | Lane, not peer | Must not dominate |
| Affinity / embeddings / DBs | **No** | Informative substrates only |
| Knowledge corpora | **Outside** | Citation + adoption bridge |

### Future capabilities — supported?

| Capability | Support path |
|------------|--------------|
| Reasoning | Activations + associations + contested attributes as premises |
| Learning | Propose→Encode under policy; repeated practice → procedures |
| Planning | Consumes Goal Space + skills; does not own memory |
| Prediction | Goal + pattern activation (M12) |
| Reflection | Replay episodes vs Identity/Goals (M11) |
| Creativity | Hypothetical sandbox activations |
| Autobiography | Narrative assembly over Experiences + Identity (M14) |
| Theory of mind | Other-person **Concepts** with perspective attributes—no new organ |
| Long-term adaptation | Sleep + reconsolidation + importance dynamics |
| Agent collaboration | **Scoped** Concept/Goal spaces + sharing policy |
| Multimodal understanding | Envelope reinforcement (already core) |
| Embodied systems | Sensorimotor streams as Envelopes + Context Frame |

### Technology independence

**Normative:** cognitive kinds, verbs, loop, policy, observability contracts.  
**Informative only:** any graph engine, vector DB, object store, embedding model, LLM, language, framework.

The architecture must remain valid if all recommended substrates are replaced.

### Human-memory behavioral checklist

Associative · changes on recall · contextual · confidence · history/lineage · strengthens · weakens · consolidates (Sleep) · supports goals · supports learning · supports identity · multimodal — **all required and present**.

---

## 0. What ACM is

**Is:** Decade-scale cognitive memory: encode, remember, reconsolidate, sleep—under Attention, Context, Goals, and Policy.

**Is not:** A Memory Manager, database, search engine, vector store, CRUD API, or RAG wrapper.

| Question | Cognitive resolve |
|----------|-------------------|
| Who am I? | Identity Schema (user) + autobiographical highlights |
| What do you know about Zeus? | Concept activation → multimodal neighborhood |
| What happened yesterday? | Episodes under temporal + context gates |
| What project were we working on? | Goal Space (active) ∩ recent episodes |
| Show me the last picture of Zeus | Concept → `depicts` → envelope, “last” |
| How do I tie a Woolly Bugger? | Skill-role concept / procedure |
| What did I learn about ROCm? | Experiences + *adopted* knowledge → attributes |

---

## 1. Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│ Cognitive Control Plane (proposes; does not silently own truth)      │
│ Conversation · Planning · Learning · Reflection · MC / Trace         │
└───────────┬─────────────────────────────┬────────────────────────────┘
            │ propose / cue                 │ inspect / user control
            ▼                               │
┌───────────────────────────────────────────┴──────────────────────────┐
│ Trust / Policy Gate (Identity, Goals, high-impact Sleep, erase)      │
├──────────────────────────────────────────────────────────────────────┤
│ Aria Cognitive Memory                                                │
│ Attention Field · Context Frame · Goal Space                         │
│        └──────────▶ Working Buffer ◀────▶ Remembering Engine         │
│                           │                      │                   │
│                           │               Reconsolidation            │
│                           ▼                      │                   │
│              Concept Space (Identity + skill roles)                  │
│              + Association Fabrics                                   │
│                     │                                                │
│      Experience Log · (optional affinity cues) · Object Store        │
│                     │                                                │
│              Sleep ──▶ Consolidation Engine                          │
└──────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ citations; adoption only
                     Knowledge Corpuses (outside ACM)
```

### Ownership (anti-circular)

| Actor | May |
|-------|-----|
| Learning Governor | Propose concepts/procedures/goal updates |
| Planning | Read Goals/skills; create/modify Goals only via Policy Gate |
| Conversation | Cue Remember; request Encode (“remember…”) |
| ACM | Encode, Activate, Reconsolidate, Sleep under policy |
| User | Ultimate assent for Identity / hard erase / veto high-impact Sleep |

### Cognitive verbs

1. **Encode** — priors + Attention × Context × Goals × prediction-error; from dialogue **or** act/perceive outcomes.  
2. **Remember** — spreading activation → answer frame (+ optional explanation class).  
3. **Reconsolidate** — awake write on substantive access/correction.  
4. **Sleep / Consolidate** — offline reorganization within policy.

---

## 2. Ontology

### Experience
Lived, time-bounded event. Versioned under reconsolidation; not silently overwritten.

### Concept
Living schema. **Includes** skill/procedure *roles*, preferences-as-attributes, places, people, topics. Associations are first-class edges among concepts (and to goals/experiences/envelopes).

### Goal Space
Peer system for future-directed objects (projects, promises, plans, unfinished work, desired outcomes, future events). Active goals bind into Working Buffer; resolution → Experience + concept residue; archive, don’t delete.

### Identity Schema
Privileged concepts: User, Aria-self, Project identities, optional App personas. Strict Policy Gate.

### Diagnostic residue
Trace/telemetry lane. Never autobiography.

### Not foundational
Embeddings, particular DBs, LLM weights—as cognition.

---

## 3. Goals (memory of the future)

`Intend → Active → Progress episodes → Complete|Abandon|Supersede → Experience → Archive`

Open goals bias Attention, Encode, Remember, Sleep. Closed goals do not, unless cued.

---

## 4. Attention · Context · Importance · Confidence · Time

**Attention** captures novelty, stakes, frequency, goals, prediction error, user pin, sensory salience—and gates encode/remember/reconsolidate/sleep/forget.

**Context** stamps and *conditions* attributes (`prefer(brevity)|work`). Conflicting contextual truths coexist. Current Context Frame biases default recall.

**Importance** is a multi-factor evolving vector (frequency, novelty, affect, confirmation, goal fit, usefulness, historical significance).

**Confidence** moves with evidence, confirmation, contestation, staleness, practice success—speech before deletion.

**Time** is a retrieval dimension (`t_first/last/confirmed`, valid intervals, narrative order).

---

## 5. Reconsolidation & Sleep

**Axiom:** Substantive remembering is a write.

Awake reconsolidation: correction, contradiction, evidence, repetition, reflection, goal binding—with lineage.

Sleep: formal state; exclusive heavy rewrite rights; prefers high-attention and open-goal rehearsal.

| Change class | Sleep rule |
|--------------|------------|
| Weak edge prune, importance refresh, alias *candidates* | May proceed (logged) |
| Identity / core preference / goal-semantics flips | Proposal + assent (Policy Gate) |
| Hard erase | User-only, audited |

---

## 6. Multimodal · Knowledge · Explanation

Envelopes reinforce concepts via typed co-activation (Zeus fabric), not file pins.

**Knowledge ≠ Memory.** Corpuses stay outside; adoption is explicit Encode into ACM.

Explanations use **template classes** only (source, strength, uncertainty, association, goal bias, context). No chain-of-thought to users. Trace holds diagnostics.

---

## 7. Working Buffer

Capacity-limited; holds dialogue bindings, active goals, Context Frame, hypotheses, perceptual set.

**Interference is designed:** new high-Attention items displace low-Importance buffer content; displaced items may Encode if above threshold or else drop.

---

## 8. Remembering pipeline

1. Policy-visible Context + Goals + Attention seeds (+ concept priors)  
2. Cues from utterance, buffer, attachments, recent acts  
3. Seed concepts/goals  
4. Spread with context, goal bias, importance, confidence  
5. Temporal/modality gates  
6. Answer frame  
7. Optional explanation class  
8. Reconsolidate if significant  
9. Trace without default contents  

---

## 9. Forgetting

Decay · archive · supersede · deactivate · relearn · (rare) hard erase. Attention-starved decays faster; pinned Identity/Goals resist.

---

## 10. Inference & imagination

Associative / schema / analogical inference allowed if tagged. Hypotheticals sandboxed. Never auto-write Identity without Policy Gate. Sleep proposes; awake/policy grounds.

---

## 11. Observability

Trace/MC: goals & bias, context, attention class, reconsolidation versions, Sleep health, pending assents, explanation class, latencies. No contents by default. User: pin, correct, forget, veto, erase, export.

---

## 12. Testability (architectural contracts)

ACM is testable **without** choosing a graph/vector vendor:

| Contract | Example behavioral probe |
|----------|---------------------------|
| Encode under Attention | Low-salience chatter does not outrank pinned identity prefs |
| Context truth | Work brevity vs docs detail both recallable in-context |
| Goal bias | Active goal surfaces unfinished thread over cold trivia |
| Reconsolidation | “Actually…” supersedes; lineage retained for dig |
| Forget precision | Forget coffee ≠ forget color |
| Sleep assent | Identity flip does not silent-apply |
| Knowledge wall | Doc ingest does not become autobiography |
| Explanation class | User text matches allowed templates only |
| Trace | Diagnostics present; secrets/contents absent in default panel |

Implementation phases must ship these as regressions under Daily Use Mode.

---

## 13. Daily Use Mode (binding)

This freeze **forbids** speculative ACM implementation outside Daily Use Mode:

1. Problem Report / measured bottleneck  
2. Measure (Trace, probes, soak)  
3. Minimal change toward the nearest cognitive milestone  
4. Behavioral Compatibility · Conversation Trace · Mission Control green  
5. No architecture thrash: substrates may swap; **normative model may not** without a new RFC  

Migration/phased delivery is planned explicitly later; **this document does not authorize coding.**

---

## 14. Migration feasibility (informative)

Behavior projections: dual-write Experiences/Concepts → harvest → Remembering primary → retire CRUD mental model. Compatibility gates at each step. Substrate choice deferred to phase planning.

---

## 15. Informative substrates (non-normative)

Local-first objects + append log + *some* association index + optional affinity cues are *examples*. Any decade replacement that preserves the cognitive contracts is compliant.

---

## 16. Risks

| Risk | Mitigation |
|------|------------|
| Goal tunnel vision | Bias decays with goal age; digression cues |
| Reconsolidation churn | Lineage; Identity assent |
| Creepy links | Typed edges; unpin; confidence |
| Sleep overreach | Tiered assent table |
| Control Plane writes truth | Ownership table + Policy Gate |
| Complexity creep | Minimum foundation list; refuse new peer “stores” |

---

## 17. Cognitive roadmap (milestones)

| Phase | Milestone |
|-------|-----------|
| **M0** | Design freeze (this document) |
| **M1** | Identity Memory |
| **M2** | Working Memory (Buffer + Context + Attention) |
| **M3** | Concept Formation |
| **M4** | Associative Remembering |
| **M5** | Multimodal Memory |
| **M6** | Goal Memory |
| **M7** | Reconsolidation |
| **M8** | Concept Evolution |
| **M9** | Sleep |
| **M10** | Inference |
| **M11** | Reflection |
| **M12** | Prediction |
| **M13** | Planning (consumes ACM) |
| **M14** | Autobiographical Memory |
| **M15** | Meta-memory |

Planning is late by design.

---

## 18. Freeze decision

**Approved as Aria’s canonical Cognitive Memory architecture (v2.1), with the final edits in this document.**

- North star for all future Memory work.  
- **No implementation** until a migration/delivery phase is explicitly planned under Daily Use Mode.  
- Recommend **committing** this file as the architectural baseline.

---

*RFC freeze. No implementation implied.*
