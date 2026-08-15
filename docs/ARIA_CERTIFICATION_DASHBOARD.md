> **Superseded (2026-07-31):** Historical certification report, not current engineering authority. Use [`Architecture Bible`](architecture/ARCHITECTURE_BIBLE.md) and [`Engineering Roadmap`](architecture/ENGINEERING_ROADMAP.md) as the governing docs.

# Aria Certification Dashboard

Evidence-driven release gate. Markdown alone is not certification.

## Authoritative surface

Open **Certification** in Aria (sidebar System menu, or **Cert** tab).

APIs:

- `GET /api/certification/home` — gate, coverage, blockers, history
- `GET /api/certification/runs/{id}` — assertions, API traces, evidence files
- `POST /api/certification/run` — background evidence run
- `POST /api/certification/run/sync` — synchronous run (`skip_image` default true)

Evidence root: `data/certification/runs/{run_id}/`

## Golden rule

No PASS without objective evidence (assertion expected/observed, API call, filesystem or cross-system check). HTTP 200 and toasts never grant PASS.

## Release gate

`READY_TO_SHIP` only when:

- No FAIL product features
- No failed product assertions
- Required workflows for the run completed
- Coverage ≥ threshold (`REQUIRED_COVERAGE_PCT`)
- API + assertion evidence present
- Mutation check detected injected failure
- False-pass resampling found no incoherent PASS
- `image_lifecycle` produced real generated-asset evidence files

Otherwise: `DO_NOT_SHIP` with blockers listed on the dashboard.

## Suites

| Suite | Proves |
|-------|--------|
| `chat_clear` | Clear Main empties messages on re-fetch |
| `image_lifecycle` | Generate → Gallery/Chat/Jobs/Search → delete scrub → restore repair |
| `planner_calendar` | Planner-owned event/task visible in Calendar + Search |
| `journal_calendar` | Journal note projected to Calendar + Search; Journal is not the event write owner |
| `search_federated` | Gallery + chat corpora enabled |
| `settings_appearance` | Theme API and disk agree |
| `projects_archive` | Create → search → archive removes from active |
| `mutation_check` | Harness integrity (meta) |

## Operator notes

- Fast cert (dashboard **Run cert**): skips long image generation.
- Full cert (**Full (image)**): includes Comfy/image lifecycle; may take minutes.
- Package a run: `POST /api/certification/package/{run_id}` → zip under `data/certification/`.
