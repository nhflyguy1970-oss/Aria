# Living Room Immersion Report
## Phase 3.5 — The Soul of Aria

**Date:** 2026-08-06  
**Mode:** Living, not testing  
**Room:** Chat · Living Room  
**Build:** Living Room immersion `3.5.1`  
**Other Rooms:** Still blocked  

This is not a QA report. It is a chronological account of interruptions while spending the day inside the room — and what was removed so software would leave.

---

## Morning

**What I was doing:** Opened Aria. Sat down. Looked without reading.

**What reminded me this was software:**
- Status bar (Ollama, model, GPU, alerts, Layouts)
- Activity / Recipe strip
- Sidebar house of menus (MODE, AI, SURFACES, Favorites, Restart)
- Copy / Share / Fork / Regenerate / timestamps on the welcome
- What’s New energy still possible at the door

**Why it interrupted immersion:**  
The first ten seconds should feel like walking into a favorite room. Instead the periphery announced infrastructure.

**What changed:**
- Status bar: removed from the room (`display: none`)
- Workspace Activity bar + tool tray: removed
- Sidebar: removed + `inert` / `aria-hidden`
- Welcome action chrome + timestamps: stripped; reply actions skipped while Living Room is active
- Soft invites only (Good morning / What should we work on? / Just listen) — no marketing chips
- Toasts muted; failures become presence whispers

**Feeling after:**  
Yes — “Aria *is here*,” invitation, hearth. Accessibility tree collapsed to More · invites · Say anything · mic · Send.

---

## Mid-morning

**What I was doing:** Staying in the empty room. Watching the hearth. Asking whether every pixel earned its place.

**What reminded me this was software:**
- Soft invite chips as bordered “buttons”
- Overflow `···` reading as a control cluster
- Progress / “Processing…” copy when conversation started earlier

**Why it interrupted immersion:**  
Controls that look like controls pull the eye from conversation. “Processing…” is factory language.

**What changed:**
- Soft chips: borderless, faint text; fade after ~14s of quiet
- Overflow button: quieter opacity until hover
- Status hints + agent-step walls hidden
- Stream status → presence (“Thinking with you” / “Still with you”) instead of bubble software copy
- Stop control: de-chromed

**Feeling after:**  
Mostly yes. The room explained less.

---

## Lunch

**What I was doing:** Trying to talk. Send failed. Text vanished. Nothing answered.

**What reminded me this was software:**  
Silence of a broken send — worse than a toast. The hearth looked alive; it was dead. Immersion defect caused by a syntax break in `chat_send.js` during the Processing silence repair.

**Why it interrupted immersion:**  
Jeff would assume Aria was ignoring him. That is not calm. That is broken trust.

**What changed:**
- Restored `chat_send.js` structure; `window.sendMessage` returned
- Warn-level toasts also become presence whispers (so “wait for reply” is not invisible)

**Feeling after:**  
Trust restored. Conversation worked again.

---

## Afternoon

**What I was doing:** Asked Aria what Jeff should focus on. Read the reply. Left the room open.

**What reminded me this was software:**
- Occasional action residue on a turn (`actions: 1` once)
- Composer still holding the last prompt when send was called directly (minor)
- Avatar “You” / “A” still slightly “UI,” but also presence — kept

**Why it interrupted immersion:**  
Any regenerate/copy strip under a sentence pulls you into operating a chat app.

**What changed:**
- Mutation observer strips action chrome whenever messages change

**Feeling after:**  
Conversation felt like the only object. Hearth stayed the center. Status bar never returned.

---

## Evening

**What I was doing:** Looking at a short thread. Idle. Presence back to “Listening quietly.” Imagining the thousandth open.

**What still reminds me this is software (honest residual):**
1. Overflow `···` — necessary power door; still a menu
2. Soft invites — invitations, but still chips until they fade
3. Message bubbles — gentle, still bubbles
4. Mic + Send icons — hearth furniture; would be missed if gone
5. Host window chrome outside Stage (Electron vs browser) — not Living Room’s to solve alone

**What disappeared today:**  
Status bar. Activity bar. Sidebar. Toasts. Reply toolstrips. Timestamps. “Processing…” copy. Marketing suggestions. What’s New at the door.

**Did I forget I was using software?**  
In stretches — yes. Especially with an empty room and only presence + hearth. During the broken-send hour — no. After repair, while reading Aria’s reply — mostly yes.

---

## Silence Law checklist

| Element | Miss it if gone? | Decision |
|---|---|---|
| Status bar | No | Removed |
| Activity / Recipe | No | Removed |
| Sidebar | Not while conversing | Removed in Living Room |
| Toast walls | No | Muted |
| Welcome actions | No | Removed |
| Soft invites | Briefly, then no | Kept faint; fade |
| Presence line | Yes | Kept |
| Hearth | Yes | Protected |
| Overflow | Rarely | Kept whisper-quiet |

---

## One Hour / Three Hour / Daily Driver

| Test | Note |
|---|---|
| One Hour | Visual fatigue low after silence pass; eye stays on conversation |
| Three Hour | Not fully claimed in one calendar day — continue living; tools must not eject |
| Daily Driver | Started; Jeff must continue morning→evening across days |

---

## What not to do next

- Do not begin Fly Tying  
- Do not begin Health  
- Do not begin Mission Control  
- Do not add features  

Continue living. Every new interruption → repair only enough → resume.

---

## Gate

The Living Room is **closer to home**. It is not yet certified by enthusiastic Jeff approval.

When Jeff opens Aria for the thousandth time and still does not think about software — then the rest of the house may be built.

Until then: stay in the Living Room.
