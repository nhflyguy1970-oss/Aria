# Coding — Quick Reference

Stored in memory namespace **`cheatsheet`** (key: `coding`). Edit in the Memory tab or say **"coding cheatsheet"**.

**Coding Home** (`Ctrl+Shift+C`) is the primary destination. The sidebar **Coding tools** drawer holds LSP/Git helpers.

## Product boundaries

| Coding | Other products |
|--------|----------------|
| Propose / Review / Apply / Undo / Verify | Projects = workspace identity |
| LSP & Git helpers | Job Center = live job queue |
| Proposal history & quality brief | Models = coding model role |
| Coding job execution | Activity = durable events |

## Chat examples

| You say | ARIA does |
|---------|-------------|
| "Fix bugs in path/to/file.py" | Proposes a patch + quality brief |
| "Improve this file" / "Refactor …" | Suggested improvements |
| "Run path/to/script.py" | Executes with captured output |
| "Review this project" | Architecture / quality review |
| "Implement … in path/to/file.py" | Creates or rewrites code |
| "Apply it" / "Apply the patch" | Writes pending proposal to disk |
| "Undo apply" | Restores backup |
| "Verify" / use Verify after apply | Operator-approved syntax/tests |
| "Search codebase for auth" | Project search |
| "Explain this selection" | Editor selection context (Cursor bridge) |
| "Debug until tests pass" | Agent loop with tests |
| "Resume task" / "Pause task" | Long-running coding tasks |

## Workflow

1. Confirm **coding root** (Projects) — Coding Home shows write target / branch.
2. Ask for a fix → **proposal** + **quality brief**.
3. **Apply** (never silent). Optionally **Verify**. **Undo** if needed.
4. Long runs appear in **Job Center** with deep links back to Coding.

## Tips

- Attach a file or mention a path; session remembers **last file**.
- Use **fix selection** when the Cursor bridge has editor context.
- Export patches from Coding Home → History.
- Coding model is configured in **Models Home** (coding role).
