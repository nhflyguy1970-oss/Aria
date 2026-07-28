# Command Palette Implementation

## Executive Summary

The Command Palette is Aria’s **structured-action control plane**.
Chat is the natural-language control plane. They complement each other —
the palette is **not** a second Chat, not a Raycast clone, and not another sidebar.

This delivery transforms the palette from a monolithic keyboard launcher into a
**modular, reliable, extensible OS command center**:

- Modular **command registry** (`command_registry.js`)
- Stable **AriaActions** product APIs (`aria_actions.js`)
- Domain **command catalog** registrations (`command_catalog.js`)
- Thin **orchestrator UI** (`command_palette.js`)
- Honest knowledge-search UX (searching / empty / error / retry)
- Ask Aria auto-send + sentence prioritization
- Modes (`>navigate`, `>action`, `>search`, `>ask`, …)
- Connections in Navigate
- Pins, recents, usage ranking, keyboard help (`?`, `Ctrl+P`, Tab)

## Architecture

```
Ctrl/Cmd+K
    → command_palette.js (UI / keyboard / search status)
    → AriaCommandRegistry.list / score / rank / modes
    → command_catalog.js (+ future module registerAriaCommand)
    → AriaActions.* (stable product APIs)
    → Views / Chat Ask Aria / Mission Control / …
```

| File | Role |
|------|------|
| `command_registry.js` | Register/list/score/rank/mode parse/sentence detect |
| `aria_actions.js` | Supported interfaces; loud failures (toasts) |
| `command_catalog.js` | Built-in domain registrations |
| `command_palette.js` | Dialog, filter, knowledge fetch, render, keys |

## Registry design

Commands expose:

`id`, `title`, `keywords`, `group`, `mode`, `description`, `hint`,
`context`, `available()`, `run()`, optional `shortcut` / `icon` / `source`.

```js
window.registerAriaCommand({
  id: "act:my-feature",
  title: "Do the thing",
  group: "Actions",
  keywords: "alias words",
  source: "module",
  run: () => window.AriaActions.goView("documents"),
});
```

The palette **never** owns the catalog. Opening rebuilds context commands via
`AriaCommandCatalog.registerAll()`.

## Command lifecycle

1. Modules/catalog register into the registry  
2. User opens palette → refresh context + dynamic selects  
3. Filter by mode prefix + fuzzy score + rank boost (pin/context/usage)  
4. Optional knowledge hits merge into **Results**  
5. NL sentences prioritize **Ask Aria**  
6. Enter → push recent → close → `run()` via AriaActions  

## Search

- Local fuzzy over title/keywords/description/id (density-aware subsequence)
- Aliases (`todo`→planner, `kg`→connections, `mc`→mission control, …)
- Knowledge: `GET /api/knowledge/search` (≥2 chars, 160ms debounce)
- Status line + live region: Searching… / N results / No matches / Error + Retry

## Ranking

Boosts: pin (+40), This page/context (+55), usage (capped), view-id hint.
Empty query order: Context → Pinned → Recent → rest (max 40).

## Context

`ctx:{view}:*` commands for the active view plus global shell actions
(Activity, Workspaces, Split, Mini chat, Workflows).

## Ask Aria integration

- `AriaActions.askAria` → `jarvisAskAria` / `AriaChatOS.askAria` with **autoSend**
- Palette `Ask Aria: “…”` always auto-sends
- `looksLikeSentence()` elevates Ask Aria above command hits
- Complete prompts only (no dead composer pre-fill for power asks)

## Modes

Type prefixes or Tab-cycle:

`>navigate` `>action` `>search` `>ask` `>context` `>system` `>recent` `>pinned`

## Accessibility

- Dialog + listbox + `aria-activedescendant`
- `#commandPaletteLive` polite announcements
- Status region for search
- Focus restore on close
- Reduced-motion rules for pins/items
- Help overlay (`?` when input empty)

## Keyboard

| Key | Action |
|-----|--------|
| Ctrl/Cmd+K | Toggle palette |
| ↑↓ | Move |
| Enter | Run |
| Esc | Close / close help |
| Ctrl+P | Pin/unpin active |
| Tab | Cycle modes |
| ? | Help (empty input) |

## Testing

```bash
./venv/bin/pytest tests/test_command_palette.py tests/test_product_ui_api_wiring.py::test_command_palette_is_wired -q
```

Coverage: registry fuzzy/modes (Node), Connections navigate, AriaActions wiring,
honest search strings, Ask Aria auto-send, HTML stack include.

## Performance

- Registry Map lookups; rebuild on open is intentional (fresh context/models)
- Knowledge search capped at 8 hits; UI capped at 40 rows
- Local-only usage/pins/recents (no cloud telemetry)

## Future roadmap

- Move catalog sections into feature modules (`documents.js` registers itself)
- Deeper Results → row selection without secondary search clicks
- Capability badges from live model metadata
- Voice-open palette (transcript prefill)
- Optional local NL→command classifier

## Design guardrails

Does this stay an OS launcher (not Chat/Raycast/Spotlight)?  
Does it reduce coupling and silent failures?  
Does it strengthen Chat as the NL plane?  
Local-first? Discoverable? Plugin-ready via `registerAriaCommand`?

If not — redesign it.
