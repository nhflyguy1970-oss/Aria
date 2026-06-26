# General chat — Quick Reference

Stored in memory namespace **`cheatsheet`** (key: `general`). Edit in the Memory tab or say **"general cheatsheet"**.

## Chat examples

| You say | ARIA does |
|---------|-------------|
| "What can you do?" | Capabilities overview |
| Normal conversation | Routes to general chat with memory context |
| "Clear conversation" | Clears current branch messages |
| Branch/fork commands | Split conversation threads |

## Personalities

Sidebar **Personality**: default, professional, casual, tutor, brief — changes tone in system prompt.

## Models

- **Fast / Quality** presets in sidebar
- Per-role models in **Model settings** (`data/model_settings.json`)
- Env overrides: `JARVIS_GENERAL_MODEL`, `JARVIS_CODER_MODEL`, etc.

## Uncensored mode

- Launch  **ARIA (Uncensored)** or toggle in sidebar
- `JARVIS_UNCENSORED=1`

## CLI

```bash
python main.py general
```
