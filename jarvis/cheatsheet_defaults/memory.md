# ARIA Memory — Quick Reference

**Lookup:** Memory tab, or say **"memory cheatsheet"** / **"list cheatsheets"**.

## Source of truth

**ACM PRIMARY** (`data/acm/cognitive.db`) is the only autobiographical authority.
Legacy `memory.json` / `memory.db` files are **forensic vaults only** — not a second SoT.
Fail-closed: under PRIMARY, writes go through ACM encode / cool / revise.

---

## Mental model

| Term | Meaning |
|------|---------|
| **Memory** | What Aria knows *about you* (autobiography) |
| **Candidate** | Staged suggestion — not a belief until you **Adopt** |
| **Cool** | Soft forget — reduce accessibility, keep lineage |
| **Correct** | Revise belief with immutable lineage |
| **Knowledge / RAG / Docs** | Separate from Memory — adopt only after review |

---

## Profile (About you)

On first GUI visit, a questionnaire collects name, style, interests, etc. Stored as profile beliefs.

| Action | How |
|--------|-----|
| First-time setup | Modal on first GUI load (or skip) |
| Update answers | Memory → **Update profile** |
| Used in chat | Injected every turn + optional system-prompt bake |

**Phrases:** "What do you remember about me?" · "What's my name?"

---

## Store & recall (chat)

| You say | ARIA does |
|---------|-------------|
| "Remember that I use Neovim" | **Encodes** (user-initiated = adopt) into ACM |
| "Remember for project phoenix …" | Encodes in project namespace |
| "What do you remember?" | Cognitive recall (not a CRUD dump) |
| "Search my memory for vim" | Search / associative recall |
| "Forget about vim keybindings" | Prefer Memory UI Safe Forget (Cool / Correct / Erase) |
| "Summarize this conversation to memory" | May stage **candidates** for review |
| "Save where I left off" | Project checkpoint |

**Smart auto-memory** stages **candidates** — it does **not** silently write identity.

---

## Memory Home

Open **Memory**. Landing is Cognitive Home:

- About you · Safety & authority · Health · Sleep
- **Candidates** (Adopt / Dismiss)
- Conflicts + coach
- What changed · What Aria believes
- Browse & tools (search, export, import)

Shortcuts: `/` search · `N` new · `?` help · `Esc` close

---

## Safe forget

Forget is never a silent delete:

1. Preview related memories  
2. **Cool** (preferred soft forget)  
3. **Correct** (revise with lineage)  
4. **Erase** (strong cool — still not hard-delete of experiences)

Always confirm.

---

## Import

Export is a **snapshot**. Import requires explicit mode:

- **Merge** — add alongside  
- **Replace** — destructive; confirm twice  
- **Cancel** — abort (does **not** replace)

---

## Adopt pipeline

Journal ★ remember, Smart auto-memory, and document learning produce **candidates**.
Open Memory Home → **Adopt** to encode into ACM.

---

## Settings

| Control | Meaning |
|---------|---------|
| Auto-memory Smart | Extract → **candidates** |
| Explicit only | Only "Remember that…" encodes |
| Off | No auto extraction |
| Profile in prompt | Bake profile into system prompt |
| Per-repo namespace | Checkpoint / project isolation |
| Journal / Docs learn | Stage candidates from those surfaces |

---

## Troubleshooting

- Beliefs wrong? Use **Correct**, not silent overwrite.  
- Junk? **Cool** or Scrub test junk.  
- Embed model is under Models (sidebar) — retrieval aid, not SoT.  
- Mission Control Memory tab is operator observe-only.
