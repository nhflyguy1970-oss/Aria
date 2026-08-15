# ARIA 1.0 Engineering Constitution

**Status:** Founding engineering law  
**Date:** 2026-08-08  
**Authority:** Permanent. Supersedes convenience. Survives rewrites of products, platforms, and teams.

This document establishes the engineering principles that govern Aria.

It is **not** a design document.  
It is **not** an implementation specification.  
It is **not** a coding guide.

It defines the engineering laws that future development must follow. These principles must remain stable even as Aria, ACM, ACR, and the future Cognitive Operating System evolve. Future features, refactors, and architectural changes are evaluated against this constitution.

Capability-Driven Development (`docs/architecture/ENGINEERING_LAW.md`) and Production Integrity remain subordinate operational laws under this constitution. Where they conflict with short-term convenience, this constitution wins.

---

## Historical Context

Aria has completed Owner Residency, Credential Owner Residency, and Final Residency Defect Repair.

Engineering has certified:

> **Jeff can use Aria as his permanent daily workspace. There is no remaining known engineering reason he cannot.**

That certification is a transition, not a finish line.

Aria is no longer merely a development project. It is a production product intended for daily owner use. Future engineering decisions must protect that achievement. Growth that erodes owner trust, contaminates production, or invents parallel truths is not progress—it is regression dressed as ambition.

---

## Constitutional Principles

### 1. Owner First

The owner experience is the highest engineering authority.

Automated tests, benchmarks, and architectural diagrams are instruments. They are not the court of last resort. If tests pass and Owner Residency fails, the product is not ready. Evidence from real owner use overrides assumptions about what “should” work.

**Why this must endure:** Over years, teams accumulate confidence in suites that no longer match how the owner actually lives in the product. Without Owner First, engineering optimizes for green dashboards while the house becomes unlivable. Trust, once broken by “it passed CI,” is expensive to rebuild and easy to lose again.

### 2. Living Workspace

The Living Workspace is the canonical production environment.

Development environments, stubs, and laboratory surfaces exist to support Living Workspace—not to replace it as the definition of done. Never optimize development velocity, tooling comfort, or demo convenience at the expense of what the owner sees and uses every day.

**Why this must endure:** Dual realities drift. If “works in the lab” becomes the success criterion, production becomes a neglected twin. Ten years of that drift produces two products: the one engineers believe in, and the one the owner suffers. Only one of those is Aria.

### 3. Owner Residency

Owner Residency is the final engineering gate.

Shipping requires successful owner residency: the owner must be able to naturally live inside Aria for the workflows that matter. Certification must represent real usability, not theoretical correctness or checklist theater.

**Why this must endure:** Checklists age into ritual. Residency ages into truth. A platform that ships on theory will eventually ship broken mornings, invisible dialogs, and lockouts that no unit test imagined. Residency is how engineering stays honest after the novelty of a feature fades.

### 4. Repair → Verify → Regress → Certify

Every defect follows the same lifecycle: discover, identify root cause, repair, verify, regression-test, certify. Never skip steps. Never assume a repair is correct without evidence.

**Why this must endure:** Skipped verification is how intermittent bugs become folklore. Assumed fixes are how the same interruption returns in a new costume. Over a decade, an undisciplined repair culture produces a codebase that “was fixed” endlessly and trusted never. The lifecycle is slower than a patch—and cheaper than a lost daily driver.

### 5. Integrity

Integrity is non-negotiable.

Development artifacts must never contaminate production. Temporary data must never silently become permanent owner data. Environments must remain distinguishable. Integrity must always remain measurable, so contamination cannot hide behind narrative.

**Why this must endure:** Contamination is irreversible in the owner’s mind even when reversible on disk. Once QA rows, demo projects, or fake health entries appear in the live house, the product feels untrustworthy. Measurable integrity is the immune system of a personal operating system; without it, every test suite becomes a threat to the owner’s life data.

### 6. Single Source of Truth

Duplicate authority creates long-term architectural drift.

Every category of knowledge—identity, memory, configuration, capability status, certification state—must have one authoritative owner. Readers may cache; writers must not invent rival truths. Future ACM development must preserve this principle as memory becomes a shared cognitive kernel.

**Why this must endure:** Two sources of truth do not stay synchronized; they become two histories. Over years, teams “fix” each copy differently until no one knows which world is real. A cognitive platform that cannot answer “what is true?” cannot earn permanent residency in a human life.

### 7. Architectural Boundaries

Every subsystem has defined responsibilities. Applications, Reasoning, Runtime, Memory, and Storage must remain separated. Do not move responsibilities across boundaries simply because it is convenient today.

**Why this must endure:** Convenience coupling is the primary long-term tax on platforms. When applications own storage semantics, or runtime owns memory policy, or UI owns truth, every change becomes a cross-cutting risk. Boundaries are not bureaucracy; they are how a system remains evolvable when the original authors are gone.

### 8. Production Before Features

A stable owner experience is more valuable than rapid feature growth.

Shipping broken innovation damages long-term trust faster than withholding a feature preserves short-term excitement. The product grows because the owner’s life grows—not because the backlog grows.

**Why this must endure:** Feature races produce surface area faster than understanding. Each unfinished surface becomes a residency interruption waiting to happen. Over a decade, a trusted smaller house outperforms an ambitious ruin. Production Before Features is how Aria stays a daily workspace instead of becoming a museum of almosts.

### 9. Explainability

Every engineering decision should be understandable.

Future developers must be able to learn why something exists, why it works that way, and why alternatives were rejected. Institutional knowledge must not live only inside conversations, tickets that expire, or the memory of a single engineer.

**Why this must endure:** Undocumented intent becomes superstition. Superstition becomes fear of change. Fear of change becomes rewrites that discard working law. Explainability is how a constitution survives personnel change; without it, every new team reinvents Aria and accidentally erases the owner’s hard-won stability.

### 10. Evolution Without Chaos

Aria should continuously improve. Improvement must preserve architectural stability. Growth should occur through disciplined evolution rather than uncontrolled expansion.

**Why this must endure:** Stagnation invites replacement; chaos invites collapse. The durable path is continuous, bounded change: deepen flagships, complete natural capabilities, repair what residency finds, refuse cool ideas that do not serve the owner. Ten years from now, the stack will look different; the discipline of evolution without chaos must not.

---

## Engineering Laws

These are the permanent laws. They should still make sense in ten years. They are few on purpose.

1. **The owner’s lived experience is the supreme engineering authority.**
2. **Living Workspace is the definition of production; all other environments are subordinate.**
3. **Never certify readiness without successful Owner Residency for the claim being certified.**
4. **Never declare a defect closed without verified repair, regression evidence, and certification of the claim.**
5. **Never allow development, QA, smoke, certification, or demo artifacts to contaminate the owner’s production world.**
6. **Never create a second source of truth for the same category of knowledge.**
7. **Never move a responsibility across architectural boundaries for convenience alone.**
8. **Never ship novelty that breaks the owner’s daily trust.**
9. **Never leave engineering debt, rejected alternatives, or residency interruptions undocumented as if they never existed.**
10. **Never grow the product for the sake of growth; grow only from real owner need, repeated friction, flagship support, or natural completion.**
11. **Prefer the smallest honest repair that restores owner truth over a redesign that postpones it.**
12. **When principles conflict with schedule, the principles win; slip the date, not the law.**

---

## Release Philosophy

### When is a feature complete?

A feature is complete when the owner can discover it, use it naturally in Living Workspace, complete the real workflow it claims to serve, leave and return without surprise, and recover from cancel, error, and retry without engineering assistance. Completeness is not “merged” or “demoable.” Completeness is livable.

### When is a release ready?

A release is ready when Owner Residency for the release claim succeeds, Integrity is clean and measurable, repaired defects have been verified and regressed, and there is no remaining known engineering reason the owner cannot use the product for the life it is being asked to hold. Green tests without residency are insufficient.

### When should work stop?

Work should stop when the residency claim is earned, or when further change would expand surface area without serving a constitutional origin of capability. Stopping is an engineering virtue. Endless polishing of non-owner problems is not.

### When should engineering refuse new features?

Engineering must refuse new features when:

- Integrity is unclean or unmeasurable.
- Known residency interruptions remain open for workflows the owner already relies on.
- The proposed work does not originate from real owner friction, repeated manual work, flagship support, or natural completion.
- Delivery would require violating Single Source of Truth, architectural boundaries, or Living Workspace primacy.
- The team cannot explain the decision in durable form for future contributors.

Refusal is not obstruction. It is protection of the permanent daily workspace.

### When should architecture take priority?

Architecture takes priority when continued feature work would deepen boundary violations, duplicate authority, or make Owner Residency unverifiable. Architecture does not take priority as aesthetic preference, résumé design, or rewrite appetite. It takes priority when the constitution cannot be upheld without restoring structure—and even then, prefer the smallest change that restores law.

---

## Relationship to ACM and the Cognitive Operating System

Aria is expected to become the first application upon a future Cognitive Operating System in which ACM matures into a Cognitive Memory Kernel and ACR into a Cognitive Runtime, with additional applications sharing the same cognitive platform.

This constitution remains valid after that transition. Product surfaces will multiply; engineering law must not fragment.

### Platform-wide standards (must outlive Aria-as-app)

These principles become platform law, not Aria folklore:

- **Owner First** — every application is judged by lived owner use of the shared cognitive world.
- **Integrity** — shared memory and storage must never confuse development worlds with owner life.
- **Single Source of Truth** — the Cognitive Memory Kernel especially; rival memories are platform failure.
- **Architectural Boundaries** — Applications, Reasoning, Runtime, Memory, Storage remain distinct across apps.
- **Repair → Verify → Regress → Certify** — platform defects follow the same lifecycle as product defects.
- **Explainability** — platform decisions must be inheritable by teams who did not invent them.
- **Evolution Without Chaos** — shared kernels change more carefully than any single application UI.

### Aria-specific emphasis (still permanent for this product)

- **Living Workspace** as Aria’s canonical production house.
- **Owner Residency** as Aria’s final ship gate for daily-driver claims.
- **Production Before Features** under Capability-Driven Development for Aria’s flagships.

Applications that join the cognitive platform inherit the platform-wide standards. They may add product gates; they may not weaken Integrity, truth ownership, or boundary law.

---

## Long-Term Vision

Imagine reading this constitution ten years from now.

Models will change. Runtimes will change. Memory representations will change. The house may look unfamiliar. None of that exempts engineering from these truths:

- A personal cognitive system earns permanence only through lived owner trust.
- Production and development must never become the same place by accident.
- Truth must have one owner.
- Boundaries preserve the freedom to evolve.
- Evidence beats narrative.
- Growth without discipline becomes chaos; discipline without growth becomes a museum.
- The measure of success is not how much the system can do, but whether a human life can reliably unfold inside it.

If those statements still hold, the constitution has done its job—regardless of how advanced the technology has become.

---

## Adoption

All contributors—human and automated—inherit this constitution upon touching Aria, ACM, ACR, or successor cognitive platform work.

Operational laws (Capability-Driven Development, Production Integrity, Execution Law, and future platform statutes) may refine *how* these principles are practiced. They may not repeal them.

Amendments require explicit owner-facing justification and must strengthen, not dilute, Owner First, Integrity, and Single Source of Truth.

---

## Certification Seal

**ARIA 1.0 Engineering Constitution** is established on the foundation of Owner Residency certification:

> Jeff can use Aria as his permanent daily workspace. There is no remaining known engineering reason he cannot.

Future engineering exists to protect and deepen that fact—not to trade it for novelty.

**— End of Constitution —**
