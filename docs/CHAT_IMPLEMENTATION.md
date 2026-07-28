# Chat Implementation — Aria AI Operating System Interface

## Executive Summary

Chat is **Aria’s operating system interface**, not a standalone chatbot and not a
ChatGPT clone. Natural language is the primary control plane for the whole AI OS.

This delivery polishes Chat into a trustworthy OS surface:

- **Unified New Chat** (branch + session as one user action)
- **Ask Aria everywhere** auto-sends with context (no mere pre-fill)
- **Paste / drag-and-drop** attachments of many types
- **Composer model chip** beside the input
- **Clickable grounding** (Memory, Documents, Connections, Knowledge Briefs, …)
- **Explicit `@` context chips**
- **Contextual reply actions** (stage Memory candidates, Planner, Journal, …)
- **Unified voice entry** (hold-to-talk + Read aloud)
- **First-class Mini Chat** with streaming
- **Themed thread dialogs** (no browser `prompt`/`confirm`)
- **Accessibility** live regions on the message log / progress bar
- **Behavioral tests** restored for sessions, API, grounding contracts, UI wiring

## Architecture

```
Ask Aria (any surface)
    → AriaChatOS.askAria / jarvisAskAria
    → optional context chips (@memory:@id …)
    → sendMessage (streaming pipeline)
    → ConversationBehavior.build_context_prefix
        → Memory · Documents · Connections · Planner grounding
    → streamed tokens → #messages (+ Mini Chat mirror)
    → citations → clickable chips → openCitation(view)
```

| Layer | Role |
|-------|------|
| `chat_os.js` | OS control helpers: Ask Aria, New Chat, chips, citations, reply actions |
| `chat_send.js` | Streaming send; `onToken` / `onDone` hooks for Mini Chat |
| `chat_sessions.py` | Named thread metadata + `create_new_chat()` |
| `POST /api/chat/new` | Unified New Chat API |
| `vision_drop.js` | Paste + multi-type drop onto composer |
| `aria_dialogs.js` | Themed prompt/confirm |
| `mini_chat.js` | Floating Ask Aria with live stream mirror |

## Conversation lifecycle

1. **New Chat** → `POST /api/chat/new` creates a branch *and* session row, switches UI.
2. **Ask Aria** → auto-sends; optional `returnView` soft-returns via toast.
3. **Streaming** → tokens update the assistant bubble; Stop cancels; recovery via truncate helpers.
4. **Bookmark** → session metadata for the *current* thread (does not fork).
5. **Fork / Trim** → advanced thread tools; primary action remains New Chat.

## Grounding architecture

Citations arrive as `memory_citations` (and document/connection payloads mixed in).
`jarvisRenderMemoryCitations` renders **buttons**; `AriaChatOS.openCitation` routes to:

- Memory browser
- Documents search
- Connections search
- Projects / Planner / Journal as appropriate
- Knowledge Briefs distinguished via toast + Documents

**Never silent.** Provenance stays visible.

## Context scoping

Composer supports `@kind:` autocomplete (`@memory`, `@document`, `@project`,
`@connection`, `@planner`, `@calendar`, `@journal`, `@knowledge`, `@gallery`).

Active scopes render as removable chips and are prefixed into the sent prompt as
`[Context: @kind:id …]` so the model and tools retain IDs.

## Reply actions

Assistant bubbles may expose contextual actions only when relevant:

- Regenerate / Retry / Edit prompt (core)
- Planner task · Stage Memory candidate · Connections review · Journal

Memory and Connections are **staged for review** — Chat never auto-writes ACM or the graph.

## Streaming

- Primary path: `sendMessage` SSE/token events
- Mini Chat registers `onToken` / `onDone`
- Model chip changes **do not** abort an active stream (apply on next message)

## Voice

Single mental model:

1. **Hold mic / PTT** → talk (Whisper / local STT)
2. **Read aloud** → TTS for replies
3. **Mute TTS** synced with Read aloud
4. Wake word remains in the status strip

## Vision & attachments

- Paste image into composer attaches immediately
- Drop image / document / audio / data onto Chat
- Overlay copy: “Drop to attach (image, document, audio, or data)”
- Attach button accept list includes docs/audio/data

## Integrations

| Surface | Behavior |
|---------|----------|
| Documents Ask Aria | Auto-send + `@document` context + return hint |
| Planner Ask Aria | Auto-send + `@planner` context |
| Mission Control / Command palette | `jarvisSendToChat` → auto-send |
| Coding / Gallery / Browser | Same Ask Aria entry |
| Export | Existing Export MD / PDF |
| Memory / Connections | Stage only from reply actions |

## Accessibility

- `#messages`: `role="log"` + `aria-live="polite"`
- `#progressBar`: `role="status"` + `aria-live="polite"`
- Voice strip already live
- Reduced-motion rules for chips/actions
- Themed dialogs replace blocking browser prompts

## Testing

```bash
./venv/bin/pytest \
  tests/test_chat_session_branches.py \
  tests/test_chat_api.py \
  tests/test_chat_cancel.py \
  tests/test_chat_conversation.py \
  tests/test_chat_assistant.py \
  tests/test_chat_router.py \
  tests/test_chat_config_memory.py \
  tests/test_product_ui_api_wiring.py -q
```

Coverage includes: unified New Chat, pin toggle, API `/api/chat/new`,
grounding citation plumbing (no Memory auto-write), static Chat OS contract,
paste/drop composer support, UI wiring for New Chat / model chip / dialogs.

## Future roadmap

- Deep-link citation IDs into Memory/Documents row selection
- Conversation summary card + searchable thread archive
- Continuous duplex voice refinements without dual Speak/Mute confusion
- Split large conversation router further behind behavior modules
- Context chip entity picker (search-as-you-type for Memory/Documents IDs)

## Design guardrails (always)

Does this strengthen Chat as the AI OS? Reduce friction? Improve trust?
Preserve local-first, Memory authority, Connections provenance?
Avoid becoming a ChatGPT clone?

If not — redesign it.
