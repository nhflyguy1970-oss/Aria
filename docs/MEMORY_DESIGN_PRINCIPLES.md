# Memory Design Principles

**Status:** Constitutional — canonical cognitive truths for Aria Memory  
**Mode:** Design only — no APIs, databases, frameworks, or code  
**Companions:**

| Document | Role |
|----------|------|
| **This file** | **Constitution** — immutable cognitive *why* |
| [`ARIA_COGNITIVE_MEMORY.md`](ARIA_COGNITIVE_MEMORY.md) | **Architecture** — *how* cognition is structured |
| [`COGNITIVE_MEMORY_TEST_STRATEGY.md`](COGNITIVE_MEMORY_TEST_STRATEGY.md) | **Validation** — *how progress is measured* |

**Governing question:** When someone proposes a Memory change, does it move Aria closer to human cognition?

The architecture may evolve. Technologies will. Implementations will. These principles must remain valid.

---

## How to use this constitution

For every proposed Memory change, map it against these principles. If it violates one, it is **probably moving away from the ACM vision** unless a formal RFC amends the constitution.

Prefer Cognitive vocabulary (encode, remember, reconsolidate, sleep, concept, experience, goal) over storage vocabulary (row, index, query, CRUD).

---

## P1 — Memory is a cognitive process, not storage

**Principle:** Memory is what Aria *does* with experience—encoding, remembering, reconsolidating, consolidating—not where bytes sit.

**Why it exists:** Confusing persistence with cognition produces searchable junk drawers that never become intelligence.

**Implications:** Success metrics are cognitive behavior, not entry counts or index hit rates.

**Examples:** Preferring a reconsolidated preference after “Actually…”; answering “Who am I?” from identity shaped by experience.

**Counterexamples:** Shipping a new collection/table and calling it “memory”; declaring victory because similarity search is faster.

**Design consequences:** Features that only add durable writing without changing remembering fail this principle.

**Future implications:** Storage engines may be replaced freely; cognition cannot be redefined by the replacement.

**Design test:** If removing the “database” would erase the product’s idea of memory, storage was mistaken for cognition.

---

## P2 — Remembering changes memory

**Principle:** Substantive recall is a write (reconsolidation). Reading without cognitive consequence is not remembering.

**Why it exists:** Human memory updates when remembered; Aria must not treat recall as a read-only fetch.

**Implications:** Access can strengthen, correct, contest, or refresh confidence and associations.

**Examples:** Recalling coffee preference while correcting it supersedes the old belief with lineage.

**Counterexamples:** Caching prompt snippets with no lasting effect; “search results” that leave cognition unchanged.

**Design consequences:** Every Remember path must define whether—and how—reconsolidation applies.

**Future implications:** Auditing “what Aria used to believe” remains possible via lineage, not silence.

**Design test:** If a high-stakes recall never alters strength, confidence, or links, the system is searching, not remembering.

---

## P3 — Experiences precede concepts

**Principle:** Lived episodes are primary; concepts crystallize from them (and from explicit teaching), not the reverse as default.

**Why it exists:** Starting from abstract labels without experience yields empty schemas and hallucinated structure.

**Implications:** Encode into experience first when sensing the world; concept growth follows evidence.

**Examples:** First camping trip creates an experience; repeated trips grow the camping concept.

**Counterexamples:** Inventing rich concepts from documentation scrape with no lived binding.

**Design consequences:** Bulk ontology import without experience is knowledge pollution, not memory.

**Future implications:** Autobiography remains grounded in what happened.

**Design test:** If concepts exist that no experience or trusted user adoption can justify, the system inverted the order.

---

## P4 — Concepts emerge from repeated experience

**Principle:** Stable concepts form through repetition, confirmation, and multimodal co-evidence—not single brittle writes alone.

**Why it exists:** One-off noise must not become lifelong “truth.”

**Implications:** Provisional concepts may exist; canonicity requires reinforcement.

**Examples:** “Zeus” solidifies across photos, walks, mentions, camping.

**Counterexamples:** One chat typo becomes a permanent person; one web snippet becomes identity.

**Design consequences:** Importance and confidence must reflect reinforcement, not creation timestamp.

**Future implications:** Sleep can propose abstractions only from patterns in experience.

**Design test:** If one unattended utterance permanently defines a major concept, emergence failed.

---

## P5 — Associations are first-class

**Principle:** Links between concepts, experiences, goals, and modalities are cognitive objects—not optional metadata.

**Why it exists:** Human remembering is associative; isolated records cannot produce Zeus→camping→trails cognition.

**Implications:** Growth of meaningful edges is progress; edge-less “facts” are incomplete memory.

**Examples:** Zeus `depicts` photo envelopes; Jeff `owns` Zeus; camping `co-activates` fly fishing.

**Counterexamples:** Tag strings used as a substitute for relation; dump of unrelated bullets as “related.”

**Design consequences:** Designs that optimize only item similarity and ignore typed association regress.

**Future implications:** Agent collaboration shares association fabrics carefully, not bag-of-facts APIs.

**Design test:** If removing association structure leaves behavior unchanged, associations were never first-class.

---

## P6 — Knowledge is not memory until adopted

**Principle:** Objective corpora (docs, web, books) are knowledge. They become memory only through experienced use, practice, or explicit adoption into autobiography/goal/identity.

**Why it exists:** Encyclopedia ingestion destroys autobiographical trust.

**Implications:** Reference organs may cite; ACM must not silently absorb.

**Examples:** “Remember that *we* use this ROCm quirk” adopts into memory; reading a CUDA manual alone does not.

**Counterexamples:** Nightly doc indexing written into “user memory”; wiki priors overwriting preferences.

**Design consequences:** Clear wall between Knowledge Corpuses and ACM; adoption is a cognitive act.

**Future implications:** Learning from the world remains possible without identity contamination.

**Design test:** If a generic doc chunk answers “Who am I?” or “What do I prefer?”, the wall failed.

---

## P7 — Goals influence remembering

**Principle:** Open goals bias attention, encoding, and retrieval; completed goals become history and stop steering by default.

**Why it exists:** Humans remember the future; unfinished work pulls salience.

**Implications:** Goal Space is peer cognition, not a sticky note on planning.

**Examples:** “What were we working on?” surfaces the active project thread.

**Counterexamples:** Priority sorting by recency alone while ignoring open commitments.

**Design consequences:** Planning consumes goals; it does not silently own Goal Space truth.

**Future implications:** Multi-goal interference and decay of stale bias must stay designed.

**Design test:** If open goals never change what is remembered, Goal Space is decoration.

---

## P8 — Attention determines encoding

**Principle:** Not everything perceived is encoded equally; attention (novelty, stakes, goals, surprise, user pin, sensory salience) gates durability.

**Why it exists:** Uniform logging recreates junk drawers.

**Implications:** Low-attention fluff should rarely become long-term cognition.

**Examples:** Explicit “Remember that…” and first meeting with Zeus encode deeply; weather chat may not.

**Counterexamples:** Persisting every tool telemetry line as autobiography.

**Design consequences:** Attention is a designed field, not a sentiment label glued on later.

**Future implications:** Embodied sensor floods require attention or ACM drowns.

**Design test:** If encode probability is roughly uniform across stimuli, attention is absent.

---

## P9 — Context determines meaning

**Principle:** The same attribute may be true in one context and false in another without contradiction.

**Why it exists:** Human norms are situated; context-free preferences lie.

**Implications:** Recall defaults to the current context frame; dig may retrieve others.

**Examples:** Brief at work chat; detailed in design docs; camping practices ≠ office practices.

**Counterexamples:** A single global “verbosity” flag fighting itself across domains.

**Design consequences:** Context-conditioned attributes and context stamps on experiences.

**Future implications:** Location, activity, device, mood, and goal context remain first-class modulators.

**Design test:** If mutually exclusive prefs cannot coexist under different contexts, meaning is flattened.

---

## P10 — Identity emerges through experience

**Principle:** Who the user is—and who Aria is—emerges from lived interaction and protected schemas, not from a form alone.

**Why it exists:** Identity is autobiographical, not a profile blob.

**Implications:** Identity Schemas are privileged and evolve under strict policy.

**Examples:** “My dog is Zeus,” growing into a multimodal identity neighborhood; Aria’s boundaries learned from corrections.

**Counterexamples:** Overwriting user identity from generic personas or scraped bios.

**Design consequences:** High-impact identity changes require assent; lineage remains.

**Future implications:** Theory of mind for others uses ordinary concepts—not a second identity organ.

**Design test:** If identity can be replaced wholesale without experience or user assent, emergence failed.

---

## P11 — Working memory is temporary

**Principle:** The Working Buffer is capacity-limited focus—not long-term storage with a short TTL name.

**Why it exists:** Without interference and limited capacity, everything stays “current” and nothing is.

**Implications:** Displacement is normal; rehearsal + importance promote Encoding.

**Examples:** Active goal and open image in buffer; prior digression drops unless encoded.

**Counterexamples:** Infinite session transcript treated as working memory.

**Design consequences:** Designed interference and promotion thresholds.

**Future implications:** Multi-modal perceptual set stays small and current.

**Design test:** If the buffer never drops anything, it is a log wearing a costume.

---

## P12 — Long-term memory continuously evolves

**Principle:** Long-term cognition reorganizes: merges, splits, abstractions, obsolescence, archival—not a write-once museum.

**Why it exists:** Lifelong learning without evolution becomes brittle debris.

**Implications:** Sleep and reconsolidation are the engines of evolution.

**Examples:** Project rename with alias; tech marked legacy; camping pattern abstracted from trips.

**Counterexamples:** Append-only facts never reorganized; duplicates forever active.

**Design consequences:** Evolution under policy; high-impact changes may require assent.

**Future implications:** Decade scale remains coherent only if evolution is continuous.

**Design test:** If five years of use produces only more rows, evolution failed.

---

## P13 — Confidence changes over time

**Principle:** Beliefs carry confidence that rises with evidence/confirmation and falls with contradiction or staleness.

**Why it exists:** Flat certainty feels inhuman and unsafe.

**Implications:** Speech (“I think…”) precedes deletion when confidence drops.

**Examples:** Preference confirmed yearly stays strong; old unconfirmed claim softens.

**Counterexamples:** Every fact spoken as absolute forever; silent averaging of contradictions.

**Design consequences:** Contested states; confirmation timestamps.

**Future implications:** Meta-memory later reports what is known vs uncertain.

**Design test:** If confidence never moves after correction or long silence, the model is fake.

---

## P14 — Importance changes over time

**Principle:** Importance is a multi-factor, evolving salience—not a static priority bit.

**Why it exists:** Not all memories deserve equal warmth forever.

**Implications:** Frequency, stakes, confirmation, goal fit, history, and usefulness reshape warmth.

**Examples:** Active project spikes importance; pinned identity resists decay; finished goals cool.

**Counterexamples:** Recency-only ranking; once-important trivia forever top-ranked.

**Design consequences:** Warm set vs cold archive as cognitive tiers, not disk tiers alone.

**Future implications:** Sleep protects autobiographical anchors even if rarely retrieved.

**Design test:** If importance never cools after goal completion, salience is broken.

---

## P15 — Memories strengthen

**Principle:** Congruent repetition, practice success, multimodal co-activation, and confirmation increase strength.

**Why it exists:** Learning must thicken what matters.

**Examples:** Successful ROCm repair strengthens the procedure; more Zeus photos thicken the concept.

**Counterexamples:** Strength independent of use; reinforcement ignored.

**Design consequences:** Strength signals feed retrieval bias and Sleep rehearsal.

**Future implications:** Skills become reliable through practice loops.

**Design test:** If repeated success never changes retrieval preference, strengthening is absent.

---

## P16 — Memories weaken

**Principle:** Neglect, low attention, superseded beliefs, and obsolescence reduce activation and warmth.

**Why it exists:** Without weakening, cognition cannot focus.

**Examples:** Abandoned draft project fades; superseded coffee preference never answers by default.

**Counterexamples:** Equal forever weights; “deleted” only by truncating the database.

**Design consequences:** Decay curves; supersession over silent equal twins.

**Future implications:** Weakening enables lifelong scale without cognitive noise.

**Design test:** If unused items remain as vivid as daily identity, weakening failed.

---

## P17 — Most forgetting is deactivation, not deletion

**Principle:** Default “forget” means remove from default remembering pathways; hard erase is rare, intentional, and audited.

**Why it exists:** Humans rarely obliterate; they stop retrieving. Privacy still requires a true erase path.

**Implications:** Dig/history may remain unless the user demands erase.

**Examples:** “Forget my coffee preference” deactivates that active belief; legal erase purges envelopes.

**Counterexamples:** Default DELETE CASCADE as the only forget; undeletable telemetry labeled memory.

**Design consequences:** Deactivate / archive / supersede first; erase as privilege.

**Future implications:** Trust rises when users control autobiographical visibility.

**Design test:** If forget always means physical destruction of history, the principle failed (unless user asked erase).

---

## P18 — Sleep is part of cognition

**Principle:** Idle reorganization (Sleep) is a cognitive state: refine, discover relations, resolve duplicates, propose abstractions, clean weak structure.

**Why it exists:** Online interaction cannot reorganize a lifelong mind alone.

**Implications:** Sleep is not “cron cleanup”; it is mental work with guardrails.

**Examples:** Alias candidates; edge prune; open-goal narrative clustering.

**Counterexamples:** Only defragmenting disk; rewriting identity with no assent.

**Design consequences:** Tiered assent for high-impact Sleep outcomes.

**Future implications:** Long-term clarity is a Sleep product.

**Design test:** If “Sleep” never changes conceptual structure, it was packaging for GC.

---

## P19 — Reconsolidation is mandatory

**Principle:** No Remember path may permanently opt out of reconsolidation design. Significance may vary; the mechanism must exist.

**Why it exists:** Optional reconsolidation becomes forgotten reconsolidation.

**Implications:** Even “light” recalls define null vs non-null reconsolidation rules.

**Examples:** Fact question lightly refreshes `t_last`; correction heavily versions.

**Counterexamples:** Parallel “search API” forever exempt from cognitive write rules.

**Design consequences:** Search-shaped UIs still terminate in Remember contracts when answering from memory.

**Future implications:** Ambiguous systems must classify memory vs knowledge retrieval before reconsolidating.

**Design test:** If a path answers from ACM and forbids all writeback by design, it violates this principle.

---

## P20 — Learning changes memory; memory changes learning

**Principle:** Learning proposes updates that encode under policy; memory biases what learning targets next.

**Why it exists:** One-way append learning never becomes wisdom; memory-blind learning thrashes.

**Implications:** Ownership stays clear—Learning proposes; ACM encodes.

**Examples:** Repeated coding failures → procedural concept → future learning focuses there.

**Counterexamples:** Learning writes raw rows past Policy Gate; memory never informs curricula.

**Design consequences:** Bidirectional loop without Control Plane owning truth.

**Future implications:** Continual adaptation without catastrophic overwrite.

**Design test:** If Learning never alters concepts/procedures—or always bypasses ACM—the loop is broken.

---

## P21 — Multimodal experiences reinforce concepts

**Principle:** Modalities mutually strengthen concepts through co-activation; files are not vanity attachments.

**Why it exists:** “Zeus” is photos, walks, voice, trips—not a text field with a thumbnail.

**Implications:** Congruent multimodal evidence accelerates importance and association weight.

**Examples:** New GPS walk + photo + journal note jointly thicken Zeus and camping.

**Counterexamples:** Separate image index never linked back to the concept neighborhood.

**Design consequences:** Answer frames may be native modality while still concept-led.

**Future implications:** Embodied streams join the same reinforcement physics.

**Design test:** If multimodal inputs never change concept strength relative to text-only, reinforcement failed.

---

## P22 — Memory explains itself without chain-of-thought

**Principle:** Aria may give template memory-reasons (source, strength, uncertainty, context, goal bias)—never internal deliberation, prompts, or latent traces.

**Why it exists:** Trust requires intelligibility without exposing private reasoning machinery.

**Implications:** Conversation Trace may hold diagnostics; user speech stays in template classes.

**Examples:** “Long-term preference”; “not confirmed recently”; “because you’re still working on X.”

**Counterexamples:** Dumping activation graphs or “because the model thought…” to the user.

**Design consequences:** Explanation classes are part of the Remember contract.

**Future implications:** Meta-memory can later elaborate templates without opening the box.

**Design test:** If a user-facing answer reveals chain-of-thought or system internals, privacy failed.

---

## P23 — The user remains in control of autobiographical memory

**Principle:** Users may pin, correct, forget/deactivate, veto high-impact Sleep, export, and hard-erase. Autobiography is not Aria’s secret property.

**Why it exists:** Cognitive agents without agency over personal memory become untrustworthy.

**Implications:** Identity and erase paths are privileged under Policy Gate.

**Examples:** User vetoes a Sleep merge of two people; user erases a sensitive episode.

**Counterexamples:** Silent identity rewrite; no path to remove a wrong “fact” from default recall.

**Design consequences:** Controls are cognitive rights, not UI afterthoughts.

**Future implications:** Multi-user/agent scopes inherit the same rights model.

**Design test:** If the user cannot reverse a wrongful autobiographical claim’s default status, control failed.

---

## P24 — Technology must never define cognition

**Principle:** Engines, indexes, models, and languages are substrates. They serve ACM; they do not rename its verbs or kinds.

**Why it exists:** Vendor gravity pulls products into “vector memory” and away from minds.

**Implications:** RFCs about technology alone cannot revise constitutional principles.

**Examples:** Replacing a graph engine while preserving association physics is fine.

**Counterexamples:** “We use Qdrant, therefore memory is nearest-neighbor search.”

**Design consequences:** Normative docs exclude vendor requirements.

**Future implications:** Decade of substrate churn without cognitive reboot.

**Design test:** If a design doc’s core verbs are product names, technology is defining cognition.

---

## P25 — The cognitive model survives technology changes

**Principle:** Experiences, Concepts, Associations, Goals, Attention, Context, Reconsolidation, and Sleep must remain meaningful under any compliant substrate.

**Why it exists:** Longevity of Aria’s mind requires model survival.

**Implications:** Migration changes projections, not the constitution.

**Examples:** Same Zeus neighborhood after storage rewrite.

**Counterexamples:** New stack that can only dump chunks and calls it ACM-compliant.

**Design consequences:** Compliance = cognitive contracts, not schema parity.

**Future implications:** Agents, embodiment, and collaboration extend the model without discarding it.

**Design test:** If a rewrite cannot express reconsolidation or goal-biased remembering, it did not survive.

---

## Architectural questions (required before any Memory implementation)

Every future Memory change must answer **yes with evidence** or revise the proposal:

1. Does this create **concepts** (or strengthen them)—or merely records?  
2. Does this strengthen **associations**, or only store more items?  
3. Does this improve **remembering**—or only searching?  
4. Does encoding respect **attention**, or log uniformly?  
5. Does meaning preserve **context**, or flatten it?  
6. Do **goals** influence remembering when open?  
7. Is **reconsolidation** defined for every answer-from-memory path?  
8. Does **Sleep** (when claimed) reorganize cognition—or only garbage-collect storage?  
9. Does this separate **knowledge** from **memory** until adoption?  
10. Does this strengthen **identity** only under user-trustable policy?  
11. Does multimodal input **reinforce concepts**, or orphan media?  
12. Does confidence/importance **move over time** in the design?  
13. Is forgetting primarily **deactivation**, with erase as assent?  
14. Can the user **control** autobiographical default recall?  
15. Are explanations limited to **template classes** (no CoT)?  
16. Does Learning↔Memory remain a **propose/encode** loop under policy?  
17. Does this improve **lifelong** clarity—not just short-term hit rate?  
18. Would this still make sense if every current database/vendor vanished?  
19. Does this move Aria **closer to human-like memory** under the principles above?  
20. Is this change justified by **Daily Use Mode** measurement—not speculation?

If answers are weak, do not implement.

---

*Constitution. Architecture may evolve; these truths should not without a new constitutional RFC.*
