# ARIA Failure Triage Report

Generated: 2026-08-11T03:41:07.427585+00:00

**Verdict:** `PRE-REPAIR TRIAGE COMPLETE — READY FOR REPAIR`

All **707** FAIL records classified. Unclassified: **0**. Unknown: **0**.

## Classification totals

- REAL APPLICATION BUG: **12**
- DUPLICATE: **0**
- TEST ARTIFACT: **665**
- INFRASTRUCTURE: **30**
- UNKNOWN: **0**

## BUG-024 (661)

```
BUG-024 REAL APPLICATION FAILURES = 0
BUG-024 TEST ARTIFACTS = 661
BUG-024 DUPLICATES = 0
BUG-024 UNKNOWN = 0
```

**Determination:** harness/discovery defect (state rediscovery, placeholder/id mismatch, truncated Export* labels, concatenated chips, meta discovery rows).

Sample evidence: `/tmp/aria-triage/samples/bug024_results.json` (n=72)

## Full FAIL classification ledger

| EXC ID | Room | Control | Bug | Category | Root | Confidence | Sample? |
|---|---|---|---|---|---|---|---|
| EXC-0002 | actions | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0003 | actions | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0004 | actions | Open Mission Control | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0006 | audio | Open Voice settings | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0007 | audio | Open Bullet Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0013 | audio | Send to chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0043 | audio | Play in player | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0060 | audio | Open editor | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0063 | audio | Path to audio file… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0064 | audio | e.g. fade in, make louder, trim first 5s | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0065 | audio | data/audio/edited/out.mp3 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0066 | audio | audioUploadFile | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0067 | audio | Or path under data/… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0068 | audio | Song path or use recent / upload | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0069 | audio | Target genre / style | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0071 | audio | Song topic e.g. summer road trip | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0072 | audio | Genre | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0073 | audio | Mood | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0075 | audio | Backing track path (music bed) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0076 | audio | Vocal path (or use last recording) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0078 | audio | Song title (optional) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0079 | audio | Style | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0080 | audio | Genre | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0082 | audio | Search indexed transcripts… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0084 | audio | Text for Piper or espeak… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0085 | audio | Lyrics (optional — auto-transcribed from recording) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0086 | audio | One path per line under data/… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0087 | audio | Calm piano, 90 BPM… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0096 | audio | EQ applied when ARIA plays audio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0097 | audio | Live system EQ via PipeWire | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0098 | audit | Open Mission Control | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0099 | audit | Open Actions checklist | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0148 | browser | Open Memory | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0149 | browser | Open Documents | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0150 | browser | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0152 | browser | Open | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0153 | browser | Bookmark current URL | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0154 | browser | Screenshot | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0155 | browser | Install Playwright | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0162 | browser | Screenshot → Coding proposal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0164 | browser | Queue in Job Center | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0172 | calendar | Jump to today (T) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0178 | calendar | Open Bullet Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0179 | calendar | Open Documents | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0188 | calendar | 2026-08-09 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0189 | calendar | 2026-08-10 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0190 | calendar | 2026-08-11 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0191 | calendar | 2026-08-12 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0192 | calendar | 2026-08-13 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0193 | calendar | 2026-08-14 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0194 | calendar | 2026-08-15 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0195 | calendar | 2026-08-16 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0196 | calendar | 2026-08-17 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0197 | calendar | 2026-08-18 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0198 | calendar | 2026-08-19 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0199 | calendar | 2026-08-20 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0200 | calendar | 2026-08-21 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0201 | calendar | 2026-08-22 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0202 | calendar | 2026-08-23 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0203 | calendar | 2026-08-24 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0220 | calendar | ghost-btn tiny cal-ws-add | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0221 | calendar | calWorkSaveBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0222 | calendar | calendarIcsTestBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0223 | calendar | calendarIcsSaveBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0224 | calendar | calendarIcsRefreshBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0225 | calendar | calendarVisionBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0226 | calendar | calendarMemoryBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0227 | calendar | calendarHaMeetingBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0235 | calendar | Label | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0236 | calendar | https://…/basic.ics | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0237 | calendar | Fly fishing, birthday, travel… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0248 | calendar | Jump to today (T) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0254 | calendar | Open Bullet Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0255 | calendar | Open Documents | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0264 | calendar | 2026-08-09 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0265 | calendar | 2026-08-10 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0273 | calendar | 2026-08-18 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0274 | calendar | 2026-08-19 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0275 | calendar | 2026-08-20 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0276 | calendar | 2026-08-21 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0277 | calendar | 2026-08-22 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0278 | calendar | 2026-08-23 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0279 | calendar | 2026-08-24 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0280 | calendar | 2026-08-25 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0281 | calendar | 2026-08-26 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0282 | calendar | 2026-08-27 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0283 | calendar | 2026-08-28 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0288 | calendar | Jump to today (T) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0294 | calendar | Open Bullet Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0295 | calendar | Open Documents | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0304 | calendar | 2026-08-09 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0305 | calendar | 2026-08-10 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0306 | calendar | 2026-08-11 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0312 | calendar | 2026-08-17 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0313 | calendar | 2026-08-18 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0314 | calendar | 2026-08-19 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0315 | calendar | 2026-08-20 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0316 | calendar | 2026-08-21 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0317 | calendar | 2026-08-22 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0318 | calendar | 2026-08-23 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0319 | calendar | 2026-08-24 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0320 | calendar | 2026-08-25 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0321 | calendar | 2026-08-26 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0322 | calendar | 2026-08-27 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0323 | calendar | 2026-08-28 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0327 | capabilities | Search capabilities… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0335 | capabilities | Search capabilities… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0341 | chat | Good morning | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0342 | chat | What should we work on? | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0343 | chat | Just listen for a bit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0346 | chat | Say anything… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0348 | chat | New conversation fresh | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0349 | chat | Place something here attach | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0350 | chat | Read aloud off | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0351 | chat | Voice when speaking | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0352 | chat | Open the front door Ctrl+K | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0353 | chat | Fork thread branch | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0354 | chat | Good morning | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0355 | chat | What should we work on? | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0356 | chat | Just listen for a bit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0359 | chat | Say anything… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0362 | coding | Workspace identity | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0363 | coding | Live coding jobs | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0364 | coding | Coding model role | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0365 | connections | Shortcuts | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0376 | connections | Shortcuts | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0387 | documents | Shortcuts | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0395 | documents | Import Folder | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0398 | documents | Learn → candidates | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0400 | documents | Document Briefing | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0401 | documents | Open Memory | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0403 | documents | test | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0404 | documents | resume | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0405 | documents | warranty | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0406 | documents | readme | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0407 | documents | aria | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0408 | documents | memory | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0409 | documents | ship | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0414 | flytying | Guided library setup & health | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0416 | flytying | Open Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0421 | flytying | Voice: next step | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0422 | flytying | Voice: repeat step | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0424 | flytying | Clear search and type filter | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0430 | flytying | What ▲ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0435 | flytying | Edit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0436 | flytying | Remove material | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0437 | flytying | Import lines | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0438 | flytying | flytyingCameraScanBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0439 | flytying | flytyingScanPhotoBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0440 | flytying | flytyingLabelBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0443 | flytying | Search patterns… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0446 | flytying | Paste YouTube, Vimeo, or Fly Fish Food URL… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0447 | flytying | Filter videos… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0449 | flytying | hook, thread… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0451 | flytying | 14, 8/0 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0452 | flytying | Uni | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0453 | flytying | optional | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0454 | flytying | Scan or type barcode… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0455 | flytying | e.g. olive 14 dry hook, grizzly hackle, Uni 8/0 olive thread | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0456 | flytying | size 14 dry hook olive dubbing | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0457 | flytying | Ask about a pattern, hatch, or design a new fly… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0458 | flytying | Fly tying model (7b = recipes, 14b = design) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0460 | flytying | Fly type | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0463 | flytying | Guided library setup & health | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0465 | flytying | Open Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0470 | flytying | Voice: next step | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0471 | flytying | Voice: repeat step | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0473 | flytying | Clear search and type filter | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0479 | flytying | What ▲ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0484 | flytying | Edit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0485 | flytying | Remove material | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0487 | flytying | flytyingCameraScanBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0488 | flytying | flytyingScanPhotoBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0489 | flytying | flytyingLabelBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0492 | flytying | Search patterns… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0495 | flytying | Paste YouTube, Vimeo, or Fly Fish Food URL… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0496 | flytying | Filter videos… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0498 | flytying | hook, thread… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0500 | flytying | Guided library setup & health | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0502 | flytying | Open Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0507 | flytying | Voice: next step | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0508 | flytying | Voice: repeat step | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0510 | flytying | Clear search and type filter | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0516 | flytying | What ▲ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0521 | flytying | Edit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0522 | flytying | Remove material | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0524 | flytying | flytyingCameraScanBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0525 | flytying | flytyingScanPhotoBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0526 | flytying | flytyingLabelBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0529 | flytying | Search patterns… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0532 | flytying | Paste YouTube, Vimeo, or Fly Fish Food URL… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0533 | flytying | Filter videos… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0535 | flytying | hook, thread… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0537 | flytying | Guided library setup & health | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0539 | flytying | Open Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0544 | flytying | Voice: next step | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0545 | flytying | Voice: repeat step | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0547 | flytying | Clear search and type filter | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0553 | flytying | What ▲ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0559 | flytying | Cancel | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0560 | flytying | Edit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0561 | flytying | Remove material | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0563 | flytying | flytyingCameraScanBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0564 | flytying | flytyingScanPhotoBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0565 | flytying | flytyingLabelBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0568 | flytying | Search patterns… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0571 | flytying | Paste YouTube, Vimeo, or Fly Fish Food URL… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0572 | flytying | Filter videos… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0577 | gallery | Open Maker lab | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0578 | gallery | Open Fly tying | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0579 | gallery | Open Video Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0580 | gallery | Open Meme Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0584 | gallery | Reuse last settings with a new seed | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0592 | gallery | Opt-in Vision caption | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0611 | gallery | Open Maker lab | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0612 | gallery | Open Fly tying | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0613 | gallery | Open Video Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0614 | gallery | Open Meme Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0618 | gallery | Reuse last settings with a new seed | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0626 | gallery | Opt-in Vision caption | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0647 | gallery | Aspect ratio | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0651 | gallery | Open Maker lab | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0652 | gallery | Open Fly tying | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0653 | gallery | Open Video Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0654 | gallery | Open Meme Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0658 | gallery | Reuse last settings with a new seed | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0666 | gallery | Opt-in Vision caption | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0669 | gallery | Vision→Coding | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0670 | gallery | Similarity clusters | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0671 | gallery | Focus prompt | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0672 | gallery | Open ComfyUI ↗ | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0673 | gallery | Image generation prompt | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0674 | gallery | on | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0675 | gallery | Negative prompt | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0676 | gallery | Seed | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0677 | gallery | on | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0678 | gallery | Steps | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0679 | gallery | CFG | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0680 | gallery | Variations count | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0681 | gallery | Width | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0682 | gallery | Height | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0683 | gallery | Search gallery | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0684 | gallery | on | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0685 | gallery | on | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0686 | gallery | Enhanced prompt | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0687 | gallery | Generation preset | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0688 | gallery | Focus prompt | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0689 | gallery | Flux Schnell (best prompts) SDXL 1.0 (quality) SDXL Turbo (f | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0690 | gallery | Auto (GPU → CPU fallback) GPU only CPU only | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0691 | gallery | Sort | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0695 | gallery | Open Maker lab | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0696 | gallery | Open Fly tying | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0697 | gallery | Open Video Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0698 | gallery | Open Meme Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0702 | gallery | Reuse last settings with a new seed | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0710 | gallery | Opt-in Vision caption | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0713 | gallery | Vision→Coding | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0714 | gallery | Similarity clusters | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0715 | gallery | Focus prompt | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0716 | gallery | Open ComfyUI ↗ | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0717 | gallery | Image generation prompt | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0718 | gallery | on | BUG-INFRA-001 | INFRASTRUCTURE | ROOT-INFRA-001 | HIGH | no |
| EXC-0766 | home | Open Planner | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0767 | home | Open Bullet Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0768 | home | Open Calendar | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0773 | home | 4–6 digit PIN | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0778 | home | Open Planner | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0779 | home | Open Bullet Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0780 | home | Open Calendar | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0785 | home | 4–6 digit PIN | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0789 | home_automation | Open Presence | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0790 | home_automation | Open Security | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0792 | home_automation | Open Home Assistant | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0799 | home_automation | ghost-btn small ha-quick-btn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0807 | home_automation | scene.leaving (optional) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0808 | home_automation | scene.leaving | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0816 | integrations | Search providers… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0822 | integrations | Search providers… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0839 | journal | Distraction-free writing (W) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0840 | journal | Calendar = scheduled commitments | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0841 | journal | Planner = actionable work | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0842 | journal | Memory = lasting knowledge | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0844 | journal | AI reflection (you start it) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0845 | journal | Suggest promotions — confirm each | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0846 | journal | Month-end review wizard | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0847 | journal | journalOpenDocumentsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0848 | journal | journalOpenAudioBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0849 | journal | journalPrintBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0850 | journal | journalPdfBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0851 | journal | journalExportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0852 | journal | journalExportEncBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0853 | journal | journalImportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0854 | journal | journalImportEncBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0855 | journal | journalBackupBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0856 | journal | Voice → rapid log draft | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0857 | journal | Paste OCR / scan text | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0858 | journal | journalShortcutsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0859 | journal | journalUndoBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0860 | journal | journalRedoBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0861 | journal | journalMigrateBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0866 | journal | Rapid log — one line per entry. Indent 2 spaces to nest unde | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0880 | journal | Distraction-free writing (W) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0881 | journal | Calendar = scheduled commitments | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0882 | journal | Planner = actionable work | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0883 | journal | Memory = lasting knowledge | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0885 | journal | AI reflection (you start it) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0886 | journal | Suggest promotions — confirm each | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0887 | journal | Month-end review wizard | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0888 | journal | journalOpenDocumentsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0889 | journal | journalOpenAudioBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0890 | journal | journalPrintBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0891 | journal | journalPdfBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0892 | journal | journalExportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0893 | journal | journalExportEncBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0894 | journal | journalImportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0895 | journal | journalImportEncBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0896 | journal | journalBackupBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0897 | journal | Voice → rapid log draft | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0898 | journal | Paste OCR / scan text | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0899 | journal | journalShortcutsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0900 | journal | journalUndoBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0901 | journal | journalRedoBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0902 | journal | journalMigrateBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0907 | journal | Rapid log — one line per entry. Indent 2 spaces to nest unde | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0920 | journal | Distraction-free writing (W) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0921 | journal | Calendar = scheduled commitments | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0922 | journal | Planner = actionable work | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0923 | journal | Memory = lasting knowledge | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0925 | journal | AI reflection (you start it) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0926 | journal | Suggest promotions — confirm each | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0927 | journal | Month-end review wizard | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0937 | journal | Voice → rapid log draft | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0938 | journal | Paste OCR / scan text | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0944 | journal | 2026-08-10 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0947 | journal | Rapid log — one line per entry. Indent 2 spaces to nest unde | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0951 | maker | Generate | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0952 | maker | Iterate | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0953 | maker | Hello cube | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0954 | maker | Slice | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0955 | maker | Download STL | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0956 | maker | Refresh | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0957 | maker | Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0961 | maker | Add | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0962 | maker | Discover KE | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0963 | maker | Status | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0964 | maker | Start print | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0965 | maker | Design a 5 inch to 4 inch hose adapter… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0966 | maker | Iterate: make it taller, add mounting holes… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0967 | maker | Printer name | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0968 | maker | IP for Creality KE (e.g. 192.168.1.50) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0969 | maker | CAD backend | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0970 | maker | Printer model | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0972 | maker | Generate | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0973 | maker | Iterate | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0974 | maker | Hello cube | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0975 | maker | Slice | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0976 | maker | Download STL | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0977 | maker | Refresh | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-0978 | maker | Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0982 | maker | Add | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0983 | maker | Discover KE | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0984 | maker | Status | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0985 | maker | Start print | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0986 | maker | Design a 5 inch to 4 inch hose adapter… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0987 | maker | Iterate: make it taller, add mounting holes… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0988 | maker | Printer name | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0989 | maker | IP for Creality KE (e.g. 192.168.1.50) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0990 | maker | CAD backend | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0991 | maker | Printer model | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0993 | meme | Open Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0994 | meme | Open Video Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0997 | meme | e.g. when ARIA finally works on the first try | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0998 | meme | WHEN YOU RESTART | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-0999 | meme | AND IT ACTUALLY HELPS | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1001 | memory | Search (/) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1002 | memory | New memory (N) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1010 | memory | cheatsheetViewBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1011 | memory | cheatsheetEditBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1012 | memory | cheatsheetResetBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1013 | memory | memoryOpenJournalBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1014 | memory | memoryOpenProjectsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1015 | memory | memoryOpenBrowserBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1016 | memory | memoryOpenDocumentsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1017 | memory | Knowledge Briefs (research) — not Connections or Memory | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1018 | memory | memoryExportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1019 | memory | memoryImportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1020 | memory | memoryPruneBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1021 | memory | memoryScrubBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1023 | memory | Relationship explorer | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1036 | memory | Search (/) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1037 | memory | New memory (N) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1045 | memory | cheatsheetViewBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1046 | memory | cheatsheetEditBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1047 | memory | cheatsheetResetBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1048 | memory | memoryOpenJournalBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1049 | memory | memoryOpenProjectsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1050 | memory | memoryOpenBrowserBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1051 | memory | memoryOpenDocumentsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1052 | memory | Knowledge Briefs (research) — not Connections or Memory | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1053 | memory | memoryExportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1054 | memory | memoryImportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1055 | memory | memoryPruneBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1056 | memory | memoryScrubBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1058 | memory | Relationship explorer | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1071 | memory | Search (/) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1072 | memory | New memory (N) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1080 | memory | cheatsheetViewBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1081 | memory | cheatsheetEditBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1082 | memory | cheatsheetResetBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1083 | memory | memoryOpenJournalBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1084 | memory | memoryOpenProjectsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1085 | memory | memoryOpenBrowserBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1086 | memory | memoryOpenDocumentsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1087 | memory | Knowledge Briefs (research) — not Connections or Memory | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1088 | memory | memoryExportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1089 | memory | memoryImportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1090 | memory | memoryPruneBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1091 | memory | memoryScrubBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1093 | memory | Relationship explorer | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1106 | memory | Search (/) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1107 | memory | New memory (N) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1115 | memory | cheatsheetViewBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1116 | memory | cheatsheetEditBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1117 | memory | cheatsheetResetBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1118 | memory | memoryOpenJournalBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1119 | memory | memoryOpenProjectsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1120 | memory | memoryOpenBrowserBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1121 | memory | memoryOpenDocumentsBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1122 | memory | Knowledge Briefs (research) — not Connections or Memory | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1123 | memory | memoryExportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1124 | memory | memoryImportBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1125 | memory | memoryPruneBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1126 | memory | memoryScrubBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1128 | memory | Relationship explorer | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1143 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1144 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1145 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1146 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1167 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1168 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1169 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1170 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1176 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1191 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1192 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1193 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1194 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1200 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1215 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1216 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1217 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1218 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1224 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1239 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1240 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1241 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1242 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1248 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1263 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1264 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1265 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1266 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1272 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1287 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1288 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1289 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1290 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1296 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1311 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1312 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1313 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1314 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1320 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1335 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1336 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1337 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1338 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1344 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1359 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1360 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1361 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1362 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1368 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1383 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1384 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1385 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1386 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1392 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1407 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1408 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1409 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1410 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1416 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1431 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1432 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1433 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1434 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1440 | mission | Advanced ▾ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1453 | mission | JSON | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1454 | mission | CSV | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1455 | mission | Markdown | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1456 | mission | HTML | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1457 | mission | Search timeline… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1458 | mission | All severities Info Warning Error | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1461 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1462 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1463 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1464 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1470 | mission | Advanced ▸ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1471 | mission | JSON | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1472 | mission | CSV | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1473 | mission | Markdown | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1474 | mission | HTML | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1475 | mission | Search timeline… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1476 | mission | All severities Info Warning Error | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1479 | mission | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1480 | mission | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1481 | mission | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1482 | mission | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1488 | mission | Advanced ▸ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1489 | mission | JSON | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1490 | mission | CSV | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1491 | mission | Markdown | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1492 | mission | HTML | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1493 | mission | Search timeline… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1494 | mission | All severities Info Warning Error | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1495 | planner | Notes, reflections, logs | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1496 | planner | Scheduled commitments | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1499 | planner | Ask Aria to promote a Journal item | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1500 | planner | Add task | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1501 | planner | Ask Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1502 | planner | Open Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1504 | planner | 25 min focus timer (with optional HA Focus scene) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1505 | planner | Start Focus 25m | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1507 | planner | Add alarm | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1509 | planner | Add event | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1510 | planner | Open Calendar | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1521 | planner | Notes, reflections, logs | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1522 | planner | Scheduled commitments | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1524 | planner | Plan My Day | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1525 | planner | Start Focus Session | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1526 | planner | Review Morning Plan | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1527 | planner | Reprioritize | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1528 | planner | Ask Aria | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1532 | planner | Vision capture | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1533 | planner | Suggest schedule | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1534 | planner | Undo last Planner delete | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1536 | planner | Ask Aria to promote a Journal item | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1537 | planner | Add task | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1538 | planner | Ask Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1539 | planner | Open Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1541 | planner | 25 min focus timer (with optional HA Focus scene) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1542 | planner | Start Focus 25m | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1544 | planner | Add alarm | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1546 | planner | Add event | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1547 | planner | Open Calendar | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1558 | planner | Notes, reflections, logs | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1559 | planner | Scheduled commitments | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1561 | planner | Plan My Day | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1562 | planner | Start Focus Session | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1563 | planner | Review Morning Plan | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1564 | planner | Reprioritize | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1565 | planner | Ask Aria | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1569 | planner | Vision capture | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1570 | planner | Suggest schedule | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1571 | planner | Undo last Planner delete | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1573 | planner | Ask Aria to promote a Journal item | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1574 | planner | Add task | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1575 | planner | Ask Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1576 | planner | Open Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1578 | planner | 25 min focus timer (with optional HA Focus scene) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1579 | planner | Start Focus 25m | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1581 | planner | Add alarm | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1583 | planner | Add event | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1584 | planner | Open Calendar | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1595 | planner | Notes, reflections, logs | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1596 | planner | Scheduled commitments | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1598 | planner | Plan My Day | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1599 | planner | Start Focus Session | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1600 | planner | Review Morning Plan | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1601 | planner | Reprioritize | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1602 | planner | Ask Aria | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1606 | planner | Vision capture | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1607 | planner | Suggest schedule | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1608 | planner | Undo last Planner delete | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1610 | planner | Ask Aria to promote a Journal item | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1611 | planner | Add task | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1612 | planner | Ask Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1613 | planner | Open Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1615 | planner | 25 min focus timer (with optional HA Focus scene) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1616 | planner | Start Focus 25m | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1618 | planner | Add alarm | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1620 | planner | Add event | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1621 | planner | Open Calendar | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1632 | planner | Notes, reflections, logs | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1633 | planner | Scheduled commitments | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1635 | planner | Plan My Day | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1636 | planner | Start Focus Session | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1637 | planner | Review Morning Plan | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1638 | planner | Reprioritize | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1639 | planner | Ask Aria | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1643 | planner | Vision capture | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1644 | planner | Suggest schedule | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1645 | planner | Undo last Planner delete | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1647 | planner | Ask Aria to promote a Journal item | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1648 | planner | Add task | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1649 | planner | Ask Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1650 | planner | Open Journal | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1652 | planner | 25 min focus timer (with optional HA Focus scene) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1653 | planner | Start Focus 25m | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1655 | planner | Add alarm | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1657 | planner | Add event | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1658 | planner | Open Calendar | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1669 | presence | Open Security | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1670 | presence | Open Voice | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1676 | projects | Shortcuts | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1684 | providers | Provider / VRAM health | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1687 | repair | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1688 | repair | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1689 | repair | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1690 | repair | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1697 | repair | JSON | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1698 | repair | CSV | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1699 | repair | Markdown | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1700 | repair | HTML | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1701 | repair | Search timeline… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1702 | repair | All severities Info Warning Error | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1705 | repair | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1706 | repair | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1707 | repair | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1708 | repair | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1714 | repair | Advanced ▸ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1717 | repair | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1718 | repair | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1719 | repair | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1720 | repair | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1726 | repair | Advanced ▸ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1727 | repair | JSON | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1728 | repair | CSV | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1729 | repair | Markdown | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1730 | repair | HTML | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1731 | repair | Search timeline… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1732 | repair | All severities Info Warning Error | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1735 | repair | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1736 | repair | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1737 | repair | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1738 | repair | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1744 | repair | Advanced ▸ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1747 | repair | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1748 | repair | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1749 | repair | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1750 | repair | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1756 | repair | Advanced ▸ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1759 | repair | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1760 | repair | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1761 | repair | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1762 | repair | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1768 | repair | Advanced ▸ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1771 | repair | Open Notifications (Activity Center inbox) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1772 | repair | Open Chat | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1773 | repair | Open System audit | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1774 | repair | Open Home | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1798 | search | Search documents, memory, code, graph, planner… | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1801 | security | Open Presence | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1802 | security | Open Voice | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1806 | security | 4–6 digit PIN | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1815 | settings | Search preferences (PIN, theme, whisper, models…) | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1821 | video | Open Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1822 | video | Open Meme Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1830 | video | Unload Ollama from GPU before AnimateDiff | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1838 | video | videoUploadInput | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1840 | video | Open Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1841 | video | Open Meme Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1849 | video | Unload Ollama from GPU before AnimateDiff | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1861 | video | videoUploadInput | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1867 | video | Open Gallery | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1868 | video | Open Meme Studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1876 | video | Unload Ollama from GPU before AnimateDiff | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1882 | video | 8 | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1888 | video | videoUploadInput | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1902 | vision | optional question | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1906 | voice | Open Audio studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1907 | voice | Open Presence | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1911 | voice | Run recovery advisor | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1912 | voice | Toggle cloud live | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1922 | voice | Open Audio studio | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1923 | voice | Open Presence | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | HIGH | yes |
| EXC-1927 | voice | Run recovery advisor | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1939 | front_door | all destinations | BUG-011 | REAL_APPLICATION_BUG | ROOT-BUG-011 | HIGH | no |
| EXC-1941 | chat | Stop | BUG-005 | REAL_APPLICATION_BUG | ROOT-BUG-005 | HIGH | no |
| EXC-1943 | memory | chat remember → memory → recall → forget | BUG-013 | REAL_APPLICATION_BUG | ROOT-BUG-013 | HIGH | no |
| EXC-1944 | flytying | all visible tabs + inventory add | BUG-014 | REAL_APPLICATION_BUG | ROOT-BUG-014 | HIGH | no |
| EXC-1945 | planner | add task form | BUG-015 | REAL_APPLICATION_BUG | ROOT-BUG-015 | HIGH | no |
| EXC-1947 | providers | Roles/Catalog tabs + selects | BUG-018 | REAL_APPLICATION_BUG | ROOT-BUG-018 | HIGH | no |
| EXC-1949 | activity | inbox open/read/dismiss + quality | BUG-003 | REAL_APPLICATION_BUG | ROOT-BUG-003 | HIGH | no |
| EXC-1950 | mission | health summary | BUG-006 | REAL_APPLICATION_BUG | ROOT-BUG-006 | HIGH | no |
| EXC-1956 | shell | health emergency report link/navigation | BUG-023 | REAL_APPLICATION_BUG | ROOT-023 | HIGH | no |
| EXC-1986 | flytying | Brand ▲ | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-1987 | flytying | Scan barcode | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-2018 | memory | memoryOpenKnowledgeBtn | BUG-024 | TEST_ARTIFACT | ROOT-024-HARNESS-STATE | MEDIUM | no |
| EXC-2158 | all | final discovery scan cycle 1 | — | TEST_ARTIFACT | ROOT-DISCOVERY-META | HIGH | no |
| EXC-2159 | all | final discovery scan cycle 2 | — | TEST_ARTIFACT | ROOT-DISCOVERY-META | HIGH | no |
| EXC-2160 | all | final discovery scan cycle 3 | — | TEST_ARTIFACT | ROOT-DISCOVERY-META | HIGH | no |
| EXC-2183 | audio | EXP-BUG-002 | BUG-002 | REAL_APPLICATION_BUG | ROOT-BUG-002 | HIGH | no |
| EXC-2184 | activity | EXP-BUG-003 | BUG-003 | REAL_APPLICATION_BUG | ROOT-BUG-003 | HIGH | no |
| EXC-2185 | mission | EXP-BUG-006 | BUG-006 | REAL_APPLICATION_BUG | ROOT-BUG-006 | HIGH | no |
| EXC-2187 | all | function-normalized final discovery | — | TEST_ARTIFACT | ROOT-DISCOVERY-META | HIGH | no |
