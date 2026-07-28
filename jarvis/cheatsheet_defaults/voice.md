# Voice

Conversational voice for Aria — one shared pipeline for PTT, wake word, Cloud Live, CLI, and API.

## Controls
- **Speak replies** — auto-speak assistant answers (Chat)
- **Mute** — turn off speak replies (same preference)
- **Read last reply** — speak the latest assistant message once
- **Stop speaking** — clear TTS queue and halt playback
- **Hold mic / PTT** — local Whisper push-to-talk (works even without browser STT)
- **Hey Aria** — wake word when wake listening is on
- **Duplex** — Off / Half / Full (Full = barge-in during TTS)
- **Cloud Live** — Gemini Live realtime voice (API key required; OpenAI Realtime hidden until WebRTC)

## Voice commands (intent router)
- Open Gallery / Browser / Coding / Mission Control / Planner / Documents / Audio Studio / Voice
- Generate image / Generate video
- Mute / Stop speaking / Speak replies

## Tips
- Prefer local Whisper for privacy; Cloud Live is opt-in.
- Use **Ctrl+K** → Stop speaking / Mute / Read aloud.
- Voice Profiles (Quiet Office, Hands-Free, Coding, …) apply STT/TTS/duplex presets.
- Audio Studio is for production audio — Voice owns conversation.
