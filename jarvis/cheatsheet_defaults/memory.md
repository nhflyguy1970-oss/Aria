# ARIA Memory — Quick Reference

**Lookup:** Memory tab → filter namespace **`cheatsheet`**, or say **"memory cheatsheet"** / **"list cheatsheets"**.

User facts and settings live in **`data/memory.json`** and **`data/chat_settings.json`**. This entry is editable here; say **"reset memory cheatsheet"** to restore defaults.

---

## Profile (About you)

On first GUI visit, a short questionnaire collects name, communication style, primary use, interests, etc. Answers are stored in namespace **`profile`**.

| Action | How |
|--------|-----|
| First-time setup | Modal on first GUI load (or skip — won't nag again) |
| Update answers | **Memory** tab → **Update profile** (replaces old profile memories) |
| Edit one fact | Memory tab → filter namespace `profile` → Edit |
| Used in chat | Injected every turn + optionally baked into the system prompt |

**Example phrases**

- "What do you remember about me?"
- "Tell me something I like to do"
- "What's my name?"

These route to **`memory_about_user`** and answer from profile data (not guesses).

---

## Store & recall (chat)

| You say | ARIA does |
|---------|-------------|
| "Remember that I use Neovim" | Stores as **fact** |
| "Remember for project phoenix the codename is Alpha" | Stores in namespace **phoenix** as **project** |
| "What do you remember?" / "Recall memories" | Lists profile + recent memories |
| "Search my memory for vim" | Semantic + keyword search |
| "Forget about vim keybindings" | Deletes matching memories |
| "Summarize this conversation to memory" | LLM extracts facts from recent chat |
| "Set memory namespace work" | New memories go to **work** until changed |
| "Prune stale memories" | Drops old low-relevance **auto** entries |
| "Remember what this image says" | Vision → memory (stores OCR/summary as fact) |

**Remember parsing tips**

- `remember for project <name> …` or `in namespace <name> …` sets the namespace.
- Words like *preference* / *project* in the sentence pick the entry type.

---

## Project checkpoints (shutdown / resume)

Save where you left off so the next session can pick up context.

| You say | ARIA does |
|---------|-------------|
| "Save where I left off" | LLM summary → one checkpoint per namespace (replaces previous) |
| "Where did I leave off?" | Shows latest checkpoint |

**Auto-checkpoint on exit** (default: on)

- Closing the GUI tab or stopping the server writes a **lightweight** checkpoint (no LLM): last file, module, recent asks, active coding task.
- Debounced: won't overwrite a recent auto-exit checkpoint within ~30 minutes.
- Toggle: Memory tab → **Auto-checkpoint on exit**, or `auto_checkpoint` in settings.

Checkpoint namespace = git repo folder name when **Per-repo namespace** is on, else your manual namespace.

**Also persisted outside memory**

| What | Where |
|------|-------|
| Chat history | `data/chat_branches.json` |
| Last file / recent files | Per-branch session in same file |
| Long coding agent runs | `data/coding_tasks.json` (`resume task`, pause/resume) |

---

## Memory types

| Type | Use for |
|------|---------|
| `fact` | Durable facts (name, location, interests) |
| `preference` | Likes/dislikes, communication style |
| `project` | Codenames, project-specific context |
| `auto` | Auto-extracted or conversation-summary facts |
| `note` | Manual notes |

Tags are free-form (e.g. `checkpoint`, `profile`, `auto-extracted`). Checkpoints use tags **`checkpoint`** + **`project-state`**.

---

## Namespaces

| Namespace | Typical content |
|-----------|-----------------|
| `default` | General memories when none specified |
| `profile` | Onboarding questionnaire (don't mix with project facts) |
| `<repo-name>` | Auto-detected from git root (e.g. `jarvis`) when per-repo mode is on |
| Custom (`work`, `phoenix`, …) | Set via chat or GUI |

**Per-repo namespace** (default: on) — session namespace follows the current git project. Turn off in Memory tab if you prefer a fixed namespace.

---

## GUI — Memory tab

**Browse**

- Search, filter by type / namespace
- Add, Edit, Delete
- Export JSON backup, Import JSON (merge)
- Prune stale auto memories

**Settings** (top of Memory tab)

| Control | Setting key | Default |
|---------|-------------|---------|
| Auto-memory: Smart / Explicit only / Off | `auto_memory_mode` | `smart` |
| Auto-checkpoint on exit | `auto_checkpoint` | `true` |
| Per-repo namespace | `auto_namespace` | `true` |
| Profile in system prompt | `memory_in_system_prompt` | `true` |

**Auto-memory modes**

| Mode | Behavior |
|------|----------|
| **Smart** | Extracts when you share personal info (`I prefer…`, `I use…`); filters generic junk |
| **Explicit only** | Only when you say *remember*, *don't forget*, etc. |
| **Off** | No auto-extraction |

**Conflicts**

- Banner lists duplicate / similar / contradictory pairs.
- **Keep A** or **Keep B** drops the other entry.

**Update profile** — clears `profile` namespace and reopens the questionnaire.

---

## How ARIA uses memory in chat

1. **System prompt** (when enabled) — profile summary, latest checkpoint, top stable facts.
2. **Per-message prefix** — profile (and interests when relevant), checkpoint, top 3 semantic matches, RAG doc context.
3. **Dedicated routes** — recall, search, about-user, checkpoint/resume bypass generic chat when phrasing matches.

Semantic search needs the embed model (`nomic-embed-text` by default). Keyword fallback still works if embeddings are unavailable.

---

## Settings file (`data/chat_settings.json`)

```json
{
  "memory_namespace": "default",
  "auto_memory_mode": "smart",
  "auto_checkpoint": true,
  "auto_namespace": true,
  "memory_in_system_prompt": true,
  "profile_questionnaire": {
    "completed": true,
    "completed_at": "2026-06-08T…",
    "skipped": false
  }
}
```

Legacy `auto_memory: false` maps to mode **`off`**.

---

## HTTP API (GUI / scripts)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/memory/all` | List/search entries |
| GET | `/api/memory/stats` | Counts + settings snapshot |
| GET/POST | `/api/memory/settings` | Read/update memory settings |
| GET | `/api/memory/conflicts` | List conflict pairs |
| POST | `/api/memory/conflicts/resolve` | `{ "keep_id", "drop_id" }` |
| POST | `/api/memory/auto-checkpoint` | Exit/shutdown checkpoint |
| POST | `/api/memory` | Add entry |
| PUT | `/api/memory/{id}` | Update entry |
| DELETE | `/api/memory/{id}` | Delete entry |
| GET | `/api/memory/export` | Full JSON export |
| POST | `/api/memory/import` | Import JSON |
| POST | `/api/memory/prune` | Prune stale auto |
| GET | `/api/profile/questionnaire` | Status + questions |
| POST | `/api/profile/questionnaire` | Submit answers |
| POST | `/api/profile/questionnaire/reset` | Clear profile + re-ask |

---

## CLI

```bash
python main.py memory
# or: python memory/main.py
```

| Command | Action |
|---------|--------|
| `add fact:I use vim` | Add typed entry |
| `add Some note text` | Add as **note** |
| `list` | All entries (with index) |
| `search vim` | Search |
| `tag 0 work` | Tag entry by index |
| `delete 0` | Delete by index |
| `clear` / `clear auto` | Clear all or by type |
| `prune` | Drop stale auto memories |
| `export` | Print JSON to stdout |

---

## Backup & restore

- **Memory tab → Export** — full `memory.json` structure.
- **Import** — merge into existing store (or replace if you edit the import flow to `merge: false` via API).
- Copy **`data/memory.json`** and **`data/chat_settings.json`** for a full memory + settings backup.

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| "No matching memories" on search | Entry may be in another namespace; search falls back globally after repo filter |
| Personal questions get generic chat | Say explicitly "tell me something I like to do" or complete profile; check `profile` namespace |
| Semantic search weak / warnings | `ollama pull nomic-embed-text`; verify embed model in sidebar |
| Stale auto junk | **Prune stale** or set auto-memory to **Explicit only** |
| Duplicate facts | Memory tab conflict banner → Keep A/B |
| Checkpoint not on exit | Enable auto-checkpoint; need enough session context (file, module, or recent messages) |

---

## Cheatsheets (in memory)

All module quick-reference guides live in memory namespace **`cheatsheet`**. Each has tags **`cheatsheet`**, **`protected`**, and **`key:<name>`**.

| You say | ARIA does |
|---------|-------------|
| "List cheatsheets" | Lists available guides |
| "Memory cheatsheet" / "cheatsheet for coding" | Shows that guide |
| "Reset memory cheatsheet" | Restores factory default for that key |

Edit any cheatsheet in the **Memory** tab (Cheatsheets panel or filter namespace `cheatsheet`). Changes persist in `memory.json`; reset brings back bundled defaults.

---
