# Source Generated with Decompyle++
# File: memory_context.cpython-312.pyc (Python 3.12)

'''Memory context: system prompt block, conflicts, project namespace, smart auto-memory.'''
from __future__ import annotations
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from jarvis.config import PROJECT_ROOT
_JOURNAL_MEMORY = re.compile('^From bullet journal \\(([^)]+)\\):\\s*(.+)$', re.I | re.S)
_JOURNAL_DATE = re.compile('(\\d{4}-\\d{2}-\\d{2})')
_RESUME_HINTS = re.compile('\\b(resume|continue|checkpoint|left off|where we|coding task|debug until|pick up|unfinished|still working on)\\b', re.I)
_CODING_FILE_HINTS = re.compile('\\b(fix|debug|implement|patch|refactor|run tests|pytest)\\b.*\\.py\\b|\\.py\\b.*\\b(fix|debug|implement|patch|refactor|tests?)\\b', re.I)
AUTO_MEMORY_MODES = ('off', 'explicit', 'smart')
JOURNAL_LEARN_TAG = 'journal-learn'
GENERIC_AUTO_PATTERNS = ('user asked', 'user wanted', 'the user is', 'assistant (said|replied|explained)', 'conversation about', 'discussed (the|a) topic')

def _profile_name_line(profile = None):
    '''Single canonical name line — env override, then latest profile name tag.'''
    import os
    if not os.getenv('JARVIS_USER_NAME'):
        os.getenv('JARVIS_USER_NAME')
    env_name = ''.strip()
    if env_name:
        return f'''User\'s name is {env_name}.'''
# WARNING: Decompyle incomplete


def resolve_project_namespace(root = None):
    '''Active workspace slug when set, else git-derived namespace.'''
    get_active_slug = get_active_slug
    import jarvis.active_project
    slug = get_active_slug()
    if slug:
        return slug
    return None(root)


def detect_project_namespace(root = None):
    '''Slug from git repo name or project folder.'''
    if not root:
        root
    base = PROJECT_ROOT.resolve()
    
    try:
        r = subprocess.run([
            'git',
            '-C',
            str(base),
            'rev-parse',
            '--show-toplevel'], capture_output = True, text = True, timeout = 3)
        if r.returncode == 0:
            base = Path(r.stdout.strip())
        name = re.sub('[^\\w-]+', '-', base.name.lower()).strip('-')
        if not name:
            name
        return 'default'
    except (OSError, subprocess.TimeoutExpired):
        continue



def system_prompt_block(memory_store = None, *, max_chars):
    '''Stable user context for the system prompt.'''
    filter_trusted_content = filter_trusted_content
    seed_default_strategies = seed_default_strategies
    import jarvis.trust_memory
    seed_default_strategies(memory_store)
    explicit_teaching_system_block = explicit_teaching_system_block
    import jarvis.explicit_teaching
    teach_block = explicit_teaching_system_block(memory_store)
    lines = []
    if teach_block:
        lines.append(teach_block)
        lines.append('')
    corrections_system_block = corrections_system_block
    import jarvis.correction_learning
    correction_block = corrections_system_block(memory_store)
    if correction_block:
        lines.append(correction_block)
        lines.append('')
    lines.append('Persistent user context (trust this over guesses):')
    profile = memory_store.list_entries(namespace = 'profile')
    name_line = _profile_name_line(profile)
    if name_line:
        lines.append(f'''- {name_line}''')
    summary = (lambda .0: pass# WARNING: Decompyle incomplete
)(profile(), None)
    if summary:
        lines.append(f'''- {summary['content']}''')
    else:
        shown = 0
        for p in profile:
            if not p.get('tags'):
                p.get('tags')
            tags = []
            if 'name' in tags:
                continue
            if shown >= 4:
                profile
            else:
                lines.append(f'''- {p['content']}''')
                shown += 1
    for e in memory_store.list_entries(entry_type = 'strategy')[:4]:
        line = filter_trusted_content(e['content'])
        if not line:
            continue
        lines.append(f'''- Rule: {line}''')
    for e in memory_store.list_entries(namespace = 'environment')[:5]:
        line = filter_trusted_content(e['content'])
        if not line:
            continue
        lines.append(f'''- {line}''')
# WARNING: Decompyle incomplete


def find_conflicts(memory_store = None, *, threshold):
    '''Find likely contradictory or duplicate memory pairs.'''
    llm = llm
    import jarvis
    is_cheatsheet_entry = is_cheatsheet_entry
    import jarvis.cheatsheets
# WARNING: Decompyle incomplete


def _normalize_conflict_text(content = None):
    if not content:
        content
    return re.sub('\\s+', ' ', ''.lower().strip())


def _is_internal_journal_mirror(a = None, b = None):
    '''Same journal-learn text stored as both fact and note — not a user conflict.'''
    if _normalize_conflict_text(a.get('content', '')) != _normalize_conflict_text(b.get('content', '')):
        return False
    if not a.get('tags'):
        a.get('tags')
    if not b.get('tags'):
        b.get('tags')
    tags_b = []
    tags_a = []
    if JOURNAL_LEARN_TAG not in tags_a or JOURNAL_LEARN_TAG not in tags_b:
        return False
    return {
        a.get('type'),
        b.get('type')} == {
        'fact',
        'note'}


def _conflict_priority(entry = None):
    '''Higher priority = keep. Explicit teach/correction beats auto; newer beats older.'''
    if not entry.get('tags'):
        entry.get('tags')
    tags = []
    score = 0
    if 'user-corrected' in tags or 'correction-learn' in tags:
        score += 40
    if entry.get('type') in ('teaching', 'strategy', 'preference'):
        score += 20
    if entry.get('type') == 'auto':
        score -= 10
    if 'brain-consolidated' in tags:
        score += 5
    if not entry.get('timestamp'):
        entry.get('timestamp')
    return (score, '')


def auto_resolve_obvious_conflicts(memory_store = None, *, threshold):
    '''Drop obvious duplicate pairs — keep higher-priority or newer entry.'''
    removed = 0
    for conflict in find_conflicts(memory_store, threshold = threshold):
        if conflict.get('kind') not in ('duplicate', 'similar'):
            continue
        b = conflict['b']
        a = conflict['a']
        pb = _conflict_priority(b)
        pa = _conflict_priority(a)
        if pa[0] != pb[0]:
            drop = b if pa[0] > pb[0] else a
        elif pa[1] != pb[1]:
            drop = a if pa[1] >= pb[1] else b
        else:
            drop = b
        if not memory_store.delete_id(drop['id']):
            continue
        removed += 1
    return {
        'removed': removed }


def _looks_contradictory(a = None, b = None):
    pass
# WARNING: Decompyle incomplete


def should_extract_auto_memory(user_msg = None, assistant_msg = None, mode = None):
    if mode == 'off':
        return False
    if mode == 'explicit':
        return bool(re.search("\\b(remember|don't forget|note that|keep in mind)\\b", user_msg, re.I))
    if None.search("\\b(remember|don't forget|note that|keep in mind)\\b", user_msg, re.I):
        return True
    if not re.search('\\?\\s*$', user_msg.strip()) and re.search("\\b(i (?:am|'m)|my name|i prefer|i like|i use|i live|call me)\\b", user_msg, re.I):
        return False
    if len(user_msg.strip()) < 12:
        return False
    return bool(re.search("\\b(i (?:am|'m)|my name|call me|i prefer|i like|i love|i hate|i use|i work|i live)\\b", user_msg, re.I))


def filter_extracted_facts(facts = None, user_msg = None):
    '''Drop low-value auto-extracted facts.'''
    pass
# WARNING: Decompyle incomplete


def build_turn_extraction_text(user_msg = None, assistant_msg = None, *, max_user, max_assistant):
    '''Format a chat turn for memory extraction (user + optional assistant reply).'''
    if not user_msg:
        user_msg
    user = ''.strip()[:max_user]
    if not assistant_msg:
        assistant_msg
    assistant = ''.strip()[:max_assistant]
    if assistant:
        return f'''User: {user}\nAssistant: {assistant}'''


def build_conversation_extraction_text(messages = None, *, max_messages, max_chars):
    '''Format recent dialogue for periodic conversation memory extraction.'''
    pass
# WARNING: Decompyle incomplete


def branch_memory_namespace(branch_id = None):
    '''Per-chat-branch namespace for conversation memory.'''
    if not branch_id:
        branch_id
    if not 'main'.strip():
        'main'.strip()
    bid = 'main'
    return f'''branch:{bid}'''


def branch_summary_text(messages = None, *, max_messages, max_chars):
    '''Compact branch dialogue for upserted branch summary.'''
    blob = build_conversation_extraction_text(messages, max_messages = max_messages, max_chars = max_chars)
    if not blob.strip():
        return ''
    return f'''Conversation summary ({len(blob.splitlines())} turns):\n{blob}'''


def summarize_branch_dialogue(messages = None, *, max_messages, max_chars):
    '''LLM summary of recent branch dialogue; falls back to compact text.'''
    blob = build_conversation_extraction_text(messages, max_messages = max_messages, max_chars = max_chars)
    if not blob.strip():
        return ''
    prompt = f'''Summarize this conversation in 3-5 short factual bullet points. Focus on user preferences, decisions, tasks, and outcomes. No fluff.\n\n{blob[:5000]}'''
    
    try:
        llm = llm
        import jarvis
        summary = llm.ask(llm.general_model(), [
            {
                'role': 'user',
                'content': prompt }]).strip()
        if summary:
            return summary[:4000]
        return branch_summary_text(messages, max_messages = max_messages, max_chars = max_chars)
    except Exception:
        continue



def should_inject_resume_context(message = None, session = None):
    '''Only surface coding resume/checkpoint hints when the user is continuing that work.'''
    is_meta_self_question = is_meta_self_question
    import jarvis.router
    if not message:
        message
    text = ''.strip()
    if text or is_meta_self_question(text):
        return False
# WARNING: Decompyle incomplete


def _journal_date_from_location(location = None):
    if not location:
        location
    m = _JOURNAL_DATE.search('')
    if not m:
        return None
    
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None



def _format_journal_date(d = None):
    return d.strftime('%B ') + str(d.day)


def normalize_journal_memory_text(content = None, *, journal_date):
    """Store journal bullets as stable facts, not relative 'today' phrasing."""
    if not content:
        content
    m = _JOURNAL_MEMORY.match(''.strip())
    if not m:
        if not content:
            content
        return ''.strip()
    body = m.group(2).strip()
    location = None.group(1).strip()
    body = re.sub('^[\\s—\\-–]+', '', body).strip()
    if not journal_date:
        journal_date
    d = _journal_date_from_location(location)
# WARNING: Decompyle incomplete


def contextualize_memory_for_chat(content = None, *, today):
    """Rewrite or drop dated journal memories so past 'today' notes do not confuse chat."""
    if not content:
        content
    text = ''.strip()
    if not text:
        return None
    m = _JOURNAL_MEMORY.match(text)
    if not m:
        return text
    body = m.group(2).strip()
    location = None.group(1).strip()
    journal_day = _journal_date_from_location(location)
    if not today:
        today
    now = datetime.now(timezone.utc).date()
# WARNING: Decompyle incomplete


def build_quick_checkpoint(session = None, messages = None, task_manager = None):
    '''Template checkpoint for shutdown — no LLM call.'''
    filter_trusted_content = filter_trusted_content
    is_test_artifact_path = is_test_artifact_path
    import jarvis.trust_memory
# WARNING: Decompyle incomplete

