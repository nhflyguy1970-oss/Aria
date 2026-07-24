# Aria GUI Inventory — Product Certification v2

**Source:** [Inventory Aria UI surface](983b6186-9723-4bec-9736-89369945c5ca)  
**Corrected:** 2026-07-24 after command palette ship (`ee5f1a0`+)

Shell: `/media/jeff/AI/jarvis/jarvis/gui/static/index.html`

## View tabs (21)

`chat` · `dashboard` · `workstation` · `planner` · `calendar` · `flytying` · `projects` · `maker` · `browser` · `security` · `presence` · `audit` · `voice` · `audio` · `journal` · `memory` · `gallery` · `video` · `meme` · `documents` · `actions`

## Modals / overlays / lock

**Overlays:** `startupOverlay`, `dropOverlay`, `listeningOverlay`  
**Modals:** uncensoredAuth, haToken, apiKey, profile, branchTrim, jobCenter, upgradeWizard, crop, inpaint, flytyingScan, flytyingNameBarcode, toolConfirm, projectPicker, settings, shortcuts, haSetup, **commandPalette**  
**Lightboxes:** imageLightbox, videoLightbox  
**Lock:** lockScreen  

## Shell control counts (static HTML)

~288 buttons · ~85 inputs · ~38 selects · ~8 textareas (~373 button+input)

## Keyboard shortcuts

| Binding | Behavior | Documented in shortcuts modal |
|---------|----------|-------------------------------|
| Ctrl/Cmd+K | Command palette | Yes |
| Ctrl/Cmd+/ | Shortcuts help | Yes |
| Ctrl/Cmd+Shift+R | Reload UI | Yes |
| Ctrl+Enter | Send chat | Yes |
| Enter (chat) | Send | Yes (added after inventory) |
| Ctrl+L | Clear chat (not in text field) | Yes (added after inventory) |
| Esc | Close top modal | Yes |

## Command palette

**Present.** `command_palette.js` · Ctrl/Cmd+K · Commands button · Navigate / MC / Actions / AI / System / **Search** (focus journal, memory, documents, flytying, MC routing).

Full federated content search across stores remains **INTENTIONALLY DEFERRED**.

## Scoped search (pre-palette)

| Control | View |
|---------|------|
| `#journalSearch` | Journal |
| `#memorySearch` | Memory |
| `#documentsSearchInput` | Documents |
| `#flytyingSearchInput` / `#flytyingVideoSearch` | Fly tying |
| `#mcRoutingSearch` | MC Routing |

## Mission Control tabs (17)

overview, routing, timeline, intent_analytics, release, connection, applications, inference, memory, knowledge, databases, hardware, jobs, activity, performance, settings, recovery

## Extensions (11)

browser, engineering, flytying, git, journal, memory, planner, projects, security, smarthome, voice

## Largest first-party static JS (lines)

| File | Lines |
|------|------:|
| app.js | ~6017 |
| journal.js | ~1771 |
| flytying.js | ~1593 |
| audio.js | ~1080 |
| movie_tiers.js | ~897 |
| mission_control.js | ~805 |
| planner.js | ~511 |
| video_studio.js | ~508 |

**Concentration risk:** god-`app.js` remains the primary architecture debt item.
