# ARIA Execution Closure Matrix

Generated: 2026-08-10T21:56:10.063080+00:00

Verdict context: `EXECUTION CLOSURE COMPLETE — BUGS FOUND`

- Ledger items: **2188**
- PASS: **1458**
- FAIL: **707**
- NOT TESTABLE: **23**
- UNTESTED: **0**
- UNACCOUNTED: **0**

| ID | Room | Control | State | Discovery | Executed | Status | Bug | Evidence | Not-testable reason |
|---|---|---|---|---|---|---|---|---|---|
| EXC-0001 | actions | Clear | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-019.json | — |
| EXC-0002 | actions | Open Chat | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-020.json | — |
| EXC-0003 | actions | Open System audit | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-021.json | — |
| EXC-0004 | actions | Open Mission Control | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-022.json | — |
| EXC-0005 | actions | All modules Coding Home Assistant Documents Image | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-023.json | — |
| EXC-0006 | audio | Open Voice settings | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-024.json | — |
| EXC-0007 | audio | Open Bullet Journal | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-025.json | — |
| EXC-0008 | audio | Test mic (2s) | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-026.json | — |
| EXC-0009 | audio | Record only | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-027.json | — |
| EXC-0010 | audio | Record + transcribe | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-028.json | — |
| EXC-0011 | audio | Play on Sound Blaster | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-029.json | — |
| EXC-0012 | audio | Copy | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-030.json | — |
| EXC-0013 | audio | Send to chat | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0013.json | — |
| EXC-0014 | audio | Add to journal | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-031.json | — |
| EXC-0015 | audio | Summarize | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-032.json | — |
| EXC-0016 | audio | Apply trim | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-033.json | — |
| EXC-0017 | audio | Normalize | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-034.json | — |
| EXC-0018 | audio | Edit | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-035.json | — |
| EXC-0019 | audio | Convert | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-183.json | — |
| EXC-0020 | audio | Transcribe upload | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-184.json | — |
| EXC-0021 | audio | Transcribe path | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-185.json | — |
| EXC-0022 | audio | Generate speech | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-186.json | — |
| EXC-0023 | audio | Generate + play | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-187.json | — |
| EXC-0024 | audio | Upload | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-188.json | — |
| EXC-0025 | audio | Transform genre | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-189.json | — |
| EXC-0026 | audio | Generate song | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-190.json | — |
| EXC-0027 | audio | Mix tracks | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0027.json | — |
| EXC-0028 | audio | Make my voice a song | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0028.json | — |
| EXC-0029 | audio | Preview trim | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0029.json | — |
| EXC-0030 | audio | Diarize speakers | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0030.json | — |
| EXC-0031 | audio | Stream transcribe file | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0031.json | — |
| EXC-0032 | audio | Detect language | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0032.json | — |
| EXC-0033 | audio | Voice | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0033.json | — |
| EXC-0034 | audio | Music | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0034.json | — |
| EXC-0035 | audio | Flat | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0035.json | — |
| EXC-0036 | audio | Process file | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0036.json | — |
| EXC-0037 | audio | Install PipeWire filter configs | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0037.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (credentials/system control) |
| EXC-0038 | audio | Start wake word | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0038.json | — |
| EXC-0039 | audio | Stop wake word | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0039.json | — |
| EXC-0040 | audio | Search | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0040.json | — |
| EXC-0041 | audio | Transcribe all | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0041.json | — |
| EXC-0042 | audio | Generate music | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0042.json | — |
| EXC-0043 | audio | Play in player | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0043.json | — |
| EXC-0044 | audio | Delete recording_ptt_20260730_161305_ptt_raw.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0044.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real recording/media file) |
| EXC-0045 | audio | Delete live_20260730_164009_raw.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0045.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real recording/media file) |
| EXC-0046 | audio | Delete recording_20260730_173355.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0046.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real recording/media file) |
| EXC-0047 | audio | Delete recording_20260730_172933.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0047.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real recording/media file) |
| EXC-0048 | audio | Delete recording_20260730_171640.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0048.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real recording/media file) |
| EXC-0049 | audio | Delete recording_20260730_152137.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0049.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real recording/media file) |
| EXC-0050 | audio | Delete live_20260726_185623.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0050.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real recording/media file) |
| EXC-0051 | audio | Delete live_20260726_165807.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0051.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real recording/media file) |
| EXC-0052 | audio | Delete ware_Foundation_2_About_the_Python_Sof.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0052.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real media/document file) |
| EXC-0053 | audio | Delete 1_For_more_about_the_foundation_s_missio.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0053.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real media/document file) |
| EXC-0054 | audio | Delete The_official_website_of_the_Python_Softw.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0054.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real media/document file) |
| EXC-0055 | audio | Delete the_RTX_3090.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0055.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real media/document file) |
| EXC-0056 | audio | Delete Stored_via_ACM_exact_acceptance_token.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0056.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real media/document file) |
| EXC-0057 | audio | Delete provide_a_list_or_more_details_I_can_he.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0057.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real media/document file) |
| EXC-0058 | audio | Delete For_example_you_might_have_things_like.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0058.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real media/document file) |
| EXC-0059 | audio | Delete Sure_To_help_you_check_your_fly_tying_m.wav | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0059.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (delete real media/document file) |
| EXC-0060 | audio | Open editor | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0060.json | — |
| EXC-0061 | audio | Ask Chat | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0061.json | — |
| EXC-0062 | audio | 5 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0062.json | — |
| EXC-0063 | audio | Path to audio file… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0063.json | — |
| EXC-0064 | audio | e.g. fade in, make louder, trim first 5s | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0064.json | — |
| EXC-0065 | audio | data/audio/edited/out.mp3 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0065.json | — |
| EXC-0066 | audio | audioUploadFile | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0066.json | — |
| EXC-0067 | audio | Or path under data/… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0067.json | — |
| EXC-0068 | audio | Song path or use recent / upload | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0068.json | — |
| EXC-0069 | audio | Target genre / style | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0069.json | — |
| EXC-0070 | audio | 30 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0070.json | — |
| EXC-0071 | audio | Song topic e.g. summer road trip | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0071.json | — |
| EXC-0072 | audio | Genre | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0072.json | — |
| EXC-0073 | audio | Mood | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0073.json | — |
| EXC-0074 | audio | 30 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0074.json | — |
| EXC-0075 | audio | Backing track path (music bed) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0075.json | — |
| EXC-0076 | audio | Vocal path (or use last recording) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0076.json | — |
| EXC-0077 | audio | 2 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0077.json | — |
| EXC-0078 | audio | Song title (optional) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0078.json | — |
| EXC-0079 | audio | Style | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0079.json | — |
| EXC-0080 | audio | Genre | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0080.json | — |
| EXC-0081 | audio | 30 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0081.json | — |
| EXC-0082 | audio | Search indexed transcripts… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0082.json | — |
| EXC-0083 | audio | 10 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0083.json | — |
| EXC-0084 | audio | Text for Piper or espeak… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0084.json | — |
| EXC-0085 | audio | Lyrics (optional — auto-transcribed from recording) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0085.json | — |
| EXC-0086 | audio | One path per line under data/… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0086.json | — |
| EXC-0087 | audio | Calm piano, 90 BPM… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0087.json | — |
| EXC-0088 | audio | tiny base small medium large | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0088.json | — |
| EXC-0089 | audio | auto en es fr de it pt ja ko zh ru ar hi | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0089.json | — |
| EXC-0090 | audio | 0.8× 0.9× 1× 1.1× 1.2× | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0090.json | — |
| EXC-0091 | audio | Rear desk mic (combo jack) Front gaming headset (combo jack) | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0091.json | — |
| EXC-0092 | audio | alsa_input.pci-0000_05_00.0.analog-stereo USB Microphone (mono-fallback) (webcam | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0092.json | — |
| EXC-0093 | audio | effect_input.jarvis_ae5_gaming effect_input.jarvis_ae5_music effect_input.jarvis | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0093.json | — |
| EXC-0094 | audio | 100% 125% 150% 175% 200% 250% | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0094.json | — |
| EXC-0095 | audio | Fixed duration VAD (trim silence) Push-to-talk (hold button) Live (VU + streamin | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0095.json | — |
| EXC-0096 | audio | EQ applied when ARIA plays audio | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0096.json | — |
| EXC-0097 | audio | Live system EQ via PipeWire | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0097.json | — |
| EXC-0098 | audit | Open Mission Control | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-036.json | — |
| EXC-0099 | audit | Open Actions checklist | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-037.json | — |
| EXC-0100 | automation | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-038.json | — |
| EXC-0101 | automation | Pause all | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-039.json | — |
| EXC-0102 | automation | Resume | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-040.json | — |
| EXC-0103 | automation | New rule | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-041.json | — |
| EXC-0104 | automation | Specialist team | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-042.json | — |
| EXC-0105 | automation | Specialists | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-043.json | — |
| EXC-0106 | automation | Team history | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-044.json | — |
| EXC-0107 | automation | View Paths | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-045.json | — |
| EXC-0108 | automation | Webhook | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-046.json | — |
| EXC-0109 | automation | Export | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-047.json | — |
| EXC-0110 | automation | Import | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-048.json | — |
| EXC-0111 | automation | Draft from NL | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-049.json | — |
| EXC-0112 | automation | NL draft | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-191.json | — |
| EXC-0113 | automation | Export | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-047.json | — |
| EXC-0114 | automation | Propose team | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-192.json | — |
| EXC-0115 | automation | Gallery | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-193.json | — |
| EXC-0116 | automation | History | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-194.json | — |
| EXC-0117 | automation | Search automation | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-195.json | — |
| EXC-0118 | automation | Natural language automation | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-196.json | — |
| EXC-0119 | automation | Search pipelines | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-197.json | — |
| EXC-0120 | automation | on | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-198.json | — |
| EXC-0121 | automation | Sort pipelines | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0121.json | — |
| EXC-0122 | automation | Refresh | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-038.json | — |
| EXC-0123 | automation | Pause all | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-039.json | — |
| EXC-0124 | automation | Resume | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-040.json | — |
| EXC-0125 | automation | New rule | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-041.json | — |
| EXC-0126 | automation | Specialist team | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-042.json | — |
| EXC-0127 | automation | Specialists | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-043.json | — |
| EXC-0128 | automation | Team history | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-044.json | — |
| EXC-0129 | automation | View Paths | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-045.json | — |
| EXC-0130 | automation | Webhook | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-046.json | — |
| EXC-0131 | automation | Export | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-047.json | — |
| EXC-0132 | automation | Import | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-048.json | — |
| EXC-0133 | automation | Draft from NL | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-049.json | — |
| EXC-0134 | automation | NL draft | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-191.json | — |
| EXC-0135 | automation | Export | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-047.json | — |
| EXC-0136 | automation | Propose team | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-192.json | — |
| EXC-0137 | automation | Gallery | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-193.json | — |
| EXC-0138 | automation | History | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-194.json | — |
| EXC-0139 | automation | Search automation | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-195.json | — |
| EXC-0140 | automation | Natural language automation | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-196.json | — |
| EXC-0141 | automation | Search pipelines | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-197.json | — |
| EXC-0142 | automation | on | AFTER:New rule | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-198.json | — |
| EXC-0143 | automation | Sort pipelines | AFTER:New rule | conditional | yes | PASS | — | by_id/EXC-0143.json | — |
| EXC-0144 | browser | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-050.json | — |
| EXC-0145 | browser | Projects | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-051.json | — |
| EXC-0146 | browser | Job Center | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-052.json | — |
| EXC-0147 | browser | Coding | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-053.json | — |
| EXC-0148 | browser | Open Memory | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-054.json | — |
| EXC-0149 | browser | Open Documents | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-055.json | — |
| EXC-0150 | browser | Open Chat | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-056.json | — |
| EXC-0151 | browser | Detach browser panel | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-057.json | — |
| EXC-0152 | browser | Open | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-058.json | — |
| EXC-0153 | browser | Bookmark current URL | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-059.json | — |
| EXC-0154 | browser | Screenshot | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-060.json | — |
| EXC-0155 | browser | Install Playwright | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-061.json | — |
| EXC-0156 | browser | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-050.json | — |
| EXC-0157 | browser | Pause | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-199.json | — |
| EXC-0158 | browser | Resume | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-200.json | — |
| EXC-0159 | browser | Takeover | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-201.json | — |
| EXC-0160 | browser | Stop | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-202.json | — |
| EXC-0161 | browser | Save to Documents | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-203.json | — |
| EXC-0162 | browser | Screenshot → Coding proposal | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-204.json | — |
| EXC-0163 | browser | Run | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-205.json | — |
| EXC-0164 | browser | Queue in Job Center | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-206.json | — |
| EXC-0165 | browser | URL to open | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0165.json | — |
| EXC-0166 | browser | Browser agent goal | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0166.json | — |
| EXC-0167 | browser | Agent mode | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0167.json | — |
| EXC-0168 | calendar | Planner | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-062.json | — |
| EXC-0169 | calendar | Journal | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-063.json | — |
| EXC-0170 | calendar | Previous | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-064.json | — |
| EXC-0171 | calendar | Next | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-065.json | — |
| EXC-0172 | calendar | Jump to today (T) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-066.json | — |
| EXC-0173 | calendar | Month | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-067.json | — |
| EXC-0174 | calendar | Week | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-068.json | — |
| EXC-0175 | calendar | Agenda | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-069.json | — |
| EXC-0176 | calendar | Timeline | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-070.json | — |
| EXC-0177 | calendar | Open Planner | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-071.json | — |
| EXC-0178 | calendar | Open Bullet Journal | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-072.json | — |
| EXC-0179 | calendar | Open Documents | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-073.json | — |
| EXC-0180 | calendar | 2026-08-01 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-207.json | — |
| EXC-0181 | calendar | 2026-08-02 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-208.json | — |
| EXC-0182 | calendar | 2026-08-03 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-209.json | — |
| EXC-0183 | calendar | 2026-08-04 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-210.json | — |
| EXC-0184 | calendar | 2026-08-05 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-211.json | — |
| EXC-0185 | calendar | 2026-08-06 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-212.json | — |
| EXC-0186 | calendar | 2026-08-07 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-213.json | — |
| EXC-0187 | calendar | 2026-08-08 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-214.json | — |
| EXC-0188 | calendar | 2026-08-09 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0188.json | — |
| EXC-0189 | calendar | 2026-08-10 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0189.json | — |
| EXC-0190 | calendar | 2026-08-11 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0190.json | — |
| EXC-0191 | calendar | 2026-08-12 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0191.json | — |
| EXC-0192 | calendar | 2026-08-13 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0192.json | — |
| EXC-0193 | calendar | 2026-08-14 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0193.json | — |
| EXC-0194 | calendar | 2026-08-15 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0194.json | — |
| EXC-0195 | calendar | 2026-08-16 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0195.json | — |
| EXC-0196 | calendar | 2026-08-17 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0196.json | — |
| EXC-0197 | calendar | 2026-08-18 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0197.json | — |
| EXC-0198 | calendar | 2026-08-19 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0198.json | — |
| EXC-0199 | calendar | 2026-08-20 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0199.json | — |
| EXC-0200 | calendar | 2026-08-21 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0200.json | — |
| EXC-0201 | calendar | 2026-08-22 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0201.json | — |
| EXC-0202 | calendar | 2026-08-23 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0202.json | — |
| EXC-0203 | calendar | 2026-08-24 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0203.json | — |
| EXC-0204 | calendar | 2026-08-25 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0204.json | — |
| EXC-0205 | calendar | 2026-08-26 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0205.json | — |
| EXC-0206 | calendar | 2026-08-27 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0206.json | — |
| EXC-0207 | calendar | 2026-08-28 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0207.json | — |
| EXC-0208 | calendar | 2026-08-29 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0208.json | — |
| EXC-0209 | calendar | 2026-08-30 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0209.json | — |
| EXC-0210 | calendar | 2026-08-31 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0210.json | — |
| EXC-0211 | calendar | Open in Journal | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0211.json | — |
| EXC-0212 | calendar | Open Planner | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-071.json | — |
| EXC-0213 | calendar | Check conflicts | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0213.json | — |
| EXC-0214 | calendar | Meeting prep | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0214.json | — |
| EXC-0215 | calendar | Focus windows | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0215.json | — |
| EXC-0216 | calendar | Add to day | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0216.json | — |
| EXC-0217 | calendar | Parse & confirm | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0217.json | — |
| EXC-0218 | calendar | Save day note | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0218.json | — |
| EXC-0219 | calendar | Remove work block | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0219.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (mutate non-disposable planner/journal/calendar item) |
| EXC-0220 | calendar | ghost-btn tiny cal-ws-add | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0220.json | — |
| EXC-0221 | calendar | calWorkSaveBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0221.json | — |
| EXC-0222 | calendar | calendarIcsTestBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0222.json | — |
| EXC-0223 | calendar | calendarIcsSaveBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0223.json | — |
| EXC-0224 | calendar | calendarIcsRefreshBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0224.json | — |
| EXC-0225 | calendar | calendarVisionBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0225.json | — |
| EXC-0226 | calendar | calendarMemoryBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0226.json | — |
| EXC-0227 | calendar | calendarHaMeetingBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0227.json | — |
| EXC-0228 | calendar | Search calendar | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0228.json | — |
| EXC-0229 | calendar | Event time | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0229.json | — |
| EXC-0230 | calendar | Event description | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0230.json | — |
| EXC-0231 | calendar | Natural language schedule | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0231.json | — |
| EXC-0232 | calendar | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0232.json | — |
| EXC-0233 | calendar | 08:30 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0233.json | — |
| EXC-0234 | calendar | 17:00 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0234.json | — |
| EXC-0235 | calendar | Label | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0235.json | — |
| EXC-0236 | calendar | https://…/basic.ics | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0236.json | — |
| EXC-0237 | calendar | Fly fishing, birthday, travel… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0237.json | — |
| EXC-0238 | calendar | Filter by source | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0238.json | — |
| EXC-0239 | calendar | Entry type | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0239.json | — |
| EXC-0240 | calendar | Save target | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0240.json | — |
| EXC-0241 | calendar | Work schedule (weekly) | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0241.json | — |
| EXC-0242 | calendar | External calendar (ICS) | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0242.json | — |
| EXC-0243 | calendar | AI & Home | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0243.json | — |
| EXC-0244 | calendar | Planner | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-062.json | — |
| EXC-0245 | calendar | Journal | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-063.json | — |
| EXC-0246 | calendar | Previous | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-064.json | — |
| EXC-0247 | calendar | Next | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-065.json | — |
| EXC-0248 | calendar | Jump to today (T) | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-066.json | — |
| EXC-0249 | calendar | Month | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-067.json | — |
| EXC-0250 | calendar | Week | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-068.json | — |
| EXC-0251 | calendar | Agenda | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-069.json | — |
| EXC-0252 | calendar | Timeline | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-070.json | — |
| EXC-0253 | calendar | Open Planner | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-071.json | — |
| EXC-0254 | calendar | Open Bullet Journal | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-072.json | — |
| EXC-0255 | calendar | Open Documents | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-073.json | — |
| EXC-0256 | calendar | 2026-08-01 | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-207.json | — |
| EXC-0257 | calendar | 2026-08-02 | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-208.json | — |
| EXC-0258 | calendar | 2026-08-03 | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-209.json | — |
| EXC-0259 | calendar | 2026-08-04 | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-210.json | — |
| EXC-0260 | calendar | 2026-08-05 | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-211.json | — |
| EXC-0261 | calendar | 2026-08-06 | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-212.json | — |
| EXC-0262 | calendar | 2026-08-07 | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-213.json | — |
| EXC-0263 | calendar | 2026-08-08 | AFTER:Add to day | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-214.json | — |
| EXC-0264 | calendar | 2026-08-09 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0264.json | — |
| EXC-0265 | calendar | 2026-08-10 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0265.json | — |
| EXC-0266 | calendar | 2026-08-11 | AFTER:Add to day | conditional | yes | PASS | — | by_id/EXC-0266.json | — |
| EXC-0267 | calendar | 2026-08-12 | AFTER:Add to day | conditional | yes | PASS | — | by_id/EXC-0267.json | — |
| EXC-0268 | calendar | 2026-08-13 | AFTER:Add to day | conditional | yes | PASS | — | by_id/EXC-0268.json | — |
| EXC-0269 | calendar | 2026-08-14 | AFTER:Add to day | conditional | yes | PASS | — | by_id/EXC-0269.json | — |
| EXC-0270 | calendar | 2026-08-15 | AFTER:Add to day | conditional | yes | PASS | — | by_id/EXC-0270.json | — |
| EXC-0271 | calendar | 2026-08-16 | AFTER:Add to day | conditional | yes | PASS | — | by_id/EXC-0271.json | — |
| EXC-0272 | calendar | 2026-08-17 | AFTER:Add to day | conditional | yes | PASS | — | by_id/EXC-0272.json | — |
| EXC-0273 | calendar | 2026-08-18 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0273.json | — |
| EXC-0274 | calendar | 2026-08-19 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0274.json | — |
| EXC-0275 | calendar | 2026-08-20 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0275.json | — |
| EXC-0276 | calendar | 2026-08-21 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0276.json | — |
| EXC-0277 | calendar | 2026-08-22 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0277.json | — |
| EXC-0278 | calendar | 2026-08-23 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0278.json | — |
| EXC-0279 | calendar | 2026-08-24 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0279.json | — |
| EXC-0280 | calendar | 2026-08-25 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0280.json | — |
| EXC-0281 | calendar | 2026-08-26 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0281.json | — |
| EXC-0282 | calendar | 2026-08-27 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0282.json | — |
| EXC-0283 | calendar | 2026-08-28 | AFTER:Add to day | conditional | yes | FAIL | BUG-024 | by_id/EXC-0283.json | — |
| EXC-0284 | calendar | Planner | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-062.json | — |
| EXC-0285 | calendar | Journal | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-063.json | — |
| EXC-0286 | calendar | Previous | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-064.json | — |
| EXC-0287 | calendar | Next | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-065.json | — |
| EXC-0288 | calendar | Jump to today (T) | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-066.json | — |
| EXC-0289 | calendar | Month | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-067.json | — |
| EXC-0290 | calendar | Week | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-068.json | — |
| EXC-0291 | calendar | Agenda | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-069.json | — |
| EXC-0292 | calendar | Timeline | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-070.json | — |
| EXC-0293 | calendar | Open Planner | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-071.json | — |
| EXC-0294 | calendar | Open Bullet Journal | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-072.json | — |
| EXC-0295 | calendar | Open Documents | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-073.json | — |
| EXC-0296 | calendar | 2026-08-01 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-207.json | — |
| EXC-0297 | calendar | 2026-08-02 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-208.json | — |
| EXC-0298 | calendar | 2026-08-03 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-209.json | — |
| EXC-0299 | calendar | 2026-08-04 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-210.json | — |
| EXC-0300 | calendar | 2026-08-05 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-211.json | — |
| EXC-0301 | calendar | 2026-08-06 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-212.json | — |
| EXC-0302 | calendar | 2026-08-07 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-213.json | — |
| EXC-0303 | calendar | 2026-08-08 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-214.json | — |
| EXC-0304 | calendar | 2026-08-09 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0304.json | — |
| EXC-0305 | calendar | 2026-08-10 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0305.json | — |
| EXC-0306 | calendar | 2026-08-11 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0306.json | — |
| EXC-0307 | calendar | 2026-08-12 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | by_id/EXC-0307.json | — |
| EXC-0308 | calendar | 2026-08-13 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | by_id/EXC-0308.json | — |
| EXC-0309 | calendar | 2026-08-14 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | by_id/EXC-0309.json | — |
| EXC-0310 | calendar | 2026-08-15 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | by_id/EXC-0310.json | — |
| EXC-0311 | calendar | 2026-08-16 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | PASS | — | by_id/EXC-0311.json | — |
| EXC-0312 | calendar | 2026-08-17 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0312.json | — |
| EXC-0313 | calendar | 2026-08-18 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0313.json | — |
| EXC-0314 | calendar | 2026-08-19 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0314.json | — |
| EXC-0315 | calendar | 2026-08-20 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0315.json | — |
| EXC-0316 | calendar | 2026-08-21 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0316.json | — |
| EXC-0317 | calendar | 2026-08-22 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0317.json | — |
| EXC-0318 | calendar | 2026-08-23 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0318.json | — |
| EXC-0319 | calendar | 2026-08-24 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0319.json | — |
| EXC-0320 | calendar | 2026-08-25 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0320.json | — |
| EXC-0321 | calendar | 2026-08-26 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0321.json | — |
| EXC-0322 | calendar | 2026-08-27 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0322.json | — |
| EXC-0323 | calendar | 2026-08-28 | AFTER:ghost-btn tiny cal-ws-add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0323.json | — |
| EXC-0324 | capabilities | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-074.json | — |
| EXC-0325 | capabilities | Load enabled | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-075.json | — |
| EXC-0326 | capabilities | Diagnostics | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-076.json | — |
| EXC-0327 | capabilities | Search capabilities… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-077.json | — |
| EXC-0328 | capabilities | Filter by layer | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-078.json | — |
| EXC-0329 | capabilities | Filter by category | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-079.json | — |
| EXC-0330 | capabilities | Filter by trust | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-080.json | — |
| EXC-0331 | capabilities | Advanced options | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0331.json | — |
| EXC-0332 | capabilities | Refresh | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-074.json | — |
| EXC-0333 | capabilities | Load enabled | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-075.json | — |
| EXC-0334 | capabilities | Diagnostics | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-076.json | — |
| EXC-0335 | capabilities | Search capabilities… | AFTER:Advanced options | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-077.json | — |
| EXC-0336 | capabilities | Filter by layer | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-078.json | — |
| EXC-0337 | capabilities | Filter by category | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-079.json | — |
| EXC-0338 | capabilities | Filter by trust | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-080.json | — |
| EXC-0339 | capabilities | Advanced options | AFTER:Advanced options | conditional | yes | PASS | — | by_id/EXC-0339.json | — |
| EXC-0340 | chat | More | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-081.json | — |
| EXC-0341 | chat | Good morning | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-082.json | — |
| EXC-0342 | chat | What should we work on? | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-083.json | — |
| EXC-0343 | chat | Just listen for a bit | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-084.json | — |
| EXC-0344 | chat | Hold to talk | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0344.json | — |
| EXC-0345 | chat | Send | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0345.json | — |
| EXC-0346 | chat | Say anything… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-085.json | — |
| EXC-0347 | chat | More | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-081.json | — |
| EXC-0348 | chat | New conversation fresh | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-386.json | — |
| EXC-0349 | chat | Place something here attach | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-387.json | — |
| EXC-0350 | chat | Read aloud off | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-388.json | — |
| EXC-0351 | chat | Voice when speaking | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-389.json | — |
| EXC-0352 | chat | Open the front door Ctrl+K | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-390.json | — |
| EXC-0353 | chat | Fork thread branch | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-391.json | — |
| EXC-0354 | chat | Good morning | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-082.json | — |
| EXC-0355 | chat | What should we work on? | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-083.json | — |
| EXC-0356 | chat | Just listen for a bit | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-084.json | — |
| EXC-0357 | chat | Hold to talk | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0357.json | — |
| EXC-0358 | chat | Send | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0358.json | — |
| EXC-0359 | chat | Say anything… | AFTER:More | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-085.json | — |
| EXC-0360 | chat | Model | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0360.json | — |
| EXC-0361 | coding | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-086.json | — |
| EXC-0362 | coding | Workspace identity | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-087.json | — |
| EXC-0363 | coding | Live coding jobs | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-088.json | — |
| EXC-0364 | coding | Coding model role | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-089.json | — |
| EXC-0365 | connections | Shortcuts | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-090.json | — |
| EXC-0366 | connections | Search | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-091.json | — |
| EXC-0367 | connections | Browse | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-092.json | — |
| EXC-0368 | connections | New (N) | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-093.json | — |
| EXC-0369 | connections | Import | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-094.json | — |
| EXC-0370 | connections | Cleanup | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-095.json | — |
| EXC-0371 | connections | Assistant | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-096.json | — |
| EXC-0372 | connections | Undo | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-097.json | — |
| EXC-0373 | connections | Clear | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-098.json | — |
| EXC-0374 | connections | Search connections | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-099.json | — |
| EXC-0375 | connections | Search mode | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-100.json | — |
| EXC-0376 | connections | Shortcuts | AFTER:New (N) | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-090.json | — |
| EXC-0377 | connections | Search | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-091.json | — |
| EXC-0378 | connections | Browse | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-092.json | — |
| EXC-0379 | connections | New (N) | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-093.json | — |
| EXC-0380 | connections | Import | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-094.json | — |
| EXC-0381 | connections | Cleanup | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-095.json | — |
| EXC-0382 | connections | Assistant | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-096.json | — |
| EXC-0383 | connections | Undo | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-097.json | — |
| EXC-0384 | connections | Clear | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-098.json | — |
| EXC-0385 | connections | Search connections | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-099.json | — |
| EXC-0386 | connections | Search mode | AFTER:New (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-100.json | — |
| EXC-0387 | documents | Shortcuts | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-101.json | — |
| EXC-0388 | documents | Import | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-102.json | — |
| EXC-0389 | documents | Search | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-103.json | — |
| EXC-0390 | documents | Rebuild Search Index | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-104.json | — |
| EXC-0391 | documents | Briefing | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-105.json | — |
| EXC-0392 | documents | Ask Aria | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0392.json | — |
| EXC-0393 | documents | Clear | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-106.json | — |
| EXC-0394 | documents | Upload | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-107.json | — |
| EXC-0395 | documents | Import Folder | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-108.json | — |
| EXC-0396 | documents | Ask Aria | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0396.json | — |
| EXC-0397 | documents | Summarize | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-109.json | — |
| EXC-0398 | documents | Learn → candidates | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-110.json | — |
| EXC-0399 | documents | Rebuild Search Index | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-104.json | — |
| EXC-0400 | documents | Document Briefing | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-111.json | — |
| EXC-0401 | documents | Open Memory | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-112.json | — |
| EXC-0402 | documents | Open Projects | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-215.json | — |
| EXC-0403 | documents | test | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-216.json | — |
| EXC-0404 | documents | resume | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-217.json | — |
| EXC-0405 | documents | warranty | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-218.json | — |
| EXC-0406 | documents | readme | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-219.json | — |
| EXC-0407 | documents | aria | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-220.json | — |
| EXC-0408 | documents | memory | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-221.json | — |
| EXC-0409 | documents | ship | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-222.json | — |
| EXC-0410 | documents | doc | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0410.json | — |
| EXC-0411 | documents | Folder path | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0411.json | — |
| EXC-0412 | documents | Search documents | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0412.json | — |
| EXC-0413 | documents | Drop files to upload | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0413.json | — |
| EXC-0414 | flytying | Guided library setup & health | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-113.json | — |
| EXC-0415 | flytying | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-114.json | — |
| EXC-0416 | flytying | Open Gallery | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-115.json | — |
| EXC-0417 | flytying | Suggest a fly | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-116.json | — |
| EXC-0418 | flytying | Open inventory | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-117.json | — |
| EXC-0419 | flytying | Start session | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-118.json | — |
| EXC-0420 | flytying | Apply profile | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-119.json | — |
| EXC-0421 | flytying | Voice: next step | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-120.json | — |
| EXC-0422 | flytying | Voice: repeat step | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-121.json | — |
| EXC-0423 | flytying | Search fly patterns | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-122.json | — |
| EXC-0424 | flytying | Clear search and type filter | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-123.json | — |
| EXC-0425 | flytying | Seasonal | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-124.json | — |
| EXC-0426 | flytying | Hide | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-223.json | — |
| EXC-0427 | flytying | Add | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-224.json | — |
| EXC-0428 | flytying | Suggest a fly | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-116.json | — |
| EXC-0429 | flytying | Save list | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-225.json | — |
| EXC-0430 | flytying | What ▲ | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-226.json | — |
| EXC-0431 | flytying | Color | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-227.json | — |
| EXC-0432 | flytying | Size | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-228.json | — |
| EXC-0433 | flytying | Brand | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-229.json | — |
| EXC-0434 | flytying | Add | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-224.json | — |
| EXC-0435 | flytying | Edit | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-230.json | — |
| EXC-0436 | flytying | Remove material | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0436.json | — |
| EXC-0437 | flytying | Import lines | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0437.json | — |
| EXC-0438 | flytying | flytyingCameraScanBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0438.json | — |
| EXC-0439 | flytying | flytyingScanPhotoBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0439.json | — |
| EXC-0440 | flytying | flytyingLabelBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0440.json | — |
| EXC-0441 | flytying | Send | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0441.json | — |
| EXC-0442 | flytying | Clear chat | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0442.json | — |
| EXC-0443 | flytying | Search patterns… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0443.json | — |
| EXC-0444 | flytying | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0444.json | — |
| EXC-0445 | flytying | 0 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0445.json | — |
| EXC-0446 | flytying | Paste YouTube, Vimeo, or Fly Fish Food URL… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0446.json | — |
| EXC-0447 | flytying | Filter videos… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0447.json | — |
| EXC-0448 | flytying | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0448.json | — |
| EXC-0449 | flytying | hook, thread… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0449.json | — |
| EXC-0450 | flytying | olive | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0450.json | — |
| EXC-0451 | flytying | 14, 8/0 | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0451.json | — |
| EXC-0452 | flytying | Uni | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0452.json | — |
| EXC-0453 | flytying | optional | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0453.json | — |
| EXC-0454 | flytying | Scan or type barcode… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0454.json | — |
| EXC-0455 | flytying | e.g. olive 14 dry hook, grizzly hackle, Uni 8/0 olive thread — or use the invent | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0455.json | — |
| EXC-0456 | flytying | size 14 dry hook olive dubbing | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0456.json | — |
| EXC-0457 | flytying | Ask about a pattern, hatch, or design a new fly… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0457.json | — |
| EXC-0458 | flytying | Fly tying model (7b = recipes, 14b = design) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0458.json | — |
| EXC-0459 | flytying | Fly Tying profile | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0459.json | — |
| EXC-0460 | flytying | Fly type | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0460.json | — |
| EXC-0461 | flytying | INVENTORY TABLE — WHAT, COLOR, SIZE, BRAND | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0461.json | — |
| EXC-0462 | flytying | Barcode scan (optional) | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0462.json | — |
| EXC-0463 | flytying | Guided library setup & health | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-113.json | — |
| EXC-0464 | flytying | Refresh | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-114.json | — |
| EXC-0465 | flytying | Open Gallery | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-115.json | — |
| EXC-0466 | flytying | Suggest a fly | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-116.json | — |
| EXC-0467 | flytying | Open inventory | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-117.json | — |
| EXC-0468 | flytying | Start session | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-118.json | — |
| EXC-0469 | flytying | Apply profile | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-119.json | — |
| EXC-0470 | flytying | Voice: next step | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-120.json | — |
| EXC-0471 | flytying | Voice: repeat step | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-121.json | — |
| EXC-0472 | flytying | Search fly patterns | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-122.json | — |
| EXC-0473 | flytying | Clear search and type filter | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-123.json | — |
| EXC-0474 | flytying | Seasonal | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-124.json | — |
| EXC-0475 | flytying | Hide | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-223.json | — |
| EXC-0476 | flytying | Add | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-224.json | — |
| EXC-0477 | flytying | Suggest a fly | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-116.json | — |
| EXC-0478 | flytying | Save list | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-225.json | — |
| EXC-0479 | flytying | What ▲ | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-226.json | — |
| EXC-0480 | flytying | Color | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-227.json | — |
| EXC-0481 | flytying | Size | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-228.json | — |
| EXC-0482 | flytying | Brand | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-229.json | — |
| EXC-0483 | flytying | Add | AFTER:Clear search and type filter | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-224.json | — |
| EXC-0484 | flytying | Edit | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-230.json | — |
| EXC-0485 | flytying | Remove material | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | by_id/EXC-0485.json | — |
| EXC-0486 | flytying | Import lines | AFTER:Clear search and type filter | conditional | yes | PASS | — | by_id/EXC-0486.json | — |
| EXC-0487 | flytying | flytyingCameraScanBtn | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | by_id/EXC-0487.json | — |
| EXC-0488 | flytying | flytyingScanPhotoBtn | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | by_id/EXC-0488.json | — |
| EXC-0489 | flytying | flytyingLabelBtn | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | by_id/EXC-0489.json | — |
| EXC-0490 | flytying | Send | AFTER:Clear search and type filter | conditional | yes | PASS | — | by_id/EXC-0490.json | — |
| EXC-0491 | flytying | Clear chat | AFTER:Clear search and type filter | conditional | yes | PASS | — | by_id/EXC-0491.json | — |
| EXC-0492 | flytying | Search patterns… | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | by_id/EXC-0492.json | — |
| EXC-0493 | flytying | on | AFTER:Clear search and type filter | conditional | yes | PASS | — | by_id/EXC-0493.json | — |
| EXC-0494 | flytying | 0 | AFTER:Clear search and type filter | conditional | yes | PASS | — | by_id/EXC-0494.json | — |
| EXC-0495 | flytying | Paste YouTube, Vimeo, or Fly Fish Food URL… | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | by_id/EXC-0495.json | — |
| EXC-0496 | flytying | Filter videos… | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | by_id/EXC-0496.json | — |
| EXC-0497 | flytying | on | AFTER:Clear search and type filter | conditional | yes | PASS | — | by_id/EXC-0497.json | — |
| EXC-0498 | flytying | hook, thread… | AFTER:Clear search and type filter | conditional | yes | FAIL | BUG-024 | by_id/EXC-0498.json | — |
| EXC-0499 | flytying | olive | AFTER:Clear search and type filter | conditional | yes | PASS | — | by_id/EXC-0499.json | — |
| EXC-0500 | flytying | Guided library setup & health | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-113.json | — |
| EXC-0501 | flytying | Refresh | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-114.json | — |
| EXC-0502 | flytying | Open Gallery | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-115.json | — |
| EXC-0503 | flytying | Suggest a fly | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-116.json | — |
| EXC-0504 | flytying | Open inventory | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-117.json | — |
| EXC-0505 | flytying | Start session | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-118.json | — |
| EXC-0506 | flytying | Apply profile | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-119.json | — |
| EXC-0507 | flytying | Voice: next step | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-120.json | — |
| EXC-0508 | flytying | Voice: repeat step | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-121.json | — |
| EXC-0509 | flytying | Search fly patterns | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-122.json | — |
| EXC-0510 | flytying | Clear search and type filter | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-123.json | — |
| EXC-0511 | flytying | Seasonal | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-124.json | — |
| EXC-0512 | flytying | Hide | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-223.json | — |
| EXC-0513 | flytying | Add | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-224.json | — |
| EXC-0514 | flytying | Suggest a fly | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-116.json | — |
| EXC-0515 | flytying | Save list | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-225.json | — |
| EXC-0516 | flytying | What ▲ | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-226.json | — |
| EXC-0517 | flytying | Color | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-227.json | — |
| EXC-0518 | flytying | Size | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-228.json | — |
| EXC-0519 | flytying | Brand | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-229.json | — |
| EXC-0520 | flytying | Add | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-224.json | — |
| EXC-0521 | flytying | Edit | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-230.json | — |
| EXC-0522 | flytying | Remove material | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0522.json | — |
| EXC-0523 | flytying | Import lines | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0523.json | — |
| EXC-0524 | flytying | flytyingCameraScanBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0524.json | — |
| EXC-0525 | flytying | flytyingScanPhotoBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0525.json | — |
| EXC-0526 | flytying | flytyingLabelBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0526.json | — |
| EXC-0527 | flytying | Send | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0527.json | — |
| EXC-0528 | flytying | Clear chat | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0528.json | — |
| EXC-0529 | flytying | Search patterns… | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0529.json | — |
| EXC-0530 | flytying | on | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0530.json | — |
| EXC-0531 | flytying | 0 | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0531.json | — |
| EXC-0532 | flytying | Paste YouTube, Vimeo, or Fly Fish Food URL… | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0532.json | — |
| EXC-0533 | flytying | Filter videos… | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0533.json | — |
| EXC-0534 | flytying | on | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0534.json | — |
| EXC-0535 | flytying | hook, thread… | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0535.json | — |
| EXC-0536 | flytying | olive | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0536.json | — |
| EXC-0537 | flytying | Guided library setup & health | AFTER:Edit | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-113.json | — |
| EXC-0538 | flytying | Refresh | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-114.json | — |
| EXC-0539 | flytying | Open Gallery | AFTER:Edit | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-115.json | — |
| EXC-0540 | flytying | Suggest a fly | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-116.json | — |
| EXC-0541 | flytying | Open inventory | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-117.json | — |
| EXC-0542 | flytying | Start session | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-118.json | — |
| EXC-0543 | flytying | Apply profile | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-119.json | — |
| EXC-0544 | flytying | Voice: next step | AFTER:Edit | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-120.json | — |
| EXC-0545 | flytying | Voice: repeat step | AFTER:Edit | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-121.json | — |
| EXC-0546 | flytying | Search fly patterns | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-122.json | — |
| EXC-0547 | flytying | Clear search and type filter | AFTER:Edit | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-123.json | — |
| EXC-0548 | flytying | Seasonal | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-124.json | — |
| EXC-0549 | flytying | Hide | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-223.json | — |
| EXC-0550 | flytying | Add | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-224.json | — |
| EXC-0551 | flytying | Suggest a fly | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-116.json | — |
| EXC-0552 | flytying | Save list | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-225.json | — |
| EXC-0553 | flytying | What ▲ | AFTER:Edit | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-226.json | — |
| EXC-0554 | flytying | Color | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-227.json | — |
| EXC-0555 | flytying | Size | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-228.json | — |
| EXC-0556 | flytying | Brand | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-229.json | — |
| EXC-0557 | flytying | Add | AFTER:Edit | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-224.json | — |
| EXC-0558 | flytying | Save | AFTER:Edit | conditional | yes | PASS | — | by_id/EXC-0558.json | — |
| EXC-0559 | flytying | Cancel | AFTER:Edit | conditional | yes | FAIL | BUG-024 | by_id/EXC-0559.json | — |
| EXC-0560 | flytying | Edit | AFTER:Edit | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-230.json | — |
| EXC-0561 | flytying | Remove material | AFTER:Edit | conditional | yes | FAIL | BUG-024 | by_id/EXC-0561.json | — |
| EXC-0562 | flytying | Import lines | AFTER:Edit | conditional | yes | PASS | — | by_id/EXC-0562.json | — |
| EXC-0563 | flytying | flytyingCameraScanBtn | AFTER:Edit | conditional | yes | FAIL | BUG-024 | by_id/EXC-0563.json | — |
| EXC-0564 | flytying | flytyingScanPhotoBtn | AFTER:Edit | conditional | yes | FAIL | BUG-024 | by_id/EXC-0564.json | — |
| EXC-0565 | flytying | flytyingLabelBtn | AFTER:Edit | conditional | yes | FAIL | BUG-024 | by_id/EXC-0565.json | — |
| EXC-0566 | flytying | Send | AFTER:Edit | conditional | yes | PASS | — | by_id/EXC-0566.json | — |
| EXC-0567 | flytying | Clear chat | AFTER:Edit | conditional | yes | PASS | — | by_id/EXC-0567.json | — |
| EXC-0568 | flytying | Search patterns… | AFTER:Edit | conditional | yes | FAIL | BUG-024 | by_id/EXC-0568.json | — |
| EXC-0569 | flytying | on | AFTER:Edit | conditional | yes | PASS | — | by_id/EXC-0569.json | — |
| EXC-0570 | flytying | 0 | AFTER:Edit | conditional | yes | PASS | — | by_id/EXC-0570.json | — |
| EXC-0571 | flytying | Paste YouTube, Vimeo, or Fly Fish Food URL… | AFTER:Edit | conditional | yes | FAIL | BUG-024 | by_id/EXC-0571.json | — |
| EXC-0572 | flytying | Filter videos… | AFTER:Edit | conditional | yes | FAIL | BUG-024 | by_id/EXC-0572.json | — |
| EXC-0573 | flytying | on | AFTER:Edit | conditional | yes | PASS | — | by_id/EXC-0573.json | — |
| EXC-0574 | gallery | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-125.json | — |
| EXC-0575 | gallery | Job Center | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-126.json | — |
| EXC-0576 | gallery | Models | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-127.json | — |
| EXC-0577 | gallery | Open Maker lab | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-128.json | — |
| EXC-0578 | gallery | Open Fly tying | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-129.json | — |
| EXC-0579 | gallery | Open Video Studio | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-130.json | — |
| EXC-0580 | gallery | Open Meme Studio | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-131.json | — |
| EXC-0581 | gallery | Generate | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-132.json | — |
| EXC-0582 | gallery | Preview enhance | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-133.json | — |
| EXC-0583 | gallery | Advanced | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-134.json | — |
| EXC-0584 | gallery | Reuse last settings with a new seed | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-135.json | — |
| EXC-0585 | gallery | Mission Control | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-136.json | — |
| EXC-0586 | gallery | Simple | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-231.json | — |
| EXC-0587 | gallery | Advanced | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-134.json | — |
| EXC-0588 | gallery | Expert | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-232.json | — |
| EXC-0589 | gallery | Search | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-233.json | — |
| EXC-0590 | gallery | → Video storyboard | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-234.json | — |
| EXC-0591 | gallery | New collection | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-235.json | — |
| EXC-0592 | gallery | Opt-in Vision caption | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-236.json | — |
| EXC-0593 | gallery | Describe | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-237.json | — |
| EXC-0594 | gallery | Save caption to Documents | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-238.json | — |
| EXC-0595 | gallery | Vision→Coding | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0595.json | — |
| EXC-0596 | gallery | Similarity clusters | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0596.json | — |
| EXC-0597 | gallery | Open ComfyUI ↗ | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0597.json | — |
| EXC-0598 | gallery | Image generation prompt | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0598.json | — |
| EXC-0599 | gallery | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0599.json | — |
| EXC-0600 | gallery | Search gallery | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0600.json | — |
| EXC-0601 | gallery | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0601.json | — |
| EXC-0602 | gallery | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0602.json | — |
| EXC-0603 | gallery | Generation preset | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0603.json | — |
| EXC-0604 | gallery | Aspect ratio | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0604.json | — |
| EXC-0605 | gallery | Flux Schnell (best prompts) SDXL 1.0 (quality) SDXL Turbo (fast) | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0605.json | — |
| EXC-0606 | gallery | Auto (GPU → CPU fallback) GPU only CPU only | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0606.json | — |
| EXC-0607 | gallery | Sort | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0607.json | — |
| EXC-0608 | gallery | Refresh | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-125.json | — |
| EXC-0609 | gallery | Job Center | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-126.json | — |
| EXC-0610 | gallery | Models | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-127.json | — |
| EXC-0611 | gallery | Open Maker lab | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-128.json | — |
| EXC-0612 | gallery | Open Fly tying | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-129.json | — |
| EXC-0613 | gallery | Open Video Studio | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-130.json | — |
| EXC-0614 | gallery | Open Meme Studio | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-131.json | — |
| EXC-0615 | gallery | Generate | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-132.json | — |
| EXC-0616 | gallery | Preview enhance | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-133.json | — |
| EXC-0617 | gallery | Advanced | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-134.json | — |
| EXC-0618 | gallery | Reuse last settings with a new seed | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-135.json | — |
| EXC-0619 | gallery | Mission Control | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-136.json | — |
| EXC-0620 | gallery | Simple | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-231.json | — |
| EXC-0621 | gallery | Advanced | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-134.json | — |
| EXC-0622 | gallery | Expert | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-232.json | — |
| EXC-0623 | gallery | Search | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-233.json | — |
| EXC-0624 | gallery | → Video storyboard | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-234.json | — |
| EXC-0625 | gallery | New collection | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-235.json | — |
| EXC-0626 | gallery | Opt-in Vision caption | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-236.json | — |
| EXC-0627 | gallery | Describe | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-237.json | — |
| EXC-0628 | gallery | Save caption to Documents | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-238.json | — |
| EXC-0629 | gallery | Vision→Coding | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0629.json | — |
| EXC-0630 | gallery | Similarity clusters | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0630.json | — |
| EXC-0631 | gallery | Open ComfyUI ↗ | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0631.json | — |
| EXC-0632 | gallery | Image generation prompt | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0632.json | — |
| EXC-0633 | gallery | on | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0633.json | — |
| EXC-0634 | gallery | Negative prompt | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0634.json | — |
| EXC-0635 | gallery | Seed | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0635.json | — |
| EXC-0636 | gallery | on | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0636.json | — |
| EXC-0637 | gallery | Steps | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0637.json | — |
| EXC-0638 | gallery | CFG | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0638.json | — |
| EXC-0639 | gallery | Variations count | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0639.json | — |
| EXC-0640 | gallery | Width | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0640.json | — |
| EXC-0641 | gallery | Height | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0641.json | — |
| EXC-0642 | gallery | Search gallery | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0642.json | — |
| EXC-0643 | gallery | on | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0643.json | — |
| EXC-0644 | gallery | on | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0644.json | — |
| EXC-0645 | gallery | Enhanced prompt | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0645.json | — |
| EXC-0646 | gallery | Generation preset | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-0646.json | — |
| EXC-0647 | gallery | Aspect ratio | AFTER:Advanced | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0647.json | — |
| EXC-0648 | gallery | Refresh | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-125.json | — |
| EXC-0649 | gallery | Job Center | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-126.json | — |
| EXC-0650 | gallery | Models | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-127.json | — |
| EXC-0651 | gallery | Open Maker lab | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-128.json | — |
| EXC-0652 | gallery | Open Fly tying | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-129.json | — |
| EXC-0653 | gallery | Open Video Studio | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-130.json | — |
| EXC-0654 | gallery | Open Meme Studio | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-131.json | — |
| EXC-0655 | gallery | Generate | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-132.json | — |
| EXC-0656 | gallery | Preview enhance | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-133.json | — |
| EXC-0657 | gallery | Advanced | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-134.json | — |
| EXC-0658 | gallery | Reuse last settings with a new seed | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-135.json | — |
| EXC-0659 | gallery | Mission Control | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-136.json | — |
| EXC-0660 | gallery | Simple | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-231.json | — |
| EXC-0661 | gallery | Advanced | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-134.json | — |
| EXC-0662 | gallery | Expert | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-232.json | — |
| EXC-0663 | gallery | Search | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-233.json | — |
| EXC-0664 | gallery | → Video storyboard | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-234.json | — |
| EXC-0665 | gallery | New collection | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-235.json | — |
| EXC-0666 | gallery | Opt-in Vision caption | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-236.json | — |
| EXC-0667 | gallery | Describe | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-237.json | — |
| EXC-0668 | gallery | Save caption to Documents | AFTER:Reuse last settings with a new seed | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-238.json | — |
| EXC-0669 | gallery | Vision→Coding | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0669.json | — |
| EXC-0670 | gallery | Similarity clusters | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0670.json | — |
| EXC-0671 | gallery | Focus prompt | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0671.json | — |
| EXC-0672 | gallery | Open ComfyUI ↗ | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0672.json | — |
| EXC-0673 | gallery | Image generation prompt | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0673.json | — |
| EXC-0674 | gallery | on | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0674.json | — |
| EXC-0675 | gallery | Negative prompt | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0675.json | — |
| EXC-0676 | gallery | Seed | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0676.json | — |
| EXC-0677 | gallery | on | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0677.json | — |
| EXC-0678 | gallery | Steps | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0678.json | — |
| EXC-0679 | gallery | CFG | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0679.json | — |
| EXC-0680 | gallery | Variations count | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0680.json | — |
| EXC-0681 | gallery | Width | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0681.json | — |
| EXC-0682 | gallery | Height | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0682.json | — |
| EXC-0683 | gallery | Search gallery | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0683.json | — |
| EXC-0684 | gallery | on | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0684.json | — |
| EXC-0685 | gallery | on | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0685.json | — |
| EXC-0686 | gallery | Enhanced prompt | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0686.json | — |
| EXC-0687 | gallery | Generation preset | AFTER:Reuse last settings with a new seed | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0687.json | — |
| EXC-0688 | gallery | Focus prompt | AFTER:Advanced | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0688.json | — |
| EXC-0689 | gallery | Flux Schnell (best prompts) SDXL 1.0 (quality) SDXL Turbo (fast) | AFTER:Advanced | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0689.json | — |
| EXC-0690 | gallery | Auto (GPU → CPU fallback) GPU only CPU only | AFTER:Advanced | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0690.json | — |
| EXC-0691 | gallery | Sort | AFTER:Advanced | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0691.json | — |
| EXC-0692 | gallery | Refresh | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-125.json | — |
| EXC-0693 | gallery | Job Center | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-126.json | — |
| EXC-0694 | gallery | Models | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-127.json | — |
| EXC-0695 | gallery | Open Maker lab | AFTER:New collection | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-128.json | — |
| EXC-0696 | gallery | Open Fly tying | AFTER:New collection | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-129.json | — |
| EXC-0697 | gallery | Open Video Studio | AFTER:New collection | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-130.json | — |
| EXC-0698 | gallery | Open Meme Studio | AFTER:New collection | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-131.json | — |
| EXC-0699 | gallery | Generate | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-132.json | — |
| EXC-0700 | gallery | Preview enhance | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-133.json | — |
| EXC-0701 | gallery | Advanced | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-134.json | — |
| EXC-0702 | gallery | Reuse last settings with a new seed | AFTER:New collection | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-135.json | — |
| EXC-0703 | gallery | Mission Control | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-136.json | — |
| EXC-0704 | gallery | Simple | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-231.json | — |
| EXC-0705 | gallery | Advanced | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-134.json | — |
| EXC-0706 | gallery | Expert | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-232.json | — |
| EXC-0707 | gallery | Search | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-233.json | — |
| EXC-0708 | gallery | → Video storyboard | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-234.json | — |
| EXC-0709 | gallery | New collection | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-235.json | — |
| EXC-0710 | gallery | Opt-in Vision caption | AFTER:New collection | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-236.json | — |
| EXC-0711 | gallery | Describe | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-237.json | — |
| EXC-0712 | gallery | Save caption to Documents | AFTER:New collection | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-238.json | — |
| EXC-0713 | gallery | Vision→Coding | AFTER:New collection | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0713.json | — |
| EXC-0714 | gallery | Similarity clusters | AFTER:New collection | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0714.json | — |
| EXC-0715 | gallery | Focus prompt | AFTER:New collection | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0715.json | — |
| EXC-0716 | gallery | Open ComfyUI ↗ | AFTER:New collection | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0716.json | — |
| EXC-0717 | gallery | Image generation prompt | AFTER:New collection | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0717.json | — |
| EXC-0718 | gallery | on | AFTER:New collection | conditional | yes | FAIL | BUG-INFRA-001 | by_id/EXC-0718.json | — |
| EXC-0719 | gallery | Search gallery | AFTER:New collection | conditional | yes | PASS | — | by_id/EXC-0719.json | — |
| EXC-0720 | gallery | on | AFTER:New collection | conditional | yes | PASS | — | by_id/EXC-0720.json | — |
| EXC-0721 | gallery | on | AFTER:New collection | conditional | yes | PASS | — | by_id/EXC-0721.json | — |
| EXC-0722 | gallery | Generation preset | AFTER:New collection | conditional | yes | PASS | — | by_id/EXC-0722.json | — |
| EXC-0723 | gallery | Aspect ratio | AFTER:New collection | conditional | yes | PASS | — | by_id/EXC-0723.json | — |
| EXC-0724 | gallery | Flux Schnell (best prompts) SDXL 1.0 (quality) SDXL Turbo (fast) | AFTER:New collection | conditional | yes | PASS | — | by_id/EXC-0724.json | — |
| EXC-0725 | gallery | Auto (GPU → CPU fallback) GPU only CPU only | AFTER:New collection | conditional | yes | PASS | — | by_id/EXC-0725.json | — |
| EXC-0726 | gallery | Sort | AFTER:New collection | conditional | yes | PASS | — | by_id/EXC-0726.json | — |
| EXC-0727 | health | Doctor visit | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-137.json | — |
| EXC-0728 | health | Emergency | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-138.json | — |
| EXC-0729 | health | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-139.json | — |
| EXC-0730 | health | Timeline | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-140.json | — |
| EXC-0731 | health | Dashboard | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-141.json | — |
| EXC-0732 | health | Check-in | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-142.json | — |
| EXC-0733 | health | Activity | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-143.json | — |
| EXC-0734 | health | Workouts | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-144.json | — |
| EXC-0735 | health | Goals | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-145.json | — |
| EXC-0736 | health | Trends | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-146.json | — |
| EXC-0737 | health | Meds | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-147.json | — |
| EXC-0738 | health | Supplements | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-148.json | — |
| EXC-0739 | health | Recovery | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-239.json | — |
| EXC-0740 | health | History | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-240.json | — |
| EXC-0741 | health | Journal | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-241.json | — |
| EXC-0742 | health | Knowledge | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-242.json | — |
| EXC-0743 | health | Providers | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-243.json | — |
| EXC-0744 | health | Procedures | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-244.json | — |
| EXC-0745 | health | Family | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-245.json | — |
| EXC-0746 | health | Preventive | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-246.json | — |
| EXC-0747 | health | Nutrition | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0747.json | — |
| EXC-0748 | health | Insights | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0748.json | — |
| EXC-0749 | health | Visit prep | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0749.json | — |
| EXC-0750 | health | Backups | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0750.json | — |
| EXC-0751 | health | Security | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0751.json | — |
| EXC-0752 | health | Vitals | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0752.json | — |
| EXC-0753 | health | Labs | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0753.json | — |
| EXC-0754 | health | Documents | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0754.json | — |
| EXC-0755 | health | Questions | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0755.json | — |
| EXC-0756 | health | Coach | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0756.json | — |
| EXC-0757 | health | Consult | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0757.json | — |
| EXC-0758 | health | Reminders | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0758.json | — |
| EXC-0759 | health | Print / Export | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0759.json | — |
| EXC-0760 | health | Profile | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0760.json | — |
| EXC-0761 | health | Search | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0761.json | — |
| EXC-0762 | health | Log | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0762.json | — |
| EXC-0763 | health | Search Health | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0763.json | — |
| EXC-0764 | health | Natural language health update | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0764.json | — |
| EXC-0765 | home | Open Mission Control | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-149.json | — |
| EXC-0766 | home | Open Planner | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-150.json | — |
| EXC-0767 | home | Open Bullet Journal | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-151.json | — |
| EXC-0768 | home | Open Calendar | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-152.json | — |
| EXC-0769 | home | Automation Home | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-153.json | — |
| EXC-0770 | home | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-154.json | — |
| EXC-0771 | home | Scan action log | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-155.json | — |
| EXC-0772 | home | Set PIN | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-156.json | — |
| EXC-0773 | home | 4–6 digit PIN | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-157.json | — |
| EXC-0774 | home | First-flight checklist ▾ | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-158.json | — |
| EXC-0775 | home | Skills & learned workflows ▾ | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-159.json | — |
| EXC-0776 | home | Security ▾ | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-160.json | — |
| EXC-0777 | home | Open Mission Control | AFTER:Running… | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-149.json | — |
| EXC-0778 | home | Open Planner | AFTER:Running… | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-150.json | — |
| EXC-0779 | home | Open Bullet Journal | AFTER:Running… | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-151.json | — |
| EXC-0780 | home | Open Calendar | AFTER:Running… | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-152.json | — |
| EXC-0781 | home | Automation Home | AFTER:Running… | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-153.json | — |
| EXC-0782 | home | Refresh | AFTER:Running… | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-154.json | — |
| EXC-0783 | home | Scan action log | AFTER:Running… | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-155.json | — |
| EXC-0784 | home | Set PIN | AFTER:Running… | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-156.json | — |
| EXC-0785 | home | 4–6 digit PIN | AFTER:Running… | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-157.json | — |
| EXC-0786 | home | First-flight checklist ▾ | AFTER:Running… | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-158.json | — |
| EXC-0787 | home | Skills & learned workflows ▾ | AFTER:Running… | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-159.json | — |
| EXC-0788 | home | Security ▾ | AFTER:Running… | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-160.json | — |
| EXC-0789 | home_automation | Open Presence | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-161.json | — |
| EXC-0790 | home_automation | Open Security | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-162.json | — |
| EXC-0791 | home_automation | Search | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-163.json | — |
| EXC-0792 | home_automation | Open Home Assistant | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-164.json | — |
| EXC-0793 | home_automation | Status | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-165.json | — |
| EXC-0794 | home_automation | Apply | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-166.json | — |
| EXC-0795 | home_automation | haPasteTokenBtn | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0795.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (credentials/system control) |
| EXC-0796 | home_automation | haTokenModalBtn | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0796.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (credentials/system control) |
| EXC-0797 | home_automation | haTestBtn | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-169.json | — |
| EXC-0798 | home_automation | haSaveBtn | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-170.json | — |
| EXC-0799 | home_automation | ghost-btn small ha-quick-btn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-171.json | — |
| EXC-0800 | home_automation | haSetupWizardBtn | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-172.json | — |
| EXC-0801 | home_automation | haSceneSaveBtn | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-247.json | — |
| EXC-0802 | home_automation | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-248.json | — |
| EXC-0803 | home_automation | Discover Kasa | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-249.json | — |
| EXC-0804 | home_automation | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-248.json | — |
| EXC-0805 | home_automation | Search Smart Home entities | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-250.json | — |
| EXC-0806 | home_automation | http://127.0.0.1:8123 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-251.json | — |
| EXC-0807 | home_automation | scene.leaving (optional) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-252.json | — |
| EXC-0808 | home_automation | scene.leaving | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-253.json | — |
| EXC-0809 | home_automation | Paste token | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0809.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (credentials/system control) |
| EXC-0810 | home_automation | Smart Home profile | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0810.json | — |
| EXC-0811 | home_automation | Entity domain | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0811.json | — |
| EXC-0812 | home_automation | SETUP & CONNECTION | DEFAULT | controlsDefault | yes | NOT TESTABLE | — | by_id/EXC-0812.json | NOT TESTABLE — LIVE SIDE EFFECT WOULD MODIFY REAL USER/SYSTEM DATA (Home Assistant device/scene write) |
| EXC-0813 | integrations | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-173.json | — |
| EXC-0814 | integrations | Test configured | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-174.json | — |
| EXC-0815 | integrations | Diagnostics | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-175.json | — |
| EXC-0816 | integrations | Search providers… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-176.json | — |
| EXC-0817 | integrations | Filter by category | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-177.json | — |
| EXC-0818 | integrations | Advanced options | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0818.json | — |
| EXC-0819 | integrations | Refresh | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-173.json | — |
| EXC-0820 | integrations | Test configured | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-174.json | — |
| EXC-0821 | integrations | Diagnostics | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-175.json | — |
| EXC-0822 | integrations | Search providers… | AFTER:Advanced options | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-176.json | — |
| EXC-0823 | integrations | Filter by category | AFTER:Advanced options | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-177.json | — |
| EXC-0824 | integrations | Advanced options | AFTER:Advanced options | conditional | yes | PASS | — | by_id/EXC-0824.json | — |
| EXC-0825 | integrity | More | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-255.json | — |
| EXC-0826 | integrity | More | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-255.json | — |
| EXC-0827 | integrity | Refresh | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-526.json | — |
| EXC-0828 | integrity | Repair | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-527.json | — |
| EXC-0829 | journal | Daily | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-256.json | — |
| EXC-0830 | journal | Weekly | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-257.json | — |
| EXC-0831 | journal | Monthly | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-258.json | — |
| EXC-0832 | journal | Habits | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-259.json | — |
| EXC-0833 | journal | Wellness | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-260.json | — |
| EXC-0834 | journal | Future | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-261.json | — |
| EXC-0835 | journal | Index | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-262.json | — |
| EXC-0836 | journal | Collections | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-263.json | — |
| EXC-0837 | journal | Projects | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0837.json | — |
| EXC-0838 | journal | Key | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0838.json | — |
| EXC-0839 | journal | Distraction-free writing (W) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0839.json | — |
| EXC-0840 | journal | Calendar = scheduled commitments | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0840.json | — |
| EXC-0841 | journal | Planner = actionable work | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0841.json | — |
| EXC-0842 | journal | Memory = lasting knowledge | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0842.json | — |
| EXC-0843 | journal | Search | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0843.json | — |
| EXC-0844 | journal | AI reflection (you start it) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0844.json | — |
| EXC-0845 | journal | Suggest promotions — confirm each | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0845.json | — |
| EXC-0846 | journal | Month-end review wizard | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0846.json | — |
| EXC-0847 | journal | journalOpenDocumentsBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0847.json | — |
| EXC-0848 | journal | journalOpenAudioBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0848.json | — |
| EXC-0849 | journal | journalPrintBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0849.json | — |
| EXC-0850 | journal | journalPdfBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0850.json | — |
| EXC-0851 | journal | journalExportBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0851.json | — |
| EXC-0852 | journal | journalExportEncBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0852.json | — |
| EXC-0853 | journal | journalImportBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0853.json | — |
| EXC-0854 | journal | journalImportEncBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0854.json | — |
| EXC-0855 | journal | journalBackupBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0855.json | — |
| EXC-0856 | journal | Voice → rapid log draft | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0856.json | — |
| EXC-0857 | journal | Paste OCR / scan text | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0857.json | — |
| EXC-0858 | journal | journalShortcutsBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0858.json | — |
| EXC-0859 | journal | journalUndoBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0859.json | — |
| EXC-0860 | journal | journalRedoBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0860.json | — |
| EXC-0861 | journal | journalMigrateBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0861.json | — |
| EXC-0862 | journal | Add | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0862.json | — |
| EXC-0863 | journal | 2026-08-10 | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0863.json | — |
| EXC-0864 | journal | Search journal | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0864.json | — |
| EXC-0865 | journal | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0865.json | — |
| EXC-0866 | journal | Rapid log — one line per entry. Indent 2 spaces to nest under the previous line. | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0866.json | — |
| EXC-0867 | journal | Month migrate destination | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0867.json | — |
| EXC-0868 | journal | Default bullet type | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0868.json | — |
| EXC-0869 | journal | More | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0869.json | — |
| EXC-0870 | journal | Daily | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-256.json | — |
| EXC-0871 | journal | Weekly | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-257.json | — |
| EXC-0872 | journal | Monthly | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-258.json | — |
| EXC-0873 | journal | Habits | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-259.json | — |
| EXC-0874 | journal | Wellness | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-260.json | — |
| EXC-0875 | journal | Future | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-261.json | — |
| EXC-0876 | journal | Index | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-262.json | — |
| EXC-0877 | journal | Collections | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-263.json | — |
| EXC-0878 | journal | Projects | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0878.json | — |
| EXC-0879 | journal | Key | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0879.json | — |
| EXC-0880 | journal | Distraction-free writing (W) | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0880.json | — |
| EXC-0881 | journal | Calendar = scheduled commitments | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0881.json | — |
| EXC-0882 | journal | Planner = actionable work | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0882.json | — |
| EXC-0883 | journal | Memory = lasting knowledge | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0883.json | — |
| EXC-0884 | journal | Search | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0884.json | — |
| EXC-0885 | journal | AI reflection (you start it) | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0885.json | — |
| EXC-0886 | journal | Suggest promotions — confirm each | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0886.json | — |
| EXC-0887 | journal | Month-end review wizard | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0887.json | — |
| EXC-0888 | journal | journalOpenDocumentsBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0888.json | — |
| EXC-0889 | journal | journalOpenAudioBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0889.json | — |
| EXC-0890 | journal | journalPrintBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0890.json | — |
| EXC-0891 | journal | journalPdfBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0891.json | — |
| EXC-0892 | journal | journalExportBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0892.json | — |
| EXC-0893 | journal | journalExportEncBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0893.json | — |
| EXC-0894 | journal | journalImportBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0894.json | — |
| EXC-0895 | journal | journalImportEncBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0895.json | — |
| EXC-0896 | journal | journalBackupBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0896.json | — |
| EXC-0897 | journal | Voice → rapid log draft | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0897.json | — |
| EXC-0898 | journal | Paste OCR / scan text | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0898.json | — |
| EXC-0899 | journal | journalShortcutsBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0899.json | — |
| EXC-0900 | journal | journalUndoBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0900.json | — |
| EXC-0901 | journal | journalRedoBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0901.json | — |
| EXC-0902 | journal | journalMigrateBtn | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0902.json | — |
| EXC-0903 | journal | Add | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0903.json | — |
| EXC-0904 | journal | 2026-08-10 | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0904.json | — |
| EXC-0905 | journal | Search journal | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0905.json | — |
| EXC-0906 | journal | on | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0906.json | — |
| EXC-0907 | journal | Rapid log — one line per entry. Indent 2 spaces to nest under the previous line. | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0907.json | — |
| EXC-0908 | journal | Month migrate destination | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0908.json | — |
| EXC-0909 | journal | Default bullet type | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0909.json | — |
| EXC-0910 | journal | Daily | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-256.json | — |
| EXC-0911 | journal | Weekly | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-257.json | — |
| EXC-0912 | journal | Monthly | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-258.json | — |
| EXC-0913 | journal | Habits | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-259.json | — |
| EXC-0914 | journal | Wellness | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-260.json | — |
| EXC-0915 | journal | Future | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-261.json | — |
| EXC-0916 | journal | Index | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-262.json | — |
| EXC-0917 | journal | Collections | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-263.json | — |
| EXC-0918 | journal | Projects | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0918.json | — |
| EXC-0919 | journal | Key | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0919.json | — |
| EXC-0920 | journal | Distraction-free writing (W) | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0920.json | — |
| EXC-0921 | journal | Calendar = scheduled commitments | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0921.json | — |
| EXC-0922 | journal | Planner = actionable work | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0922.json | — |
| EXC-0923 | journal | Memory = lasting knowledge | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0923.json | — |
| EXC-0924 | journal | Search | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0924.json | — |
| EXC-0925 | journal | AI reflection (you start it) | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0925.json | — |
| EXC-0926 | journal | Suggest promotions — confirm each | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0926.json | — |
| EXC-0927 | journal | Month-end review wizard | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0927.json | — |
| EXC-0928 | journal | Documents | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-557.json | — |
| EXC-0929 | journal | Audio | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-558.json | — |
| EXC-0930 | journal | Print month | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-559.json | — |
| EXC-0931 | journal | Export PDF | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-560.json | — |
| EXC-0932 | journal | Export JSON | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-561.json | — |
| EXC-0933 | journal | Export encrypted | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-562.json | — |
| EXC-0934 | journal | Import | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-563.json | — |
| EXC-0935 | journal | Import encrypted | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-564.json | — |
| EXC-0936 | journal | Backup now | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-565.json | — |
| EXC-0937 | journal | Voice → rapid log draft | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0937.json | — |
| EXC-0938 | journal | Paste OCR / scan text | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0938.json | — |
| EXC-0939 | journal | Shortcuts (?) | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-568.json | — |
| EXC-0940 | journal | Undo | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-569.json | — |
| EXC-0941 | journal | Redo | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-570.json | — |
| EXC-0942 | journal | Migrate month | AFTER:More | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-571.json | — |
| EXC-0943 | journal | Add | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0943.json | — |
| EXC-0944 | journal | 2026-08-10 | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0944.json | — |
| EXC-0945 | journal | Search journal | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0945.json | — |
| EXC-0946 | journal | on | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0946.json | — |
| EXC-0947 | journal | Rapid log — one line per entry. Indent 2 spaces to nest under the previous line. | AFTER:More | conditional | yes | FAIL | BUG-024 | by_id/EXC-0947.json | — |
| EXC-0948 | journal | Month migrate destination | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0948.json | — |
| EXC-0949 | journal | Default bullet type | AFTER:More | conditional | yes | PASS | — | by_id/EXC-0949.json | — |
| EXC-0950 | maker | Detach maker lab panel | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-264.json | — |
| EXC-0951 | maker | Generate | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-265.json | — |
| EXC-0952 | maker | Iterate | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-266.json | — |
| EXC-0953 | maker | Hello cube | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-267.json | — |
| EXC-0954 | maker | Slice | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-268.json | — |
| EXC-0955 | maker | Download STL | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-269.json | — |
| EXC-0956 | maker | Refresh | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-270.json | — |
| EXC-0957 | maker | Gallery | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-271.json | — |
| EXC-0958 | maker | Documents | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0958.json | — |
| EXC-0959 | maker | Clear gallery | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0959.json | — |
| EXC-0960 | maker | Detach printer panel | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-0960.json | — |
| EXC-0961 | maker | Add | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0961.json | — |
| EXC-0962 | maker | Discover KE | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0962.json | — |
| EXC-0963 | maker | Status | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0963.json | — |
| EXC-0964 | maker | Start print | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0964.json | — |
| EXC-0965 | maker | Design a 5 inch to 4 inch hose adapter… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0965.json | — |
| EXC-0966 | maker | Iterate: make it taller, add mounting holes… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0966.json | — |
| EXC-0967 | maker | Printer name | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0967.json | — |
| EXC-0968 | maker | IP for Creality KE (e.g. 192.168.1.50) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0968.json | — |
| EXC-0969 | maker | CAD backend | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0969.json | — |
| EXC-0970 | maker | Printer model | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-0970.json | — |
| EXC-0971 | maker | Detach maker lab panel | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-264.json | — |
| EXC-0972 | maker | Generate | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-265.json | — |
| EXC-0973 | maker | Iterate | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-266.json | — |
| EXC-0974 | maker | Hello cube | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-267.json | — |
| EXC-0975 | maker | Slice | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-268.json | — |
| EXC-0976 | maker | Download STL | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-269.json | — |
| EXC-0977 | maker | Refresh | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-270.json | — |
| EXC-0978 | maker | Gallery | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-271.json | — |
| EXC-0979 | maker | Documents | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0979.json | — |
| EXC-0980 | maker | Clear gallery | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0980.json | — |
| EXC-0981 | maker | Detach printer panel | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-0981.json | — |
| EXC-0982 | maker | Add | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0982.json | — |
| EXC-0983 | maker | Discover KE | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0983.json | — |
| EXC-0984 | maker | Status | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0984.json | — |
| EXC-0985 | maker | Start print | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0985.json | — |
| EXC-0986 | maker | Design a 5 inch to 4 inch hose adapter… | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0986.json | — |
| EXC-0987 | maker | Iterate: make it taller, add mounting holes… | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0987.json | — |
| EXC-0988 | maker | Printer name | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0988.json | — |
| EXC-0989 | maker | IP for Creality KE (e.g. 192.168.1.50) | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0989.json | — |
| EXC-0990 | maker | CAD backend | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0990.json | — |
| EXC-0991 | maker | Printer model | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-0991.json | — |
| EXC-0992 | meme | Generate in chat | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-272.json | — |
| EXC-0993 | meme | Open Gallery | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-273.json | — |
| EXC-0994 | meme | Open Video Studio | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-274.json | — |
| EXC-0995 | meme | Quick preview (text only) | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-275.json | — |
| EXC-0996 | meme | Generate meme | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-276.json | — |
| EXC-0997 | meme | e.g. when ARIA finally works on the first try | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-277.json | — |
| EXC-0998 | meme | WHEN YOU RESTART | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-278.json | — |
| EXC-0999 | meme | AND IT ACTUALLY HELPS | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-279.json | — |
| EXC-1000 | meme | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1000.json | — |
| EXC-1001 | memory | Search (/) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-280.json | — |
| EXC-1002 | memory | New memory (N) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-281.json | — |
| EXC-1003 | memory | Briefing | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-282.json | — |
| EXC-1004 | memory | Assist | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-283.json | — |
| EXC-1005 | memory | ? | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-284.json | — |
| EXC-1006 | memory | Update profile | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-285.json | — |
| EXC-1007 | memory | Edit answers | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-286.json | — |
| EXC-1008 | memory | Save preferences | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-287.json | — |
| EXC-1009 | memory | Refresh machine facts | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1009.json | — |
| EXC-1010 | memory | cheatsheetViewBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1010.json | — |
| EXC-1011 | memory | cheatsheetEditBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1011.json | — |
| EXC-1012 | memory | cheatsheetResetBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1012.json | — |
| EXC-1013 | memory | memoryOpenJournalBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1013.json | — |
| EXC-1014 | memory | memoryOpenProjectsBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1014.json | — |
| EXC-1015 | memory | memoryOpenBrowserBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1015.json | — |
| EXC-1016 | memory | memoryOpenDocumentsBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1016.json | — |
| EXC-1017 | memory | Knowledge Briefs (research) — not Connections or Memory | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1017.json | — |
| EXC-1018 | memory | memoryExportBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1018.json | — |
| EXC-1019 | memory | memoryImportBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1019.json | — |
| EXC-1020 | memory | memoryPruneBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1020.json | — |
| EXC-1021 | memory | memoryScrubBtn | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1021.json | — |
| EXC-1022 | memory | Open Knowledge Briefs | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1022.json | — |
| EXC-1023 | memory | Relationship explorer | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1023.json | — |
| EXC-1024 | memory | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1024.json | — |
| EXC-1025 | memory | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1025.json | — |
| EXC-1026 | memory | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1026.json | — |
| EXC-1027 | memory | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1027.json | — |
| EXC-1028 | memory | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1028.json | — |
| EXC-1029 | memory | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1029.json | — |
| EXC-1030 | memory | Search memories | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1030.json | — |
| EXC-1031 | memory | Auto-memory mode | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1031.json | — |
| EXC-1032 | memory | Select cheatsheet | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1032.json | — |
| EXC-1033 | memory | Filter by type | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1033.json | — |
| EXC-1034 | memory | Filter by namespace | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1034.json | — |
| EXC-1035 | memory | Browse & tools | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1035.json | — |
| EXC-1036 | memory | Search (/) | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-280.json | — |
| EXC-1037 | memory | New memory (N) | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-281.json | — |
| EXC-1038 | memory | Briefing | AFTER:New memory (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-282.json | — |
| EXC-1039 | memory | Assist | AFTER:New memory (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-283.json | — |
| EXC-1040 | memory | ? | AFTER:New memory (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-284.json | — |
| EXC-1041 | memory | Update profile | AFTER:New memory (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-285.json | — |
| EXC-1042 | memory | Edit answers | AFTER:New memory (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-286.json | — |
| EXC-1043 | memory | Save preferences | AFTER:New memory (N) | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-287.json | — |
| EXC-1044 | memory | Refresh machine facts | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1044.json | — |
| EXC-1045 | memory | cheatsheetViewBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1045.json | — |
| EXC-1046 | memory | cheatsheetEditBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1046.json | — |
| EXC-1047 | memory | cheatsheetResetBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1047.json | — |
| EXC-1048 | memory | memoryOpenJournalBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1048.json | — |
| EXC-1049 | memory | memoryOpenProjectsBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1049.json | — |
| EXC-1050 | memory | memoryOpenBrowserBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1050.json | — |
| EXC-1051 | memory | memoryOpenDocumentsBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1051.json | — |
| EXC-1052 | memory | Knowledge Briefs (research) — not Connections or Memory | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1052.json | — |
| EXC-1053 | memory | memoryExportBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1053.json | — |
| EXC-1054 | memory | memoryImportBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1054.json | — |
| EXC-1055 | memory | memoryPruneBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1055.json | — |
| EXC-1056 | memory | memoryScrubBtn | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1056.json | — |
| EXC-1057 | memory | Open Knowledge Briefs | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1057.json | — |
| EXC-1058 | memory | Relationship explorer | AFTER:New memory (N) | conditional | yes | FAIL | BUG-024 | by_id/EXC-1058.json | — |
| EXC-1059 | memory | on | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1059.json | — |
| EXC-1060 | memory | on | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1060.json | — |
| EXC-1061 | memory | on | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1061.json | — |
| EXC-1062 | memory | on | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1062.json | — |
| EXC-1063 | memory | on | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1063.json | — |
| EXC-1064 | memory | on | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1064.json | — |
| EXC-1065 | memory | Search memories | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1065.json | — |
| EXC-1066 | memory | Auto-memory mode | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1066.json | — |
| EXC-1067 | memory | Select cheatsheet | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1067.json | — |
| EXC-1068 | memory | Filter by type | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1068.json | — |
| EXC-1069 | memory | Filter by namespace | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1069.json | — |
| EXC-1070 | memory | Browse & tools | AFTER:New memory (N) | conditional | yes | PASS | — | by_id/EXC-1070.json | — |
| EXC-1071 | memory | Search (/) | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-280.json | — |
| EXC-1072 | memory | New memory (N) | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-281.json | — |
| EXC-1073 | memory | Briefing | AFTER:Edit answers | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-282.json | — |
| EXC-1074 | memory | Assist | AFTER:Edit answers | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-283.json | — |
| EXC-1075 | memory | ? | AFTER:Edit answers | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-284.json | — |
| EXC-1076 | memory | Update profile | AFTER:Edit answers | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-285.json | — |
| EXC-1077 | memory | Edit answers | AFTER:Edit answers | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-286.json | — |
| EXC-1078 | memory | Save preferences | AFTER:Edit answers | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-287.json | — |
| EXC-1079 | memory | Refresh machine facts | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1079.json | — |
| EXC-1080 | memory | cheatsheetViewBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1080.json | — |
| EXC-1081 | memory | cheatsheetEditBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1081.json | — |
| EXC-1082 | memory | cheatsheetResetBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1082.json | — |
| EXC-1083 | memory | memoryOpenJournalBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1083.json | — |
| EXC-1084 | memory | memoryOpenProjectsBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1084.json | — |
| EXC-1085 | memory | memoryOpenBrowserBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1085.json | — |
| EXC-1086 | memory | memoryOpenDocumentsBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1086.json | — |
| EXC-1087 | memory | Knowledge Briefs (research) — not Connections or Memory | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1087.json | — |
| EXC-1088 | memory | memoryExportBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1088.json | — |
| EXC-1089 | memory | memoryImportBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1089.json | — |
| EXC-1090 | memory | memoryPruneBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1090.json | — |
| EXC-1091 | memory | memoryScrubBtn | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1091.json | — |
| EXC-1092 | memory | Open Knowledge Briefs | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1092.json | — |
| EXC-1093 | memory | Relationship explorer | AFTER:Edit answers | conditional | yes | FAIL | BUG-024 | by_id/EXC-1093.json | — |
| EXC-1094 | memory | on | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1094.json | — |
| EXC-1095 | memory | on | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1095.json | — |
| EXC-1096 | memory | on | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1096.json | — |
| EXC-1097 | memory | on | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1097.json | — |
| EXC-1098 | memory | on | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1098.json | — |
| EXC-1099 | memory | on | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1099.json | — |
| EXC-1100 | memory | Search memories | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1100.json | — |
| EXC-1101 | memory | Auto-memory mode | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1101.json | — |
| EXC-1102 | memory | Select cheatsheet | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1102.json | — |
| EXC-1103 | memory | Filter by type | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1103.json | — |
| EXC-1104 | memory | Filter by namespace | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1104.json | — |
| EXC-1105 | memory | Browse & tools | AFTER:Edit answers | conditional | yes | PASS | — | by_id/EXC-1105.json | — |
| EXC-1106 | memory | Search (/) | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-280.json | — |
| EXC-1107 | memory | New memory (N) | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-281.json | — |
| EXC-1108 | memory | Briefing | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-282.json | — |
| EXC-1109 | memory | Assist | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-283.json | — |
| EXC-1110 | memory | ? | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-284.json | — |
| EXC-1111 | memory | Update profile | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-285.json | — |
| EXC-1112 | memory | Edit answers | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-286.json | — |
| EXC-1113 | memory | Save preferences | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-287.json | — |
| EXC-1114 | memory | Refresh machine facts | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1114.json | — |
| EXC-1115 | memory | cheatsheetViewBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1115.json | — |
| EXC-1116 | memory | cheatsheetEditBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1116.json | — |
| EXC-1117 | memory | cheatsheetResetBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1117.json | — |
| EXC-1118 | memory | memoryOpenJournalBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1118.json | — |
| EXC-1119 | memory | memoryOpenProjectsBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1119.json | — |
| EXC-1120 | memory | memoryOpenBrowserBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1120.json | — |
| EXC-1121 | memory | memoryOpenDocumentsBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1121.json | — |
| EXC-1122 | memory | Knowledge Briefs (research) — not Connections or Memory | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1122.json | — |
| EXC-1123 | memory | memoryExportBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1123.json | — |
| EXC-1124 | memory | memoryImportBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1124.json | — |
| EXC-1125 | memory | memoryPruneBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1125.json | — |
| EXC-1126 | memory | memoryScrubBtn | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1126.json | — |
| EXC-1127 | memory | Open Knowledge Briefs | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1127.json | — |
| EXC-1128 | memory | Relationship explorer | AFTER:cheatsheetEditBtn | conditional | yes | FAIL | BUG-024 | by_id/EXC-1128.json | — |
| EXC-1129 | memory | on | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1129.json | — |
| EXC-1130 | memory | on | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1130.json | — |
| EXC-1131 | memory | on | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1131.json | — |
| EXC-1132 | memory | on | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1132.json | — |
| EXC-1133 | memory | on | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1133.json | — |
| EXC-1134 | memory | on | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1134.json | — |
| EXC-1135 | memory | Search memories | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1135.json | — |
| EXC-1136 | memory | Auto-memory mode | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1136.json | — |
| EXC-1137 | memory | Select cheatsheet | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1137.json | — |
| EXC-1138 | memory | Filter by type | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1138.json | — |
| EXC-1139 | memory | Filter by namespace | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1139.json | — |
| EXC-1140 | memory | Browse & tools | AFTER:cheatsheetEditBtn | conditional | yes | PASS | — | by_id/EXC-1140.json | — |
| EXC-1141 | mission | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1142 | mission | Open Job Center | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1143 | mission | Open Notifications (Activity Center inbox) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1144 | mission | Open Chat | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1145 | mission | Open System audit | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1146 | mission | Open Home | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1147 | mission | Overview | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1148 | mission | Routing | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1149 | mission | Performance | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1149.json | — |
| EXC-1150 | mission | Recovery | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1150.json | — |
| EXC-1151 | mission | Connection | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1151.json | — |
| EXC-1152 | mission | Advanced ▾ | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1152.json | — |
| EXC-1153 | mission | Hardware | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1153.json | — |
| EXC-1154 | mission | Inference | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1154.json | — |
| EXC-1155 | mission | Memory | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1155.json | — |
| EXC-1156 | mission | Knowledge | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1156.json | — |
| EXC-1157 | mission | Databases | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1157.json | — |
| EXC-1158 | mission | Settings | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1158.json | — |
| EXC-1159 | mission | Timeline | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1159.json | — |
| EXC-1160 | mission | Release | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1160.json | — |
| EXC-1161 | mission | Applications | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1161.json | — |
| EXC-1162 | mission | Queue Snapshot | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1162.json | — |
| EXC-1163 | mission | Operations Event Log | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1163.json | — |
| EXC-1164 | mission | Intent Analytics | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1164.json | — |
| EXC-1165 | mission | Refresh | TAB:Connection | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1166 | mission | Open Job Center | TAB:Connection | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1167 | mission | Open Notifications (Activity Center inbox) | TAB:Connection | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1168 | mission | Open Chat | TAB:Connection | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1169 | mission | Open System audit | TAB:Connection | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1170 | mission | Open Home | TAB:Connection | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1171 | mission | Overview | TAB:Connection | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1172 | mission | Routing | TAB:Connection | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1173 | mission | Performance | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1173.json | — |
| EXC-1174 | mission | Recovery | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1174.json | — |
| EXC-1175 | mission | Connection | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1175.json | — |
| EXC-1176 | mission | Advanced ▾ | TAB:Connection | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1176.json | — |
| EXC-1177 | mission | Hardware | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1177.json | — |
| EXC-1178 | mission | Inference | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1178.json | — |
| EXC-1179 | mission | Memory | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1179.json | — |
| EXC-1180 | mission | Knowledge | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1180.json | — |
| EXC-1181 | mission | Databases | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1181.json | — |
| EXC-1182 | mission | Settings | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1182.json | — |
| EXC-1183 | mission | Timeline | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1183.json | — |
| EXC-1184 | mission | Release | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1184.json | — |
| EXC-1185 | mission | Applications | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1185.json | — |
| EXC-1186 | mission | Queue Snapshot | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1186.json | — |
| EXC-1187 | mission | Operations Event Log | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1187.json | — |
| EXC-1188 | mission | Intent Analytics | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1188.json | — |
| EXC-1189 | mission | Refresh | TAB:Databases | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1190 | mission | Open Job Center | TAB:Databases | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1191 | mission | Open Notifications (Activity Center inbox) | TAB:Databases | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1192 | mission | Open Chat | TAB:Databases | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1193 | mission | Open System audit | TAB:Databases | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1194 | mission | Open Home | TAB:Databases | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1195 | mission | Overview | TAB:Databases | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1196 | mission | Routing | TAB:Databases | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1197 | mission | Performance | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1197.json | — |
| EXC-1198 | mission | Recovery | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1198.json | — |
| EXC-1199 | mission | Connection | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1199.json | — |
| EXC-1200 | mission | Advanced ▾ | TAB:Databases | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1200.json | — |
| EXC-1201 | mission | Hardware | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1201.json | — |
| EXC-1202 | mission | Inference | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1202.json | — |
| EXC-1203 | mission | Memory | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1203.json | — |
| EXC-1204 | mission | Knowledge | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1204.json | — |
| EXC-1205 | mission | Databases | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1205.json | — |
| EXC-1206 | mission | Settings | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1206.json | — |
| EXC-1207 | mission | Timeline | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1207.json | — |
| EXC-1208 | mission | Release | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1208.json | — |
| EXC-1209 | mission | Applications | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1209.json | — |
| EXC-1210 | mission | Queue Snapshot | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1210.json | — |
| EXC-1211 | mission | Operations Event Log | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1211.json | — |
| EXC-1212 | mission | Intent Analytics | TAB:Databases | tabStates | yes | PASS | — | by_id/EXC-1212.json | — |
| EXC-1213 | mission | Refresh | TAB:Hardware | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1214 | mission | Open Job Center | TAB:Hardware | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1215 | mission | Open Notifications (Activity Center inbox) | TAB:Hardware | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1216 | mission | Open Chat | TAB:Hardware | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1217 | mission | Open System audit | TAB:Hardware | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1218 | mission | Open Home | TAB:Hardware | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1219 | mission | Overview | TAB:Hardware | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1220 | mission | Routing | TAB:Hardware | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1221 | mission | Performance | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1221.json | — |
| EXC-1222 | mission | Recovery | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1222.json | — |
| EXC-1223 | mission | Connection | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1223.json | — |
| EXC-1224 | mission | Advanced ▾ | TAB:Hardware | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1224.json | — |
| EXC-1225 | mission | Hardware | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1225.json | — |
| EXC-1226 | mission | Inference | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1226.json | — |
| EXC-1227 | mission | Memory | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1227.json | — |
| EXC-1228 | mission | Knowledge | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1228.json | — |
| EXC-1229 | mission | Databases | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1229.json | — |
| EXC-1230 | mission | Settings | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1230.json | — |
| EXC-1231 | mission | Timeline | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1231.json | — |
| EXC-1232 | mission | Release | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1232.json | — |
| EXC-1233 | mission | Applications | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1233.json | — |
| EXC-1234 | mission | Queue Snapshot | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1234.json | — |
| EXC-1235 | mission | Operations Event Log | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1235.json | — |
| EXC-1236 | mission | Intent Analytics | TAB:Hardware | tabStates | yes | PASS | — | by_id/EXC-1236.json | — |
| EXC-1237 | mission | Refresh | TAB:Inference | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1238 | mission | Open Job Center | TAB:Inference | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1239 | mission | Open Notifications (Activity Center inbox) | TAB:Inference | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1240 | mission | Open Chat | TAB:Inference | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1241 | mission | Open System audit | TAB:Inference | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1242 | mission | Open Home | TAB:Inference | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1243 | mission | Overview | TAB:Inference | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1244 | mission | Routing | TAB:Inference | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1245 | mission | Performance | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1245.json | — |
| EXC-1246 | mission | Recovery | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1246.json | — |
| EXC-1247 | mission | Connection | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1247.json | — |
| EXC-1248 | mission | Advanced ▾ | TAB:Inference | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1248.json | — |
| EXC-1249 | mission | Hardware | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1249.json | — |
| EXC-1250 | mission | Inference | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1250.json | — |
| EXC-1251 | mission | Memory | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1251.json | — |
| EXC-1252 | mission | Knowledge | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1252.json | — |
| EXC-1253 | mission | Databases | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1253.json | — |
| EXC-1254 | mission | Settings | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1254.json | — |
| EXC-1255 | mission | Timeline | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1255.json | — |
| EXC-1256 | mission | Release | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1256.json | — |
| EXC-1257 | mission | Applications | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1257.json | — |
| EXC-1258 | mission | Queue Snapshot | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1258.json | — |
| EXC-1259 | mission | Operations Event Log | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1259.json | — |
| EXC-1260 | mission | Intent Analytics | TAB:Inference | tabStates | yes | PASS | — | by_id/EXC-1260.json | — |
| EXC-1261 | mission | Refresh | TAB:Knowledge | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1262 | mission | Open Job Center | TAB:Knowledge | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1263 | mission | Open Notifications (Activity Center inbox) | TAB:Knowledge | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1264 | mission | Open Chat | TAB:Knowledge | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1265 | mission | Open System audit | TAB:Knowledge | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1266 | mission | Open Home | TAB:Knowledge | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1267 | mission | Overview | TAB:Knowledge | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1268 | mission | Routing | TAB:Knowledge | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1269 | mission | Performance | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1269.json | — |
| EXC-1270 | mission | Recovery | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1270.json | — |
| EXC-1271 | mission | Connection | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1271.json | — |
| EXC-1272 | mission | Advanced ▾ | TAB:Knowledge | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1272.json | — |
| EXC-1273 | mission | Hardware | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1273.json | — |
| EXC-1274 | mission | Inference | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1274.json | — |
| EXC-1275 | mission | Memory | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1275.json | — |
| EXC-1276 | mission | Knowledge | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1276.json | — |
| EXC-1277 | mission | Databases | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1277.json | — |
| EXC-1278 | mission | Settings | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1278.json | — |
| EXC-1279 | mission | Timeline | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1279.json | — |
| EXC-1280 | mission | Release | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1280.json | — |
| EXC-1281 | mission | Applications | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1281.json | — |
| EXC-1282 | mission | Queue Snapshot | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1282.json | — |
| EXC-1283 | mission | Operations Event Log | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1283.json | — |
| EXC-1284 | mission | Intent Analytics | TAB:Knowledge | tabStates | yes | PASS | — | by_id/EXC-1284.json | — |
| EXC-1285 | mission | Refresh | TAB:Memory | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1286 | mission | Open Job Center | TAB:Memory | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1287 | mission | Open Notifications (Activity Center inbox) | TAB:Memory | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1288 | mission | Open Chat | TAB:Memory | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1289 | mission | Open System audit | TAB:Memory | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1290 | mission | Open Home | TAB:Memory | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1291 | mission | Overview | TAB:Memory | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1292 | mission | Routing | TAB:Memory | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1293 | mission | Performance | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1293.json | — |
| EXC-1294 | mission | Recovery | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1294.json | — |
| EXC-1295 | mission | Connection | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1295.json | — |
| EXC-1296 | mission | Advanced ▾ | TAB:Memory | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1296.json | — |
| EXC-1297 | mission | Hardware | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1297.json | — |
| EXC-1298 | mission | Inference | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1298.json | — |
| EXC-1299 | mission | Memory | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1299.json | — |
| EXC-1300 | mission | Knowledge | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1300.json | — |
| EXC-1301 | mission | Databases | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1301.json | — |
| EXC-1302 | mission | Settings | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1302.json | — |
| EXC-1303 | mission | Timeline | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1303.json | — |
| EXC-1304 | mission | Release | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1304.json | — |
| EXC-1305 | mission | Applications | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1305.json | — |
| EXC-1306 | mission | Queue Snapshot | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1306.json | — |
| EXC-1307 | mission | Operations Event Log | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1307.json | — |
| EXC-1308 | mission | Intent Analytics | TAB:Memory | tabStates | yes | PASS | — | by_id/EXC-1308.json | — |
| EXC-1309 | mission | Refresh | TAB:Overview | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1310 | mission | Open Job Center | TAB:Overview | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1311 | mission | Open Notifications (Activity Center inbox) | TAB:Overview | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1312 | mission | Open Chat | TAB:Overview | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1313 | mission | Open System audit | TAB:Overview | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1314 | mission | Open Home | TAB:Overview | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1315 | mission | Overview | TAB:Overview | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1316 | mission | Routing | TAB:Overview | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1317 | mission | Performance | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1317.json | — |
| EXC-1318 | mission | Recovery | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1318.json | — |
| EXC-1319 | mission | Connection | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1319.json | — |
| EXC-1320 | mission | Advanced ▾ | TAB:Overview | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1320.json | — |
| EXC-1321 | mission | Hardware | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1321.json | — |
| EXC-1322 | mission | Inference | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1322.json | — |
| EXC-1323 | mission | Memory | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1323.json | — |
| EXC-1324 | mission | Knowledge | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1324.json | — |
| EXC-1325 | mission | Databases | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1325.json | — |
| EXC-1326 | mission | Settings | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1326.json | — |
| EXC-1327 | mission | Timeline | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1327.json | — |
| EXC-1328 | mission | Release | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1328.json | — |
| EXC-1329 | mission | Applications | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1329.json | — |
| EXC-1330 | mission | Queue Snapshot | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1330.json | — |
| EXC-1331 | mission | Operations Event Log | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1331.json | — |
| EXC-1332 | mission | Intent Analytics | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1332.json | — |
| EXC-1333 | mission | Refresh | TAB:Performance | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1334 | mission | Open Job Center | TAB:Performance | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1335 | mission | Open Notifications (Activity Center inbox) | TAB:Performance | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1336 | mission | Open Chat | TAB:Performance | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1337 | mission | Open System audit | TAB:Performance | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1338 | mission | Open Home | TAB:Performance | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1339 | mission | Overview | TAB:Performance | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1340 | mission | Routing | TAB:Performance | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1341 | mission | Performance | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1341.json | — |
| EXC-1342 | mission | Recovery | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1342.json | — |
| EXC-1343 | mission | Connection | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1343.json | — |
| EXC-1344 | mission | Advanced ▾ | TAB:Performance | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1344.json | — |
| EXC-1345 | mission | Hardware | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1345.json | — |
| EXC-1346 | mission | Inference | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1346.json | — |
| EXC-1347 | mission | Memory | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1347.json | — |
| EXC-1348 | mission | Knowledge | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1348.json | — |
| EXC-1349 | mission | Databases | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1349.json | — |
| EXC-1350 | mission | Settings | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1350.json | — |
| EXC-1351 | mission | Timeline | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1351.json | — |
| EXC-1352 | mission | Release | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1352.json | — |
| EXC-1353 | mission | Applications | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1353.json | — |
| EXC-1354 | mission | Queue Snapshot | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1354.json | — |
| EXC-1355 | mission | Operations Event Log | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1355.json | — |
| EXC-1356 | mission | Intent Analytics | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1356.json | — |
| EXC-1357 | mission | Refresh | TAB:Recovery | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1358 | mission | Open Job Center | TAB:Recovery | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1359 | mission | Open Notifications (Activity Center inbox) | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1360 | mission | Open Chat | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1361 | mission | Open System audit | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1362 | mission | Open Home | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1363 | mission | Overview | TAB:Recovery | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1364 | mission | Routing | TAB:Recovery | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1365 | mission | Performance | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1365.json | — |
| EXC-1366 | mission | Recovery | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1366.json | — |
| EXC-1367 | mission | Connection | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1367.json | — |
| EXC-1368 | mission | Advanced ▾ | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1368.json | — |
| EXC-1369 | mission | Hardware | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1369.json | — |
| EXC-1370 | mission | Inference | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1370.json | — |
| EXC-1371 | mission | Memory | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1371.json | — |
| EXC-1372 | mission | Knowledge | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1372.json | — |
| EXC-1373 | mission | Databases | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1373.json | — |
| EXC-1374 | mission | Settings | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1374.json | — |
| EXC-1375 | mission | Timeline | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1375.json | — |
| EXC-1376 | mission | Release | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1376.json | — |
| EXC-1377 | mission | Applications | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1377.json | — |
| EXC-1378 | mission | Queue Snapshot | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1378.json | — |
| EXC-1379 | mission | Operations Event Log | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1379.json | — |
| EXC-1380 | mission | Intent Analytics | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1380.json | — |
| EXC-1381 | mission | Refresh | TAB:Routing | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1382 | mission | Open Job Center | TAB:Routing | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1383 | mission | Open Notifications (Activity Center inbox) | TAB:Routing | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1384 | mission | Open Chat | TAB:Routing | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1385 | mission | Open System audit | TAB:Routing | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1386 | mission | Open Home | TAB:Routing | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1387 | mission | Overview | TAB:Routing | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1388 | mission | Routing | TAB:Routing | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1389 | mission | Performance | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1389.json | — |
| EXC-1390 | mission | Recovery | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1390.json | — |
| EXC-1391 | mission | Connection | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1391.json | — |
| EXC-1392 | mission | Advanced ▾ | TAB:Routing | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1392.json | — |
| EXC-1393 | mission | Hardware | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1393.json | — |
| EXC-1394 | mission | Inference | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1394.json | — |
| EXC-1395 | mission | Memory | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1395.json | — |
| EXC-1396 | mission | Knowledge | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1396.json | — |
| EXC-1397 | mission | Databases | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1397.json | — |
| EXC-1398 | mission | Settings | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1398.json | — |
| EXC-1399 | mission | Timeline | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1399.json | — |
| EXC-1400 | mission | Release | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1400.json | — |
| EXC-1401 | mission | Applications | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1401.json | — |
| EXC-1402 | mission | Queue Snapshot | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1402.json | — |
| EXC-1403 | mission | Operations Event Log | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1403.json | — |
| EXC-1404 | mission | Intent Analytics | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1404.json | — |
| EXC-1405 | mission | Refresh | TAB:Settings | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1406 | mission | Open Job Center | TAB:Settings | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1407 | mission | Open Notifications (Activity Center inbox) | TAB:Settings | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1408 | mission | Open Chat | TAB:Settings | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1409 | mission | Open System audit | TAB:Settings | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1410 | mission | Open Home | TAB:Settings | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1411 | mission | Overview | TAB:Settings | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1412 | mission | Routing | TAB:Settings | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1413 | mission | Performance | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1413.json | — |
| EXC-1414 | mission | Recovery | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1414.json | — |
| EXC-1415 | mission | Connection | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1415.json | — |
| EXC-1416 | mission | Advanced ▾ | TAB:Settings | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1416.json | — |
| EXC-1417 | mission | Hardware | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1417.json | — |
| EXC-1418 | mission | Inference | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1418.json | — |
| EXC-1419 | mission | Memory | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1419.json | — |
| EXC-1420 | mission | Knowledge | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1420.json | — |
| EXC-1421 | mission | Databases | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1421.json | — |
| EXC-1422 | mission | Settings | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1422.json | — |
| EXC-1423 | mission | Timeline | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1423.json | — |
| EXC-1424 | mission | Release | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1424.json | — |
| EXC-1425 | mission | Applications | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1425.json | — |
| EXC-1426 | mission | Queue Snapshot | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1426.json | — |
| EXC-1427 | mission | Operations Event Log | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1427.json | — |
| EXC-1428 | mission | Intent Analytics | TAB:Settings | tabStates | yes | PASS | — | by_id/EXC-1428.json | — |
| EXC-1429 | mission | Refresh | TAB:Timeline | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1430 | mission | Open Job Center | TAB:Timeline | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1431 | mission | Open Notifications (Activity Center inbox) | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1432 | mission | Open Chat | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1433 | mission | Open System audit | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1434 | mission | Open Home | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1435 | mission | Overview | TAB:Timeline | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1436 | mission | Routing | TAB:Timeline | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1437 | mission | Performance | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1437.json | — |
| EXC-1438 | mission | Recovery | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1438.json | — |
| EXC-1439 | mission | Connection | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1439.json | — |
| EXC-1440 | mission | Advanced ▾ | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1440.json | — |
| EXC-1441 | mission | Hardware | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1441.json | — |
| EXC-1442 | mission | Inference | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1442.json | — |
| EXC-1443 | mission | Memory | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1443.json | — |
| EXC-1444 | mission | Knowledge | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1444.json | — |
| EXC-1445 | mission | Databases | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1445.json | — |
| EXC-1446 | mission | Settings | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1446.json | — |
| EXC-1447 | mission | Timeline | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1447.json | — |
| EXC-1448 | mission | Release | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1448.json | — |
| EXC-1449 | mission | Applications | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1449.json | — |
| EXC-1450 | mission | Queue Snapshot | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1450.json | — |
| EXC-1451 | mission | Operations Event Log | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1451.json | — |
| EXC-1452 | mission | Intent Analytics | TAB:Timeline | tabStates | yes | PASS | — | by_id/EXC-1452.json | — |
| EXC-1453 | mission | JSON | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1453.json | — |
| EXC-1454 | mission | CSV | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1454.json | — |
| EXC-1455 | mission | Markdown | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1455.json | — |
| EXC-1456 | mission | HTML | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1456.json | — |
| EXC-1457 | mission | Search timeline… | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1457.json | — |
| EXC-1458 | mission | All severities Info Warning Error | TAB:Timeline | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1458.json | — |
| EXC-1459 | mission | Refresh | AFTER:Advanced ▾ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1460 | mission | Open Job Center | AFTER:Advanced ▾ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1461 | mission | Open Notifications (Activity Center inbox) | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1462 | mission | Open Chat | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1463 | mission | Open System audit | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1464 | mission | Open Home | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1465 | mission | Overview | AFTER:Advanced ▾ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1466 | mission | Routing | AFTER:Advanced ▾ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1467 | mission | Performance | AFTER:Advanced ▾ | conditional | yes | PASS | — | by_id/EXC-1467.json | — |
| EXC-1468 | mission | Recovery | AFTER:Advanced ▾ | conditional | yes | PASS | — | by_id/EXC-1468.json | — |
| EXC-1469 | mission | Connection | AFTER:Advanced ▾ | conditional | yes | PASS | — | by_id/EXC-1469.json | — |
| EXC-1470 | mission | Advanced ▸ | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-413.json | — |
| EXC-1471 | mission | JSON | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | by_id/EXC-1471.json | — |
| EXC-1472 | mission | CSV | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | by_id/EXC-1472.json | — |
| EXC-1473 | mission | Markdown | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | by_id/EXC-1473.json | — |
| EXC-1474 | mission | HTML | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | by_id/EXC-1474.json | — |
| EXC-1475 | mission | Search timeline… | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | by_id/EXC-1475.json | — |
| EXC-1476 | mission | All severities Info Warning Error | AFTER:Advanced ▾ | conditional | yes | FAIL | BUG-024 | by_id/EXC-1476.json | — |
| EXC-1477 | mission | Refresh | AFTER:Settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-288.json | — |
| EXC-1478 | mission | Open Job Center | AFTER:Settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-289.json | — |
| EXC-1479 | mission | Open Notifications (Activity Center inbox) | AFTER:Settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-290.json | — |
| EXC-1480 | mission | Open Chat | AFTER:Settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-291.json | — |
| EXC-1481 | mission | Open System audit | AFTER:Settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-292.json | — |
| EXC-1482 | mission | Open Home | AFTER:Settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-293.json | — |
| EXC-1483 | mission | Overview | AFTER:Settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-294.json | — |
| EXC-1484 | mission | Routing | AFTER:Settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-295.json | — |
| EXC-1485 | mission | Performance | AFTER:Settings | conditional | yes | PASS | — | by_id/EXC-1485.json | — |
| EXC-1486 | mission | Recovery | AFTER:Settings | conditional | yes | PASS | — | by_id/EXC-1486.json | — |
| EXC-1487 | mission | Connection | AFTER:Settings | conditional | yes | PASS | — | by_id/EXC-1487.json | — |
| EXC-1488 | mission | Advanced ▸ | AFTER:Settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-413.json | — |
| EXC-1489 | mission | JSON | AFTER:Settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1489.json | — |
| EXC-1490 | mission | CSV | AFTER:Settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1490.json | — |
| EXC-1491 | mission | Markdown | AFTER:Settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1491.json | — |
| EXC-1492 | mission | HTML | AFTER:Settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1492.json | — |
| EXC-1493 | mission | Search timeline… | AFTER:Settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1493.json | — |
| EXC-1494 | mission | All severities Info Warning Error | AFTER:Settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1494.json | — |
| EXC-1495 | planner | Notes, reflections, logs | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-296.json | — |
| EXC-1496 | planner | Scheduled commitments | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-297.json | — |
| EXC-1497 | planner | Documents | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1498 | planner | Add | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1499 | planner | Ask Aria to promote a Journal item | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1499.json | — |
| EXC-1500 | planner | Add task | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-300.json | — |
| EXC-1501 | planner | Ask Chat | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-301.json | — |
| EXC-1502 | planner | Open Journal | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-302.json | — |
| EXC-1503 | planner | Start | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-303.json | — |
| EXC-1504 | planner | 25 min focus timer (with optional HA Focus scene) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1504.json | — |
| EXC-1505 | planner | Start Focus 25m | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1505.json | — |
| EXC-1506 | planner | Set | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1506.json | — |
| EXC-1507 | planner | Add alarm | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1507.json | — |
| EXC-1508 | planner | Add | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1509 | planner | Add event | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1509.json | — |
| EXC-1510 | planner | Open Calendar | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1510.json | — |
| EXC-1511 | planner | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1511.json | — |
| EXC-1512 | planner | New planner task | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1512.json | — |
| EXC-1513 | planner | Timer duration | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1513.json | — |
| EXC-1514 | planner | Alarm time | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1514.json | — |
| EXC-1515 | planner | Event title | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1515.json | — |
| EXC-1516 | planner | Event time | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1516.json | — |
| EXC-1517 | planner | Tasks ▾ | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1517.json | — |
| EXC-1518 | planner | Timers ▾ | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1518.json | — |
| EXC-1519 | planner | Alarms ▾ | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1519.json | — |
| EXC-1520 | planner | Today ▾ | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1520.json | — |
| EXC-1521 | planner | Notes, reflections, logs | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-296.json | — |
| EXC-1522 | planner | Scheduled commitments | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-297.json | — |
| EXC-1523 | planner | Documents | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1524 | planner | Plan My Day | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1524.json | — |
| EXC-1525 | planner | Start Focus Session | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1525.json | — |
| EXC-1526 | planner | Review Morning Plan | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1526.json | — |
| EXC-1527 | planner | Reprioritize | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1527.json | — |
| EXC-1528 | planner | Ask Aria | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1528.json | — |
| EXC-1529 | planner | Calendar | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-416.json | — |
| EXC-1530 | planner | Journal | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-415.json | — |
| EXC-1531 | planner | Documents | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1532 | planner | Vision capture | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1532.json | — |
| EXC-1533 | planner | Suggest schedule | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1533.json | — |
| EXC-1534 | planner | Undo last Planner delete | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1534.json | — |
| EXC-1535 | planner | Add | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1536 | planner | Ask Aria to promote a Journal item | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1536.json | — |
| EXC-1537 | planner | Add task | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-300.json | — |
| EXC-1538 | planner | Ask Chat | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-301.json | — |
| EXC-1539 | planner | Open Journal | AFTER:Add | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-302.json | — |
| EXC-1540 | planner | Start | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-303.json | — |
| EXC-1541 | planner | 25 min focus timer (with optional HA Focus scene) | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1541.json | — |
| EXC-1542 | planner | Start Focus 25m | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1542.json | — |
| EXC-1543 | planner | Set | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1543.json | — |
| EXC-1544 | planner | Add alarm | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1544.json | — |
| EXC-1545 | planner | Add | AFTER:Add | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1546 | planner | Add event | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1546.json | — |
| EXC-1547 | planner | Open Calendar | AFTER:Add | conditional | yes | FAIL | BUG-024 | by_id/EXC-1547.json | — |
| EXC-1548 | planner | on | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1548.json | — |
| EXC-1549 | planner | New planner task | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1549.json | — |
| EXC-1550 | planner | Timer duration | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1550.json | — |
| EXC-1551 | planner | Alarm time | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1551.json | — |
| EXC-1552 | planner | Event title | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1552.json | — |
| EXC-1553 | planner | Event time | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1553.json | — |
| EXC-1554 | planner | Tasks ▾ | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1554.json | — |
| EXC-1555 | planner | Timers ▾ | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1555.json | — |
| EXC-1556 | planner | Alarms ▾ | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1556.json | — |
| EXC-1557 | planner | Today ▾ | AFTER:Add | conditional | yes | PASS | — | by_id/EXC-1557.json | — |
| EXC-1558 | planner | Notes, reflections, logs | AFTER:Add task | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-296.json | — |
| EXC-1559 | planner | Scheduled commitments | AFTER:Add task | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-297.json | — |
| EXC-1560 | planner | Documents | AFTER:Add task | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1561 | planner | Plan My Day | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1561.json | — |
| EXC-1562 | planner | Start Focus Session | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1562.json | — |
| EXC-1563 | planner | Review Morning Plan | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1563.json | — |
| EXC-1564 | planner | Reprioritize | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1564.json | — |
| EXC-1565 | planner | Ask Aria | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1565.json | — |
| EXC-1566 | planner | Calendar | AFTER:Add task | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-416.json | — |
| EXC-1567 | planner | Journal | AFTER:Add task | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-415.json | — |
| EXC-1568 | planner | Documents | AFTER:Add task | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1569 | planner | Vision capture | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1569.json | — |
| EXC-1570 | planner | Suggest schedule | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1570.json | — |
| EXC-1571 | planner | Undo last Planner delete | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1571.json | — |
| EXC-1572 | planner | Add | AFTER:Add task | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1573 | planner | Ask Aria to promote a Journal item | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1573.json | — |
| EXC-1574 | planner | Add task | AFTER:Add task | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-300.json | — |
| EXC-1575 | planner | Ask Chat | AFTER:Add task | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-301.json | — |
| EXC-1576 | planner | Open Journal | AFTER:Add task | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-302.json | — |
| EXC-1577 | planner | Start | AFTER:Add task | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-303.json | — |
| EXC-1578 | planner | 25 min focus timer (with optional HA Focus scene) | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1578.json | — |
| EXC-1579 | planner | Start Focus 25m | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1579.json | — |
| EXC-1580 | planner | Set | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1580.json | — |
| EXC-1581 | planner | Add alarm | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1581.json | — |
| EXC-1582 | planner | Add | AFTER:Add task | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1583 | planner | Add event | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1583.json | — |
| EXC-1584 | planner | Open Calendar | AFTER:Add task | conditional | yes | FAIL | BUG-024 | by_id/EXC-1584.json | — |
| EXC-1585 | planner | on | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1585.json | — |
| EXC-1586 | planner | New planner task | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1586.json | — |
| EXC-1587 | planner | Timer duration | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1587.json | — |
| EXC-1588 | planner | Alarm time | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1588.json | — |
| EXC-1589 | planner | Event title | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1589.json | — |
| EXC-1590 | planner | Event time | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1590.json | — |
| EXC-1591 | planner | Tasks ▾ | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1591.json | — |
| EXC-1592 | planner | Timers ▾ | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1592.json | — |
| EXC-1593 | planner | Alarms ▾ | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1593.json | — |
| EXC-1594 | planner | Today ▾ | AFTER:Add task | conditional | yes | PASS | — | by_id/EXC-1594.json | — |
| EXC-1595 | planner | Notes, reflections, logs | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-296.json | — |
| EXC-1596 | planner | Scheduled commitments | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-297.json | — |
| EXC-1597 | planner | Documents | AFTER:Add alarm | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1598 | planner | Plan My Day | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1598.json | — |
| EXC-1599 | planner | Start Focus Session | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1599.json | — |
| EXC-1600 | planner | Review Morning Plan | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1600.json | — |
| EXC-1601 | planner | Reprioritize | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1601.json | — |
| EXC-1602 | planner | Ask Aria | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1602.json | — |
| EXC-1603 | planner | Calendar | AFTER:Add alarm | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-416.json | — |
| EXC-1604 | planner | Journal | AFTER:Add alarm | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-415.json | — |
| EXC-1605 | planner | Documents | AFTER:Add alarm | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1606 | planner | Vision capture | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1606.json | — |
| EXC-1607 | planner | Suggest schedule | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1607.json | — |
| EXC-1608 | planner | Undo last Planner delete | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1608.json | — |
| EXC-1609 | planner | Add | AFTER:Add alarm | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1610 | planner | Ask Aria to promote a Journal item | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1610.json | — |
| EXC-1611 | planner | Add task | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-300.json | — |
| EXC-1612 | planner | Ask Chat | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-301.json | — |
| EXC-1613 | planner | Open Journal | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-302.json | — |
| EXC-1614 | planner | Start | AFTER:Add alarm | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-303.json | — |
| EXC-1615 | planner | 25 min focus timer (with optional HA Focus scene) | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1615.json | — |
| EXC-1616 | planner | Start Focus 25m | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1616.json | — |
| EXC-1617 | planner | Set | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1617.json | — |
| EXC-1618 | planner | Add alarm | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1618.json | — |
| EXC-1619 | planner | Add | AFTER:Add alarm | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1620 | planner | Add event | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1620.json | — |
| EXC-1621 | planner | Open Calendar | AFTER:Add alarm | conditional | yes | FAIL | BUG-024 | by_id/EXC-1621.json | — |
| EXC-1622 | planner | on | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1622.json | — |
| EXC-1623 | planner | New planner task | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1623.json | — |
| EXC-1624 | planner | Timer duration | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1624.json | — |
| EXC-1625 | planner | Alarm time | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1625.json | — |
| EXC-1626 | planner | Event title | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1626.json | — |
| EXC-1627 | planner | Event time | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1627.json | — |
| EXC-1628 | planner | Tasks ▾ | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1628.json | — |
| EXC-1629 | planner | Timers ▾ | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1629.json | — |
| EXC-1630 | planner | Alarms ▾ | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1630.json | — |
| EXC-1631 | planner | Today ▾ | AFTER:Add alarm | conditional | yes | PASS | — | by_id/EXC-1631.json | — |
| EXC-1632 | planner | Notes, reflections, logs | AFTER:Add event | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-296.json | — |
| EXC-1633 | planner | Scheduled commitments | AFTER:Add event | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-297.json | — |
| EXC-1634 | planner | Documents | AFTER:Add event | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1635 | planner | Plan My Day | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1635.json | — |
| EXC-1636 | planner | Start Focus Session | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1636.json | — |
| EXC-1637 | planner | Review Morning Plan | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1637.json | — |
| EXC-1638 | planner | Reprioritize | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1638.json | — |
| EXC-1639 | planner | Ask Aria | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1639.json | — |
| EXC-1640 | planner | Calendar | AFTER:Add event | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-416.json | — |
| EXC-1641 | planner | Journal | AFTER:Add event | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-415.json | — |
| EXC-1642 | planner | Documents | AFTER:Add event | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-298.json | — |
| EXC-1643 | planner | Vision capture | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1643.json | — |
| EXC-1644 | planner | Suggest schedule | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1644.json | — |
| EXC-1645 | planner | Undo last Planner delete | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1645.json | — |
| EXC-1646 | planner | Add | AFTER:Add event | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1647 | planner | Ask Aria to promote a Journal item | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1647.json | — |
| EXC-1648 | planner | Add task | AFTER:Add event | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-300.json | — |
| EXC-1649 | planner | Ask Chat | AFTER:Add event | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-301.json | — |
| EXC-1650 | planner | Open Journal | AFTER:Add event | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-302.json | — |
| EXC-1651 | planner | Start | AFTER:Add event | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-303.json | — |
| EXC-1652 | planner | 25 min focus timer (with optional HA Focus scene) | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1652.json | — |
| EXC-1653 | planner | Start Focus 25m | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1653.json | — |
| EXC-1654 | planner | Set | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1654.json | — |
| EXC-1655 | planner | Add alarm | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1655.json | — |
| EXC-1656 | planner | Add | AFTER:Add event | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-299.json | — |
| EXC-1657 | planner | Add event | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1657.json | — |
| EXC-1658 | planner | Open Calendar | AFTER:Add event | conditional | yes | FAIL | BUG-024 | by_id/EXC-1658.json | — |
| EXC-1659 | planner | on | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1659.json | — |
| EXC-1660 | planner | New planner task | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1660.json | — |
| EXC-1661 | planner | Timer duration | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1661.json | — |
| EXC-1662 | planner | Alarm time | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1662.json | — |
| EXC-1663 | planner | Event title | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1663.json | — |
| EXC-1664 | planner | Event time | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1664.json | — |
| EXC-1665 | planner | Tasks ▾ | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1665.json | — |
| EXC-1666 | planner | Timers ▾ | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1666.json | — |
| EXC-1667 | planner | Alarms ▾ | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1667.json | — |
| EXC-1668 | planner | Today ▾ | AFTER:Add event | conditional | yes | PASS | — | by_id/EXC-1668.json | — |
| EXC-1669 | presence | Open Security | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-304.json | — |
| EXC-1670 | presence | Open Voice | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-305.json | — |
| EXC-1671 | presence | Start camera | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-306.json | — |
| EXC-1672 | presence | Stop | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-307.json | — |
| EXC-1673 | presence | Enroll face | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-308.json | — |
| EXC-1674 | presence | Calibrate gestures | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-309.json | — |
| EXC-1675 | presence | Off Preview only Control — pinch click, fist drag panels CPU-only (low FPS) | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-310.json | — |
| EXC-1676 | projects | Shortcuts | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-311.json | — |
| EXC-1677 | projects | Create | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-312.json | — |
| EXC-1678 | projects | Import | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-313.json | — |
| EXC-1679 | projects | Search projects | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-314.json | — |
| EXC-1680 | projects | New project name | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-315.json | — |
| EXC-1681 | projects | Description | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-316.json | — |
| EXC-1682 | projects | Git path | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-317.json | — |
| EXC-1683 | providers | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-318.json | — |
| EXC-1684 | providers | Provider / VRAM health | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-319.json | — |
| EXC-1685 | repair | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-320.json | — |
| EXC-1686 | repair | Open Job Center | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-321.json | — |
| EXC-1687 | repair | Open Notifications (Activity Center inbox) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-322.json | — |
| EXC-1688 | repair | Open Chat | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-323.json | — |
| EXC-1689 | repair | Open System audit | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-324.json | — |
| EXC-1690 | repair | Open Home | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-325.json | — |
| EXC-1691 | repair | Overview | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-326.json | — |
| EXC-1692 | repair | Routing | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-327.json | — |
| EXC-1693 | repair | Performance | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1693.json | — |
| EXC-1694 | repair | Recovery | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1694.json | — |
| EXC-1695 | repair | Connection | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1695.json | — |
| EXC-1696 | repair | Advanced ▸ | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1696.json | — |
| EXC-1697 | repair | JSON | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1697.json | — |
| EXC-1698 | repair | CSV | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1698.json | — |
| EXC-1699 | repair | Markdown | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1699.json | — |
| EXC-1700 | repair | HTML | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1700.json | — |
| EXC-1701 | repair | Search timeline… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1701.json | — |
| EXC-1702 | repair | All severities Info Warning Error | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1702.json | — |
| EXC-1703 | repair | Refresh | TAB:Connection | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-320.json | — |
| EXC-1704 | repair | Open Job Center | TAB:Connection | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-321.json | — |
| EXC-1705 | repair | Open Notifications (Activity Center inbox) | TAB:Connection | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-322.json | — |
| EXC-1706 | repair | Open Chat | TAB:Connection | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-323.json | — |
| EXC-1707 | repair | Open System audit | TAB:Connection | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-324.json | — |
| EXC-1708 | repair | Open Home | TAB:Connection | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-325.json | — |
| EXC-1709 | repair | Overview | TAB:Connection | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-326.json | — |
| EXC-1710 | repair | Routing | TAB:Connection | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-327.json | — |
| EXC-1711 | repair | Performance | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1711.json | — |
| EXC-1712 | repair | Recovery | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1712.json | — |
| EXC-1713 | repair | Connection | TAB:Connection | tabStates | yes | PASS | — | by_id/EXC-1713.json | — |
| EXC-1714 | repair | Advanced ▸ | TAB:Connection | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1714.json | — |
| EXC-1715 | repair | Refresh | TAB:Overview | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-320.json | — |
| EXC-1716 | repair | Open Job Center | TAB:Overview | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-321.json | — |
| EXC-1717 | repair | Open Notifications (Activity Center inbox) | TAB:Overview | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-322.json | — |
| EXC-1718 | repair | Open Chat | TAB:Overview | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-323.json | — |
| EXC-1719 | repair | Open System audit | TAB:Overview | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-324.json | — |
| EXC-1720 | repair | Open Home | TAB:Overview | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-325.json | — |
| EXC-1721 | repair | Overview | TAB:Overview | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-326.json | — |
| EXC-1722 | repair | Routing | TAB:Overview | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-327.json | — |
| EXC-1723 | repair | Performance | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1723.json | — |
| EXC-1724 | repair | Recovery | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1724.json | — |
| EXC-1725 | repair | Connection | TAB:Overview | tabStates | yes | PASS | — | by_id/EXC-1725.json | — |
| EXC-1726 | repair | Advanced ▸ | TAB:Overview | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1726.json | — |
| EXC-1727 | repair | JSON | TAB:Overview | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1727.json | — |
| EXC-1728 | repair | CSV | TAB:Overview | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1728.json | — |
| EXC-1729 | repair | Markdown | TAB:Overview | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1729.json | — |
| EXC-1730 | repair | HTML | TAB:Overview | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1730.json | — |
| EXC-1731 | repair | Search timeline… | TAB:Overview | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1731.json | — |
| EXC-1732 | repair | All severities Info Warning Error | TAB:Overview | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1732.json | — |
| EXC-1733 | repair | Refresh | TAB:Performance | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-320.json | — |
| EXC-1734 | repair | Open Job Center | TAB:Performance | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-321.json | — |
| EXC-1735 | repair | Open Notifications (Activity Center inbox) | TAB:Performance | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-322.json | — |
| EXC-1736 | repair | Open Chat | TAB:Performance | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-323.json | — |
| EXC-1737 | repair | Open System audit | TAB:Performance | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-324.json | — |
| EXC-1738 | repair | Open Home | TAB:Performance | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-325.json | — |
| EXC-1739 | repair | Overview | TAB:Performance | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-326.json | — |
| EXC-1740 | repair | Routing | TAB:Performance | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-327.json | — |
| EXC-1741 | repair | Performance | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1741.json | — |
| EXC-1742 | repair | Recovery | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1742.json | — |
| EXC-1743 | repair | Connection | TAB:Performance | tabStates | yes | PASS | — | by_id/EXC-1743.json | — |
| EXC-1744 | repair | Advanced ▸ | TAB:Performance | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1744.json | — |
| EXC-1745 | repair | Refresh | TAB:Recovery | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-320.json | — |
| EXC-1746 | repair | Open Job Center | TAB:Recovery | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-321.json | — |
| EXC-1747 | repair | Open Notifications (Activity Center inbox) | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-322.json | — |
| EXC-1748 | repair | Open Chat | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-323.json | — |
| EXC-1749 | repair | Open System audit | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-324.json | — |
| EXC-1750 | repair | Open Home | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-325.json | — |
| EXC-1751 | repair | Overview | TAB:Recovery | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-326.json | — |
| EXC-1752 | repair | Routing | TAB:Recovery | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-327.json | — |
| EXC-1753 | repair | Performance | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1753.json | — |
| EXC-1754 | repair | Recovery | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1754.json | — |
| EXC-1755 | repair | Connection | TAB:Recovery | tabStates | yes | PASS | — | by_id/EXC-1755.json | — |
| EXC-1756 | repair | Advanced ▸ | TAB:Recovery | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1756.json | — |
| EXC-1757 | repair | Refresh | TAB:Routing | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-320.json | — |
| EXC-1758 | repair | Open Job Center | TAB:Routing | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-321.json | — |
| EXC-1759 | repair | Open Notifications (Activity Center inbox) | TAB:Routing | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-322.json | — |
| EXC-1760 | repair | Open Chat | TAB:Routing | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-323.json | — |
| EXC-1761 | repair | Open System audit | TAB:Routing | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-324.json | — |
| EXC-1762 | repair | Open Home | TAB:Routing | tabStates | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-325.json | — |
| EXC-1763 | repair | Overview | TAB:Routing | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-326.json | — |
| EXC-1764 | repair | Routing | TAB:Routing | tabStates | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-327.json | — |
| EXC-1765 | repair | Performance | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1765.json | — |
| EXC-1766 | repair | Recovery | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1766.json | — |
| EXC-1767 | repair | Connection | TAB:Routing | tabStates | yes | PASS | — | by_id/EXC-1767.json | — |
| EXC-1768 | repair | Advanced ▸ | TAB:Routing | tabStates | yes | FAIL | BUG-024 | by_id/EXC-1768.json | — |
| EXC-1769 | repair | Refresh | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-320.json | — |
| EXC-1770 | repair | Open Job Center | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-321.json | — |
| EXC-1771 | repair | Open Notifications (Activity Center inbox) | AFTER:Advanced ▸ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-322.json | — |
| EXC-1772 | repair | Open Chat | AFTER:Advanced ▸ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-323.json | — |
| EXC-1773 | repair | Open System audit | AFTER:Advanced ▸ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-324.json | — |
| EXC-1774 | repair | Open Home | AFTER:Advanced ▸ | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-325.json | — |
| EXC-1775 | repair | Overview | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-326.json | — |
| EXC-1776 | repair | Routing | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-327.json | — |
| EXC-1777 | repair | Performance | AFTER:Advanced ▸ | conditional | yes | PASS | — | by_id/EXC-1777.json | — |
| EXC-1778 | repair | Recovery | AFTER:Advanced ▸ | conditional | yes | PASS | — | by_id/EXC-1778.json | — |
| EXC-1779 | repair | Connection | AFTER:Advanced ▸ | conditional | yes | PASS | — | by_id/EXC-1779.json | — |
| EXC-1780 | repair | Advanced ▾ | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-452.json | — |
| EXC-1781 | repair | Hardware | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-453.json | — |
| EXC-1782 | repair | Inference | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-515.json | — |
| EXC-1783 | repair | Memory | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-516.json | — |
| EXC-1784 | repair | Knowledge | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-517.json | — |
| EXC-1785 | repair | Databases | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-518.json | — |
| EXC-1786 | repair | Settings | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-519.json | — |
| EXC-1787 | repair | Timeline | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-520.json | — |
| EXC-1788 | repair | Release | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-521.json | — |
| EXC-1789 | repair | Applications | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-522.json | — |
| EXC-1790 | repair | Queue Snapshot | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-523.json | — |
| EXC-1791 | repair | Operations Event Log | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-524.json | — |
| EXC-1792 | repair | Intent Analytics | AFTER:Advanced ▸ | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-525.json | — |
| EXC-1793 | search | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-328.json | — |
| EXC-1794 | search | Save search | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-329.json | — |
| EXC-1795 | search | Diagnostics | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-330.json | — |
| EXC-1796 | search | Search | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-331.json | — |
| EXC-1797 | search | Clear history | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-332.json | — |
| EXC-1798 | search | Search documents, memory, code, graph, planner… | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-333.json | — |
| EXC-1799 | search | Browse or answer mode | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-334.json | — |
| EXC-1800 | search | Code search mode | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-335.json | — |
| EXC-1801 | security | Open Presence | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-336.json | — |
| EXC-1802 | security | Open Voice | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-337.json | — |
| EXC-1803 | security | Set PIN | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-338.json | — |
| EXC-1804 | security | Lock now | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-339.json | — |
| EXC-1805 | security | Presence | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-340.json | — |
| EXC-1806 | security | 4–6 digit PIN | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-341.json | — |
| EXC-1807 | settings | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-342.json | — |
| EXC-1808 | settings | Voice & Chat | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-343.json | — |
| EXC-1809 | settings | Diagnostics | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-344.json | — |
| EXC-1810 | settings | Export | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-345.json | — |
| EXC-1811 | settings | Search | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-346.json | — |
| EXC-1812 | settings | Reset appearance | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-347.json | — |
| EXC-1813 | settings | Activate | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-348.json | — |
| EXC-1814 | settings | Save profile | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-349.json | — |
| EXC-1815 | settings | Search preferences (PIN, theme, whisper, models…) | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1815.json | — |
| EXC-1816 | settings | Filter by category | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1816.json | — |
| EXC-1817 | settings | Theme | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1817.json | — |
| EXC-1818 | settings | Accent | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1818.json | — |
| EXC-1819 | settings | UI density | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1819.json | — |
| EXC-1820 | settings | Preference profile | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1820.json | — |
| EXC-1821 | video | Open Gallery | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-350.json | — |
| EXC-1822 | video | Open Meme Studio | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-351.json | — |
| EXC-1823 | video | Mission Control | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-352.json | — |
| EXC-1824 | video | Generate | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-353.json | — |
| EXC-1825 | video | Preview enhance | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-354.json | — |
| EXC-1826 | video | Advanced | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-355.json | — |
| EXC-1827 | video | Generate another | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-356.json | — |
| EXC-1828 | video | Simple | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-357.json | — |
| EXC-1829 | video | Expert | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1829.json | — |
| EXC-1830 | video | Unload Ollama from GPU before AnimateDiff | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1830.json | — |
| EXC-1831 | video | Save clip settings | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1831.json | — |
| EXC-1832 | video | Build storyboard | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1832.json | — |
| EXC-1833 | video | Video generation prompt | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1833.json | — |
| EXC-1834 | video | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1834.json | — |
| EXC-1835 | video | Clip duration seconds | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1835.json | — |
| EXC-1836 | video | Storyboard image paths | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1836.json | — |
| EXC-1837 | video | Seconds per slide | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1837.json | — |
| EXC-1838 | video | videoUploadInput | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1838.json | — |
| EXC-1839 | video | Video generation preset | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1839.json | — |
| EXC-1840 | video | Open Gallery | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-350.json | — |
| EXC-1841 | video | Open Meme Studio | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-351.json | — |
| EXC-1842 | video | Mission Control | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-352.json | — |
| EXC-1843 | video | Generate | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-353.json | — |
| EXC-1844 | video | Preview enhance | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-354.json | — |
| EXC-1845 | video | Advanced | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-355.json | — |
| EXC-1846 | video | Generate another | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-356.json | — |
| EXC-1847 | video | Simple | AFTER:Advanced | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-357.json | — |
| EXC-1848 | video | Expert | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1848.json | — |
| EXC-1849 | video | Unload Ollama from GPU before AnimateDiff | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | by_id/EXC-1849.json | — |
| EXC-1850 | video | Save clip settings | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1850.json | — |
| EXC-1851 | video | Build storyboard | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1851.json | — |
| EXC-1852 | video | Video generation prompt | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1852.json | — |
| EXC-1853 | video | on | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1853.json | — |
| EXC-1854 | video | Clip duration seconds | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1854.json | — |
| EXC-1855 | video | 8 | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1855.json | — |
| EXC-1856 | video | Width | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1856.json | — |
| EXC-1857 | video | Height | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1857.json | — |
| EXC-1858 | video | Negative prompt | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1858.json | — |
| EXC-1859 | video | Storyboard image paths | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1859.json | — |
| EXC-1860 | video | Seconds per slide | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1860.json | — |
| EXC-1861 | video | videoUploadInput | AFTER:Advanced | conditional | yes | FAIL | BUG-024 | by_id/EXC-1861.json | — |
| EXC-1862 | video | Enhanced prompt | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1862.json | — |
| EXC-1863 | video | Video generation preset | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1863.json | — |
| EXC-1864 | video | Auto (AnimateDiff → Ken Burns) AnimateDiff only Ken Burns only | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1864.json | — |
| EXC-1865 | video | Flux Schnell SDXL 1.0 SDXL Turbo | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1865.json | — |
| EXC-1866 | video | Use preset above | AFTER:Advanced | conditional | yes | PASS | — | by_id/EXC-1866.json | — |
| EXC-1867 | video | Open Gallery | AFTER:Save clip settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-350.json | — |
| EXC-1868 | video | Open Meme Studio | AFTER:Save clip settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-351.json | — |
| EXC-1869 | video | Mission Control | AFTER:Save clip settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-352.json | — |
| EXC-1870 | video | Generate | AFTER:Save clip settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-353.json | — |
| EXC-1871 | video | Preview enhance | AFTER:Save clip settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-354.json | — |
| EXC-1872 | video | Advanced | AFTER:Save clip settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-355.json | — |
| EXC-1873 | video | Generate another | AFTER:Save clip settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-356.json | — |
| EXC-1874 | video | Simple | AFTER:Save clip settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-357.json | — |
| EXC-1875 | video | Expert | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1875.json | — |
| EXC-1876 | video | Unload Ollama from GPU before AnimateDiff | AFTER:Save clip settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1876.json | — |
| EXC-1877 | video | Save clip settings | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1877.json | — |
| EXC-1878 | video | Build storyboard | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1878.json | — |
| EXC-1879 | video | Video generation prompt | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1879.json | — |
| EXC-1880 | video | on | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1880.json | — |
| EXC-1881 | video | Clip duration seconds | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1881.json | — |
| EXC-1882 | video | 8 | AFTER:Save clip settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1882.json | — |
| EXC-1883 | video | Width | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1883.json | — |
| EXC-1884 | video | Height | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1884.json | — |
| EXC-1885 | video | Negative prompt | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1885.json | — |
| EXC-1886 | video | Storyboard image paths | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1886.json | — |
| EXC-1887 | video | Seconds per slide | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1887.json | — |
| EXC-1888 | video | videoUploadInput | AFTER:Save clip settings | conditional | yes | FAIL | BUG-024 | by_id/EXC-1888.json | — |
| EXC-1889 | video | Enhanced prompt | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1889.json | — |
| EXC-1890 | video | Video generation preset | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1890.json | — |
| EXC-1891 | video | Auto (AnimateDiff → Ken Burns) AnimateDiff only Ken Burns only | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1891.json | — |
| EXC-1892 | video | Flux Schnell SDXL 1.0 SDXL Turbo | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1892.json | — |
| EXC-1893 | video | Use preset above | AFTER:Save clip settings | conditional | yes | PASS | — | by_id/EXC-1893.json | — |
| EXC-1894 | vision | Chat attach | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-358.json | — |
| EXC-1895 | vision | Gallery | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-359.json | — |
| EXC-1896 | vision | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-360.json | — |
| EXC-1897 | vision | Apply profile | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-361.json | — |
| EXC-1898 | vision | Speak OCR (Voice) | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-362.json | — |
| EXC-1899 | vision | Refresh batch | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-363.json | — |
| EXC-1900 | vision | Vision image or PDF page path for OCR | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-364.json | — |
| EXC-1901 | vision | Compare image path B | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-365.json | — |
| EXC-1902 | vision | optional question | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | by_id/EXC-1902.json | — |
| EXC-1903 | vision | Vision profile | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1903.json | — |
| EXC-1904 | vision | OCR mode | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1904.json | — |
| EXC-1905 | vision | Preview Journal Planner Calendar Memory Documents Gallery | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1905.json | — |
| EXC-1906 | voice | Open Audio studio | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-366.json | — |
| EXC-1907 | voice | Open Presence | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-367.json | — |
| EXC-1908 | voice | Apply profile | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-368.json | — |
| EXC-1909 | voice | Save settings | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-369.json | — |
| EXC-1910 | voice | Refresh | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-370.json | — |
| EXC-1911 | voice | Run recovery advisor | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-371.json | — |
| EXC-1912 | voice | Toggle cloud live | DEFAULT | controlsDefault | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-372.json | — |
| EXC-1913 | voice | 220 | DEFAULT | controlsDefault | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-373.json | — |
| EXC-1914 | voice | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1914.json | — |
| EXC-1915 | voice | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1915.json | — |
| EXC-1916 | voice | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1916.json | — |
| EXC-1917 | voice | on | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1917.json | — |
| EXC-1918 | voice | Off Half Full | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1918.json | — |
| EXC-1919 | voice | Whisper RealtimeSTT | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1919.json | — |
| EXC-1920 | voice | Voice profile | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1920.json | — |
| EXC-1921 | voice | Voice cheatsheet | DEFAULT | controlsDefault | yes | PASS | — | by_id/EXC-1921.json | — |
| EXC-1922 | voice | Open Audio studio | AFTER:Save settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-366.json | — |
| EXC-1923 | voice | Open Presence | AFTER:Save settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-367.json | — |
| EXC-1924 | voice | Apply profile | AFTER:Save settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-368.json | — |
| EXC-1925 | voice | Save settings | AFTER:Save settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-369.json | — |
| EXC-1926 | voice | Refresh | AFTER:Save settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-370.json | — |
| EXC-1927 | voice | Run recovery advisor | AFTER:Save settings | conditional | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-371.json | — |
| EXC-1928 | voice | Start cloud live | AFTER:Save settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-447.json | — |
| EXC-1929 | voice | 220 | AFTER:Save settings | conditional | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-373.json | — |
| EXC-1930 | voice | on | AFTER:Save settings | conditional | yes | PASS | — | by_id/EXC-1930.json | — |
| EXC-1931 | voice | on | AFTER:Save settings | conditional | yes | PASS | — | by_id/EXC-1931.json | — |
| EXC-1932 | voice | on | AFTER:Save settings | conditional | yes | PASS | — | by_id/EXC-1932.json | — |
| EXC-1933 | voice | on | AFTER:Save settings | conditional | yes | PASS | — | by_id/EXC-1933.json | — |
| EXC-1934 | voice | Off Half Full | AFTER:Save settings | conditional | yes | PASS | — | by_id/EXC-1934.json | — |
| EXC-1935 | voice | Whisper RealtimeSTT | AFTER:Save settings | conditional | yes | PASS | — | by_id/EXC-1935.json | — |
| EXC-1936 | voice | Voice profile | AFTER:Save settings | conditional | yes | PASS | — | by_id/EXC-1936.json | — |
| EXC-1937 | voice | Voice cheatsheet | AFTER:Save settings | conditional | yes | PASS | — | by_id/EXC-1937.json | — |
| EXC-1938 | shell | entry / | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-001.json | — |
| EXC-1939 | front_door | all destinations | MODAL | exp_workflow | yes | FAIL | BUG-011 | /tmp/aria-exp-accept/by_id/EXP-002.json | — |
| EXC-1940 | chat | composer Send | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-003.json | — |
| EXC-1941 | chat | Stop | LOADING | exp_workflow | yes | FAIL | BUG-005 | /tmp/aria-exp-accept/by_id/EXP-004.json | — |
| EXC-1942 | chat | More menu | MENU | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-005.json | — |
| EXC-1943 | memory | chat remember → memory → recall → forget | DEFAULT | exp_workflow | yes | FAIL | BUG-013 | /tmp/aria-exp-accept/by_id/EXP-006.json | — |
| EXC-1944 | flytying | all visible tabs + inventory add | TAB/EDITING | exp_workflow | yes | FAIL | BUG-014 | /tmp/aria-exp-accept/by_id/EXP-007.json | — |
| EXC-1945 | planner | add task form | EDITING | exp_workflow | yes | FAIL | BUG-015 | /tmp/aria-exp-accept/by_id/EXP-008.json | — |
| EXC-1946 | documents | text search vs file input | SEARCH | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-009.json | — |
| EXC-1947 | providers | Roles/Catalog tabs + selects | TAB | exp_workflow | yes | FAIL | BUG-018 | /tmp/aria-exp-accept/by_id/EXP-010.json | — |
| EXC-1948 | settings | theme/density nested controls | EDITING | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-011.json | — |
| EXC-1949 | activity | inbox open/read/dismiss + quality | MODAL | exp_workflow | yes | FAIL | BUG-003 | /tmp/aria-exp-accept/by_id/EXP-012.json | — |
| EXC-1950 | mission | health summary | DEFAULT | exp_workflow | yes | FAIL | BUG-006 | /tmp/aria-exp-accept/by_id/EXP-013.json | — |
| EXC-1951 | audio | status bar | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-014.json | — |
| EXC-1952 | home_automation | status + entity search | SEARCH | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-015.json | — |
| EXC-1953 | gallery | generate | LOADING→SUCCESS/ERROR | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-016.json | — |
| EXC-1954 | coding | propose UI | EDITING | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-017.json | — |
| EXC-1955 | command_palette | palette commands | MODAL | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-018.json | — |
| EXC-1956 | shell | health emergency report link/navigation | ERROR | exp_workflow | yes | FAIL | BUG-023 | /tmp/aria-exp-accept/by_id/EXP-178.json | — |
| EXC-1957 | chat | research current info | LOADING→SUCCESS | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-179.json | — |
| EXC-1958 | lock | lock screen open/cancel | MODAL | exp_workflow | yes | NOT TESTABLE | — | /tmp/aria-exp-accept/by_id/EXP-180.json | No lock control discovered in chrome |
| EXC-1959 | jobs | job center / media queue | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-181.json | — |
| EXC-1960 | onboarding | What's New / tour | MODAL | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-182.json | — |
| EXC-1961 | chat | Skip — open UI now | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-374.json | — |
| EXC-1962 | chat | Menu | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-375.json | — |
| EXC-1963 | chat | Wake: — | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-376.json | — |
| EXC-1964 | chat | Cursor · not synced | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-377.json | — |
| EXC-1965 | chat | New Chat | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-378.json | — |
| EXC-1966 | chat | Fork | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-379.json | — |
| EXC-1967 | chat | Trim | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-380.json | — |
| EXC-1968 | chat | Clear Main | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-381.json | — |
| EXC-1969 | chat | Voice input | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-382.json | — |
| EXC-1970 | chat | Read aloud | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-383.json | — |
| EXC-1971 | chat | Compare | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-384.json | — |
| EXC-1972 | chat | Webcam | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-385.json | — |
| EXC-1973 | chat | Dismiss | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-392.json | — |
| EXC-1974 | chat | Stop responding | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-393.json | — |
| EXC-1975 | flytying | Setup | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-394.json | — |
| EXC-1976 | flytying | Rebuild | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-395.json | — |
| EXC-1977 | flytying | Gallery | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-396.json | — |
| EXC-1978 | flytying | Next step | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-397.json | — |
| EXC-1979 | flytying | Repeat | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-398.json | — |
| EXC-1980 | flytying | Clear | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-399.json | — |
| EXC-1981 | flytying | Show | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-400.json | — |
| EXC-1982 | flytying | Compare | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-401.json | — |
| EXC-1983 | flytying | Export | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-402.json | — |
| EXC-1984 | flytying | Print | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-403.json | — |
| EXC-1985 | flytying | What | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-404.json | — |
| EXC-1986 | flytying | Brand ▲ | DEFAULT | exp_workflow | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-405.json | — |
| EXC-1987 | flytying | Scan barcode | DEFAULT | exp_workflow | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-406.json | — |
| EXC-1988 | flytying | Stop | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-407.json | — |
| EXC-1989 | health | Add | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-408.json | — |
| EXC-1990 | mission | Open Notifications | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-409.json | — |
| EXC-1991 | mission | Chat | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-410.json | — |
| EXC-1992 | mission | Audit | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-411.json | — |
| EXC-1993 | mission | Home | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-412.json | — |
| EXC-1994 | documents | Ask | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-414.json | — |
| EXC-1995 | planner | From Journal | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-417.json | — |
| EXC-1996 | planner | Focus 25m | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-418.json | — |
| EXC-1997 | calendar | Today | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-419.json | — |
| EXC-1998 | calendar | Documents | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-420.json | — |
| EXC-1999 | calendar | Add commitment | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-421.json | — |
| EXC-2000 | calendar | Ask Chat | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-422.json | — |
| EXC-2001 | gallery | Maker | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-423.json | — |
| EXC-2002 | gallery | Fly tying | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-424.json | — |
| EXC-2003 | gallery | Video | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-425.json | — |
| EXC-2004 | gallery | Meme | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-426.json | — |
| EXC-2005 | gallery | Cancel generation | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-427.json | — |
| EXC-2006 | gallery | Generate another | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-428.json | — |
| EXC-2007 | gallery | Install NSFW checkpoints | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-429.json | — |
| EXC-2008 | gallery | Generate metadata | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-430.json | — |
| EXC-2009 | gallery | Load more | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-431.json | — |
| EXC-2010 | gallery | Reuse | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-432.json | — |
| EXC-2011 | gallery | Favorite prompt | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-433.json | — |
| EXC-2012 | gallery | Delete saved prompt | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-434.json | — |
| EXC-2013 | coding | Projects | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-435.json | — |
| EXC-2014 | coding | Job Center | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-436.json | — |
| EXC-2015 | coding | Models | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-437.json | — |
| EXC-2016 | memory | Search | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-438.json | — |
| EXC-2017 | memory | New | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-439.json | — |
| EXC-2018 | memory | memoryOpenKnowledgeBtn | DEFAULT | exp_workflow | yes | FAIL | BUG-024 | /tmp/aria-exp-accept/by_id/EXP-440.json | — |
| EXC-2019 | memory | Open Connections | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-441.json | — |
| EXC-2020 | voice | Audio | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-442.json | — |
| EXC-2021 | voice | Presence | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-443.json | — |
| EXC-2022 | voice | Recovery | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-444.json | — |
| EXC-2023 | voice | Warm router | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-445.json | — |
| EXC-2024 | voice | Voice smoke | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-446.json | — |
| EXC-2025 | repair | Open Notifications | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-448.json | — |
| EXC-2026 | repair | Chat | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-449.json | — |
| EXC-2027 | repair | Audit | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-450.json | — |
| EXC-2028 | repair | Home | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-451.json | — |
| EXC-2029 | flytying | Sculpin streamer fly | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-454.json | — |
| EXC-2030 | flytying | Unfavorite pattern | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-455.json | — |
| EXC-2031 | flytying | Adams dry fly #16 terrestrial · 9 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-456.json | — |
| EXC-2032 | flytying | Favorite pattern | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-457.json | — |
| EXC-2033 | flytying | Adams dry fly #18 dry · 23 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-458.json | — |
| EXC-2034 | flytying | Adams dry fly olive terrestrial · 10 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-459.json | — |
| EXC-2035 | flytying | Adams Irresistible dry · 21 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-460.json | — |
| EXC-2036 | flytying | Adams Irresistible dry · 12 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-461.json | — |
| EXC-2037 | flytying | Adams Irresistible #12 dry · 6 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-462.json | — |
| EXC-2038 | flytying | Adams Irresistible #14 terrestrial · 11 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-463.json | — |
| EXC-2039 | flytying | Adams parachute dry · 3 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-464.json | — |
| EXC-2040 | flytying | Adams parachute #14 dry · 12 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-465.json | — |
| EXC-2041 | flytying | Adams parachute #14 dry · 16 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-466.json | — |
| EXC-2042 | flytying | Adams parachute chartreuse post dry · 7 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-467.json | — |
| EXC-2043 | flytying | Adams parachute chartreuse post dry · 8 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-468.json | — |
| EXC-2044 | flytying | Adams parachute orange post terrestrial · 10 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-469.json | — |
| EXC-2045 | flytying | Adams rusty spinner #18 dry · 9 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-470.json | — |
| EXC-2046 | flytying | Adams snowshoe terrestrial · 12 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-471.json | — |
| EXC-2047 | flytying | Adams snowshoe #16 dry · 10 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-472.json | — |
| EXC-2048 | flytying | Adams Wulff terrestrial · 7 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-473.json | — |
| EXC-2049 | flytying | Adams Wulff streamer · 22 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-474.json | — |
| EXC-2050 | flytying | Alexandra streamer streamer · 17 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-475.json | — |
| EXC-2051 | flytying | Anchovy fly terrestrial · 9 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-476.json | — |
| EXC-2052 | flytying | Anchovy fly dry · 14 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-477.json | — |
| EXC-2053 | flytying | Anchovy fly olive nymph · 15 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-478.json | — |
| EXC-2054 | flytying | Anchovy fly olive dry · 8 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-479.json | — |
| EXC-2055 | flytying | Anchovy fly white dry · 9 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-480.json | — |
| EXC-2056 | flytying | Ant pattern CDC terrestrial · 6 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-481.json | — |
| EXC-2057 | flytying | Ant pattern cinnamon terrestrial · 8 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-482.json | — |
| EXC-2058 | flytying | Ant pattern winged terrestrial · 6 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-483.json | — |
| EXC-2059 | flytying | Baitfish articulated streamer · 7 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-484.json | — |
| EXC-2060 | flytying | Baitfish pattern terrestrial · 7 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-485.json | — |
| EXC-2061 | flytying | Baitfish pearl dry · 9 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-486.json | — |
| EXC-2062 | flytying | Baitfish pearl dry · 5 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-487.json | — |
| EXC-2063 | flytying | Baitfish pearl dry · 8 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-488.json | — |
| EXC-2064 | flytying | Baitfish tan dry · 7 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-489.json | — |
| EXC-2065 | flytying | Baitfish UV dry · 4 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-490.json | — |
| EXC-2066 | flytying | Big Game streamer articulated streamer · 29 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-491.json | — |
| EXC-2067 | flytying | Blue Wing Olive parachute dry · 7 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-492.json | — |
| EXC-2068 | flytying | Crayfish brown dry · 8 steps 100 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-493.json | — |
| EXC-2069 | coding | Overview | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-494.json | — |
| EXC-2070 | coding | Proposals | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-495.json | — |
| EXC-2071 | coding | History | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-496.json | — |
| EXC-2072 | coding | Jobs | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-497.json | — |
| EXC-2073 | coding | LSP & Git | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-498.json | — |
| EXC-2074 | coding | Preferences | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-499.json | — |
| EXC-2075 | coding | Advanced | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-500.json | — |
| EXC-2076 | coding | Analyze & propose | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-501.json | — |
| EXC-2077 | coding | Plan & propose | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-502.json | — |
| EXC-2078 | memory | View | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-503.json | — |
| EXC-2079 | memory | Edit | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-504.json | — |
| EXC-2080 | memory | Reset default | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-505.json | — |
| EXC-2081 | memory | Journal | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-506.json | — |
| EXC-2082 | memory | Projects | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-507.json | — |
| EXC-2083 | memory | Browser | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-508.json | — |
| EXC-2084 | memory | Documents | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-509.json | — |
| EXC-2085 | memory | Knowledge Briefs | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-510.json | — |
| EXC-2086 | memory | Export | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-511.json | — |
| EXC-2087 | memory | Import | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-512.json | — |
| EXC-2088 | memory | Prune stale | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-513.json | — |
| EXC-2089 | memory | Scrub test junk | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-514.json | — |
| EXC-2090 | home | Mission Control | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-528.json | — |
| EXC-2091 | home | Planner | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-529.json | — |
| EXC-2092 | home | Journal | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-530.json | — |
| EXC-2093 | home | Calendar | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-531.json | — |
| EXC-2094 | home | Retry | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-532.json | — |
| EXC-2095 | home | Running… | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-533.json | — |
| EXC-2096 | automation | Run | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-534.json | — |
| EXC-2097 | automation | Dry run | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-535.json | — |
| EXC-2098 | automation | Enable | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-536.json | — |
| EXC-2099 | automation | Edit | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-537.json | — |
| EXC-2100 | automation | Mute | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-538.json | — |
| EXC-2101 | automation | Delete | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-539.json | — |
| EXC-2102 | automation | Schedule | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-540.json | — |
| EXC-2103 | automation | Create | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-541.json | — |
| EXC-2104 | automation | Details | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-542.json | — |
| EXC-2105 | providers | Mission Control · Inference | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-543.json | — |
| EXC-2106 | home_automation | Presence | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-544.json | — |
| EXC-2107 | home_automation | Security | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-545.json | — |
| EXC-2108 | home_automation | Open HA | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-546.json | — |
| EXC-2109 | home_automation | haCopyWebhookBtn | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-547.json | — |
| EXC-2110 | presence | Security | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-548.json | — |
| EXC-2111 | presence | Voice | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-549.json | — |
| EXC-2112 | journal | Writing mode | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-550.json | — |
| EXC-2113 | journal | Calendar | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-551.json | — |
| EXC-2114 | journal | Planner | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-552.json | — |
| EXC-2115 | journal | Memory | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-553.json | — |
| EXC-2116 | journal | Reflect | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-554.json | — |
| EXC-2117 | journal | Promote assist | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-555.json | — |
| EXC-2118 | journal | Month-end | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-556.json | — |
| EXC-2119 | journal | Voice log | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-566.json | — |
| EXC-2120 | journal | Vision import | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-567.json | — |
| EXC-2121 | journal | Exit writing (Esc) | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-572.json | — |
| EXC-2122 | video | Gallery | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-573.json | — |
| EXC-2123 | video | Meme | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-574.json | — |
| EXC-2124 | video | Cancel generation | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-575.json | — |
| EXC-2125 | video | Free VRAM before video | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-576.json | — |
| EXC-2126 | video | Install AnimateDiff (~2 GB) | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-577.json | — |
| EXC-2127 | video | Install NSFW checkpoints | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-578.json | — |
| EXC-2128 | audio | Journal | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-579.json | — |
| EXC-2129 | audio | Start live record | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-580.json | — |
| EXC-2130 | audio | Stop + transcribe | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-581.json | — |
| EXC-2131 | audio | Record (VAD) | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-582.json | — |
| EXC-2132 | audio | VAD + transcribe | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-583.json | — |
| EXC-2133 | audio | Cancel job | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-584.json | — |
| EXC-2134 | audio | Install live EQ | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-585.json | — |
| EXC-2135 | audio | recording_ptt_20260730_161305_ptt_raw.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-586.json | — |
| EXC-2136 | audio | live_20260730_164009_raw.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-587.json | — |
| EXC-2137 | audio | recording_20260730_173355.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-588.json | — |
| EXC-2138 | audio | recording_20260730_172933.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-589.json | — |
| EXC-2139 | audio | recording_20260730_171640.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-590.json | — |
| EXC-2140 | audio | recording_20260730_152137.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-591.json | — |
| EXC-2141 | audio | live_20260726_185623.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-592.json | — |
| EXC-2142 | audio | live_20260726_165807.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-593.json | — |
| EXC-2143 | audio | ware_Foundation_2_About_the_Python_Sof.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-594.json | — |
| EXC-2144 | audio | 1_For_more_about_the_foundation_s_missio.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-595.json | — |
| EXC-2145 | audio | The_official_website_of_the_Python_Softw.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-596.json | — |
| EXC-2146 | audio | the_RTX_3090.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-597.json | — |
| EXC-2147 | audio | Stored_via_ACM_exact_acceptance_token.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-598.json | — |
| EXC-2148 | audio | provide_a_list_or_more_details_I_can_he.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-599.json | — |
| EXC-2149 | audio | For_example_you_might_have_things_like.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-600.json | — |
| EXC-2150 | audio | Sure_To_help_you_check_your_fly_tying_m.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-601.json | — |
| EXC-2151 | audio | recording_20260610_194808_edited.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-602.json | — |
| EXC-2152 | audio | Delete recording_20260610_194808_edited.wav | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-603.json | — |
| EXC-2153 | browser | Memory | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-604.json | — |
| EXC-2154 | browser | Documents | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-605.json | — |
| EXC-2155 | browser | Chat | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-606.json | — |
| EXC-2156 | browser | Overview | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-607.json | — |
| EXC-2157 | browser | Session | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-608.json | — |
| EXC-2158 | all | final discovery scan cycle 1 | DEFAULT | exp_workflow | yes | FAIL | — | /tmp/aria-exp-accept/by_id/EXP-FINAL-PASS.json | — |
| EXC-2159 | all | final discovery scan cycle 2 | DEFAULT | exp_workflow | yes | FAIL | — | /tmp/aria-exp-accept/by_id/EXP-FINAL-PASS-2.json | — |
| EXC-2160 | all | final discovery scan cycle 3 | DEFAULT | exp_workflow | yes | FAIL | — | /tmp/aria-exp-accept/by_id/EXP-FINAL-PASS-3.json | — |
| EXC-2161 | shell | bare / vs ?workspace=1 | DEFAULT | exp_workflow | yes | PASS | BUG-001 | /tmp/aria-exp-accept/by_id/EXP-000-LEGACY.json | — |
| EXC-2162 | chat | hold to talk | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-900.json | — |
| EXC-2163 | chat | send | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-901.json | — |
| EXC-2164 | flytying | remove | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-902.json | — |
| EXC-2165 | flytying | import | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-903.json | — |
| EXC-2166 | flytying | send | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-904.json | — |
| EXC-2167 | health | search | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-905.json | — |
| EXC-2168 | mission | settings | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-906.json | — |
| EXC-2169 | documents | ask aria | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-907.json | — |
| EXC-2170 | documents | cancel | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-908.json | — |
| EXC-2171 | documents | close | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-909.json | — |
| EXC-2172 | memory | refresh | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-910.json | — |
| EXC-2173 | journal | search | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-911.json | — |
| EXC-2174 | journal | add | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-912.json | — |
| EXC-2175 | video | save | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-913.json | — |
| EXC-2176 | maker | clear | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-914.json | — |
| EXC-2177 | maker | add | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-915.json | — |
| EXC-2178 | maker | start | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-916.json | — |
| EXC-2179 | connections | cancel | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-917.json | — |
| EXC-2180 | connections | close | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-918.json | — |
| EXC-2181 | capabilities | new | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-919.json | — |
| EXC-2182 | audit | run | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-920.json | — |
| EXC-2183 | audio | EXP-BUG-002 | DEFAULT | exp_workflow | yes | FAIL | BUG-002 | /tmp/aria-exp-accept/by_id/EXP-BUG-002.json | — |
| EXC-2184 | activity | EXP-BUG-003 | DEFAULT | exp_workflow | yes | FAIL | BUG-003 | /tmp/aria-exp-accept/by_id/EXP-BUG-003.json | — |
| EXC-2185 | mission | EXP-BUG-006 | DEFAULT | exp_workflow | yes | FAIL | BUG-006 | /tmp/aria-exp-accept/by_id/EXP-BUG-006.json | — |
| EXC-2186 | front_door | EXP-BUG-011 | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-BUG-011.json | — |
| EXC-2187 | all | function-normalized final discovery | DEFAULT | exp_workflow | yes | FAIL | — | /tmp/aria-exp-accept/by_id/EXP-FINAL-PASS-FN.json | — |
| EXC-2188 | all | second function-normalized final discovery | DEFAULT | exp_workflow | yes | PASS | — | /tmp/aria-exp-accept/by_id/EXP-FINAL-PASS-FN-2.json | — |
