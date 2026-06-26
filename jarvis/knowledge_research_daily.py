# Source Generated with Decompyle++
# File: knowledge_research_daily.cpython-312.pyc (Python 3.12)

'''Nightly self-upgrading knowledge — web research digests stored for ARIA.'''
from __future__ import annotations
import json
import logging
import os
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable
from jarvis.config import PROJECT_ROOT
from jarvis.knowledge import KNOWLEDGE_DIR, _utc_now, extract_key_points, remember_key_points, slugify
from jarvis.modules.journal import _today
log = logging.getLogger('jarvis.knowledge_research')
RESEARCH_DIR = KNOWLEDGE_DIR / 'research'
STATE_FILE = RESEARCH_DIR / '_state.json'
DAILY_RESEARCH_TAG = 'daily-research'
Category = dict[(str, Any)]

def _comfyui_context():
    lines = []
    
    try:
        checkpoint_label = checkpoint_label
        get_settings_dict = get_settings_dict
        import jarvis.comfyui_settings
        settings = get_settings_dict()
        if not settings.get('checkpoint'):
            settings.get('checkpoint')
            if not settings.get('checkpoint_name'):
                settings.get('checkpoint_name')
        ckpt = ''
        if ckpt:
            if not checkpoint_label(ckpt):
                checkpoint_label(ckpt)
            lines.append(f'''Active checkpoint: {ckpt}''')
        host = os.getenv('COMFYUI_HOST', '127.0.0.1:8188')
        lines.append(f'''ComfyUI host: {host}''')
        return '\n'.join(lines)
    except Exception:
        continue



def _smart_home_context():
    lines = []
    if not os.getenv('HOMEASSISTANT_URL'):
        os.getenv('HOMEASSISTANT_URL')
        if not os.getenv('HA_URL'):
            os.getenv('HA_URL')
    ha = ''.strip()
    if ha:
        lines.append(f'''Home Assistant URL: {ha}''')
    if os.getenv('JARVIS_KASA_ENABLED', '').lower() in ('1', 'true', 'yes'):
        lines.append('Kasa integration enabled')
    if not '\n'.join(lines):
        '\n'.join(lines)
    return 'No smart-home URLs configured in jarvis.env.'


def _env_flag(name = None, *, default):
    raw = os.getenv(name)
# WARNING: Decompyle incomplete


def _stack_categories():
    year = datetime.now().year
    month = datetime.now().strftime('%B %Y')
    stack = [
        {
            'id': 'ai_news',
            'slug': 'ai-news',
            'title': 'AI news',
            'kind': 'stack',
            'queries': [
                f'''artificial intelligence news {month}''',
                'open source LLM news this week',
                'AI agents tools news'] },
        {
            'id': 'ollama',
            'slug': 'ollama-updates',
            'title': 'Ollama updates',
            'kind': 'stack',
            'queries': [
                'Ollama release notes new version',
                f'''Ollama changelog {year}''',
                'Ollama blog update models'],
            'local_context': _ollama_context },
        {
            'id': 'comfyui',
            'slug': 'comfyui-image',
            'title': 'ComfyUI & image models',
            'kind': 'stack',
            'queries': [
                'ComfyUI release notes update',
                f'''Flux Schnell ComfyUI workflow {year}''',
                'Stable Diffusion XL checkpoint news',
                'local image generation VRAM optimization'],
            'local_context': _comfyui_context },
        {
            'id': 'coding_agents',
            'slug': 'coding-agents',
            'title': 'Coding agents & MCP',
            'kind': 'stack',
            'queries': [
                'Model Context Protocol MCP server news',
                f'''AI coding agent tools {month}''',
                'Cursor IDE agent features update',
                'local LLM coding assistant best practices'] },
        {
            'id': 'local_gpu',
            'slug': 'local-gpu',
            'title': 'Local GPU & inference',
            'kind': 'stack',
            'queries': [
                f'''NVIDIA CUDA driver release notes {year}''',
                '12GB VRAM local LLM optimization',
                'ROCm PyTorch Linux update',
                'quantized model inference VRAM tips'],
            'local_context': _ollama_context },
        {
            'id': 'smart_home',
            'slug': 'smart-home',
            'title': 'Smart home & automation',
            'kind': 'stack',
            'queries': [
                'Home Assistant release notes',
                f'''Home Assistant {year} new integrations''',
                'Kasa smart plug local API',
                'home automation LLM assistant'],
            'local_context': _smart_home_context },
        {
            'id': 'memory_graph',
            'slug': 'memory-graph',
            'title': 'Memory & knowledge graphs',
            'kind': 'stack',
            'queries': [
                'Memgraph release notes',
                f'''vector database RAG local {year}''',
                'knowledge graph LLM memory',
                'ChromaDB Qdrant comparison self-hosted'] },
        {
            'id': 'zorin',
            'slug': 'zorin-updates',
            'title': 'Zorin OS updates',
            'kind': 'stack',
            'queries': [
                'Zorin OS update release',
                f'''Zorin OS {year} news''',
                'Zorin OS security updates'],
            'local_context': _os_context },
        {
            'id': 'dependencies',
            'slug': 'dependency-updates',
            'title': 'Dependency updates',
            'kind': 'stack',
            'queries_fn': _dependency_queries,
            'local_context': _dependency_context },
        {
            'id': 'cad_print',
            'slug': 'cad-print',
            'title': 'CAD & 3D printing',
            'kind': 'stack',
            'queries': [
                'OrcaSlicer Linux CLI headless slice',
                'Moonraker API upload start print',
                'Klipper printer status API',
                'build123d export STL tutorial'] },
        {
            'id': 'security',
            'slug': 'security-selfhost',
            'title': 'Self-hosted security',
            'kind': 'stack',
            'queries': [
                f'''self-hosted AI security best practices {year}''',
                'Ollama API expose localhost security',
                'Home Assistant security advisory',
                'local LLM privacy hardening'] }]
    return stack


def _intel_categories():
    year = datetime.now().year
    month = datetime.now().strftime('%B %Y')
    return [
        {
            'id': 'science_discoveries',
            'slug': 'science-discoveries',
            'title': 'Science & discoveries',
            'kind': 'intel',
            'queries': [
                f'''science breakthrough news {month}''',
                'space exploration discovery this week',
                'medicine research breakthrough explained'] },
        {
            'id': 'world_briefing',
            'slug': 'world-briefing',
            'title': 'World briefing',
            'kind': 'intel',
            'queries': [
                f'''world news summary {month}''',
                'technology society trends explained',
                'major global developments factual overview'] },
        {
            'id': 'clear_thinking',
            'slug': 'clear-thinking',
            'title': 'Clear thinking & communication',
            'kind': 'intel',
            'queries': [
                'cognitive bias practical guide',
                'how to explain complex ideas clearly',
                'critical thinking techniques summary'] },
        {
            'id': 'software_craft',
            'slug': 'software-craft',
            'title': 'Software craft',
            'kind': 'intel',
            'queries': [
                'software architecture best practices',
                'debugging complex systems strategies',
                'writing maintainable code principles'] },
        {
            'id': 'learning_skills',
            'slug': 'learning-skills',
            'title': 'Learning & problem solving',
            'kind': 'intel',
            'queries': [
                'how to learn hard subjects effectively',
                'problem decomposition techniques',
                'spaced repetition active learning research'] },
        {
            'id': 'history_ideas',
            'slug': 'history-ideas',
            'title': 'History of ideas',
            'kind': 'intel',
            'queries': [
                f'''history of ideas {year} explainer''',
                'philosophy concepts practical summary',
                'innovation history lessons for builders'] }]


def _parse_topic_list(raw = None):
    topics = []
    if not raw:
        raw
# WARNING: Decompyle incomplete

_PROFILE_FIELD_PATTERNS: 'dict[str, re.Pattern[str]]' = {
    'interests': re.compile('^User often works on:\\s*(.+?)\\.?\\s*$', re.I),
    'learning_goals': re.compile('^User wants to learn about:\\s*(.+?)\\.?\\s*$', re.I),
    'expertise_areas': re.compile('^User already knows:\\s*(.+?)\\.?\\s*$', re.I),
    'notes': re.compile('^User notes for Jarvis:\\s*(.+?)\\.?\\s*$', re.I) }

def _extract_profile_field_value(text = None, field_id = None):
    '''Return the user-supplied value from a formatted profile memory line.'''
    if not text:
        text
    text = ''.strip()
    pat = _PROFILE_FIELD_PATTERNS.get(field_id)
    if not pat:
        return ''
    m = pat.match(text)
    if m:
        return m.group(1).strip()


def _interests_from_profile(memory = None):
    pass
# WARNING: Decompyle incomplete


def _topics_from_active_project():
    
    try:
        get_active_slug = get_active_slug
        import jarvis.active_project
        if not get_active_slug():
            get_active_slug()
        slug = ''.strip()
        if slug and slug not in ('default', 'main'):
            return [
                slug.replace('-', ' ').replace('_', ' ')]
        return None
    except Exception:
        return []



def _topic_to_category(topic = None):
    year = datetime.now().year
    slug = slugify(topic)
    cat_id = f'''custom_{slug.replace('-', '_')}'''
    return {
        'id': cat_id,
        'slug': f'''interest-{slug}''',
        'title': topic.strip()[:60],
        'kind': 'personal',
        'topic': topic.strip(),
        'queries': [
            f'''{topic} news developments {year}''',
            f'''{topic} explained overview guide''',
            f'''what is new in {topic} {year}'''] }


def _custom_categories(memory = None):
    topics = []
    topics.extend(_parse_topic_list(os.getenv('JARVIS_KNOWLEDGE_RESEARCH_TOPICS', '')))
    topics.extend(_interests_from_profile(memory))
    topics.extend(_topics_from_active_project())
    seen = set()
    out = []
    for topic in topics:
        key = topic.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(_topic_to_category(topic))
    return out


def _rotate_subset(categories = None, day = None, limit = None):
    if limit <= 0 or len(categories) <= limit:
        return categories
    start = (lambda .0: pass# WARNING: Decompyle incomplete
)(day()) % len(categories)
# WARNING: Decompyle incomplete


def _all_categories(memory = None):
    cats = []
    if _env_flag('JARVIS_KNOWLEDGE_RESEARCH_STACK', default = True):
        cats.extend(_stack_categories())
    if _env_flag('JARVIS_KNOWLEDGE_RESEARCH_INTEL', default = True):
        cats.extend(_intel_categories())
    if _env_flag('JARVIS_KNOWLEDGE_RESEARCH_CUSTOM', default = True):
        cats.extend(_custom_categories(memory))
    return cats


def _categories_for_run(*, memory, day):
    if not day:
        day
    d = _today()
    cats = []
    if _env_flag('JARVIS_KNOWLEDGE_RESEARCH_STACK', default = True):
        cats.extend(_stack_categories())
    if _env_flag('JARVIS_KNOWLEDGE_RESEARCH_INTEL', default = True):
        
        try:
            intel_limit = int(os.getenv('JARVIS_KNOWLEDGE_RESEARCH_INTEL_PER_NIGHT', '4'))
            cats.extend(_rotate_subset(_intel_categories(), d, intel_limit))
            if _env_flag('JARVIS_KNOWLEDGE_RESEARCH_CUSTOM', default = True):
                
                try:
                    custom_limit = int(os.getenv('JARVIS_KNOWLEDGE_RESEARCH_CUSTOM_PER_NIGHT', '2'))
                    cats.extend(_custom_categories(memory)[:max(0, custom_limit)])
                    return cats
                    except ValueError:
                        intel_limit = 4
                        continue
                except ValueError:
                    custom_limit = 2
                    continue




def _categories(memory = None):
    return _all_categories(memory)


def list_research_categories(*, memory):
    pass
# WARNING: Decompyle incomplete


def research_enabled():
    return os.getenv('JARVIS_KNOWLEDGE_RESEARCH_DAILY', '1').lower() not in ('0', 'false', 'off', 'no')


def research_hour():
    
    try:
        return int(os.getenv('JARVIS_KNOWLEDGE_RESEARCH_HOUR', '23'))
    except ValueError:
        return 23



def auto_remember():
    return os.getenv('JARVIS_KNOWLEDGE_RESEARCH_REMEMBER', '1').lower() not in ('0', 'false', 'off', 'no')


def _load_state():
    if not STATE_FILE.is_file():
        return {
            'days': { },
            'last_run_day': '' }
    
    try:
        data = json.loads(STATE_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            data.setdefault('days', { })
            return data
        return {
            'days': { },
            'last_run_day': '' }
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt knowledge research state: %s', exc)
        exc = None
        del exc
        continue
        exc = None
        del exc



def _save_state(data = None):
    RESEARCH_DIR.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(STATE_FILE)
    STATE_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _already_ran(day = None):
    if not day:
        day
    d = _today()
    data = _load_state()
    return bool(data.get('days', { }).get(d, { }).get('completed'))


def _category_slugs():
    pass
# WARNING: Decompyle incomplete


def _sync_day_state(state = None, day = None, slug = None):
    '''Record per-category timestamps; _mark_ran sets completed after the nightly run.'''
    day_state = state.setdefault('days', { }).setdefault(day, { })
    day_state[slug] = datetime.now(timezone.utc).isoformat()
    state['last_run_day'] = day


def _mark_ran(day = None, results = None):
    data = _load_state()
    day_state = data.setdefault('days', { }).setdefault(day, { })
    for r in results:
        slug = r.get('slug')
        if not slug:
            continue
        if not r.get('ok'):
            continue
        if r.get('skipped'):
            continue
        day_state[slug] = datetime.now(timezone.utc).isoformat()
    day_state['completed'] = True
    day_state['at'] = datetime.now(timezone.utc).isoformat()
# WARNING: Decompyle incomplete


def _ollama_context():
    lines = []
    
    try:
        ollama_version = ollama_version
        import jarvis.ollama_health
        ver = ollama_version()
        if ver:
            None(f'''{(lambda .0: pass# WARNING: Decompyle incomplete
)(ver())}''')
        ollama = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
        lines.append(f'''Ollama host: {ollama}''')
        return '\n'.join(lines)
    except Exception:
        continue



def _os_context():
    
    try:
        return Path('/etc/os-release').read_text(encoding = 'utf-8').strip()
    except OSError:
        return ''



def _read_requirements_names(limit = None):
    names = []
    for rel in ('requirements.txt', 'requirements-optional.txt'):
        path = PROJECT_ROOT / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding = 'utf-8').splitlines():
            line = line.strip()
            if line or line.startswith('#'):
                continue
            pkg = re.split('[<>=!~\\[]', line, maxsplit = 1)[0].strip()
            if pkg and pkg not in names:
                names.append(pkg)
            if not len(names) >= limit:
                continue
            
            
            return ('requirements.txt', 'requirements-optional.txt'), path.read_text(encoding = 'utf-8').splitlines(), names
    return names


def _dependency_context():
    lines = []
    for rel in ('requirements.txt', 'requirements-optional.txt'):
        path = PROJECT_ROOT / rel
        if not path.is_file():
            continue
        lines.append(f'''**{rel}** (project root):\n```\n{path.read_text(encoding = 'utf-8')[:1800]}\n```''')
    
    try:
        proc = subprocess.run([
            os.environ.get('PIP', 'pip'),
            'list',
            '--format=freeze'], capture_output = True, text = True, timeout = 30)
        if proc.returncode == 0 and proc.stdout.strip():
            pkgs = proc.stdout.strip().splitlines()[:40]
            lines.append('**Installed (pip freeze, partial):**\n' + '\n'.join(pkgs))
        lines.append(_ollama_context())
        return '\n\n'.join(lines)
    except (OSError, subprocess.TimeoutExpired):
        continue



def _dependency_queries():
    year = datetime.now().year
    pkgs = _read_requirements_names(6)
# WARNING: Decompyle incomplete


def _collect_results(queries = None, *, per_query):
    web_search = web_search
    import jarvis
    web_search_disabled = web_search_disabled
    import jarvis.profiles
    if web_search_disabled():
        return []
    seen = None()
    merged = []
# WARNING: Decompyle incomplete


def _digest_system_prompt(kind = None):
    if kind == 'intel':
        return 'You write nightly general-knowledge briefings for a personal AI assistant (ARIA). Summarize factual context, key ideas, and why they matter for a smart assistant helping with real work and conversation. Use markdown with:\n### Summary (2-3 sentences)\n### Key facts & context (bullet list)\n### Why it matters (1-3 bullets for an assistant)\nUse ONLY the snippets and local context. Say when information is uncertain.'
    if kind == 'personal':
        return "You write nightly knowledge briefings tailored to the user's stated interests. Focus on developments, background, and practical takeaways for this specific topic. Use markdown with:\n### Summary (2-3 sentences)\n### What's new or notable (bullet list)\n### Useful context (optional bullets — concepts, people, or resources)\nUse ONLY the snippets and local context. Say when information is uncertain."
    return 'You write nightly knowledge digests for a personal AI assistant (ARIA). Focus on what is NEW or CHANGED since typical daily use. Use markdown with:\n### Summary (2-3 sentences)\n### Key updates (bullet list, include version numbers when known)\n### Suggested follow-ups (optional bullets — install, read, or test)\nUse ONLY the snippets and local context. Say when information is uncertain.'


def build_daily_digest(title = None, results = None, *, day, local_context, kind):
    llm = llm
    web_search = web_search
    import jarvis
    if not results and local_context:
        return f'''## {day}\n\n### Summary\n\nNo web results found (offline profile or search unavailable).\n'''
    context = web_search.format_results_for_llm(results) if None else '(no web hits)'
    system = _digest_system_prompt(kind)
    if not local_context:
        local_context
    user = f'''Category: {title}\nDate: {day}\n\nLocal context:\n{'(none)'}\n\nWeb snippets:\n{context}'''
    
    try:
        body = llm.ask(llm.general_model(), [
            {
                'role': 'system',
                'content': system },
            {
                'role': 'user',
                'content': user }]).strip()
        if not body.startswith('##'):
            body = f'''## {day}\n\n{body}'''
        elif not body.startswith(f'''## {day}'''):
            body = f'''## {day}\n\n{body}'''
        return body[:6000]
    except Exception:
        exc = None
        body = f'''### Summary\n\nDigest synthesis failed: {exc}\n\n### Raw snippets\n\n{context[:3000]}'''
        exc = None
        del exc
        continue
        exc = None
        del exc



def _parse_front_matter(raw = None):
    if not raw.startswith('---'):
        return ({ }, raw)
    parts = None.split('---', 2)
    if len(parts) < 3:
        return ({ }, raw)
    
    try:
        meta = json.loads(parts[1])
        return (meta, parts[2].strip())
    except json.JSONDecodeError:
        meta = { }
        continue



def append_research_digest(slug, title = None, day = None, section = None, results = ('slug', 'str', 'title', 'str', 'day', 'str', 'section', 'str', 'results', 'list[dict]', 'return', 'dict[str, str]')):
    RESEARCH_DIR.mkdir(parents = True, exist_ok = True)
    path = RESEARCH_DIR / f'''{slugify(slug)}.md'''
    meta = {
        'topic': title,
        'slug': slugify(slug),
        'category': slugify(slug),
        'updated': _utc_now(),
        'last_day': day,
        'source_count': len(results) }
    front = '---\n' + json.dumps(meta, indent = 2) + '\n---\n\n'
# WARNING: Decompyle incomplete


def get_category(category_id = None, *, memory):
    for cat in _all_categories(memory):
        if not cat['id'] == category_id and cat['slug'] == category_id:
            continue
        
        return _all_categories(memory), cat


def research_category(category_id = None, *, day, memory, force):
    cat = get_category(category_id, memory = memory)
    if not cat:
        return {
            'ok': False,
            'message': f'''Unknown research category: {category_id}''' }
    if not None:
        pass
    d = _today()
    slug = cat['slug']
    state = _load_state()
    day_state = state.setdefault('days', { }).setdefault(d, { })
    if force and day_state.get(slug):
        return {
            'ok': True,
            'slug': slug,
            'skipped': True,
            'message': 'Already researched today.' }
    queries_fn = None.get('queries_fn')
    if queries_fn:
        pass
    elif not cat.get('queries'):
        cat.get('queries')
    queries = list([])
    local_fn = cat.get('local_context')
    local_context = local_fn() if local_fn else ''
    results = _collect_results(queries)
    section = build_daily_digest(cat['title'], results, day = d, local_context = local_context, kind = cat.get('kind', 'stack'))
    saved = append_research_digest(slug, cat['title'], d, section, results)
    remembered = 0
# WARNING: Decompyle incomplete


def run_nightly_research(*, day, memory, force, categories):
    if not research_enabled() and force:
        return [
            {
                'ok': False,
                'message': 'Nightly knowledge research disabled.' }]
    if not None:
        pass
    d = _today()
    if force and _already_ran(d):
        return [
            {
                'ok': True,
                'skipped': True,
                'message': f'''Already completed research for {d}.''' }]
# WARNING: Decompyle incomplete


def run_scheduled(now = None, *, memory):
    if not research_enabled():
        return []
    if not None:
        pass
    now = datetime.now()
    if now.hour != research_hour() or now.minute >= 15:
        return []
    return None(memory = memory)


def run_startup_catchup(*, memory):
    if not research_enabled():
        return []
    if None():
        return []
    now = None.now()
    if now.hour >= research_hour():
        return run_nightly_research(memory = memory)


def _kind_for_research_slug(slug = None, *, memory):
    for cat in _all_categories(memory):
        if not cat['slug'] == slug:
            continue
        
        return _all_categories(memory), cat.get('kind', 'stack')
    if slug.startswith('interest-'):
        return 'personal'
    return 'stack'


def list_research_briefs(*, memory):
    if not RESEARCH_DIR.is_dir():
        return []
    items = None
    for path in sorted(RESEARCH_DIR.glob('*.md')):
        if path.name.startswith('_'):
            continue
        (meta, _) = _parse_front_matter(path.read_text(encoding = 'utf-8')[:4000])
        slug = path.stem
        if not meta.get('topic'):
            meta.get('topic')
        items.append({
            'slug': slug,
            'title': slug.replace('-', ' ').title(),
            'updated': meta.get('updated', ''),
            'last_day': meta.get('last_day', ''),
            'path': str(path),
            'kind': _kind_for_research_slug(slug, memory = memory) })
    return items

