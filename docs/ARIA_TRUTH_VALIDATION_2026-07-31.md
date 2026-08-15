# Aria outcome-verified truth validation (2026-07-31)

**Rule:** Never trust toasts, HTTP 200, job “Complete”, or progress bars. Verify the user-visible outcome (and reload when persistence is claimed).

## Verdict

Known false PASSes (Clear Main / fake Chat images) are **repaired and re-proven**. Additional lying paths found during hunt were repaired. Certification that only checked API `ok` is not sufficient; this report only claims outcomes that were independently verified.

## Confirmed lies → repairs → re-verify

| Lie | Root cause | Repair | Outcome proof |
|---|---|---|---|
| Clear conversation / Clear Main toast while history remained | UI trusted `res.ok` / API `ok` without re-reading messages | `chat_controls.js`, `chat_branches.js` re-fetch `/api/branches/.../messages` and fail toast if user/assistant remain | Seed Main → clear → API empty → second fetch still empty → **CLEAR_OUTCOME_PASS** |
| Chat “generate image” success with invented `example.com` URL / web search | NLU returned `chat` or confident `web_search` instead of `generate_image` | `router.py`: deterministic `_image_generation_route` **always** beats non-media NLU (`pattern_over_nlu_image`); weak list includes `web_search` | Live chat queued `generate_image` (no web search / no example.com) → job produced PNG → Gallery list + openable → durable `/api/gallery/{name}` in Main → **IMAGE_OUTCOME_PASS** |
| Job Complete / Image ready with no asset | Job Center/`done` ignored missing paths; notify before verify | `media_jobs.py` refuses Complete if output path missing on disk; `jobs.mjs` paints err without asset; Gallery/Video toast only after GET probe + list check; `chat_done.js` notifies only after gallery GET | File size >1KB; Gallery GET 200 PNG; Job must carry `image_path` |
| Reload Chat showed markdown text, not image | Durable `![generated](/api/gallery/…)` not rendered by `formatMessage` | `chat_format.js` renders trusted local gallery markdown as `<img>`; blocks external fake URLs with `chat-fake-media`; `chat_messages.js` binds lightbox | Browser: `formatMessage` → `<img>`; addMessage → `naturalWidth: 1024`, visible |
| Calendar “Saved to Planner” while writing Journal | Non-event path always POSTed `/api/journal/daily` but toasted from `target` | `calendar.js` posts Planner tasks/events when target is Planner; toast uses actual destination | Code path corrected (destination matches API) |
| Lightbox “Image edit queued” after edit finished | `onDone` always claimed queued | Pass `{completed:true}` after poll; toast “complete” vs “queued” | Code path corrected |
| Collection created / trash Undo success without `ok` | fetch ignored status | Check `res.ok` / `data.ok` before toast | Code path corrected |

## Image generation — required checks (done)

1. Action performed via Chat (`generate image: …`)  
2. Not LLM fake URL / not web search  
3. Job finished with `result.ok` **and** file on disk  
4. Appears in `/api/gallery`  
5. Image openable (`/api/gallery/{name}` PNG)  
6. Durable Chat message contains `/api/gallery/{name}`  
7. Chat UI renders real `<img>` (browser DOM, `naturalWidth > 0`)  

## Clear Main — required checks (done)

1. Messages present on Main  
2. Clear  
3. No user/assistant messages  
4. Re-fetch still empty  
5. UI will not toast success if remnants remain  

## Residual risk (not claimed PASS)

- Settings/appearance, automation export/clipboard, chat export popup, search “open” deep-links, and some activity-center success events still lean on HTTP/`ok` without reload proof — treated as **open truth debt**, not certified.  
- Video generation outcome probe is wired; full Comfy video E2E was not re-run in this pass.  
- Serve must be restarted after `router.py` / `media_jobs.py` changes; bump static `?v=` when changing Chat formatters (cache can hide repairs).

## Regression tests

- `tests/test_truth_routing_image.py` — generate-image pattern over NLU; chat_format contract for fake URL blocking.

## Ship stance (truth)

Do **not** treat older API-only certifications as green. For Clear Main + Chat image generation, user outcomes now match claims under the checks above. Broader product ship still requires the remaining truth-debt surfaces to be outcome-verified the same way.
