# Coding Implementation

## Philosophy

**Coding** is Aria's software-development product.

| Coding owns | Does not own |
|-------------|--------------|
| Propose | Projects (workspace identity) |
| Review | Job Center (queue UX) |
| Apply | Activity Center (durable history) |
| Undo | Mission Control (health) |
| Verify | Models (role→model config) |
| LSP / Git helpers | |
| Coding job *execution* | |
| Proposal history / quality brief | |
| Coding Home | |

**Coding proposes. Projects identify. Job Center tracks. Activity records. Models configure. Mission Control monitors.**

Trusted loop: **Propose → Review → Apply → Undo → Verify**. Never silent auto-apply.

## Architecture

```
UI: Coding Home (coding_home.js) + Coding tools sidebar + Chat proposals
        ↓
APIs: /api/coding/home, proposals/*, verify, guardrails, vision-fix, spec-to-code
        ↓
jarvis/coding_product/
  home.py guardrails.py history.py brief.py verify_workflow.py
  preferences.py vision_fix.py spec_to_code.py job_links.py terminology.py
        ↓
jarvis/coding_agent.py · behaviors/engineering · proposal_store
jarvis/coding_jobs.py · coding_verify.py · cursor_bridge / MCP
```

## Proposal lifecycle

1. Agent / EngineeringEngine / specialist / MCP creates a proposal via `_store_agent_proposal`
2. Quality brief attached; row recorded in `coding_proposal_history.json`
3. Operator reviews diff + brief
4. Apply writes files (optional force); history → `applied`; verify offer returned
5. Operator may Undo (restores backups; history → `undone`) or Verify (approved actions only)
6. Dismiss / reject marks history `rejected`

## CodingAgent

`CodingAgent(base: Path)` — iterative plan → edit → verify.  
`run(task, path=, mode=)` returns `AgentResult` with files/diff; proposals are stored by the assistant.

## EngineeringEngine

Facade over propose / create / fix / refactor / LSP / git helpers. Direct proposal writes go through `_store_agent_proposal` so history + brief stay consistent.

## Verification workflow

Post-apply `verify_offer` lists syntax / lint / tests / build / summary.  
`POST /api/coding/verify` requires `approved=true`. Never auto-runs heavy suites.

## Job integration

Coding jobs execute in `coding_jobs`; Job Center displays them with deep links to Coding Home, proposal, Chat, Verify, Undo, Projects.

## Models integration

Coding Home shows the active **coding** role model and deep-links to Models Home. Configuration stays in Models.

## Specialist integration

Coder specialist calls `CodingAgent(assistant.coding._base()).run(...)` and stores proposals — not `CodingAgent(assistant)`.

## Guardrails

Always surface project, coding root, write target, repo, branch. Warn on missing root, multiple roots, or writes outside the active project.

## Shortcuts

- **Ctrl+Shift+C** — Coding Home  
- Command palette: Open Coding Home / proposal history / Verify last apply

## Experimental

- Vision-assisted bug fix (screenshot → proposal; never auto-apply)
- Spec-to-code (documents → plan → proposal)
- Preference memory (suggestions only)

## Testing

`tests/test_coding.py` and related modules cover agent, proposals, history, guardrails, verify, jobs, LSP, cursor bridge, home APIs.

## Roadmap

Richer multi-repo packs, stronger RAG citations in briefs, optional PR summary after apply (never force-push).
