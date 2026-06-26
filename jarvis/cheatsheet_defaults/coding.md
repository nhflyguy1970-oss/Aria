# Coding — Quick Reference

Stored in memory namespace **`cheatsheet`** (key: `coding`). Edit in the Memory tab or say **"coding cheatsheet"**.

## Chat examples

| You say | ARIA does |
|---------|-------------|
| "Fix bugs in path/to/file.py" | Proposes a patch |
| "Improve this file" / "Refactor …" | Suggested improvements |
| "Run path/to/script.py" | Executes with captured output |
| "Review this project" | Architecture / quality review |
| "Implement … in path/to/file.py" | Creates or rewrites code |
| "Apply it" / "Apply the patch" | Writes pending proposal to disk |
| "Undo apply" | Restores backup |
| "Search codebase for auth" | Project search |
| "Explain this selection" | Editor selection context (Cursor bridge) |
| "Debug until tests pass" | Agent loop with tests |
| "Resume task" / "Pause task" | Long-running coding tasks |

## Workflow

1. Ask for a fix or improvement → Jarvis shows a **proposal** (diff).
2. Say **apply it** to write changes (backup kept for undo).
3. Say **run** to test; **fix** again if needed.

## CLI

```bash
python main.py coding
python coding/main.py
```

## Tips

- Attach a file or mention a path; session remembers **last file**.
- Use **fix selection** when the Cursor bridge has editor context.
- Coding tasks checkpoint to `data/coding_tasks.json` for pause/resume.
