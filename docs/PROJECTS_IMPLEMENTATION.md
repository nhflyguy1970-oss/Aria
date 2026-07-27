# Projects Implementation

## Executive Summary

Projects is Aria’s **Workspace Identity Layer** — not Jira, not Linear, not Planner.

This delivery transforms Projects from a thin registry/switcher into a **complete
workspace home**: one project slug is the single authority for coding root,
memory namespace, knowledge namespace, journal, browser session, checkpoint, and git.

## Workspace philosophy

| Principle | Behavior |
|-----------|----------|
| One identity | Registry `slug` drives every subsystem |
| Enter a room | Project Home surfaces everything needed to continue |
| Visible switch | Effects checklist shows what changed — never silent |
| Local-first | Registry under `data/projects/{slug}/`; journals under journal projects |
| Not PM | No kanban, tickets, roadmaps, or sprint boards |

**Does not replace:** Planner (actionable work), Calendar (commitments), Journal
(Bullet Journal method), Memory (ACM cognition), Documents (files).

## Unified identity

Canonical map for slug `lab-bench`:

| Concern | Value |
|---------|--------|
| Registry | `data/projects/lab-bench/meta.json` |
| Memory namespace | `lab-bench` |
| Knowledge namespace | `project:lab-bench` |
| Checkpoint namespace | `lab-bench` |
| Journal slug | `lab-bench` |
| Coding root | `git_path` if set, else project workspace folder |
| Browser session | `data/projects/lab-bench/browser/` |
| Git | Always project `git_path` — never accidental Aria repo fallback |

Legacy project metas are migrated on read (identity fields filled in place).
Display rename does **not** change the slug (identity stays stable).

### Key modules

- `jarvis/project_registry.py` — CRUD, identity fields, import-git, archive
- `jarvis/active_project.py` — active slug + `apply_active_project_effects`
- `jarvis/project_services.py` — home, briefing, continue, status, export, suggest
- `jarvis/session.py` — `coding_root`, `knowledge_namespace`, `project_slug`
- `jarvis/extensions/projects/` — HTTP API, chat/voice routes & handlers

## Project Home

GUI: Projects view (`projects.js` + `#projectsView`).

Sections:

1. **Project** — name, slug, status, git, workspace, created, last opened, activity
2. **Continue working** — coding, journal, documents, memory, checkpoint, AI
3. **Today’s workspace** — journal preview, commits, open files, memories, candidates
4. **Coding** — repo, branch, status, coding root, knowledge index
5. **AI context** — checkpoint, namespaces (deep-link Memory; no CRUD duplicate)
6. **Journal / Memory / Knowledge** — summaries + deep-links
7. **Quick actions** — rename, archive/restore, export, import, briefing, continue
8. **Active effects** — checklist of what the workspace is bound to

## Workspace Dashboard (effects)

Switching a project updates and displays:

- ✓ Coding Root  
- ✓ Memory Namespace  
- ✓ Knowledge Namespace  
- ✓ Browser Session  
- ✓ Current Checkpoint  
- ✓ Git Repository  
- ✓ Active Workspace  

`POST /api/projects/switch` returns an effects report. Failures are listed, not swallowed.

## Coding integration

- `SessionContext.coding_root` set from project `git_path` / workspace
- Daily project journals gather git activity from **project** repo
  (`project_journal_daily._git_repo_root_for_slug`)
- Knowledge sync tags matching repos as `project:{slug}`

## Memory integration

- Active project sets `session.memory_namespace = slug`
- `detect_project_namespace()` prefers active project slug
- Project Home shows recent/candidate memories and deep-links to Memory Browser
- Never duplicates Memory CRUD

## Knowledge integration

- Namespace `project:{slug}`
- Home lists indexed repositories / coverage
- Deep-links to Documents — does not duplicate the Documents browser

## Journal integration

- Creating a registry project ensures a matching `ProjectJournal`
- Bidirectional deep-links:
  - Projects → `window.openProjectJournal(slug)`
  - Journal Projects tab → `window.openProjectHome(slug)`
- Home shows today’s bullets and recent journal days

## AI Briefing

User-initiated only (`project briefing` / `POST /api/projects/briefing`):

- Where we left off (checkpoint)
- Current objective (description)
- Recent commits, journal, memories
- Coding root / branch / index
- Open questions prompt

## Continue Project

`continue project` / `POST /api/projects/continue`:

Restores coding root, memory NS, knowledge NS, browser session, checkpoint NS,
and surfaces today’s journal + checkpoint for resume.

## Smart suggestions

`GET /api/projects/suggest?q=` — ranked suggestions with `confirm_required: true`.
**Never auto-switches.**

## Chat & voice routing

Wired via extension `routes()` + handlers:

| Phrase | Action |
|--------|--------|
| switch / open / use project … | `project_switch` |
| list / show projects | `project_list` |
| current / active / which project | `project_current` |
| project status | `project_status` |
| continue project | `project_continue` |
| project briefing | `project_briefing` |
| create / new project … | `project_create` |
| project home | `project_home` |

Voice uses the same router table.

## HTTP API (selected)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/projects` | Registry snapshot |
| GET | `/api/projects/home` | Project Home payload |
| GET | `/api/projects/active` | Active + identity |
| POST | `/api/projects/switch` | Switch + effects |
| POST | `/api/projects/continue` | Continue Project |
| POST | `/api/projects/briefing` | Briefing |
| GET | `/api/projects/suggest` | Suggestions |
| POST | `/api/projects` | Create (+ activate) |
| POST | `/api/projects/import-git` | Import repo |
| PATCH | `/api/projects/{slug}` | Rename / description / git |
| POST | `/api/projects/{slug}/archive` | Archive |
| POST | `/api/projects/{slug}/restore` | Restore |
| GET | `/api/projects/{slug}/export` | Export JSON |

## Accessibility & UX

- Searchable list, keyboard: `/` search, `N` new, arrows, `Esc`, `?` help, Ctrl+Enter create
- Semantic regions, focusable list items, `aria-live` home
- Loading skeletons, empty states, responsive two-column → stacked layout
- Breadcrumbs / command palette already open Projects view

## Performance

- Home aggregates best-effort snapshots (git, journal, memory) with short timeouts
- No background auto-briefing; briefing is on demand
- Effects apply synchronously on switch (session in-memory)

## Testing

```bash
./venv/bin/pytest tests/test_projects_workspace.py tests/test_p2_projects.py -q
```

Coverage includes: unified identity, switch effects, coding root, git path isolation,
continue, home, briefing, chat routes/handlers, export/archive, suggestions confirm.

## Future roadmap

- Optional Planner tags / Calendar milestones (labels only — not issue tracking)
- Richer conversation history strip on Today’s workspace
- One-click “open folder” via native host when available
- Knowledge graph preview card (read-only) when graph APIs stabilize
- Migrate any orphan journal-only slugs into registry with user confirm

## Design gate (always ask)

1. Does one project have one identity?  
2. Does switching visibly change the workspace?  
3. Can users continue where they left off?  
4. Does this reduce confusion between Projects / Journal / Memory / Knowledge / Git?  
5. Does this stay local-first and avoid becoming a PM product?  

If not — redesign it.
