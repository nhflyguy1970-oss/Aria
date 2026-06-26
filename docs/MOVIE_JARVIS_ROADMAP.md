# Movie Jarvis — Deep Dive & Upgrade Roadmap

Analysis date: 2026-06-14. Hardware context: RX 7600 · 8GB VRAM · local Ollama · Jarvis 3.x.

The **Iron Man build order is complete** (trust, briefing, documents, upgrade wizard, LAN, HA, environment API). What remains is mostly **presence**, **proactive UI**, and **polish** — not missing core backends.

---

## What you already have (strong)

| Pillar | Highlights |
|--------|------------|
| **Trust** | Failure/strategy memory, forget/correct, test isolation, context gating, memory browser |
| **Chief-of-staff** | Morning briefing (weather, tasks, news, ICS, HA), bullet journal, PDF/DOCX + library RAG |
| **Lab manager** | Coding agent, propose/apply/undo, upgrade wizard + rollback, git/LSP/Cursor, queued fix-tests |
| **Environment** | GPU/VRAM routing, services watchdog, HA chat + webhook, LAN + API key |
| **Creative lab** | ComfyUI, image/video/meme, Song Studio, AE-5 audio stack |

---

## Gap vs movie Jarvis (honest)

| Movie trait | Your gap |
|-------------|----------|
| Calm voice always there | TTS exists but manual; wake word buried in Audio Advanced |
| Knows the lab without asking | `/api/environment` exists; not visible in main UI |
| Briefing when you arrive | Launch message scrolls away; no pinned “today” card |
| Controls the house naturally | HA works in chat; no entity browser or tap-to-control |
| Witty, brief, confident | Personalities exist; no auto-brevity from learned prefs |
| Upgrades with Tony’s OK | Wizard done; restart still manual |

**Cannot replicate on 8GB:** holograms, swarms, 4K video, always-on satellite awareness, silent self-repair without approval.

---

## Prioritized upgrades

### Tier 1 — Presence & daily feel (highest movie impact)

1. **Global push-to-talk → local Whisper** — One voice path; end chat mic vs Audio tab confusion.
2. **“Speak replies” toggle** — Auto Piper/XTTS after assistant messages.
3. **Wake word pill in chat header** — Status + start/stop without opening Audio Advanced.
4. **Pinned briefing card** — Today’s schedule/tasks stay above composer after launch.
5. **Collapsible sidebar sections** — Reduce scroll; fold Coding / Models when unused.
6. **Environment strip in header** — Profile, free VRAM, offline services from `/api/environment`.
7. **Context-aware suggestion chips** — Morning → briefing; PDF attached → summarize; file open → run tests.
8. **Unified Voice settings** — Mic, Whisper model, wake model, TTS voice in one panel.
9. **Default wake STT to `small`** — `JARVIS_WAKEWORD_WHISPER_MODEL` defaults to `tiny` today.
10. **Module chips → filter or remove** — Click to filter suggestions, or drop decorative chips.

### Tier 2 — Chief-of-staff & trust

11. **Document library tab** — Browse `data/documents/`, reindex, attach (RAG backend exists).
12. **Calendar ICS wizard in Journal** — Guided paste + test for `JARVIS_ICS_URL`.
13. **Memory citations in chat** — Footer: “From memory · date · type”.
14. **Auto-strategy from corrections** — Promote `memory_correct` to behavior rules.
15. **Tool-outcome memory** — Record “warranty PDF → document_search worked”.
16. **Knowledge topic browser** — View `data/knowledge/*.md` from Memory tab.
17. **Briefing ↔ journal task sync widget** — Same open tasks in Journal and briefing card.
18. **PDF page picker in attach preview** — Surface `pdf_page` for clause work.
19. **Proactive task nudge** — Optional desktop notify when open tasks > N after 10am.
20. **Offline/Gaming profile banner** — “Web search off” in header when profile active.

### Tier 3 — Lab manager & environment

21. **Coding job cancel** — API + Stop for queued agent/fix-tests jobs.
22. **Parallel coding workers** — `JARVIS_CODING_WORKERS` like media parallel workers.
23. **Live agent-step stream** — Show coding agent steps in bubble while running.
24. **Upgrade “Restart Jarvis” button** — One-click after `requires_restart`.
25. **HA entity browser** — List entities; tap on/off (reduce chat ambiguity).
26. **Scene composer UI** — Edit “heading out” scenes without env strings only.
27. **Service recovery buttons** — Restart Ollama / ComfyUI / HA from Services panel.
28. **Gallery “last good settings”** — Surface `resource_router` last success for image/video.
29. **Strict VRAM gate** — Block heavy media enqueue below threshold unless confirmed.
30. **Trust health card** — Disk free, last scrub, test-junk filter status visible.

### Tier 4 — Polish & general good ideas

31. **Consistent Jarvis voice (XTTS / tuned Piper)** — Same voice for read-aloud + wake responses.
32. **Compact always-on HUD** — Mini window: status + PTT + last transcript.
33. **Action history filters** — By module (HA, coding, document).
34. **Chat mic → server Whisper** — Route header mic through faster-whisper, not browser STT.
35. **Native notification actions** — “Run briefing” / “Dismiss” on desktop notify.
36. **Smart home setup wizard** — Geeni/Wyze → Smart Life / ha-wyzeapi checklist in UI.
37. **Session export with memory snapshot** — MD/PDF includes relevant memories used.
38. **Keyboard shortcuts panel** — Discoverability for power users.
39. **Theme: “Jarvis blue”** — Optional accent palette closer to movie aesthetic.
40. **Mobile sidebar sections** — Accordion on phone; same gray boxes, one open at a time.

---

## General improvements (not movie-specific, still worth it)

- **Settings modal** — Single place for env-backed options instead of sidebar + env file.
- **Error toast stack** — Non-blocking errors instead of only chat bubbles.
- **Faster cold start** — Lazy-load ComfyUI; show briefing while models warm.
- **Integration test suite for HA** — Mock HA API in CI.
- **Plugin hook for custom chat actions** — `data/plugins/` without editing router.
- **Encrypted backup option** — For journal + memory export.
- **Rate-limit visibility** — Show when Ollama/API is throttling.
- **Compare model A/B in chat** — Side-by-side for same prompt (dev tool).

---

## UI fixes applied (2026-06-14)

- Sidebar split into **gray section boxes**: Mode, Capabilities, Services, Smart home, Chat & data, Coding, Models, Footer.
- Capability chips in **2-column grid** to fit narrow sidebar.
- HA token area **compact** (3 rows, max-height).
- Removed **duplicate Free VRAM** button from Services (kept under Models).
- Fixed overflow: `box-sizing`, `min-width: 0`, compact button rows.

Hard-refresh after pull: **Ctrl+Shift+R**.

---

## Suggested build order (next 4 sprints)

1. **Sprint A:** PTT + speak replies + wake pill + pinned briefing  
2. **Sprint B:** Document library tab + HA entity browser + service restart buttons  
3. **Sprint C:** Coding job cancel + live agent stream + upgrade restart button  
4. **Sprint D:** Collapsible sections + settings modal + profile banner  

Pick any tier and say “implement Tier 1” to continue.
