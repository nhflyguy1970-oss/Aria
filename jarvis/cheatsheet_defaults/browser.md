# Browser — Quick Reference

Stored in memory namespace **`cheatsheet`** (key: `browser`). Edit in the Memory tab or say **"browser cheatsheet"**.

**Browser Home** (`Ctrl+Shift+B`) is the primary destination for live web automation.

## Product boundaries

| Browser | Other products |
|---------|----------------|
| Live page automation / screenshots | Projects = workspace + Playwright profile |
| DOM / Vision browsing under operator control | Documents = store page extracts |
| Safe URL + download policy | Memory = remembered facts |
| Session / step log / takeover | Automation = orchestrates (with approval) |
| Browser tasks | Job Center = long-running queue |
| | Mission Control = runtime health |
| | Chat = conversation surface |
| | Models = `browser_vision` role |

Browser is **not** Chrome/Firefox/Edge. Never silent purchases or downloads.

## Chat examples

| You say | ARIA does |
|---------|-----------|
| "Browse https://example.com" | Real Playwright navigate + screenshot |
| "Search the web for cats and open" | Search then browse a result |
| "Click Sign in on the page" | DOM agent task on the live page |
| "Summarize the page" | Extract + summarize current page |
| "Take over the browser" | Pause agent for human control |
| "Pause the browser" / "Resume the browser" | Voice-safe control verbs |
| "Save this page to Documents" | Extract → Documents (Documents owns storage) |

## Workflow

1. Confirm Playwright ready (Browser Home banner).
2. Open a URL → live screenshot updates.
3. Run a DOM/auto task — watch the **step log**.
4. Pause / Takeover / Resume / Stop as needed.
5. Long tasks: **Queue** → Job Center.
6. Save extracts to Documents; Vision→Coding goes through Coding proposals only.

## Safety

- Checkout/payment URLs need `allow_risky` confirmation.
- Downloads are gated by extension allowlists.
- Failures report what happened, why, and recovery — never fake "Opened".

## Tips

- Active Project binds the Playwright profile (cookies/storage).
- Install stack: `pip install playwright && playwright install chromium`
- Prefer DOM mode when structure is clear; VLM when visual.
