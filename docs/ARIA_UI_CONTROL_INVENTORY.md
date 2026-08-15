# ARIA UI Control Inventory

Generated: 2026-08-10T20:25:25.083966+00:00

Primary evidence: live browser recursive discovery (`/tmp/aria-exp-accept/discover.json`).
This document proves interface exploration, not merely replay of the prior 110 test IDs.

- Rooms discovered: **34**
- Controls discovered (default states): **794**
- Tabs discovered: **22**
- Menu/revealer-like controls: **8**
- Front Door destinations (expanded): **37**
- Candidates queued: **673**

## Room: `actions` — What happened

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('actions') / Front Door
- **Preview:** Aria · Action history Listening quietly Action history All modules Coding Home Assistant Documents Image Clear Chat Audit Mission Control 2026-08-10T19:27:18 api http /api/connections/home 2026-08-10T
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Clear
- `button`/button — Open Chat
- `button`/button — Open System audit
- `button`/button — Open Mission Control
- `select`/- — All modules Coding Home Assistant Documents Image

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-019` — Clear → **PASS**
- `EXP-020` — Open Chat → **FAIL**
- `EXP-021` — Open System audit → **FAIL**
- `EXP-022` — Open Mission Control → **FAIL**
- `EXP-023` — All modules Coding Home Assistant Documents Image → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `audio` — Sound

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('audio') / Front Door
- **Preview:** Aria · Audio studioListening quietly Audio Voice Journal ✓ Whisper (medium) ✓ ffmpeg ✓ Piper · ♫ transformers 🔊 alsa_output.pci-0000_05_00.0.iec958-stereo 🎤 Microphone · 100% ✓ Record & transcribe Cha
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Open Voice settings
- `button`/button — Open Bullet Journal
- `button`/button — Test mic (2s)
- `button`/button — Record only
- `button`/button — Record + transcribe
- `button`/button — Play on Sound Blaster
- `button`/button — Copy
- `button`/button — Send to chat
- `button`/button — Add to journal
- `button`/button — Summarize
- `button`/button — Apply trim
- `button`/button — Normalize
- `button`/button — Edit
- `button`/button — Convert
- `button`/button — Transcribe upload
- `button`/button — Transcribe path
- `button`/button — Generate speech
- `button`/button — Generate + play
- `button`/button — Upload
- `button`/button — Transform genre
- `button`/button — Generate song
- `button`/button — Mix tracks
- `button`/button — Make my voice a song
- `button`/button — Preview trim
- `button`/button — Diarize speakers
- `button`/button — Stream transcribe file
- `button`/button — Detect language
- `button`/button — Voice
- `button`/button — Music
- `button`/button — Flat
- `button`/button — Process file
- `button`/button — Install PipeWire filter configs
- `button`/button — Start wake word
- `button`/button — Stop wake word
- `button`/button — Search
- `button`/button — Transcribe all
- `button`/button — Generate music
- `button`/button — Play in player
- `button`/button — Delete recording_ptt_20260730_161305_ptt_raw.wav
- `button`/button — Delete live_20260730_164009_raw.wav
- `button`/button — Delete recording_20260730_173355.wav
- `button`/button — Delete recording_20260730_172933.wav
- `button`/button — Delete recording_20260730_171640.wav
- `button`/button — Delete recording_20260730_152137.wav
- `button`/button — Delete live_20260726_185623.wav
- `button`/button — Delete live_20260726_165807.wav
- `button`/button — Delete ware_Foundation_2_About_the_Python_Sof.wav
- `button`/button — Delete 1_For_more_about_the_foundation_s_missio.wav
- `button`/button — Delete The_official_website_of_the_Python_Softw.wav
- `button`/button — Delete the_RTX_3090.wav
- `button`/button — Delete Stored_via_ACM_exact_acceptance_token.wav
- `button`/button — Delete provide_a_list_or_more_details_I_can_he.wav
- `button`/button — Delete For_example_you_might_have_things_like.wav
- `button`/button — Delete Sure_To_help_you_check_your_fly_tying_m.wav
- `button`/button — Open editor
- `button`/button — Ask Chat
- `input`/number — 5
- `input`/text — Path to audio file…
- `input`/text — e.g. fade in, make louder, trim first 5s
- `input`/text — data/audio/edited/out.mp3
- `input`/file — audioUploadFile
- `input`/text — Or path under data/…
- `input`/text — Song path or use recent / upload
- `input`/text — Target genre / style
- `input`/number — 30
- `input`/text — Song topic e.g. summer road trip
- `input`/text — Genre
- `input`/text — Mood
- `input`/number — 30
- `input`/text — Backing track path (music bed)
- `input`/text — Vocal path (or use last recording)
- `input`/number — 2
- `input`/text — Song title (optional)
- `input`/text — Style
- `input`/text — Genre
- `input`/number — 30
- `input`/search — Search indexed transcripts…
- `input`/number — 10
- `textarea`/- — Text for Piper or espeak…
- `textarea`/- — Lyrics (optional — auto-transcribed from recording)
- `textarea`/- — One path per line under data/…
- `textarea`/- — Calm piano, 90 BPM…
- `select`/- — tiny base small medium large
- `select`/- — auto en es fr de it pt ja ko zh ru ar hi
- `select`/- — 0.8× 0.9× 1× 1.1× 1.2×
- `select`/- — Rear desk mic (combo jack) Front gaming headset (combo jack)
- `select`/- — alsa_input.pci-0000_05_00.0.analog-stereo USB Microphone (mono-fallback) (webcam
- `select`/- — effect_input.jarvis_ae5_gaming effect_input.jarvis_ae5_music effect_input.jarvis
- `select`/- — 100% 125% 150% 175% 200% 250%
- `select`/- — Fixed duration VAD (trim silence) Push-to-talk (hold button) Live (VU + streamin
- `select`/- — EQ applied when ARIA plays audio
- `select`/- — Live system EQ via PipeWire
- `label`/- — Whisper model tiny base small medium large
- `label`/- — Language auto en es fr de it pt ja ko zh ru ar hi
- `label`/- — Piper speed 0.8× 0.9× 1× 1.1× 1.2×
- `label`/- — Mic setup Rear desk mic (combo jack) Front gaming headset (combo jack)
- `label`/- — Microphone alsa_input.pci-0000_05_00.0.analog-stereo USB Microphone (mono-fallba
- `label`/- — Output effect_input.jarvis_ae5_gaming effect_input.jarvis_ae5_music effect_input
- `label`/- — PipeWire gain 100% 125% 150% 175% 200% 250%
- `label`/- — Record mode Fixed duration VAD (trim silence) Push-to-talk (hold button) Live (V
- … +5 more

### TABS
- (none observed)

### MENUS
- Delete 1_For_more_about_the_foundation_s_missio.wav
- Delete provide_a_list_or_more_details_I_can_he.wav

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Open Voice settings**: 0 controls revealed
- After **Add to journal**: 0 controls revealed
- After **Edit**: 0 controls revealed
- After **Install PipeWire filter configs**: 0 controls revealed
- After **Delete 1_For_more_about_the_foundation_s_missio.wav**: 0 controls revealed
- After **Delete provide_a_list_or_more_details_I_can_he.wav**: 0 controls revealed
- After **Open editor**: 0 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-014` — status bar → **PASS**
- `EXP-024` — Open Voice settings → **FAIL**
- `EXP-025` — Open Bullet Journal → **FAIL**
- `EXP-026` — Test mic (2s) → **PASS**
- `EXP-027` — Record only → **PASS**
- `EXP-028` — Record + transcribe → **PASS**
- `EXP-029` — Play on Sound Blaster → **PASS**
- `EXP-030` — Copy → **PASS**
- `EXP-031` — Add to journal → **PASS**
- `EXP-032` — Summarize → **PASS**
- `EXP-033` — Apply trim → **PASS**
- `EXP-034` — Normalize → **PASS**
- `EXP-035` — Edit → **PASS**
- `EXP-183` — Convert → **PASS**
- `EXP-184` — Transcribe upload → **PASS**
- `EXP-185` — Transcribe path → **PASS**
- `EXP-186` — Generate speech → **PASS**
- `EXP-187` — Generate + play → **PASS**
- `EXP-188` — Upload → **PASS**
- `EXP-189` — Transform genre → **PASS**
- `EXP-190` — Generate song → **PASS**
- `EXP-579` — Journal → **PASS**
- `EXP-580` — Start live record → **PASS**
- `EXP-581` — Stop + transcribe → **PASS**
- `EXP-582` — Record (VAD) → **PASS**
- `EXP-583` — VAD + transcribe → **PASS**
- `EXP-584` — Cancel job → **PASS**
- `EXP-585` — Install live EQ → **PASS**
- `EXP-586` — recording_ptt_20260730_161305_ptt_raw.wav → **PASS**
- `EXP-587` — live_20260730_164009_raw.wav → **PASS**
- `EXP-588` — recording_20260730_173355.wav → **PASS**
- `EXP-589` — recording_20260730_172933.wav → **PASS**
- `EXP-590` — recording_20260730_171640.wav → **PASS**
- `EXP-591` — recording_20260730_152137.wav → **PASS**
- `EXP-592` — live_20260726_185623.wav → **PASS**
- `EXP-593` — live_20260726_165807.wav → **PASS**
- `EXP-594` — ware_Foundation_2_About_the_Python_Sof.wav → **PASS**
- `EXP-595` — 1_For_more_about_the_foundation_s_missio.wav → **PASS**
- `EXP-596` — The_official_website_of_the_Python_Softw.wav → **PASS**
- `EXP-597` — the_RTX_3090.wav → **PASS**
- `EXP-598` — Stored_via_ACM_exact_acceptance_token.wav → **PASS**
- `EXP-599` — provide_a_list_or_more_details_I_can_he.wav → **PASS**
- `EXP-600` — For_example_you_might_have_things_like.wav → **PASS**
- `EXP-601` — Sure_To_help_you_check_your_fly_tying_m.wav → **PASS**
- `EXP-602` — recording_20260610_194808_edited.wav → **PASS**
- `EXP-603` — Delete recording_20260610_194808_edited.wav → **PASS**
- `EXP-BUG-002` — EXP-BUG-002 → **FAIL**

### UNTESTED
- Send to chat
- Mix tracks
- Make my voice a song
- Preview trim
- Diarize speakers
- Stream transcribe file
- Detect language
- Voice
- Music
- Flat
- Process file
- Install PipeWire filter configs
- Start wake word
- Stop wake word
- Search
- Transcribe all
- Generate music
- Play in player
- Delete recording_ptt_20260730_161305_ptt_raw.wav
- Delete live_20260730_164009_raw.wav
- Delete recording_20260730_173355.wav
- Delete recording_20260730_172933.wav
- Delete recording_20260730_171640.wav
- Delete recording_20260730_152137.wav
- Delete live_20260726_185623.wav
- Delete live_20260726_165807.wav
- Delete ware_Foundation_2_About_the_Python_Sof.wav
- Delete 1_For_more_about_the_foundation_s_missio.wav
- Delete The_official_website_of_the_Python_Softw.wav
- Delete the_RTX_3090.wav
- Delete Stored_via_ACM_exact_acceptance_token.wav
- Delete provide_a_list_or_more_details_I_can_he.wav
- Delete For_example_you_might_have_things_like.wav
- Delete Sure_To_help_you_check_your_fly_tying_m.wav
- Open editor
- Ask Chat

---

## Room: `audit` — Audit

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('audit') / Front Door
- **Preview:** Aria · System auditListening quietly System Audit Loading audit… Mission Control Actions Run audit 14 phases: OS · packages · storage/SMART · memory · hardware/sensors · GPU · services/desktop · conta
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Open Mission Control
- `button`/button — Open Actions checklist
- `button`/button — Run audit (disabled)

### TABS
- (none observed)

### MENUS
- Open Actions checklist

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Open Actions checklist**: 0 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-036` — Open Mission Control → **FAIL**
- `EXP-037` — Open Actions checklist → **FAIL**
- `EXP-920` — run → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `automation` — Skills

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('automation') / Front Door
- **Preview:** Aria · Automation loft Listening quietly Automation Home Orchestrates schedules, rules, skills, and workflows. Not Job Center, Activity Center, Mission Control, or Home Assistant. Refresh Pause all Re
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Pause all
- `button`/button — Resume
- `button`/button — New rule
- `button`/button — Specialist team
- `button`/button — Specialists
- `button`/button — Team history
- `button`/button — View Paths
- `button`/button — Webhook
- `button`/button — Export
- `button`/button — Import
- `button`/button — Draft from NL
- `button`/button — NL draft
- `button`/button — Export
- `button`/button — Propose team
- `button`/button — Gallery
- `button`/button — History
- `input`/search — Search automation
- `input`/text — Natural language automation
- `input`/search — Search pipelines
- `input`/checkbox — on
- `select`/- — Sort pipelines
- `label`/- — Favorites

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **New rule**: 23 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-038` — Refresh → **PASS**
- `EXP-039` — Pause all → **PASS**
- `EXP-040` — Resume → **PASS**
- `EXP-041` — New rule → **PASS**
- `EXP-042` — Specialist team → **PASS**
- `EXP-043` — Specialists → **PASS**
- `EXP-044` — Team history → **PASS**
- `EXP-045` — View Paths → **PASS**
- `EXP-046` — Webhook → **PASS**
- `EXP-047` — Export → **PASS**
- `EXP-048` — Import → **PASS**
- `EXP-049` — Draft from NL → **PASS**
- `EXP-191` — NL draft → **PASS**
- `EXP-192` — Propose team → **PASS**
- `EXP-193` — Gallery → **PASS**
- `EXP-194` — History → **PASS**
- `EXP-195` — Search automation → **PASS**
- `EXP-196` — Natural language automation → **PASS**
- `EXP-197` — Search pipelines → **PASS**
- `EXP-198` — on → **PASS**
- `EXP-534` — Run → **PASS**
- `EXP-535` — Dry run → **PASS**
- `EXP-536` — Enable → **PASS**
- `EXP-537` — Edit → **PASS**
- `EXP-538` — Mute → **PASS**
- `EXP-539` — Delete → **PASS**
- `EXP-540` — Schedule → **PASS**
- `EXP-541` — Create → **PASS**
- `EXP-542` — Details → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `browser` — The web

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('browser') / Front Door
- **Preview:** Aria · Browser Listening quietly Browser Live web interaction agent — Playwright navigation, screenshots, DOM/Vision tasks. Not a full Chrome replacement. Documents store knowledge; Chat converses. Re
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Projects
- `button`/button — Job Center
- `button`/button — Coding
- `button`/button — Open Memory
- `button`/button — Open Documents
- `button`/button — Open Chat
- `button`/button — Detach browser panel
- `button`/button — Open
- `button`/button — Bookmark current URL
- `button`/button — Screenshot
- `button`/button — Install Playwright
- `button`/button — Refresh
- `button`/button — Pause
- `button`/button — Resume
- `button`/button — Takeover
- `button`/button — Stop
- `button`/button — Save to Documents
- `button`/button — Screenshot → Coding proposal
- `button`/button — Run
- `button`/button — Queue in Job Center
- `input`/url — URL to open
- `input`/text — Browser agent goal
- `select`/- — Agent mode

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-050` — Refresh → **PASS**
- `EXP-051` — Projects → **PASS**
- `EXP-052` — Job Center → **PASS**
- `EXP-053` — Coding → **PASS**
- `EXP-054` — Open Memory → **FAIL**
- `EXP-055` — Open Documents → **FAIL**
- `EXP-056` — Open Chat → **FAIL**
- `EXP-057` — Detach browser panel → **PASS**
- `EXP-058` — Open → **FAIL**
- `EXP-059` — Bookmark current URL → **FAIL**
- `EXP-060` — Screenshot → **FAIL**
- `EXP-061` — Install Playwright → **FAIL**
- `EXP-199` — Pause → **PASS**
- `EXP-200` — Resume → **PASS**
- `EXP-201` — Takeover → **PASS**
- `EXP-202` — Stop → **PASS**
- `EXP-203` — Save to Documents → **PASS**
- `EXP-204` — Screenshot → Coding proposal → **FAIL**
- `EXP-205` — Run → **PASS**
- `EXP-206` — Queue in Job Center → **FAIL**
- `EXP-604` — Memory → **PASS**
- `EXP-605` — Documents → **PASS**
- `EXP-606` — Chat → **PASS**
- `EXP-607` — Overview → **PASS**
- `EXP-608` — Session → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `calendar` — The week

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('calendar') / Front Door
- **Preview:** Aria · Wall calendar Listening quietly Calendar Scheduled commitments · use Planner for today’s actionable work · Journal for notes ← Prev August 2026 Next → Today Month Week Agenda Timeline All sourc
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Planner
- `button`/button — Journal
- `button`/button — Previous
- `button`/button — Next
- `button`/button — Jump to today (T)
- `button`/button — Month
- `button`/button — Week
- `button`/button — Agenda
- `button`/button — Timeline
- `button`/button — Open Planner
- `button`/button — Open Bullet Journal
- `button`/button — Open Documents
- `button`/button — 2026-08-01
- `button`/button — 2026-08-02
- `button`/button — 2026-08-03
- `button`/button — 2026-08-04
- `button`/button — 2026-08-05
- `button`/button — 2026-08-06
- `button`/button — 2026-08-07
- `button`/button — 2026-08-08
- `button`/button — 2026-08-09
- `button`/button — 2026-08-10
- `button`/button — 2026-08-11
- `button`/button — 2026-08-12
- `button`/button — 2026-08-13
- `button`/button — 2026-08-14
- `button`/button — 2026-08-15
- `button`/button — 2026-08-16
- `button`/button — 2026-08-17
- `button`/button — 2026-08-18
- `button`/button — 2026-08-19
- `button`/button — 2026-08-20
- `button`/button — 2026-08-21
- `button`/button — 2026-08-22
- `button`/button — 2026-08-23
- `button`/button — 2026-08-24
- `button`/button — 2026-08-25
- `button`/button — 2026-08-26
- `button`/button — 2026-08-27
- `button`/button — 2026-08-28
- `button`/button — 2026-08-29
- `button`/button — 2026-08-30
- `button`/button — 2026-08-31
- `button`/button — Open in Journal
- `button`/button — Open Planner
- `button`/button — Check conflicts
- `button`/button — Meeting prep
- `button`/button — Focus windows
- `button`/button — Add to day
- `button`/button — Parse & confirm
- `button`/button — Save day note
- `button`/button — Remove work block
- `button`/button — ghost-btn tiny cal-ws-add
- `button`/button — calWorkSaveBtn
- `button`/button — calendarIcsTestBtn
- `button`/button — calendarIcsSaveBtn
- `button`/button — calendarIcsRefreshBtn
- `button`/button — calendarVisionBtn
- `button`/button — calendarMemoryBtn
- `button`/button — calendarHaMeetingBtn
- `input`/search — Search calendar
- `input`/time — Event time
- `input`/text — Event description
- `input`/text — Natural language schedule
- `input`/checkbox — on
- `input`/time — 08:30
- `input`/time — 17:00
- `input`/text — Label
- `input`/url — https://…/basic.ics
- `textarea`/- — Fly fishing, birthday, travel…
- `select`/- — Filter by source
- `select`/- — Entry type
- `select`/- — Save target
- `summary`/- — Work schedule (weekly)
- `summary`/- — External calendar (ICS)
- `summary`/- — AI & Home
- `label`/- — memory-setting

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Add to day**: 40 controls revealed
- After **ghost-btn tiny cal-ws-add**: 40 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-062` — Planner → **PASS**
- `EXP-063` — Journal → **PASS**
- `EXP-064` — Previous → **PASS**
- `EXP-065` — Next → **PASS**
- `EXP-066` — Jump to today (T) → **FAIL**
- `EXP-067` — Month → **PASS**
- `EXP-068` — Week → **PASS**
- `EXP-069` — Agenda → **PASS**
- `EXP-070` — Timeline → **PASS**
- `EXP-071` — Open Planner → **PASS**
- `EXP-072` — Open Bullet Journal → **FAIL**
- `EXP-073` — Open Documents → **FAIL**
- `EXP-207` — 2026-08-01 → **PASS**
- `EXP-208` — 2026-08-02 → **PASS**
- `EXP-209` — 2026-08-03 → **PASS**
- `EXP-210` — 2026-08-04 → **PASS**
- `EXP-211` — 2026-08-05 → **PASS**
- `EXP-212` — 2026-08-06 → **PASS**
- `EXP-213` — 2026-08-07 → **PASS**
- `EXP-214` — 2026-08-08 → **PASS**
- `EXP-419` — Today → **PASS**
- `EXP-420` — Documents → **PASS**
- `EXP-421` — Add commitment → **PASS**
- `EXP-422` — Ask Chat → **PASS**

### UNTESTED
- 2026-08-09
- 2026-08-10
- 2026-08-11
- 2026-08-12
- 2026-08-13
- 2026-08-14
- 2026-08-15
- 2026-08-16
- 2026-08-17
- 2026-08-18
- 2026-08-19
- 2026-08-20
- 2026-08-21
- 2026-08-22
- 2026-08-23
- 2026-08-24
- 2026-08-25
- 2026-08-26
- 2026-08-27
- 2026-08-28
- 2026-08-29
- 2026-08-30
- 2026-08-31
- Open in Journal
- Check conflicts
- Meeting prep
- Focus windows
- Add to day
- Parse & confirm
- Save day note
- Remove work block
- ghost-btn tiny cal-ws-add
- calWorkSaveBtn
- calendarIcsTestBtn
- calendarIcsSaveBtn
- calendarIcsRefreshBtn
- calendarVisionBtn
- calendarMemoryBtn
- calendarHaMeetingBtn

---

## Room: `capabilities` — Extensions

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('capabilities') / Front Door
- **Preview:** Aria · Capabilities Listening quietly Capabilities Unified management for everything that extends Aria. Products stay product owners — Capabilities only extends them. Refresh Load enabled Diagnostics 
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Load enabled
- `button`/button — Diagnostics
- `input`/search — Search capabilities…
- `select`/- — Filter by layer
- `select`/- — Filter by category
- `select`/- — Filter by trust
- `summary`/- — Advanced options

### TABS
- (none observed)

### MENUS
- Advanced options

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Advanced options**: 8 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-074` — Refresh → **PASS**
- `EXP-075` — Load enabled → **PASS**
- `EXP-076` — Diagnostics → **PASS**
- `EXP-077` — Search capabilities… → **FAIL**
- `EXP-078` — Filter by layer → **PASS**
- `EXP-079` — Filter by category → **PASS**
- `EXP-080` — Filter by trust → **PASS**
- `EXP-919` — new → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `chat` — Conversation

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('chat') / Front Door
- **Preview:** Aria is here Listening quietly NEARBY New conversation fresh Place something here attach Model Chat model: (default) Read aloud off Voice when speaking Open the front door Ctrl+K Fork thread branch A 
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — More
- `button`/button — Good morning
- `button`/button — What should we work on?
- `button`/button — Just listen for a bit
- `button`/button — Hold to talk
- `button`/submit — Send
- `textarea`/- — Say anything…

### TABS
- (none observed)

### MENUS
- More

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **More**: 14 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-003` — composer Send → **PASS**
- `EXP-004` — Stop → **FAIL**
- `EXP-005` — More menu → **PASS**
- `EXP-081` — More → **PASS**
- `EXP-082` — Good morning → **FAIL**
- `EXP-083` — What should we work on? → **FAIL**
- `EXP-084` — Just listen for a bit → **FAIL**
- `EXP-085` — Say anything… → **FAIL**
- `EXP-179` — research current info → **PASS**
- `EXP-374` — Skip — open UI now → **PASS**
- `EXP-375` — Menu → **PASS**
- `EXP-376` — Wake: — → **PASS**
- `EXP-377` — Cursor · not synced → **PASS**
- `EXP-378` — New Chat → **PASS**
- `EXP-379` — Fork → **PASS**
- `EXP-380` — Trim → **PASS**
- `EXP-381` — Clear Main → **PASS**
- `EXP-382` — Voice input → **PASS**
- `EXP-383` — Read aloud → **PASS**
- `EXP-384` — Compare → **PASS**
- `EXP-385` — Webcam → **PASS**
- `EXP-386` — New conversation fresh → **FAIL**
- `EXP-387` — Place something here attach → **FAIL**
- `EXP-388` — Read aloud off → **FAIL**
- `EXP-389` — Voice when speaking → **FAIL**
- `EXP-390` — Open the front door Ctrl+K → **FAIL**
- `EXP-391` — Fork thread branch → **FAIL**
- `EXP-392` — Dismiss → **PASS**
- `EXP-393` — Stop responding → **PASS**
- `EXP-900` — hold to talk → **PASS**
- `EXP-901` — send → **PASS**

### UNTESTED
- Hold to talk
- Send

---

## Room: `coding` — Current work

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('coding') / Front Door
- **Preview:** Aria · Engineering studio Listening quietly Coding Propose → Review → Apply → Undo → Verify. Projects identify workspaces; Job Center tracks execution; Models configures the coding model. Refresh Proj
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Workspace identity
- `button`/button — Live coding jobs
- `button`/button — Coding model role

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-017` — propose UI → **PASS**
- `EXP-086` — Refresh → **PASS**
- `EXP-087` — Workspace identity → **FAIL**
- `EXP-088` — Live coding jobs → **FAIL**
- `EXP-089` — Coding model role → **FAIL**
- `EXP-435` — Projects → **PASS**
- `EXP-436` — Job Center → **PASS**
- `EXP-437` — Models → **PASS**
- `EXP-494` — Overview → **PASS**
- `EXP-495` — Proposals → **PASS**
- `EXP-496` — History → **PASS**
- `EXP-497` — Jobs → **PASS**
- `EXP-498` — LSP & Git → **PASS**
- `EXP-499` — Preferences → **PASS**
- `EXP-500` — Advanced → **PASS**
- `EXP-501` — Analyze & propose → **PASS**
- `EXP-502` — Plan & propose → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `connections` — Relationships

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('connections') / Front Door
- **Preview:** Aria · Connections Listening quietly Connections Relationship explorer — models how things relate. Not Memory, not Documents, not Knowledge Briefs. ACM remains cognitive source of truth; the graph mir
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Shortcuts
- `button`/button — Search
- `button`/button — Browse
- `button`/button — New (N)
- `button`/button — Import
- `button`/button — Cleanup
- `button`/button — Assistant
- `button`/button — Undo
- `button`/button — Clear
- `input`/search — Search connections
- `select`/- — Search mode
- `label`/- — Mode All Entities Relationships People Places Organizations Concepts Project nam

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **New (N)**: 12 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-090` — Shortcuts → **FAIL**
- `EXP-091` — Search → **PASS**
- `EXP-092` — Browse → **PASS**
- `EXP-093` — New (N) → **PASS**
- `EXP-094` — Import → **PASS**
- `EXP-095` — Cleanup → **PASS**
- `EXP-096` — Assistant → **PASS**
- `EXP-097` — Undo → **PASS**
- `EXP-098` — Clear → **PASS**
- `EXP-099` — Search connections → **PASS**
- `EXP-100` — Search mode → **PASS**
- `EXP-917` — cancel → **PASS**
- `EXP-918` — close → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `documents` — Knowledge

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('documents') / Front Door
- **Preview:** Aria · Private library Listening quietly Documents Personal document intelligence — local files, grounded search, Memory candidates. Not Drive, SharePoint, or Notion. Documents = library · Knowledge =
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Shortcuts
- `button`/button — Import
- `button`/button — Search
- `button`/button — Rebuild Search Index
- `button`/button — Briefing
- `button`/button — Ask Aria
- `button`/button — Clear
- `button`/button — Upload
- `button`/button — Import Folder
- `button`/button — Ask Aria
- `button`/button — Summarize
- `button`/button — Learn → candidates
- `button`/button — Rebuild Search Index
- `button`/button — Document Briefing
- `button`/button — Open Memory
- `button`/button — Open Projects
- `button`/button — test
- `button`/button — resume
- `button`/button — warranty
- `button`/button — readme
- `button`/button — aria
- `button`/button — memory
- `button`/button — ship
- `button`/button — doc
- `input`/text — Folder path
- `input`/search — Search documents
- `div`/button — Drop files to upload
- `label`/- — Upload

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-009` — text search vs file input → **PASS**
- `EXP-101` — Shortcuts → **FAIL**
- `EXP-102` — Import → **PASS**
- `EXP-103` — Search → **PASS**
- `EXP-104` — Rebuild Search Index → **PASS**
- `EXP-105` — Briefing → **PASS**
- `EXP-106` — Clear → **PASS**
- `EXP-107` — Upload → **PASS**
- `EXP-108` — Import Folder → **FAIL**
- `EXP-109` — Summarize → **PASS**
- `EXP-110` — Learn → candidates → **FAIL**
- `EXP-111` — Document Briefing → **FAIL**
- `EXP-112` — Open Memory → **FAIL**
- `EXP-215` — Open Projects → **PASS**
- `EXP-216` — test → **FAIL**
- `EXP-217` — resume → **FAIL**
- `EXP-218` — warranty → **FAIL**
- `EXP-219` — readme → **FAIL**
- `EXP-220` — aria → **FAIL**
- `EXP-221` — memory → **FAIL**
- `EXP-222` — ship → **FAIL**
- `EXP-414` — Ask → **PASS**
- `EXP-907` — ask aria → **PASS**
- `EXP-908` — cancel → **PASS**
- `EXP-909` — close → **PASS**

### UNTESTED
- Ask Aria
- Ask Aria
- doc

---

## Room: `flytying` — The fly

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('flytying') / Front Door
- **Preview:** Aria · Streamside cabin Listening quietly Fly tying Loading… Model qwen2.5:7b (recipes — recommended) qwen2.5:14b (design & new patterns) qwen2.5:3b (fast) Setup Refresh Gallery Inventory first — Sugg
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Guided library setup & health
- `button`/button — Refresh
- `button`/button — Open Gallery
- `button`/button — Suggest a fly
- `button`/button — Open inventory
- `button`/button — Start session
- `button`/button — Apply profile
- `button`/button — Voice: next step
- `button`/button — Voice: repeat step
- `button`/button — Search fly patterns
- `button`/button — Clear search and type filter
- `button`/button — Seasonal
- `button`/button — Hide
- `button`/button — Add
- `button`/button — Compare (disabled)
- `button`/button — Export (disabled)
- `button`/button — Print (disabled)
- `button`/button — Suggest a fly
- `button`/button — Save list
- `button`/button — What ▲
- `button`/button — Color
- `button`/button — Size
- `button`/button — Brand
- `button`/button — Add
- `button`/button — Edit
- `button`/button — Remove material
- `button`/button — Import lines
- `button`/button — flytyingCameraScanBtn
- `button`/button — flytyingScanPhotoBtn
- `button`/button — flytyingLabelBtn
- `button`/submit — Send
- `button`/button — Clear chat
- `input`/search — Search patterns…
- `input`/checkbox — on
- `input`/number — 0
- `input`/url — Paste YouTube, Vimeo, or Fly Fish Food URL…
- `input`/search — Filter videos…
- `input`/checkbox — on
- `input`/text — hook, thread…
- `input`/text — olive
- `input`/text — 14, 8/0
- `input`/text — Uni
- `input`/text — optional
- `input`/text — Scan or type barcode…
- `textarea`/- — e.g. olive 14 dry hook, grizzly hackle, Uni 8/0 olive thread — or use the invent
- `textarea`/- — size 14 dry hook olive dubbing
- `textarea`/- — Ask about a pattern, hatch, or design a new fly…
- `select`/- — Fly tying model (7b = recipes, 14b = design)
- `select`/- — Fly Tying profile
- `select`/- — Fly type
- `summary`/- — INVENTORY TABLE — WHAT, COLOR, SIZE, BRAND
- `summary`/- — Barcode scan (optional)
- `label`/- — Model qwen2.5:7b (recipes — recommended) qwen2.5:14b (design & new patterns) qwe
- `label`/- — Profile
- `label`/- — Favorites
- `label`/- — Min Q
- `label`/- — MATERIALS ON HAND
- `label`/- — Ask ARIA to explain matches (slower)
- `label`/- — Quick import — one per line

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Clear search and type filter**: 40 controls revealed
- After **Add**: 40 controls revealed
- After **Add**: 40 controls revealed
- After **Edit**: 40 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-007` — all visible tabs + inventory add → **FAIL**
- `EXP-113` — Guided library setup & health → **FAIL**
- `EXP-114` — Refresh → **PASS**
- `EXP-115` — Open Gallery → **FAIL**
- `EXP-116` — Suggest a fly → **PASS**
- `EXP-117` — Open inventory → **PASS**
- `EXP-118` — Start session → **PASS**
- `EXP-119` — Apply profile → **PASS**
- `EXP-120` — Voice: next step → **FAIL**
- `EXP-121` — Voice: repeat step → **FAIL**
- `EXP-122` — Search fly patterns → **PASS**
- `EXP-123` — Clear search and type filter → **FAIL**
- `EXP-124` — Seasonal → **PASS**
- `EXP-223` — Hide → **PASS**
- `EXP-224` — Add → **PASS**
- `EXP-225` — Save list → **PASS**
- `EXP-226` — What ▲ → **FAIL**
- `EXP-227` — Color → **PASS**
- `EXP-228` — Size → **PASS**
- `EXP-229` — Brand → **PASS**
- `EXP-230` — Edit → **FAIL**
- `EXP-394` — Setup → **PASS**
- `EXP-395` — Rebuild → **PASS**
- `EXP-396` — Gallery → **PASS**
- `EXP-397` — Next step → **PASS**
- `EXP-398` — Repeat → **PASS**
- `EXP-399` — Clear → **PASS**
- `EXP-400` — Show → **PASS**
- `EXP-401` — Compare → **PASS**
- `EXP-402` — Export → **PASS**
- `EXP-403` — Print → **PASS**
- `EXP-404` — What → **PASS**
- `EXP-405` — Brand ▲ → **FAIL**
- `EXP-406` — Scan barcode → **FAIL**
- `EXP-407` — Stop → **PASS**
- `EXP-454` — Sculpin streamer fly → **PASS**
- `EXP-455` — Unfavorite pattern → **PASS**
- `EXP-456` — Adams dry fly #16 terrestrial · 9 steps 100 → **PASS**
- `EXP-457` — Favorite pattern → **PASS**
- `EXP-458` — Adams dry fly #18 dry · 23 steps 100 → **PASS**
- `EXP-459` — Adams dry fly olive terrestrial · 10 steps 100 → **PASS**
- `EXP-460` — Adams Irresistible dry · 21 steps 100 → **PASS**
- `EXP-461` — Adams Irresistible dry · 12 steps 100 → **PASS**
- `EXP-462` — Adams Irresistible #12 dry · 6 steps 100 → **PASS**
- `EXP-463` — Adams Irresistible #14 terrestrial · 11 steps 100 → **PASS**
- `EXP-464` — Adams parachute dry · 3 steps 100 → **PASS**
- `EXP-465` — Adams parachute #14 dry · 12 steps 100 → **PASS**
- `EXP-466` — Adams parachute #14 dry · 16 steps 100 → **PASS**
- `EXP-467` — Adams parachute chartreuse post dry · 7 steps 100 → **PASS**
- `EXP-468` — Adams parachute chartreuse post dry · 8 steps 100 → **PASS**
- `EXP-469` — Adams parachute orange post terrestrial · 10 steps 100 → **PASS**
- `EXP-470` — Adams rusty spinner #18 dry · 9 steps 100 → **PASS**
- `EXP-471` — Adams snowshoe terrestrial · 12 steps 100 → **PASS**
- `EXP-472` — Adams snowshoe #16 dry · 10 steps 100 → **PASS**
- `EXP-473` — Adams Wulff terrestrial · 7 steps 100 → **PASS**
- `EXP-474` — Adams Wulff streamer · 22 steps 100 → **PASS**
- `EXP-475` — Alexandra streamer streamer · 17 steps 100 → **PASS**
- `EXP-476` — Anchovy fly terrestrial · 9 steps 100 → **PASS**
- `EXP-477` — Anchovy fly dry · 14 steps 100 → **PASS**
- `EXP-478` — Anchovy fly olive nymph · 15 steps 100 → **PASS**

### UNTESTED
- Remove material
- Import lines
- flytyingCameraScanBtn
- flytyingScanPhotoBtn
- flytyingLabelBtn
- Send
- Clear chat

---

## Room: `gallery` — Artwork

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('gallery') / Front Door
- **Preview:** Aria · Museum Listening quietly Gallery Local AI image product — generate, browse, organize, and edit stills. Video and Meme stay separate. Chat converses; Documents store knowledge. Refresh Job Cente
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Job Center
- `button`/button — Models
- `button`/button — Open Maker lab
- `button`/button — Open Fly tying
- `button`/button — Open Video Studio
- `button`/button — Open Meme Studio
- `button`/button — Generate
- `button`/button — Preview enhance
- `button`/button — Advanced
- `button`/button — Reuse last settings with a new seed
- `button`/button — Mission Control
- `button`/button — Simple
- `button`/button — Advanced
- `button`/button — Expert
- `button`/button — Search
- `button`/button — → Video storyboard
- `button`/button — New collection
- `button`/button — Opt-in Vision caption
- `button`/button — Describe
- `button`/button — Save caption to Documents
- `button`/button — Vision→Coding
- `button`/button — Similarity clusters
- `a`/- — Open ComfyUI ↗
- `input`/text — Image generation prompt
- `input`/checkbox — on
- `input`/search — Search gallery
- `input`/checkbox — on
- `input`/checkbox — on
- `select`/- — Generation preset
- `select`/- — Aspect ratio
- `select`/- — Flux Schnell (best prompts) SDXL 1.0 (quality) SDXL Turbo (fast)
- `select`/- — Auto (GPU → CPU fallback) GPU only CPU only
- `select`/- — Sort
- `label`/- — Enhance prompt
- `label`/- — Preset — none — Fast Draft High Quality Photoreal Portrait Landscape Anime Pixel
- `label`/- — Aspect Square Portrait Landscape
- `label`/- — PRESET MODEL Flux Schnell (best prompts) SDXL 1.0 (quality) SDXL Turbo (fast)
- `label`/- — DEVICE Auto (GPU → CPU fallback) GPU only CPU only
- `label`/- — Favorites
- `label`/- — Show artifacts

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Advanced**: 40 controls revealed
- After **Reuse last settings with a new seed**: 40 controls revealed
- After **Advanced**: 40 controls revealed
- After **New collection**: 40 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-016` — generate → **PASS**
- `EXP-125` — Refresh → **PASS**
- `EXP-126` — Job Center → **PASS**
- `EXP-127` — Models → **PASS**
- `EXP-128` — Open Maker lab → **FAIL**
- `EXP-129` — Open Fly tying → **FAIL**
- `EXP-130` — Open Video Studio → **FAIL**
- `EXP-131` — Open Meme Studio → **FAIL**
- `EXP-132` — Generate → **PASS**
- `EXP-133` — Preview enhance → **PASS**
- `EXP-134` — Advanced → **PASS**
- `EXP-135` — Reuse last settings with a new seed → **FAIL**
- `EXP-136` — Mission Control → **PASS**
- `EXP-231` — Simple → **PASS**
- `EXP-232` — Expert → **PASS**
- `EXP-233` — Search → **PASS**
- `EXP-234` — → Video storyboard → **PASS**
- `EXP-235` — New collection → **PASS**
- `EXP-236` — Opt-in Vision caption → **FAIL**
- `EXP-237` — Describe → **PASS**
- `EXP-238` — Save caption to Documents → **PASS**
- `EXP-423` — Maker → **PASS**
- `EXP-424` — Fly tying → **PASS**
- `EXP-425` — Video → **PASS**
- `EXP-426` — Meme → **PASS**
- `EXP-427` — Cancel generation → **PASS**
- `EXP-428` — Generate another → **PASS**
- `EXP-429` — Install NSFW checkpoints → **PASS**
- `EXP-430` — Generate metadata → **PASS**
- `EXP-431` — Load more → **PASS**
- `EXP-432` — Reuse → **PASS**
- `EXP-433` — Favorite prompt → **PASS**
- `EXP-434` — Delete saved prompt → **PASS**

### UNTESTED
- Vision→Coding
- Similarity clusters
- Open ComfyUI ↗

---

## Room: `health` — Jeff’s today

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('health') / Front Door
- **Preview:** Aria · Wellness clinic Listening quietly Health Personal Health Record — local, private, printable. Not an EMR. Aria does not diagnose or prescribe. Doctor visit Emergency Refresh Timeline Dashboard C
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Doctor visit
- `button`/button — Emergency
- `button`/button — Refresh
- `button`/button — Timeline
- `button`/button — Dashboard
- `button`/button — Check-in
- `button`/button — Activity
- `button`/button — Workouts
- `button`/button — Goals
- `button`/button — Trends
- `button`/button — Meds
- `button`/button — Supplements
- `button`/button — Recovery
- `button`/button — History
- `button`/button — Journal
- `button`/button — Knowledge
- `button`/button — Providers
- `button`/button — Procedures
- `button`/button — Family
- `button`/button — Preventive
- `button`/button — Nutrition
- `button`/button — Insights
- `button`/button — Visit prep
- `button`/button — Backups
- `button`/button — Security
- `button`/button — Vitals
- `button`/button — Labs
- `button`/button — Documents
- `button`/button — Questions
- `button`/button — Coach
- `button`/button — Consult
- `button`/button — Reminders
- `button`/button — Print / Export
- `button`/button — Profile
- `button`/button — Search
- `button`/button — Log
- `input`/search — Search Health
- `input`/text — Natural language health update

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-137` — Doctor visit → **PASS**
- `EXP-138` — Emergency → **PASS**
- `EXP-139` — Refresh → **PASS**
- `EXP-140` — Timeline → **PASS**
- `EXP-141` — Dashboard → **PASS**
- `EXP-142` — Check-in → **PASS**
- `EXP-143` — Activity → **PASS**
- `EXP-144` — Workouts → **PASS**
- `EXP-145` — Goals → **PASS**
- `EXP-146` — Trends → **PASS**
- `EXP-147` — Meds → **PASS**
- `EXP-148` — Supplements → **PASS**
- `EXP-239` — Recovery → **PASS**
- `EXP-240` — History → **PASS**
- `EXP-241` — Journal → **PASS**
- `EXP-242` — Knowledge → **PASS**
- `EXP-243` — Providers → **PASS**
- `EXP-244` — Procedures → **PASS**
- `EXP-245` — Family → **PASS**
- `EXP-246` — Preventive → **PASS**
- `EXP-408` — Add → **PASS**
- `EXP-905` — search → **PASS**

### UNTESTED
- Nutrition
- Insights
- Visit prep
- Backups
- Security
- Vitals
- Labs
- Documents
- Questions
- Coach
- Consult
- Reminders
- Print / Export
- Profile
- Search
- Log

---

## Room: `home` — Orientation

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('home') / Front Door
- **Preview:** Aria · Foyer Listening quietly Welcome back Home Mission Control Planner Journal Calendar Ctrl+Home First-flight checklist ▾ Running… Running… Running first-flight checks… Skills & learned workflows ▾
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Open Mission Control
- `button`/button — Open Planner
- `button`/button — Open Bullet Journal
- `button`/button — Open Calendar
- `button`/button — Running… (disabled)
- `button`/button — Automation Home
- `button`/button — Refresh
- `button`/button — Scan action log
- `button`/button — Set PIN
- `input`/password — 4–6 digit PIN
- `h3`/button — First-flight checklist ▾
- `h3`/button — Skills & learned workflows ▾
- `h3`/button — Security ▾

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Running…**: 13 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-149` — Open Mission Control → **PASS**
- `EXP-150` — Open Planner → **FAIL**
- `EXP-151` — Open Bullet Journal → **FAIL**
- `EXP-152` — Open Calendar → **FAIL**
- `EXP-153` — Automation Home → **PASS**
- `EXP-154` — Refresh → **PASS**
- `EXP-155` — Scan action log → **PASS**
- `EXP-156` — Set PIN → **PASS**
- `EXP-157` — 4–6 digit PIN → **FAIL**
- `EXP-158` — First-flight checklist ▾ → **PASS**
- `EXP-159` — Skills & learned workflows ▾ → **PASS**
- `EXP-160` — Security ▾ → **PASS**
- `EXP-528` — Mission Control → **PASS**
- `EXP-529` — Planner → **PASS**
- `EXP-530` — Journal → **PASS**
- `EXP-531` — Calendar → **PASS**
- `EXP-532` — Retry → **PASS**
- `EXP-533` — Running… → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `home_automation` — Environment

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('home_automation') / Front Door
- **Preview:** Aria · Home control Listening quietly Home Automation Presence Security Lights, scenes, and Home Assistant — control the room around you. Search Open HA Status Home failed Favorites Scenes Rooms Profi
- **Fail text in panel:** True

### VISIBLE CONTROLS
- `button`/button — Open Presence
- `button`/button — Open Security
- `button`/button — Search
- `button`/button — Open Home Assistant
- `button`/button — Status
- `button`/button — Apply
- `button`/button — haPasteTokenBtn
- `button`/button — haTokenModalBtn
- `button`/button — haTestBtn
- `button`/button — haSaveBtn
- `button`/button — ghost-btn small ha-quick-btn
- `button`/button — haSetupWizardBtn
- `button`/button — haSceneSaveBtn
- `button`/button — Refresh
- `button`/button — Discover Kasa
- `button`/button — Refresh
- `input`/search — Search Smart Home entities
- `input`/url — http://127.0.0.1:8123
- `input`/text — scene.leaving (optional)
- `input`/text — scene.leaving
- `textarea`/- — Paste token
- `select`/- — Smart Home profile
- `select`/- — Entity domain
- `summary`/- — SETUP & CONNECTION
- `label`/- — Profile Apply
- `label`/- — ha-field
- `label`/- — toggle-row ha-enabled-row

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-015` — status + entity search → **PASS**
- `EXP-161` — Open Presence → **FAIL**
- `EXP-162` — Open Security → **FAIL**
- `EXP-163` — Search → **PASS**
- `EXP-164` — Open Home Assistant → **FAIL**
- `EXP-165` — Status → **PASS**
- `EXP-166` — Apply → **PASS**
- `EXP-167` — haPasteTokenBtn → **PASS**
- `EXP-168` — haTokenModalBtn → **PASS**
- `EXP-169` — haTestBtn → **PASS**
- `EXP-170` — haSaveBtn → **PASS**
- `EXP-171` — ghost-btn small ha-quick-btn → **FAIL**
- `EXP-172` — haSetupWizardBtn → **PASS**
- `EXP-247` — haSceneSaveBtn → **PASS**
- `EXP-248` — Refresh → **PASS**
- `EXP-249` — Discover Kasa → **PASS**
- `EXP-250` — Search Smart Home entities → **PASS**
- `EXP-251` — http://127.0.0.1:8123 → **PASS**
- `EXP-252` — scene.leaving (optional) → **FAIL**
- `EXP-253` — scene.leaving → **FAIL**
- `EXP-254` — Paste token → **FAIL**
- `EXP-544` — Presence → **PASS**
- `EXP-545` — Security → **PASS**
- `EXP-546` — Open HA → **PASS**
- `EXP-547` — haCopyWebhookBtn → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `integrations` — Keys & services

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('integrations') / Front Door
- **Preview:** Aria · Integrations Listening quietly Integrations Provider credentials, connection tests, and unlock matrix. Products own behavior — Integrations owns keys and health. Refresh Test configured Diagnos
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Test configured
- `button`/button — Diagnostics
- `input`/search — Search providers…
- `select`/- — Filter by category
- `summary`/- — Advanced options

### TABS
- (none observed)

### MENUS
- Advanced options

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Advanced options**: 6 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-173` — Refresh → **PASS**
- `EXP-174` — Test configured → **PASS**
- `EXP-175` — Diagnostics → **PASS**
- `EXP-176` — Search providers… → **FAIL**
- `EXP-177` — Filter by category → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `integrity` — Truth

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('integrity') / Front Door
- **Preview:** Aria · Quiet caretaker Listening quietly Truth Score 100 · ready No deductions on record. ··· Refresh Repair
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — More

### TABS
- (none observed)

### MENUS
- More

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **More**: 3 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-255` — More → **PASS**
- `EXP-526` — Refresh → **PASS**
- `EXP-527` — Repair → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `journal` — Daily pages

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('journal') / Front Door
- **Preview:** Aria · Bullet journal Listening quietly Bullet Journal Notes, thoughts, reflections · promote actionable items to Planner · scheduled commitments live in Calendar No special keys? Type t: task · e: ev
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Daily
- `button`/button — Weekly
- `button`/button — Monthly
- `button`/button — Habits
- `button`/button — Wellness
- `button`/button — Future
- `button`/button — Index
- `button`/button — Collections
- `button`/button — Projects
- `button`/button — Key
- `button`/button — Distraction-free writing (W)
- `button`/button — Calendar = scheduled commitments
- `button`/button — Planner = actionable work
- `button`/button — Memory = lasting knowledge
- `button`/button — Search
- `button`/button — AI reflection (you start it)
- `button`/button — Suggest promotions — confirm each
- `button`/button — Month-end review wizard
- `button`/button — journalOpenDocumentsBtn
- `button`/button — journalOpenAudioBtn
- `button`/button — journalPrintBtn
- `button`/button — journalPdfBtn
- `button`/button — journalExportBtn
- `button`/button — journalExportEncBtn
- `button`/button — journalImportBtn
- `button`/button — journalImportEncBtn
- `button`/button — journalBackupBtn
- `button`/button — Voice → rapid log draft
- `button`/button — Paste OCR / scan text
- `button`/button — journalShortcutsBtn
- `button`/button — journalUndoBtn
- `button`/button — journalRedoBtn
- `button`/button — journalMigrateBtn
- `button`/button — Add
- `input`/date — 2026-08-10
- `input`/search — Search journal
- `input`/checkbox — on
- `textarea`/- — Rapid log — one line per entry. Indent 2 spaces to nest under the previous line.
- `select`/- — Month migrate destination
- `select`/- — Default bullet type
- `summary`/- — More
- `label`/- — Typewriter scroll

### TABS
- (none observed)

### MENUS
- More

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Add**: 40 controls revealed
- After **More**: 40 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-256` — Daily → **PASS**
- `EXP-257` — Weekly → **PASS**
- `EXP-258` — Monthly → **PASS**
- `EXP-259` — Habits → **PASS**
- `EXP-260` — Wellness → **PASS**
- `EXP-261` — Future → **PASS**
- `EXP-262` — Index → **PASS**
- `EXP-263` — Collections → **PASS**
- `EXP-550` — Writing mode → **PASS**
- `EXP-551` — Calendar → **PASS**
- `EXP-552` — Planner → **PASS**
- `EXP-553` — Memory → **PASS**
- `EXP-554` — Reflect → **PASS**
- `EXP-555` — Promote assist → **PASS**
- `EXP-556` — Month-end → **PASS**
- `EXP-557` — Documents → **PASS**
- `EXP-558` — Audio → **PASS**
- `EXP-559` — Print month → **PASS**
- `EXP-560` — Export PDF → **PASS**
- `EXP-561` — Export JSON → **PASS**
- `EXP-562` — Export encrypted → **PASS**
- `EXP-563` — Import → **PASS**
- `EXP-564` — Import encrypted → **PASS**
- `EXP-565` — Backup now → **PASS**
- `EXP-566` — Voice log → **PASS**
- `EXP-567` — Vision import → **PASS**
- `EXP-568` — Shortcuts (?) → **PASS**
- `EXP-569` — Undo → **PASS**
- `EXP-570` — Redo → **PASS**
- `EXP-571` — Migrate month → **PASS**
- `EXP-572` — Exit writing (Esc) → **PASS**
- `EXP-911` — search → **PASS**
- `EXP-912` — add → **PASS**

### UNTESTED
- Projects
- Key
- Distraction-free writing (W)
- Calendar = scheduled commitments
- Planner = actionable work
- Memory = lasting knowledge
- Search
- AI reflection (you start it)
- Suggest promotions — confirm each
- Month-end review wizard
- journalOpenDocumentsBtn
- journalOpenAudioBtn
- journalPrintBtn
- journalPdfBtn
- journalExportBtn
- journalExportEncBtn
- journalImportBtn
- journalImportEncBtn
- journalBackupBtn
- Voice → rapid log draft
- Paste OCR / scan text
- journalShortcutsBtn
- journalUndoBtn
- journalRedoBtn
- journalMigrateBtn
- Add

---

## Room: `maker` — CAD & print

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('maker') / Front Door
- **Preview:** Aria · Maker lab Listening quietly Maker lab ⧉ Loading CAD status… auto OpenSCAD build123d Meshy Generate Iterate Hello cube Slice Download STL Refresh Gallery Documents Clear gallery Printer ⧉ Loadin
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Detach maker lab panel
- `button`/button — Generate
- `button`/button — Iterate
- `button`/button — Hello cube
- `button`/button — Slice
- `button`/button — Download STL
- `button`/button — Refresh
- `button`/button — Gallery
- `button`/button — Documents
- `button`/button — Clear gallery
- `button`/button — Detach printer panel
- `button`/button — Add
- `button`/button — Discover KE
- `button`/button — Status
- `button`/button — Start print
- `input`/text — Design a 5 inch to 4 inch hose adapter…
- `input`/text — Iterate: make it taller, add mounting holes…
- `input`/text — Printer name
- `input`/text — IP for Creality KE (e.g. 192.168.1.50)
- `select`/- — CAD backend
- `select`/- — Printer model
- `label`/- — Bed clear
- `label`/- — Filament loaded

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Add**: 23 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-264` — Detach maker lab panel → **PASS**
- `EXP-265` — Generate → **FAIL**
- `EXP-266` — Iterate → **FAIL**
- `EXP-267` — Hello cube → **FAIL**
- `EXP-268` — Slice → **FAIL**
- `EXP-269` — Download STL → **FAIL**
- `EXP-270` — Refresh → **FAIL**
- `EXP-271` — Gallery → **FAIL**
- `EXP-914` — clear → **PASS**
- `EXP-915` — add → **PASS**
- `EXP-916` — start → **PASS**

### UNTESTED
- Documents
- Clear gallery
- Detach printer panel
- Add
- Discover KE
- Status
- Start print

---

## Room: `meme` — Memes

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('meme') / Front Door
- **Preview:** Aria · Meme studio Listening quietly Meme Generator Classic top/bottom captions · AI background optional · safe / uncensored follows global toggle Generate in chat Gallery Video MEME IDEA (OPTIONAL — 
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Generate in chat
- `button`/button — Open Gallery
- `button`/button — Open Video Studio
- `button`/button — Quick preview (text only)
- `button`/button — Generate meme
- `input`/text — e.g. when ARIA finally works on the first try
- `input`/text — WHEN YOU RESTART
- `input`/text — AND IT ACTUALLY HELPS
- `input`/checkbox — on
- `label`/- — MEME IDEA (OPTIONAL — AI WRITES CAPTIONS)
- `label`/- — TOP TEXT
- `label`/- — BOTTOM TEXT
- `label`/- — AI BACKGROUND (COMFYUI)

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-272` — Generate in chat → **PASS**
- `EXP-273` — Open Gallery → **FAIL**
- `EXP-274` — Open Video Studio → **FAIL**
- `EXP-275` — Quick preview (text only) → **PASS**
- `EXP-276` — Generate meme → **PASS**
- `EXP-277` — e.g. when ARIA finally works on the first try → **FAIL**
- `EXP-278` — WHEN YOU RESTART → **FAIL**
- `EXP-279` — AND IT ACTUALLY HELPS → **FAIL**

### UNTESTED
- none within exploration caps

---

## Room: `memory` — Personal history

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('memory') / Front Door
- **Preview:** Aria · Memory archive Listening quietly Memory What Aria knows about you — autobiographical cognition (ACM), not a note database. Search New Briefing Assist ? Auto-memory Smart → candidates Explicit o
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Search (/)
- `button`/button — New memory (N)
- `button`/button — Briefing
- `button`/button — Assist
- `button`/button — ?
- `button`/button — Update profile
- `button`/button — Edit answers
- `button`/button — Save preferences
- `button`/button — Refresh machine facts
- `button`/button — cheatsheetViewBtn
- `button`/button — cheatsheetEditBtn
- `button`/button — cheatsheetResetBtn
- `button`/button — memoryOpenJournalBtn
- `button`/button — memoryOpenProjectsBtn
- `button`/button — memoryOpenBrowserBtn
- `button`/button — memoryOpenDocumentsBtn
- `button`/button — Knowledge Briefs (research) — not Connections or Memory
- `button`/button — memoryExportBtn
- `button`/button — memoryImportBtn
- `button`/button — memoryPruneBtn
- `button`/button — memoryScrubBtn
- `button`/button — Open Knowledge Briefs
- `button`/button — Relationship explorer
- `input`/checkbox — on
- `input`/checkbox — on
- `input`/checkbox — on
- `input`/checkbox — on
- `input`/checkbox — on
- `input`/checkbox — on
- `input`/search — Search memories
- `select`/- — Auto-memory mode
- `select`/- — Select cheatsheet
- `select`/- — Filter by type
- `select`/- — Filter by namespace
- `summary`/- — Browse & tools
- `label`/- — Auto-memory Smart → candidates Explicit only Off
- `label`/- — Brain learning
- `label`/- — Journal → candidates
- `label`/- — Docs → candidates
- `label`/- — Auto-checkpoint
- `label`/- — Per-repo namespace
- `label`/- — Profile in prompt

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **New memory (N)**: 40 controls revealed
- After **Edit answers**: 40 controls revealed
- After **cheatsheetEditBtn**: 40 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-006` — chat remember → memory → recall → forget → **FAIL**
- `EXP-280` — Search (/) → **FAIL**
- `EXP-281` — New memory (N) → **FAIL**
- `EXP-282` — Briefing → **PASS**
- `EXP-283` — Assist → **PASS**
- `EXP-284` — ? → **PASS**
- `EXP-285` — Update profile → **PASS**
- `EXP-286` — Edit answers → **PASS**
- `EXP-287` — Save preferences → **PASS**
- `EXP-438` — Search → **PASS**
- `EXP-439` — New → **PASS**
- `EXP-440` — memoryOpenKnowledgeBtn → **FAIL**
- `EXP-441` — Open Connections → **PASS**
- `EXP-503` — View → **PASS**
- `EXP-504` — Edit → **PASS**
- `EXP-505` — Reset default → **PASS**
- `EXP-506` — Journal → **PASS**
- `EXP-507` — Projects → **PASS**
- `EXP-508` — Browser → **PASS**
- `EXP-509` — Documents → **PASS**
- `EXP-510` — Knowledge Briefs → **PASS**
- `EXP-511` — Export → **PASS**
- `EXP-512` — Import → **PASS**
- `EXP-513` — Prune stale → **PASS**
- `EXP-514` — Scrub test junk → **PASS**
- `EXP-910` — refresh → **PASS**

### UNTESTED
- Refresh machine facts
- cheatsheetViewBtn
- cheatsheetEditBtn
- cheatsheetResetBtn
- memoryOpenJournalBtn
- memoryOpenProjectsBtn
- memoryOpenBrowserBtn
- memoryOpenDocumentsBtn
- Knowledge Briefs (research) — not Connections or Memory
- memoryExportBtn
- memoryImportBtn
- memoryPruneBtn
- memoryScrubBtn
- Open Knowledge Briefs
- Relationship explorer

---

## Room: `mission` — The system

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('mission') / Front Door
- **Preview:** Aria · Aerospace ops Listening quietly Mission Control Infrastructure health console — providers, runtime, hardware, recovery, routing, and performance. Not Job Center or Activity Center. Refresh Open
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Open Job Center
- `button`/button — Open Notifications (Activity Center inbox)
- `button`/button — Open Chat
- `button`/button — Open System audit
- `button`/button — Open Home
- `button`/button — Overview
- `button`/button — Routing
- `button`/button — Performance
- `button`/button — Recovery
- `button`/button — Connection
- `button`/button — Advanced ▾
- `button`/button — Hardware
- `button`/button — Inference
- `button`/button — Memory
- `button`/button — Knowledge
- `button`/button — Databases
- `button`/button — Settings
- `button`/button — Timeline
- `button`/button — Release
- `button`/button — Applications
- `button`/button — Queue Snapshot
- `button`/button — Operations Event Log
- `button`/button — Intent Analytics

### TABS
- Overview
- Routing
- Performance
- Recovery
- Connection
- Hardware
- Inference
- Memory
- Knowledge
- Databases
- Settings
- Timeline
- Release
- Applications
- Queue Snapshot
- Operations Event Log
- Intent Analytics

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Advanced ▾**: 18 controls revealed
- After **Settings**: 18 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-013` — health summary → **FAIL**
- `EXP-288` — Refresh → **PASS**
- `EXP-289` — Open Job Center → **PASS**
- `EXP-290` — Open Notifications (Activity Center inbox) → **FAIL**
- `EXP-291` — Open Chat → **FAIL**
- `EXP-292` — Open System audit → **FAIL**
- `EXP-293` — Open Home → **FAIL**
- `EXP-294` — Overview → **PASS**
- `EXP-295` — Routing → **PASS**
- `EXP-409` — Open Notifications → **PASS**
- `EXP-410` — Chat → **PASS**
- `EXP-411` — Audit → **PASS**
- `EXP-412` — Home → **PASS**
- `EXP-413` — Advanced ▸ → **FAIL**
- `EXP-906` — settings → **PASS**
- `EXP-BUG-006` — EXP-BUG-006 → **FAIL**

### UNTESTED
- Performance
- Recovery
- Connection
- Advanced ▾
- Hardware
- Inference
- Memory
- Knowledge
- Databases
- Settings
- Timeline
- Release
- Applications
- Queue Snapshot
- Operations Event Log
- Intent Analytics

---

## Room: `planner` — Today’s page

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('planner') / Front Door
- **Preview:** Aria · Leather notebook Listening quietly Planner Today’s actionable work · Journal for notes · Calendar for commitments · Documents HA Focus mode Shortcuts: N · P · F · T · U DAILY FOCUS Today’s day 
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Notes, reflections, logs
- `button`/button — Scheduled commitments
- `button`/button — Documents
- `button`/button — Add
- `button`/button — Ask Aria to promote a Journal item
- `button`/button — Add task
- `button`/button — Ask Chat
- `button`/button — Open Journal
- `button`/button — Start
- `button`/button — 25 min focus timer (with optional HA Focus scene)
- `button`/button — Start Focus 25m
- `button`/button — Set
- `button`/button — Add alarm
- `button`/button — Add
- `button`/button — Add event
- `button`/button — Open Calendar
- `input`/checkbox — on
- `input`/text — New planner task
- `input`/text — Timer duration
- `input`/text — Alarm time
- `input`/text — Event title
- `input`/text — Event time
- `h3`/button — Tasks ▾
- `h3`/button — Timers ▾
- `h3`/button — Alarms ▾
- `h3`/button — Today ▾
- `label`/- — When starting Focus Session, try Home Assistant Focus scene

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Add**: 38 controls revealed
- After **Add task**: 38 controls revealed
- After **Add alarm**: 38 controls revealed
- After **Add**: 38 controls revealed
- After **Add event**: 38 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-008` — add task form → **FAIL**
- `EXP-296` — Notes, reflections, logs → **FAIL**
- `EXP-297` — Scheduled commitments → **FAIL**
- `EXP-298` — Documents → **PASS**
- `EXP-299` — Add → **PASS**
- `EXP-300` — Add task → **FAIL**
- `EXP-301` — Ask Chat → **FAIL**
- `EXP-302` — Open Journal → **FAIL**
- `EXP-303` — Start → **PASS**
- `EXP-415` — Journal → **PASS**
- `EXP-416` — Calendar → **PASS**
- `EXP-417` — From Journal → **PASS**
- `EXP-418` — Focus 25m → **PASS**

### UNTESTED
- Ask Aria to promote a Journal item
- 25 min focus timer (with optional HA Focus scene)
- Start Focus 25m
- Set
- Add alarm
- Add event
- Open Calendar

---

## Room: `presence` — Camera & gestures

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('presence') / Front Door
- **Preview:** Aria · Presence Listening quietly Presence Security Voice Webcam + gestures Start camera Stop Enroll face Gestures Off Preview only Control — pinch click, fist drag panels CPU-only (low FPS) Calibrate
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Open Security
- `button`/button — Open Voice
- `button`/button — Start camera
- `button`/button — Stop
- `button`/button — Enroll face
- `button`/button — Calibrate gestures
- `select`/- — Off Preview only Control — pinch click, fist drag panels CPU-only (low FPS)
- `label`/- — Gestures Off Preview only Control — pinch click, fist drag panels CPU-only (low 

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-304` — Open Security → **FAIL**
- `EXP-305` — Open Voice → **FAIL**
- `EXP-306` — Start camera → **PASS**
- `EXP-307` — Stop → **PASS**
- `EXP-308` — Enroll face → **PASS**
- `EXP-309` — Calibrate gestures → **PASS**
- `EXP-310` — Off Preview only Control — pinch click, fist drag panels CPU-only (low FPS) → **PASS**
- `EXP-548` — Security → **PASS**
- `EXP-549` — Voice → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `projects` — Alive work

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('projects') / Front Door
- **Preview:** Aria · Creative workshop Listening quietly Projects Workspace identity layer — one slug connects coding, memory, journal, knowledge, browser, and AI. Not a task tracker. Loading… ? Create Import
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Shortcuts
- `button`/button — Create
- `button`/button — Import
- `input`/search — Search projects
- `input`/text — New project name
- `input`/text — Description
- `input`/text — Git path

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-311` — Shortcuts → **FAIL**
- `EXP-312` — Create → **PASS**
- `EXP-313` — Import → **PASS**
- `EXP-314` — Search projects → **PASS**
- `EXP-315` — New project name → **PASS**
- `EXP-316` — Description → **PASS**
- `EXP-317` — Git path → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `providers` — Models

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('providers') / Front Door
- **Preview:** Aria · Provider bay Listening quietly Models AI model configuration and routing center — roles, catalog, providers, presets. Mission Control owns health; Models owns configuration. Refresh Mission Con
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Provider / VRAM health

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-010` — Roles/Catalog tabs + selects → **FAIL**
- `EXP-318` — Refresh → **PASS**
- `EXP-319` — Provider / VRAM health → **FAIL**
- `EXP-543` — Mission Control · Inference → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `repair` — Evidence

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('repair') / Front Door
- **Preview:** Aria · Restoration bench Listening quietly Mission Control Infrastructure health console — providers, runtime, hardware, recovery, routing, and performance. Not Job Center or Activity Center. Refresh 
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Open Job Center
- `button`/button — Open Notifications (Activity Center inbox)
- `button`/button — Open Chat
- `button`/button — Open System audit
- `button`/button — Open Home
- `button`/button — Overview
- `button`/button — Routing
- `button`/button — Performance
- `button`/button — Recovery
- `button`/button — Connection
- `button`/button — Advanced ▸
- `a`/- — JSON
- `a`/- — CSV
- `a`/- — Markdown
- `a`/- — HTML
- `input`/search — Search timeline…
- `select`/- — All severities Info Warning Error

### TABS
- Overview
- Routing
- Performance
- Recovery
- Connection

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Advanced ▸**: 24 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-320` — Refresh → **PASS**
- `EXP-321` — Open Job Center → **PASS**
- `EXP-322` — Open Notifications (Activity Center inbox) → **FAIL**
- `EXP-323` — Open Chat → **FAIL**
- `EXP-324` — Open System audit → **FAIL**
- `EXP-325` — Open Home → **FAIL**
- `EXP-326` — Overview → **PASS**
- `EXP-327` — Routing → **PASS**
- `EXP-448` — Open Notifications → **PASS**
- `EXP-449` — Chat → **PASS**
- `EXP-450` — Audit → **PASS**
- `EXP-451` — Home → **PASS**
- `EXP-452` — Advanced ▾ → **PASS**
- `EXP-453` — Hardware → **PASS**
- `EXP-515` — Inference → **PASS**
- `EXP-516` — Memory → **PASS**
- `EXP-517` — Knowledge → **PASS**
- `EXP-518` — Databases → **PASS**
- `EXP-519` — Settings → **PASS**
- `EXP-520` — Timeline → **PASS**
- `EXP-521` — Release → **PASS**
- `EXP-522` — Applications → **PASS**
- `EXP-523` — Queue Snapshot → **PASS**
- `EXP-524` — Operations Event Log → **PASS**
- `EXP-525` — Intent Analytics → **PASS**

### UNTESTED
- Performance
- Recovery
- Connection
- Advanced ▸
- JSON
- CSV
- Markdown
- HTML

---

## Room: `search` — Discovery

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('search') / Front Door
- **Preview:** Aria · Research study Listening quietly Search One federated engine. Browse everything here — Ctrl+K for commands, Chat for answers, products own their data. Refresh Save search Diagnostics Federated 
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Save search
- `button`/button — Diagnostics
- `button`/button — Search
- `button`/button — Clear history
- `input`/search — Search documents, memory, code, graph, planner…
- `select`/- — Browse or answer mode
- `select`/- — Code search mode
- `label`/- — Gallery
- `label`/- — Home Assistant

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-328` — Refresh → **PASS**
- `EXP-329` — Save search → **PASS**
- `EXP-330` — Diagnostics → **PASS**
- `EXP-331` — Search → **PASS**
- `EXP-332` — Clear history → **PASS**
- `EXP-333` — Search documents, memory, code, graph, planner… → **FAIL**
- `EXP-334` — Browse or answer mode → **PASS**
- `EXP-335` — Code search mode → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `security` — Lock & trust

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('security') / Front Door
- **Preview:** Aria · Security Listening quietly Security Presence Voice PIN lock off (set JARVIS_PIN_LOCK=1) PIN lock Set a PIN and enable JARVIS_PIN_LOCK=1 in jarvis.env. Set PIN Lock now Trusted devices No truste
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Open Presence
- `button`/button — Open Voice
- `button`/button — Set PIN
- `button`/button — Lock now
- `button`/button — Presence
- `input`/password — 4–6 digit PIN

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-336` — Open Presence → **FAIL**
- `EXP-337` — Open Voice → **FAIL**
- `EXP-338` — Set PIN → **PASS**
- `EXP-339` — Lock now → **PASS**
- `EXP-340` — Presence → **PASS**
- `EXP-341` — 4–6 digit PIN → **FAIL**

### UNTESTED
- none within exploration caps

---

## Room: `settings` — Preferences

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('settings') / Front Door
- **Preview:** Aria · Settings Listening quietly Settings Preference catalog and deep links. Products own their stores — Settings indexes them. Ctrl+, opens this Home. Refresh Voice & Chat Diagnostics Export Search 
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Refresh
- `button`/button — Voice & Chat
- `button`/button — Diagnostics
- `button`/button — Export
- `button`/button — Search
- `button`/button — Reset appearance
- `button`/button — Activate
- `button`/button — Save profile
- `input`/search — Search preferences (PIN, theme, whisper, models…)
- `select`/- — Filter by category
- `select`/- — Theme
- `select`/- — Accent
- `select`/- — UI density
- `select`/- — Preference profile
- `label`/- — Theme Professional Dark Professional Light
- `label`/- — Accent Steel blue Slate blue Muted teal Deep emerald
- `label`/- — Density Comfortable Standard Compact Operator
- `label`/- — Quick dock
- `label`/- — Status bar
- `label`/- — Mini chat
- `label`/- — Room atmosphere
- `label`/- — Weather light
- `label`/- — Season tint
- `label`/- — Soft UI sounds

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-011` — theme/density nested controls → **PASS**
- `EXP-342` — Refresh → **PASS**
- `EXP-343` — Voice & Chat → **PASS**
- `EXP-344` — Diagnostics → **PASS**
- `EXP-345` — Export → **PASS**
- `EXP-346` — Search → **PASS**
- `EXP-347` — Reset appearance → **PASS**
- `EXP-348` — Activate → **PASS**
- `EXP-349` — Save profile → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `video` — Motion

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('video') / Front Door
- **Preview:** Aria · Video studio Listening quietly Video Studio Stay-in-Studio generation · AnimateDiff or Ken Burns · shared media queue Gallery Meme Mission Control Generate Enhance prompt Preset — none — Fast D
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Open Gallery
- `button`/button — Open Meme Studio
- `button`/button — Mission Control
- `button`/button — Generate
- `button`/button — Preview enhance
- `button`/button — Advanced
- `button`/button — Generate another
- `button`/button — Simple
- `button`/button — Expert
- `button`/button — Unload Ollama from GPU before AnimateDiff
- `button`/button — Save clip settings
- `button`/button — Build storyboard
- `input`/text — Video generation prompt
- `input`/checkbox — on
- `input`/number — Clip duration seconds
- `input`/text — Storyboard image paths
- `input`/number — Seconds per slide
- `input`/file — videoUploadInput
- `select`/- — Video generation preset
- `label`/- — Enhance prompt
- `label`/- — Preset — none — Fast Draft Portrait Motion Landscape Pan Storyboard Preview Cine
- `label`/- — Duration
- `label`/- — Sec/slide
- `label`/- — UPLOAD VIDEO

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Advanced**: 40 controls revealed
- After **Save clip settings**: 40 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-350` — Open Gallery → **FAIL**
- `EXP-351` — Open Meme Studio → **FAIL**
- `EXP-352` — Mission Control → **PASS**
- `EXP-353` — Generate → **PASS**
- `EXP-354` — Preview enhance → **PASS**
- `EXP-355` — Advanced → **PASS**
- `EXP-356` — Generate another → **PASS**
- `EXP-357` — Simple → **PASS**
- `EXP-573` — Gallery → **PASS**
- `EXP-574` — Meme → **PASS**
- `EXP-575` — Cancel generation → **PASS**
- `EXP-576` — Free VRAM before video → **PASS**
- `EXP-577` — Install AnimateDiff (~2 GB) → **PASS**
- `EXP-578` — Install NSFW checkpoints → **PASS**
- `EXP-913` — save → **PASS**

### UNTESTED
- Expert
- Unload Ollama from GPU before AnimateDiff
- Save clip settings
- Build storyboard

---

## Room: `vision` — Seeing

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('vision') / Front Door
- **Preview:** Aria · Vision bench Listening quietly Vision Chat attach Gallery Refresh Loading… OCR entry point: enter an image/PDF page path, then choose OCR or Structured OCR below. Command Palette also knows “Ru
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Chat attach
- `button`/button — Gallery
- `button`/button — Refresh
- `button`/button — Apply profile
- `button`/button — Speak OCR (Voice)
- `button`/button — Refresh batch
- `input`/text — Vision image or PDF page path for OCR
- `input`/text — Compare image path B
- `input`/text — optional question
- `select`/- — Vision profile
- `select`/- — OCR mode
- `select`/- — Preview Journal Planner Calendar Memory Documents Gallery
- `label`/- — Profile
- `label`/- — OCR mode Auto Classic VLM Hybrid
- `label`/- — Speak results (Voice)
- `label`/- — Image/PDF page path for OCR
- `label`/- — Compare path B
- `label`/- — Question
- `label`/- — Import target Preview Journal Planner Calendar Memory Documents Gallery

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- (no revealer expansions recorded)

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-358` — Chat attach → **PASS**
- `EXP-359` — Gallery → **PASS**
- `EXP-360` — Refresh → **PASS**
- `EXP-361` — Apply profile → **PASS**
- `EXP-362` — Speak OCR (Voice) → **PASS**
- `EXP-363` — Refresh batch → **PASS**
- `EXP-364` — Vision image or PDF page path for OCR → **PASS**
- `EXP-365` — Compare image path B → **PASS**

### UNTESTED
- none within exploration caps

---

## Room: `voice` — Speaking

- **How discovered:** registry+AriaHouse.enter
- **Entry path:** AriaHouse.enter('voice') / Front Door
- **Preview:** Aria · Presence Listening quietly Voice Audio Presence State: speaking · Duplex: off · STT: whisper TTS engine: piper Cloud live ready (gemini live) · OpenAI Realtime hidden (no WebRTC) Duplex Off Hal
- **Fail text in panel:** False

### VISIBLE CONTROLS
- `button`/button — Open Audio studio
- `button`/button — Open Presence
- `button`/button — Apply profile
- `button`/button — Save settings
- `button`/button — Refresh
- `button`/button — Run recovery advisor
- `button`/button — Toggle cloud live
- `input`/number — 220
- `input`/checkbox — on
- `input`/checkbox — on
- `input`/checkbox — on
- `input`/checkbox — on
- `select`/- — Off Half Full
- `select`/- — Whisper RealtimeSTT
- `select`/- — Voice profile
- `select`/- — Voice cheatsheet
- `label`/- — Duplex Off Half Full
- `label`/- — STT backend Whisper RealtimeSTT
- `label`/- — TTS chunk chars
- `label`/- — Speak replies
- `label`/- — Server Whisper (mic)
- `label`/- — Interrupt on speak
- `label`/- — Chunk sentences
- `label`/- — Profile — none —

### TABS
- (none observed)

### MENUS
- (none labeled as menu/more/options)

### DIALOGS
- Opened via revealers / Front Door / Activity / palette during EXP runs; Escape used to dismiss.

### CONDITIONAL CONTROLS
- After **Save settings**: 24 controls revealed

### NAVIGATION
- Front Door option
- `AriaHouse.enter`
- Command palette

### KEYBOARD/COMMAND ENTRY
- Ctrl+K

### DISCOVERED FUNCTIONS (EXP)
- `EXP-366` — Open Audio studio → **FAIL**
- `EXP-367` — Open Presence → **FAIL**
- `EXP-368` — Apply profile → **PASS**
- `EXP-369` — Save settings → **PASS**
- `EXP-370` — Refresh → **PASS**
- `EXP-371` — Run recovery advisor → **FAIL**
- `EXP-372` — Toggle cloud live → **FAIL**
- `EXP-373` — 220 → **PASS**
- `EXP-442` — Audio → **PASS**
- `EXP-443` — Presence → **PASS**
- `EXP-444` — Recovery → **PASS**
- `EXP-445` — Warm router → **PASS**
- `EXP-446` — Voice smoke → **PASS**
- `EXP-447` — Start cloud live → **PASS**

### UNTESTED
- none within exploration caps

---

