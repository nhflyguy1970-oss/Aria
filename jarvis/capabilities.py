# Source Generated with Decompyle++
# File: capabilities.cpython-312.pyc (Python 3.12)

'''Built-in capability descriptions — instant responses, no LLM required.'''
from jarvis.branding import assistant_full_name, assistant_intro, assistant_name
from jarvis.config import is_uncensored
from jarvis.model_store import get_all_settings, get_models

def capabilities_message():
    mode = 'uncensored' if is_uncensored() else 'standard'
    models = get_models()
    hw = get_all_settings().get('hardware', { })
    name = assistant_name()
    lines = [][f'''Hello! I\'m **{name}** ({assistant_full_name()}), your local AI assistant. Here\'s what I can help with:''']['']['**Coding** — create/fix/debug with pytest verify, proposals (Apply/Undo), Cursor editor sync.']['  _Try:_ "Implement X in data/scripts/foo.py with tests" → **Apply** · `undo`']['  _Try:_ "fix data/scripts/foo.py" · "debug until tests pass for …"']['  _Try:_ With **Cursor extension**: select code → `fix selection` · `explain selection`']['  _Try:_ "find references parse_duration" · "run command: pytest data/scripts/ -q"']['  _Try:_ "Diagnose …" → "fix it" · rename/move/extract → proposal (not instant write)']['']['**Memory** — I remember facts about you across sessions.']['  _Try:_ "Remember that I prefer short answers" · "What do you remember?"']['  _Try:_ "Correct that …" · "Forget about …" · "Remember strategy: …"']['']['**Bullet Journal** — Index, Future Log, Monthly/Daily logs, Collections, migration & AI reflection.']['  _Try:_ "Morning briefing" (weather, tasks, national + local headlines) · "Tell me more about headline 2"']['  _Try:_ "Journal today"']['']["**Vision** — attach an image and I'll describe or analyze it."]['  _Try:_ attach a photo, or "What\'s in this image?"']['']['**Audio** — transcribe, summarize, generate speech, and edit recordings.']['  _Try:_ attach a .wav · "Generate audio that says hello world"']['  _Try:_ attach audio · "Trim the first 5 seconds and normalize volume"']['']['**Data** — load CSV, JSON, XLSX, or SQLite; query, chart, and run SELECT.']['  _Try:_ attach a spreadsheet · "Chart sales by region" · `SELECT * FROM users LIMIT 10`']['']['**Documents** — PDF and Word (.docx): summarize, Q&A, warranty clause lookup.']['  _Try:_ attach a PDF · "Summarize this warranty PDF" · "What does clause 4 say about coverage?"']['  _Try:_ drop files in `data/documents/` · follow-up questions without re-attaching']['']['**Web search** — SearXNG (local) or DuckDuckGo fallback.']['  _Try:_ "Search the web for ROCm RX 7600 setup"']['']['**Learn** — research a topic and save a brief for future chats.']['  _Try:_ "Learn about: edge AI accelerators" · "Remember key points"']['**Nightly research** — auto-digests for AI news, Ollama, Zorin, dependencies (11 PM).']['  _Try:_ "Run nightly knowledge research" · "Research ollama" · "Saved research briefs"']['**Skills** — reusable install/repair procedures you can save and run.']['  _Try:_ "List skills" · "Run docker repair skill" · "Show skill install ollama"']['**Workflows** — learns when you repeat the same actions; run or convert to skills.']['  _Try:_ "List workflows" · "Scan workflows" · "Run morning routine workflow"']['**Self-upgrade** — git branch pipeline: change code, run tests, you approve merge.']['  _Try:_ "Self upgrade: add /api/ping" · "Merge upgrade" · Upgrade panel → Run pipeline']['']['**Images** — ComfyUI (local) with Ollama image-model fallback when ComfyUI is offline.']['  _Try:_ "Generate an image of a sunset over mountains"']['']['**Music & Song Studio** — MusicGen, genre remix, AI lyrics+songs, voice→song.']['  _Try:_ "Write a song about stargazing" · attach song · "transform into jazz"']['  _Try:_ record voice · "make my voice a song"']['  _Try:_ "Generate music: calm piano for studying"']['']['**Coding Tier 3** — Cursor bridge, MCP propose/apply, tasks pause/resume, git PR via `gh`.']['  _Try:_ `./scripts/install-cursor-extension.sh` then status pill shows live file']['  _Try:_ MCP in Cursor: jarvis_propose_fix, jarvis_apply_proposal, jarvis_get_editor_context']['']['**Syntax checker** — py_compile + ruff + pyright + mypy (Python), node/bash/json/yaml.']['  _Try:_ "Syntax check jarvis/assistant.py" · "Lint this file" · shown on every proposal before apply']['']['**Coding extras** — git commit/branch/diff, AST rename, firejail/docker sandbox runner.']['  _Try:_ "Summarize the diff" · "Rename foo to bar" · "Run data/scripts/hello_world.py"']['']['**Chat branches** — fork conversations without losing the main thread.']['  _Try:_ use **+ Branch** in the header, or "list branches"']['']['**Chat** — ask me anything else conversationally.']['']
    ha_enabled = ha_enabled
    import jarvis.home_assistant
    if ha_enabled():
        lines += [
            '**Home Assistant** — read device state, control lights/switches, run scenes.',
            '  _Try:_ "House status" · "Turn off the living room lights" · "Activate scene goodnight"',
            '  _Try:_ "I\'m heading out" (uses JARVIS_HA_SCENE_LEAVE when set)',
            '']
    lines += [
        f'''**Mode:** {mode} · **Models:** {models['general']} (chat), {models['coder']} (code), {models['vision']} (vision)''',
        f'''**Your PC:** {hw.get('gpu', '')} · {hw.get('ram', '')} — change models in sidebar settings.''',
        '',
        f'''**One-click launch** — use the desktop shortcut or `./scripts/launch-jarvis.sh`. {name} auto-starts Ollama, pulls missing models, and manages everything from this GUI.''',
        '',
        'Just talk naturally — no commands to memorize. Say **what models** for hardware-specific recommendations.']
    return '\n'.join(lines)


def greeting_message():
    name = assistant_name()
    return f'''Hello! I\'m {name}, running entirely on your machine via Ollama.\n\nAsk me **what can you do?** to see everything I handle, or just tell me what you need.'''


def models_guide():
    settings = get_all_settings()
    active = settings.get('active', { })
    hw = settings.get('hardware', { })
    gpu_line = hw.get('gpu', 'your GPU')
    uncensored = is_uncensored()
    mode = 'uncensored' if uncensored else 'standard'
    lines = [
        f'''**Your PC:** {hw.get('cpu', '')} · {gpu_line} · {hw.get('ram', '')}''',
        f'''**Active mode:** {mode}''',
        '',
        '**Currently configured:**',
        f'''- Chat: `{active.get('general', '?')}`''',
        f'''- Code: `{active.get('coder', '?')}`''',
        f'''- Review: `{active.get('review', '?')}`''',
        f'''- Vision: `{active.get('vision', '?')}`''',
        f'''- Image: `{active.get('image', '?')}`''',
        f'''- Memory: `{active.get('embed', '?')}`''',
        '',
        'Change these in the sidebar under **Model settings**.',
        '']
    if uncensored:
        lines += [
            f'''**Optimized uncensored picks for {gpu_line}:**''',
            '- Chat: `dolphin3:latest` (uncensored; falls back to dolphin-mistral)',
            '- Code: `qwen2.5-coder:14b`',
            '- Vision: `llava:13b` (uncensored-friendly)',
            '- Images: RealVisXL / Lustify / Pony XL checkpoints in Gallery',
            '- Memory: `nomic-embed-text`']
    else:
        lines += [
            f'''**Optimized standard picks for {gpu_line}:**''',
            '- Chat: `qwen2.5:14b` (installed)',
            '- Code: `qwen2.5-coder:14b` (installed)',
            '- Review: `deepseek-r1:14b` (installed)',
            '- Vision: `moondream:latest` (recommended on 8GB) or `llava:13b` for max quality',
            '- Fast alternative: `qwen2.5:7b` for chat if 14b feels slow',
            '- Memory: `nomic-embed-text` (installed)']
    lines.append(f'''\n{hw.get('note', '')}''')
    return '\n'.join(lines)

