# Aria Phase 6 — Live in the House
## Daily Driver Engineering

**Date:** 2026-08-06  
**Status:** ACTIVE — residency begins  
**Authority:** Next Generation Master Package + Phase 6 directive  
**Construction:** Major construction ended with Phase 5 (flagship native Rooms).  

Aria is no longer a project under construction.  
Aria is the environment in which future engineering happens.

---

## Mission

Stop building Aria from imagination.  
Start living in Aria.  

Every engineering decision must originate from genuine daily use — real interruptions, real friction, real discoveries. Not brainstorming. Not hypothetical improvements.

---

## The Daily Driver Law

1. Open Aria and do real work first.  
2. Only after something interrupts that work may engineering begin.  
3. Every interruption is evidence.  
4. Every repeated interruption may become engineering work.  
5. Every change must solve a real interruption.  

No speculative features. No polish because something “might” be better.

---

## Rule of Three

| Occurrences | Action |
|---|---|
| Once | Observe. Log it. |
| Twice | Watch carefully. |
| Three times | Engineering work (unless critical — fix immediately). |

Critical defects that prevent work may be fixed on first sight.

---

## Classification (House Problems)

Every issue is classified before it is fixed:

| Class | Prefer solving here when… |
|---|---|
| Workspace | Chrome, stage, shell, global transitions |
| Activity Engine | Activity start/exit, recipes, tool surfacing |
| Room | One Room’s interior, layout, empty/loading |
| Tool | Contextual capability appearance |
| Backend | API, storage, correctness |
| Performance | Memory, CPU, GPU, long sessions |
| Rendering | Paint, layout thrash, dual trees |
| Trust | Honesty, presence, familiarity, faked state |
| Atmosphere | Light, motion, silence |
| Transition | Walking between Rooms |

Solve at the **highest** useful level. Prefer whole-house improvements over one-Room novelty. Never duplicate solutions.

---

## What is frozen

Do **not** reopen unless daily use proves fundamental failure:

- Architecture / Living Workspace model  
- Runtime R1 (Electron)  
- Activity Engine as primary interaction unit  
- Engineering laws (Charter)  
- House Integrity (one stage, no legacy underpaint)  

Build on the foundation. Do not rebuild the foundation.

---

## No new features unless all are true

1. A real need appeared during daily use.  
2. It cannot already be solved inside Aria.  
3. It strengthens the Living Workspace.  
4. It does not add unnecessary complexity.  
5. It fits the engineering laws.  

Otherwise: do not build it.

---

## Interruption Log = backlog

The engineering backlog is **not** a feature request list.  
It is `docs/ARIA_INTERRUPTION_LOG.md`.

Every immersion break is recorded there. Engineering picks from patterns (Rule of Three), criticals, and whole-house wins.

Every completed fix must answer:

- What interrupted daily use?  
- Why did it matter?  
- How was it repaired?  
- How verified?  
- What evidence?  
- How does the whole house improve?  

---

## Success metrics (changed)

Not feature count, line count, commits, or visual polish.

Success is:

- How long Aria stays open  
- How often Jeff leaves Aria  
- How often interruptions occur  
- How naturally work flows  
- How quickly problems disappear  
- How much trust Aria earns through daily use  

---

## Legacy cleanup (ongoing, opportunistic)

When compatibility mode is unused and Runtime Independence fully owns launch:

- Remove legacy HTML / JS / CSS  
- Remove migration bridges and flags  
- Remove obsolete assets  

Until then: do not invest in improving legacy mode. Shrink it when safe. Prefer deleting dead code when a daily-driver fix touches the same area.

---

## Final law

When choosing among solutions, pick the one that makes Aria more trustworthy, comfortable, coherent, timeless, and easier to live with.

Never optimize for novelty.  
Always optimize for living.

The project has crossed from construction to residency.  
Live in the house. Let real life shape every future version of Aria.
