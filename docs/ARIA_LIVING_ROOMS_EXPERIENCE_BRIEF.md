# Aria Living Rooms — Experience Design Brief

**Status:** Awaiting Jeff approval. **No implementation until approved.**

**Rejection:** The prior Living Interface pass (accents, gradients, micro-animations, room CSS tokens) is rejected as the destinations redesign. Supporting details are not Experience Design.

**House law:** Aria is a home. Flagship products are rooms. Within three seconds — without reading the title — Jeff must know where he is. Content dominates; controls support. One hero, one secondary area, one supporting area. If it can live in a drawer until needed, it should.

**Success:** Jeff forgets he is using software. Each room becomes a destination he wants to inhabit for its purpose.

Interactive review: open the canvas beside chat — `Aria-Living-Rooms-Design-Brief.canvas.tsx`.

---

## Chat — Living room

| Field | Brief |
|---|---|
| **Purpose** | Sit with Aria. Conversation is the product. |
| **Emotional goal** | Warm, inviting, unhurried — linger like a good couch. |
| **Three-second tell** | Large conversation surface with presence — not a control panel with a message box. |
| **Hero** | The conversation itself. |
| **Supporting** | Quiet composer as hearth; soft presence; contextual suggestions as whispers. |
| **Disappears** | Dense permanent toolbars; equal-weight button rows; session-admin chrome. |
| **Becomes larger** | Message column, typography, whitespace between turns, composer focus. |
| **Secondary UI** | Model/provider/session → drawer; attachments → expand on need; history/branches → panel/palette. |
| **Inspiration** | Things 3 calm; Arc quiet chrome; hotel lounge — not lobby digital signage. |
| **Lighting / materials / palette** | Warm lamp-lit neutrals; cloth/wood softness; amber + muted sage — never clinical blue OLED. |
| **Imagery** | No “AI brain” stock. Quiet warmth only if needed. |
| **Hierarchy** | 1 Conversation → 2 Composer → 3 Turn actions → 4 House chrome. |
| **Empty state** | Invitation to sit + one gentle prompt — never a form or empty table. |
| **Daily workflow** | Open → conversation is the room → speak/type → deepen via contextual actions only when relevant. |
| **Anti-pattern** | Chat as another product page with tabs, filters, and a skinny input. |

---

## Mission Control — NASA operations floor

| Field | Brief |
|---|---|
| **Purpose** | Know at a glance whether the house is healthy. |
| **Emotional goal** | Confidence and composure — the system is watched. |
| **Three-second tell** | Live vitals: large telemetry for CPU, GPU, memory, providers, jobs, alerts. |
| **Hero** | The system itself — live telemetry as centerpiece. |
| **Supporting** | Provider constellation; jobs runway; calm/urgent alert strip. |
| **Disappears** | Admin tabs as first impression; dense settings tables; checklist-as-identity. |
| **Becomes larger** | Vital cards/gauges; hardware visualization; current degraded signal. |
| **Secondary UI** | Diagnostics/logs → drawers; config/policy → Settings; history → on demand. |
| **Inspiration** | NASA Mission Control walls; Linear status; aerospace glass — not Kubernetes admin. |
| **Lighting / materials / palette** | Cool instrument-bay light; matte metal + glass instruments; graphite + steel blue; semantic status only. |
| **Imagery** | Abstract machine vitality; quiet machine diagram — no sci-fi HUD spam / RGB. |
| **Hierarchy** | 1 Vitals → 2 Providers + jobs → 3 Alerts / Guided Repair → 4 Deep tools. |
| **Empty state** | Quiet “all clear” landscape — stillness, not vacancy. |
| **Daily workflow** | Glance → confident or investigate → tap degraded card → repair only with a clear path. |
| **Anti-pattern** | Mission Control as a settings dashboard with tabs. |

---

## Fly Tying — Streamside cabin / tying bench

| Field | Brief |
|---|---|
| **Purpose** | Tie flies. Study hatches. Feel the river — not manage a materials database. |
| **Emotional goal** | Adventurous calm — wood, water, vise. |
| **Three-second tell** | Stream/lodge atmosphere + the fly as large photographic hero — not a search form. |
| **Hero** | The fly (pattern of the day / selected pattern). |
| **Supporting** | Hatch + river conditions board; recipe as premium book pages; visual materials; workbench + optional video. |
| **Disappears** | Search as dominant first element; CRUD admin landing; software-module tabs. |
| **Becomes larger** | Hero photography; hatch narrative; recipe typography; material board. |
| **Secondary UI** | Library browse → rail/drawer; import/edit → overflow; full catalog admin → deep mode. |
| **Inspiration** | Fly lodges; field guides; leather/copper/canvas workshops — not inventory software. |
| **Lighting / materials / palette** | Warm cabin + cool water; wood, leather, copper, canvas, cork, paper; river greens, wet-stone, cream paper. |
| **Imagery** | Signature trout stream header; macro flies; material close-ups; restrained maps — cohesive, not random stock. |
| **Hierarchy** | 1 Stream/hatch/pattern hero → 2 Recipe + materials + video → 3 Library → 4 Admin. |
| **Empty state** | Empty vise with “Start with today’s hatch” — never a blank data grid. |
| **Daily workflow** | Enter → hatch + pattern of the day → open recipe like a book → lay materials → tie. |
| **Anti-pattern** | Fly Tying as a searchable admin table of recipes. |

---

## Health — Premium wellness clinic

| Field | Brief |
|---|---|
| **Purpose** | Care for himself daily without medical-admin anxiety. |
| **Emotional goal** | Calm trust; soft encouragement; want to check in every morning. |
| **Three-second tell** | Personal greeting + today’s wellbeing — not a tab bar. |
| **Hero** | The person (Jeff’s today) — feeling, meds, goals, body signals as one composition. |
| **Supporting** | Today’s meds; sleep/BP/weight charts; next appointment; recent improvements. |
| **Disappears** | Tabs first; dense PHR CRUD; EMR density. |
| **Becomes larger** | Greeting + feeling check-in; today cards with whitespace; generous calm graphs. |
| **Secondary UI** | Full history → drawers; data entry after intent; reports/exports → overflow. |
| **Inspiration** | High-end wellness clinics; Apple Health hierarchy (inspiration only) — not hospital billing portals. |
| **Lighting / materials / palette** | Morning clinic light; linen, soft plaster, pale wood; soft teal/sage, warm off-white. |
| **Imagery** | Abstract wellness — light, breath. Never alarming medical stock. |
| **Hierarchy** | 1 Greeting + feeling → 2 Today → 3 Trends → 4 Records & tools. |
| **Empty state** | Calm first morning — invite feeling + one med/goal — never “no rows found.” |
| **Daily workflow** | Morning greeting → feeling → meds → glance sleep → log lightly → weekly improvements. |
| **Anti-pattern** | Health as a tabbed medical database. |

---

## Documents — Private library

| Field | Brief |
|---|---|
| **Purpose** | Find, read, keep knowledge — research with dignity. |
| **Emotional goal** | Quiet focus and curiosity — want to read. |
| **Three-second tell** | Shelves / collections / recent reading — not a flat upload list. |
| **Hero** | Knowledge — collections and reading presence. |
| **Supporting** | Recent reading desk; shelves; beautiful previews; research tools secondary. |
| **Disappears** | Filesystem list as hero; upload-first admin; dense metadata tables. |
| **Becomes larger** | Collection/shelf presence; reading preview; recent reading narrative. |
| **Secondary UI** | Indexing/OCR/diagnostics → drawer; bulk ops → advanced. |
| **Inspiration** | Private libraries; Craft/Notion calm; museum archives — not SharePoint. |
| **Lighting / materials / palette** | Desk lamp + study light; paper, cloth bindings, oak, leather; warm paper + forest/oxblood. |
| **Imagery** | Shelf silhouettes, open-book previews — never clip-art folders. |
| **Hierarchy** | 1 Shelves/recent → 2 Open reading surface → 3 Search → 4 Maintenance. |
| **Empty state** | Empty shelf inviting the first volume — teach gently. |
| **Daily workflow** | Enter → resume reading → browse shelf → open preview like paper. |
| **Anti-pattern** | Documents as upload + file table. |

---

## Gallery — Art gallery / museum wing

| Field | Brief |
|---|---|
| **Purpose** | Look at work with pride — collections, not thumbnail management. |
| **Emotional goal** | Quiet awe; want to wander the walls. |
| **Three-second tell** | One large artwork (or curated wall) with museum spacing — not dense thumbs. |
| **Hero** | The artwork — large framed pieces with breathing room. |
| **Supporting** | Collections/albums; favorites wall; generation as a studio door, not the lobby. |
| **Disappears** | Dense thumbnail grids as default; jobs/settings as first paint. |
| **Becomes larger** | Featured piece; frame + whitespace; collection storytelling. |
| **Secondary UI** | Pipelines/jobs → studio drawer; metadata on detail; trash/admin secondary. |
| **Inspiration** | Museums; photography portfolios; Craft restraint — not DAM software. |
| **Lighting / materials / palette** | Museum wash on the piece; mat board, thin frames, plaster; artwork carries color. |
| **Imagery** | Jeff’s media is the imagery — UI never competes. |
| **Hierarchy** | 1 Featured wall → 2 Collections → 3 Browse/favorites → 4 Studio tools. |
| **Empty state** | Empty wall with dignity — create/import first piece. |
| **Daily workflow** | Wander → stop at a piece → open collection → create from studio when inspired. |
| **Anti-pattern** | Gallery as media-manager thumbnail dump. |

---

## Planner — Premium leather notebook

| Field | Brief |
|---|---|
| **Purpose** | Organize today with focus — not spreadsheets. |
| **Emotional goal** | Encouraging clarity — opening the book starts the day well. |
| **Three-second tell** | Today’s page — date, important tasks, focus — as a notebook spread. |
| **Hero** | Today — the open page for this day. |
| **Supporting** | Few large important tasks; calm timeline ribbon; focus/intention; small tomorrow peek. |
| **Disappears** | Spreadsheet density; equal-weight project admin; control-heavy top toolbars. |
| **Becomes larger** | Today heading/page metaphor; primary tasks; whitespace. |
| **Secondary UI** | Projects/backlog → back of notebook; recurrence/automation → settings; multi-week → secondary modes. |
| **Inspiration** | Things 3; Fantastical; paper planners — not Jira-as-home. |
| **Lighting / materials / palette** | Desk lamp on cream paper; leather, ink, ribbon; copper/forest for today. |
| **Imagery** | Paper texture, subtle binding — restrained. |
| **Hierarchy** | 1 Today → 2 Timeline → 3 Upcoming → 4 Systems/projects. |
| **Empty state** | Blank page: “What matters today?” — never empty rows. |
| **Daily workflow** | Open Today → check a few things → glance timeline → close settled. |
| **Anti-pattern** | Planner as project-management spreadsheet. |

---

## Search — Spotlight / invisible librarian

| Field | Brief |
|---|---|
| **Purpose** | Find anything across the house instantly — then disappear. |
| **Emotional goal** | Effortless competence — magic without ceremony. |
| **Three-second tell** | Large quiet search + beautiful content results — chrome almost gone. |
| **Hero** | Query + results (content cards). |
| **Supporting** | Previews that feel like source rooms; gentle place grouping; instant feedback. |
| **Disappears** | Default cluttered filter sidebars; settings on the search stage. |
| **Becomes larger** | Search input; result typography/previews; idle calm. |
| **Secondary UI** | Advanced filters on demand; index diagnostics → Mission/Settings. |
| **Inspiration** | Raycast; Spotlight; Arc command — not enterprise federated portals. |
| **Lighting / materials / palette** | Neutral focus; almost no material; accent only on focus/selection. |
| **Imagery** | None required — results carry room identity. |
| **Hierarchy** | 1 Query → 2 Results → 3 Facets optional → 4 Diagnostics elsewhere. |
| **Empty state** | “Search the house” + 2–3 example destinations. |
| **Daily workflow** | Invoke → type → jump to room → leave (Search is not a place to live). |
| **Anti-pattern** | Search as a dense filter dashboard. |

---

## Coding — Professional engineering studio

| Field | Brief |
|---|---|
| **Purpose** | Real work on projects — current change, jobs, git, workspace. |
| **Emotional goal** | Competent focus — entered a studio, not a ticket form. |
| **Three-second tell** | Current project / current work on the bench — not configuration forms. |
| **Hero** | Current work (active project + what is in motion). |
| **Supporting** | Projects as workbenches; jobs/proposals as WIP trays; git as craft instrument. |
| **Disappears** | Forms-first landing; equal-weight settings; admin chrome as identity. |
| **Becomes larger** | Active project identity; current job/proposal; diff/work surface entry. |
| **Secondary UI** | Model/policy → drawer; historical jobs → archive; env diagnostics → Mission. |
| **Inspiration** | Linear + IDE calm; clean craft studios — not enterprise ALM portals. |
| **Lighting / materials / palette** | Focused task light; steel/concrete desk order; slate + muted cyan; status for git/jobs only. |
| **Imagery** | Project identity marks — never neon terminal wallpaper. |
| **Hierarchy** | 1 Current work → 2 Projects → 3 Jobs/git → 4 Studio settings. |
| **Empty state** | Empty bench: “Open a project.” |
| **Daily workflow** | Enter → resume work → propose/apply/watch → git glance → leave tidy. |
| **Anti-pattern** | Coding as a form wizard with dropdowns. |

---

## Approval checklist

Reply per room: **Approved** / **Revise: …** / **Veto: …**

- [ ] Chat
- [ ] Mission Control
- [ ] Fly Tying
- [ ] Health
- [ ] Documents
- [ ] Gallery
- [ ] Planner
- [ ] Search
- [ ] Coding

Implementation begins only after this set is approved (or explicitly sequenced).
