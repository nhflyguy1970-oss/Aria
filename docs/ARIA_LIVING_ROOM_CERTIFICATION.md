# Living Room Certification Report
## Phase 3 — Chat as the first flagship Room

**Date:** 2026-08-06  
**Room:** Chat · The Living Room  
**Runtime:** R1 Electron / Workspace Stage (`app=1&workspace=1&shell=electron`)  
**Status:** **BUILT — awaiting Jeff’s enthusiastic approval**  
**Next room:** Fly Tying — **blocked** until Chat receives enthusiastic approval  

---

## Verdict (honest)

The Living Room **exists**. Conversation is the hero. The composer feels like a hearth. Legacy chat chrome is gone from the primary surface. The Workspace is consumed, not redesigned.

It does **not** yet fully pass “Jeff forgets he is using software” for an entire day — a few mechanical edges remain (listed below). Those are immersion defects, not missing features.

**Certification claim:** Chat is ready for Jeff to live in and judge. It is **not** certified as complete until he feels the place.

---

## What was built

| Surface | Path |
|---|---|
| Living Room CSS | `jarvis/gui/static/workspace/rooms/living_room.css` |
| Living Room JS | `jarvis/gui/static/workspace/rooms/living_room.js` |
| Workspace wiring | `workspace.js`, `activity_engine.js`, `registry.js`, `tools.js` |
| Soft welcome / branches | `chat_branches.js` |
| Soft suggestions | `chat_suggestions.js` (defers when Living Room active) |
| Discoverability | What’s New suppressed while conversing |

**Activation:** `body.living-workspace.living-room` during Activity `converse`.

**Bridge:** Same `#messages`, `#messageInput`, `#chatForm`, send/stream pipeline — presentation only changed. No backend rewrite.

---

## Three Second Test

| Expectation | Result |
|---|---|
| Feel “I’m in Aria” without reading | **PASS (strong)** — amber “Aria *is here*”, quiet status, warm room wash |
| Not “I’m looking at software” | **PASS with notes** — header wall gone; status bar still exists if you hunt the bottom edge |

---

## What felt warm

- Presence line: “Aria *is here*” / “Listening quietly”
- Hearth composer: rounded wood field, italic “Say anything…”, amber send, mic seated beside it
- Conversation column centered; bubbles soft; welcome “Come in. Sit down.”
- Soft chips only: Good morning / What should we work on? / Just listen for a bit
- Overflow `···` for model, attach, new conversation — not a toolbar wall
- Sidebar collapsed under minimal chrome; view tabs hidden
- What’s New changelog wall suppressed on enter

---

## What interrupted immersion

1. **Message action residue** — Copy / Share / Fork / Regenerate still in the accessibility tree and briefly visible on the welcome turn (hover policy helps; welcome should stay quieter).
2. **Status bar** — Ollama / GPU / alerts / version whisper at the bottom; still “computer.”
3. **External host chrome** — if opened outside pure Stage, desktop menus can still appear (Electron Stage is the intended home).
4. **Activity bar** — near-invisible until hover; still software furniture if discovered.
5. **Suggestion rotation race** — fixed by Living Room ownership; watch for regressions after long idle.

---

## What felt mechanical

- Reply action buttons on assistant turns (regenerate / stage memory) — power-user residue
- Any toast that still fires from tools outside the Living Room path
- Branch/thread concepts living only in overflow (correct placement; still “app” vocabulary)

---

## What disappeared

- Dense chat header (“How can I help?”, branch row, attach wall, wake pills)
- Permanent model chip in the composer
- Feature-marketing suggestion chips
- Permanent Voice / Clipboard tool tray during converse
- Sidebar favorites wall during Living Room
- View-tab strip (Workspace chrome policy)
- What’s New auto-modal during converse

---

## One Hour / Three Hour / Daily Driver

| Test | Status |
|---|---|
| One Hour | **Ready for Jeff** — visual fatigue should be low; watch action-button creep |
| Three Hour | **Ready for Jeff** — coding-via-conversation should stay in-room; tools must not eject to pages |
| Daily Driver | **Not claimed yet** — requires Jeff living in it across morning / idle / heavy use |

---

## What should change before another Room is built

1. **Enthusiastic Jeff approval** of the Living Room as a *place* (mandatory gate).
2. Quieter welcome turn — no action chrome on the invitation message.
3. Status bar fully optional / hover-only in converse (near done; verify Electron Stage).
4. Confirm Voice tool never leaves the room (contextual chip only — implemented; live-dogfood).
5. Capture lessons for Fly Tying: **hero first, overflow for power, tools ephemeral, no product chrome**.

---

## How to enter

```bash
./scripts/launch-aria-workspace.sh
# or open Stage with:
# ?app=1&workspace=1&shell=electron#chat
```

---

## Decision requested

Jeff: spend real time in the Living Room.  

If it feels like a place you want to stay — **approve enthusiastically**, and Fly Tying may begin.  
If anything still feels like software — name it; we repair before any other Room.
