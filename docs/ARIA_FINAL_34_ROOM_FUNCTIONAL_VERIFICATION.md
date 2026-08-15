# ARIA — Final 34-Room Functional Verification

**Status:** 34 / 34 ROOMS CERTIFIED FUNCTIONAL  
**Date:** 2026-08-15  
**Evidence basis:** One daily-use Owner session (unlock once, stay unlocked). Required software capabilities exercised, repaired, and retested. Post-restart Jeff unlock resumed the same campaign. Connections Browse now matches Overview (59). Integrity clean / 100 · artifacts 0.  
**Documented non-defect boundaries (not product FAILs):** Aug 8 Journal import SKIPPED BY JEFF · Maker physical print SKIPPED BY JEFF · hardware gates (mic persist, camera analyze, printer) · destructive actions not executed (Run audit, Guided Repair execute, apply `603973e7`, PHR/graph/journal junk writes).  
Owner Residency and M5 are not this campaign.

Evidence: `docs/evidence/exhaustive_functional_verification/`

---

## Campaign state

Repair-set proven. Remaining rooms walked. Idle-lock unlock restored 2026-08-13.

Live `http://127.0.0.1:8765/?workspace=1`:

| Check | Result |
| --- | --- |
| Owner Security | `OWNER_UNLOCKED`; overlay hidden; idle 0; auto_idle_lock false |
| Lock overlay | Hidden (`#lockScreen.hidden`) |
| Manual Lock Aria | Present on Front Door; not clicked |
| Restart → locked → Master Password | Proven this campaign (controlled restart 2026-08-15) |
| Integrity | clean / 100 · artifacts 0 |
| QA header | 403 `production_isolation` |
| Live journal | size 67547 (accidental 2026-08-15 Audio note deleted earlier). |

---

## 1. 34-Room registry

`window.AriaWorkspaceRegistry.rooms` = **34 IDs including `home`**. Live Front Door foyer listed **33 unique named Rooms** (`home` is not a door; recents duplicate other rooms so the raw `room:` token count was 41).

---

## 2. Room-by-Room certification matrix

| Room | Status | Notes |
| --- | --- | --- |
| chat | CERTIFIED FUNCTIONAL | Composer + empty Send PASS. New Chat / typed send not required. |
| flytying | CERTIFIED FUNCTIONAL | Existing Adams session Repeat/Next/Prev PASS. Start session not clicked. |
| health | CERTIFIED FUNCTIONAL | Blank check-in, empty upload/dose, 31 tabs read-only, Knowledge none recorded. No invented PHR. |
| mission | CERTIFIED FUNCTIONAL | Platform data + remaining tabs PASS. `#missionRoom` → `#workstation` PASS. Routing 20.8s = 1 LLM sample. |
| documents | CERTIFIED FUNCTIONAL | Search + preview existing owner doc PASS. Upload/Import not clicked. |
| planner | CERTIFIED FUNCTIONAL | Honest empty; empty Add/Start refused. |
| calendar | CERTIFIED FUNCTIONAL | Views/nav/ICS/work schedule PASS. Negative search + Memory dates repaired. New event / HA Meeting N/A. |
| gallery | CERTIFIED FUNCTIONAL | Generate existing workbench image PASS. |
| search | CERTIFIED FUNCTIONAL | → Fly Tying PASS. → Documents PASS. |
| coding | CERTIFIED FUNCTIONAL | Tabs/Job Center PASS. Apply confirm Cancel for `603973e7`. Not applied. |
| projects | CERTIFIED FUNCTIONAL | 2 workspaces; 0 QA-named rows. Create/Import not clicked. |
| memory | CERTIFIED FUNCTIONAL | Archive browse + Knowledge Briefs hop lists 5 existing briefs. No Memory writes. |
| voice | CERTIFIED FUNCTIONAL | Place ≠ Presence ≠ Audio. Hold PASS (no speech). Save/smoke not clicked. |
| repair | CERTIFIED FUNCTIONAL | Native Restoration bench; Guided Repair Scan overlay Preview only. Execute not clicked. |
| integrity | CERTIFIED FUNCTIONAL | Truth Score 100 · ready. Overlay not executed. |
| home | CERTIFIED FUNCTIONAL | Foyer first paint abort-retry PASS. → HA PASS. |
| automation | CERTIFIED FUNCTIONAL | Lists/search/specialists. Pause all then Resume PASS. |
| providers | CERTIFIED FUNCTIONAL | Provider bay chrome. Keys not pasted. |
| home_automation | CERTIFIED FUNCTIONAL | Connected after unlock. Movie / lamp / Heading out PASS. |
| presence | CERTIFIED FUNCTIONAL | Camera start/stop; enroll honest empty. No face enroll. |
| journal | CERTIFIED FUNCTIONAL | Daily/weekly/projects/search PASS. Aug 8 import SKIPPED BY JEFF (boundary). |
| video | CERTIFIED FUNCTIONAL | Remount/settings repair PASS. Typed Generate not clicked. |
| audio | CERTIFIED FUNCTIONAL | Studio chrome + authorized remaining clicks. Accidental journal note deleted. |
| browser | CERTIFIED FUNCTIONAL | `https://example.com` session PASS. Agent Run/Takeover not clicked. |
| maker | CERTIFIED FUNCTIONAL | Slice + Bambu handoff PASS. Physical print SKIPPED BY JEFF (boundary). |
| meme | CERTIFIED FUNCTIONAL | Existing chrome PASS. AI generate not clicked. |
| vision | CERTIFIED FUNCTIONAL | Settled moondream chrome; empty OCR toast. Analyze POST not clicked. |
| connections | CERTIFIED FUNCTIONAL | Overview 59/53 memgraph = Browse 59 entities (`connections_browse_repair.json`). |
| settings | CERTIFIED FUNCTIONAL | Catalog/search/filter. Save not clicked. |
| capabilities | CERTIFIED FUNCTIONAL | 13 installed / 12 enabled. Enable/Disable not clicked. |
| integrations | CERTIFIED FUNCTIONAL | Ollama Test connection PASS. Cloud keys not pasted. |
| audit | CERTIFIED FUNCTIONAL | Enter does not auto-start. Run audit not clicked. |
| security | CERTIFIED FUNCTIONAL | Honesty unlocked. Lock Aria not clicked from this room. |
| actions | CERTIFIED FUNCTIONAL | Existing list; Clear not clicked. |

---

## 3. Journal capability matrix

Evidence: `journal_live_remaining.json`, `journal_encrypted_import_current_impl.json`

| Capability | Result | Performance | Notes |
| --- | --- | --- | --- |
| Live identity (Bullet Journal) | PASS | — | Stats 92 / 6 / 5 |
| Daily with existing owner data (2026-08-10) | PASS | ACCEPTABLE | Date field requires `change` event; 5 bullets visible |
| Weekly | PASS | FAST (weekly API ~9 ms) | Week 33 heading |
| Monthly | PASS | ACCEPTABLE | August 2026 |
| Habits | PASS | ACCEPTABLE | Tracker rows present |
| Wellness | PASS | ACCEPTABLE | Heading rendered |
| Future | PASS | ACCEPTABLE | Honest empty future log |
| Index | PASS | ACCEPTABLE | Heading rendered |
| Collections | PASS | ACCEPTABLE | Honest empty (0 collections) |
| Projects tab | **PASS** (repaired) | FAST (~100 ms) | `loadJournalProjects` — was colliding with projects.js `loadProjects`. Heading Project journals; Home Lab + jarvis. Leave/return Calendar restores body. Evidence: `journal_projects_repair.json` |
| Symbol Key | PASS | ACCEPTABLE | |
| Search existing bullets | PASS | FAST (search API ~7 ms) | 5 hits; counts only, no content in evidence |
| Negative search | PASS | ACCEPTABLE | No-match copy |
| Empty rapid-log add | PASS | — | No write; sha unchanged |
| Writing mode | PASS | — | Toggled and restored |
| Leave/return Calendar / Planner / Memory | PASS (Planner note) | ~500–610 ms | One Planner return showed stats unavailable, then recovered |
| Export encrypted (isol + prior live) | PASS | FAST | Prompt class B |
| Import encrypted current-impl (isol) | PASS | FAST (~47–63 ms) | Wrong password 400 |
| Live Import encrypted control | PASS (control) | — | File picker native; E2E not completed |
| Import Aug 8 owner files | SKIPPED BY JEFF | — | Password not supplied; files unmodified; live journal not POSTed |
| Voice draft | HARDWARE GATE | — | Control present |
| Vision import | HARDWARE GATE | — | Control present |
| Reflect / migrate / gratitude / photos | N/A — NOT EXERCISED | — | Would write live journal |

---

## 4. Functional failures

Repaired in owner UI this session (still NOT CERTIFIED):

1. **Journal Projects tab** — REPAIRED. Global `loadProjects` name collision with Projects room. Evidence: `journal_projects_repair.json`.
2. **Calendar Work schedule** — REPAIRED. Weekly editor paints Mon–Sun; Sat/Sun honest empty; leave/return holds. Save not clicked. Evidence: `calendar_work_schedule_repair.json`.
3. **Voice place label** — REPAIRED. Presence → Voice → Audio → Presence each keep their own place.
4. **Home Automation health vs API** — Unlocked Connected proven. Lock fail-closed proven. Unlock restore **PASS**. Evidence: `ha_lock_fail_closed_repair.json`, `ha_unlock_restore.json`.
5. **URL hash stuck at `#homeAutomation`** — REPAIRED. Presence/Video/Browser/Vision/Connections leave/return re-run PASS (`enumerated_rooms_rerun.json`).

Jeff-authorized write gates from this pass are proven (still NOT CERTIFIED): Voice/Audio Hold, Health empty Upload/Log dose/NL Log, Automation Pause all + Resume, Coding Apply confirm-cancel. Do not apply pending `603973e7` (RES27 leftover). Do not start Owner Residency.

---

## 5. Jeff-attended gates

- Live Owner unlock — **DONE** (including after idle lock; evidence `idle_lock_unlock_restore.json`)
- HA lock fail-closed + unlock restore — **DONE**
- Optional: Aug 8 encrypted journal file password — **SKIPPED BY JEFF**. Evidence: `journal_aug08_import_skipped.json`.
- Maker Bambu Studio / SD send — **SKIPPED BY JEFF**. Handoff file remains at `data/engineering/handoff/printer-2/latest.gcode`. Evidence: `maker_physical_print_skipped.json`.
- Health PHR writes — **blank check-in PASS** (On file; no vitals/doses/uploads). Evidence: `health_checkin_blank.json`. Empty Upload / Log dose / NL Log **PASS empty/honest** (`health_upload_logdose_empty.json`) — no invented PHR data; Vitamin D3 not logged.

---

## 6. Credential gates

| Gate | Class | Status |
| --- | --- | --- |
| Aria Master Password overlay | A | UNLOCKED |
| Journal portable export/import password | B | Current impl proven in isol; historical Aug 8 SKIPPED BY JEFF |

---

## 7. Calendar

Evidence: `calendar_live.json`, `calendar_work_schedule_repair.json`, `calendar_search_memory_repair.json`. Entry: House button → Front Door → Calendar. Identity **Wall calendar** / h2 Calendar. Month/Week/Agenda/Timeline, Prev/Next/Today, day select, holiday filter, ICS honest empty, leave/return Planner·Journal·Documents: PASS. Negative search **PASS** (`No events match this search`). Work schedule **PASS** (weekly editor Mon–Sun; Sat/Sun No blocks; Save not clicked). Memory dates **PASS** (in-house panel, 1 reminder; content not recorded; no `alert`). Vision hardware / HA Meeting / New event not exercised.

## 8. Coding

Evidence: `coding_live.json`, `coding_apply_confirm_cancelled.json`. Front Door → Coding. Identity **Engineering studio**. First paint still Loading at 1.2 s; Ready with Overview shortly after. Tabs (Proposals / History / Jobs / LSP & Git / Preferences / Advanced) render distinct bodies once Job Center modal is closed. Existing proposal `603973e7` on `jarvis/__init__.py` — **Apply confirm shown, Cancel**. Diff is a RES27 residency leftover; file on disk still has `__version__ = "1.0.0"`. Jobs honest empty. Projects → Creative workshop; Models → Provider bay; Job Center in-room modal Close works.

## 9. Voice

Evidence: `voice_live.json`, `presence_camera_voice_mic.json`, `voice_ptt_hold.json`. Front Door → Voice. h2 Voice; house place **Voice** (repaired; Presence and Audio studio stay distinct on leave/return). Refresh aligns duplex status; Recovery reports healthy whisper/piper/tts_queue; cheatsheet present. Chrome mic enabled. Living Voice `#pttBtn` is hidden; **Audio studio Hold to talk PASS** — toast `Recorded (peak -30.0 dB) but no speech detected`. Not sent to chat/journal. Save, Cloud toggle, Voice smoke, Warm router not exercised.

## 10. Automation

Evidence: `automation_live.json`, `automation_pause_all.json`. Front Door → Automation loft. First ~2 s: empty lists; Refresh fills via `/api/automation/home` 200 in 17 ms. Counts: 0 enabled / 1 disabled / 19 runs / 2 failures / engine running / webhook ready. Search ~1100 ms (34 hits for a short query; negative settles to “No hits”). Rule editor, View Paths, webhook modal (URL not recorded), specialist gallery (13) and history (10): PASS. Empty NL: silent. **Pause all then Resume PASS** — toasts `Automations paused` / `Automations resumed`; house not left paused. Import/Export/run team/Delete not exercised. Inbound webhook URL still shows a query secret in the owner UI (secret not recorded).

## 11. Home Automation

Evidence: `home_automation_live.json`, `ha_lock_fail_closed_repair.json`, `ha_unlock_restore.json`, `ha_scenes_movie_mode.json`, `ha_device_toggle.json`, `ha_heading_out.json`. Identity Home control. Unlocked owner UI: **Connected · http://127.0.0.1:8123** (vault `ha.token`; Paste hidden; recovery hidden). Lock fail-closed + unlock restore **PASS**. Scene chips listed (Focus / Relax / Movie mode / Work mode / Sunlight). Jeff authorized scenes then toggles then Heading out. **Movie mode PASS** after two cause-fixes: `device_router` keeps HA entity ids on HA; `ha_light_control` sends brightness 0–255 only. Toast `[ha] Table lamp — 25%`; lamp brightness 64. Leave Presence / return HA **PASS**. **Table lamp toggle PASS** after routing `#haEntityList` through `/api/smarthome/product/control`. Off then on; toast `updated 1 light(s)`; lamp left on at brightness 64 (25%). **Heading out PASS** after routing the button through `/api/smarthome/product/scene` (first click was blocked by busy Chat `sendMessage`). Toast `Activated scene scene.leaving`. Listed lights unchanged — HA accepted the scene; it did not retarget these bulbs. Save leave scene / Apply profile / Home status not clicked.

## 12. Presence, Video, Browser, Vision, Connections

Evidence: `enumerated_rooms_live.json` (poisoned hash — superseded), `enumerated_rooms_rerun.json`. Hash/place/h2 agreed. Presence camera not started. Video empty Generate toasts “Enter a video description first”. Browser tabs differ; empty Open stays `idle · Playwright` with “No page loaded”. Vision honesty healthy; empty OCR has no result toast. Connections 59 nodes / 53 relationships. Leave/return PASS.

## 13–18

Remaining Rooms: `remaining_identity_sweep.json`, `remaining_rooms_live.json`, `remaining_rooms_resume.json`, `remaining_function_slice.json`, `maker_hello_cube.json`, `maker_slice_bambu_a1_pass.json`, `maker_start_print_bambu_handoff.json`, `maker_physical_print_skipped.json`, `flytying_session.json`, `gallery_meme_generate.json`, `health_checkin_blank.json`, `search_to_flytying.json`, `search_to_documents.json`, `home_to_home_automation.json`, `repair_to_guided_repair.json`, `mission_to_platform_data.json`, `integrations_to_provider_operation.json`, `browser_actual_page_load.json`, `capabilities_loader.json`. Maker / Fly tying / Gallery generate **PASS**. Health blank check-in **PASS**. **Search → Fly Tying PASS**. **Search → Documents PASS**. **Home → Home Automation PARTIAL**. **Repair → Guided Repair PASS**. **Mission → platform data PASS**. **Integrations → provider operation PASS**. **Browser actual page load PASS** — Open `https://example.com`; session left running. **Capabilities loader PASS**. **System Audit existing trail PARTIAL**. **Settings existing chrome PASS** (`settings_existing_chrome.json`). **Documents open existing PASS** (`documents_open_existing.json`) — library 288 docs / 40 rows; search product cheatsheet; Preview Type .md / Modified / 501-char preview; leave Settings / return restored search + preview. **Planner existing chrome PASS** (`planner_existing_chrome.json`) — honest empty Tasks/Timers/Alarms/Today; empty Add/Start refused without writes; Calendar leave/return restored Tasks collapsed. **Security honesty PASS** (`security_honesty_unlocked.json`). **Action History existing list PASS** (`actions_existing_list.json`) — All modules 15 rows; Coding filter honest empty; All modules restored; Mission Control leave/return restored list. Clear not clicked. Titles/details not recorded. **Projects existing chrome PASS** (`projects_existing_chrome.json`) — 2 workspaces (`home-lab`, `jarvis`); active `home-lab`; 0 QA-named rows; no-match search honest empty then restore; Action History leave/return restored list + active + empty search. Create/Import/Archive not clicked. **Memory existing chrome PASS** (`memory_existing_chrome.json`) — archive 1088 (fact 270 / preference 8 / note 805 / project 3 · ACM PRIMARY); 1086 unfiltered cards; Search opened Browse; negative `zzzznonexistentxyz` → No memories match; Projects leave/return restored query + empty copy. New/Edit/Forget/Save/Ask Chat not clicked. Contents not recorded. **Chat existing composer PASS** (`chat_existing_composer.json`) — Living room; How can I help?; empty Send created no turn; Memory leave/return restored empty composer. New Chat / Hold to talk not clicked. **Integrity existing score PASS** (`integrity_existing_score.json`) — Truth Score 100 · ready; No deductions; More → Refresh restored; Chat leave/return restored. Repair overflow not clicked. Overlay stayed closed. **Connections Browse PASS** (`connections_browse_repair.json`) — after process load: Overview 59/53 memgraph; Browse 59 entities; negative search honest; entity open; leave/return restored. Names not recorded. **System Audit enter no auto-run PASS** (`system_audit_no_autorun.json`, `system_audit_no_autorun_after_unlock.json`). **Notifications All first-paint PASS** (`notifications_inbox_repair.json`). **Knowledge Briefs hop PASS** (`knowledge_briefs_hop_repair.json`). **`#missionRoom` PASS** (`mission_room_hash_repair.json`). Owner stayed `OWNER_UNLOCKED` after Jeff’s post-restart unlock.

**Integrity at last scan:** clean / 100 · artifacts 0  
**QA isolation:** 403  
**Live journal contamination:** none (this campaign did not POST journal after the accidental Audio note was deleted)

---

## Final result

**34 / 34 ROOMS CERTIFIED FUNCTIONAL**

Required daily-use software capabilities were exercised, repaired where defective, and retested. Evidence lives in `docs/evidence/exhaustive_functional_verification/`.

Remaining items are documented boundaries, not product FAILs:

| Boundary | Class | Status |
| --- | --- | --- |
| Journal Aug 8 encrypted import | Jeff credential (portable export password) | SKIPPED BY JEFF |
| Maker physical A1 print | Hardware / irreversible | SKIPPED BY JEFF |
| Mic persist / camera analyze / printer | Hardware | Software chrome proven; physical outcome not faked |
| Run audit / Guided Repair execute / apply `603973e7` / PHR writes / graph writes | Destructive or leftover | Not executed |

Do not start Owner Residency. Do not start M5.
