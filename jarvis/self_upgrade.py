# Source Generated with Decompyle++
# File: self_upgrade.cpython-312.pyc (Python 3.12)

'''Semi-automatic self-upgrading code — git branch, change, test, report, merge on approval.'''
from __future__ import annotations
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any
from jarvis.config import PROJECT_ROOT
from jarvis.upgrade_wizard import get_session, normalize_rel_path, save_session, verify_proposal
log = logging.getLogger('jarvis.self_upgrade')
_SELF_UPGRADE = re.compile('^(?:please\\s+)?(?:self[- ]?upgrad(?:e|ing)(?:\\s+code)?[:\\s]+.+|run\\s+self[- ]?upgrade[:\\s]+.+)', re.I | re.S)

def pipeline_enabled():
    return os.getenv('JARVIS_SELF_UPGRADE_PIPELINE', '1').lower() not in ('0', 'false', 'off', 'no')


def is_self_upgrade_task(message = None):
    if not message:
        message
    text = ''.strip()
    if not text:
        return False
    if _SELF_UPGRADE.match(text):
        return True
    lower = text.lower()
    return bool(re.search('\\b(self[- ]?upgrad(?:e|ing)(?:\\s+code)?|run\\s+self[- ]?upgrade\\s+pipeline)\\b', lower))


def parse_self_upgrade_task(message = None):
    if not message:
        message
    text = ''.strip()
    for pat in ('^self[- ]?upgrad(?:e|ing)(?:\\s+code)?[:\\s]+(.+)$', '^run\\s+self[- ]?upgrade(?:\\s+pipeline)?[:\\s]+(.+)$'):
        m = re.match(pat, text, re.I | re.S)
        if not m:
            continue
        
        return ('^self[- ]?upgrad(?:e|ing)(?:\\s+code)?[:\\s]+(.+)$', '^run\\s+self[- ]?upgrade(?:\\s+pipeline)?[:\\s]+(.+)$'), m.group(1).strip()
    if not re.sub('^(please\\s+)?(self[- ]?upgrad(?:e|ing)(?:\\s+code)?|run\\s+self[- ]?upgrade)[:\\s]*', '', text, flags = re.I).strip():
        re.sub('^(please\\s+)?(self[- ]?upgrad(?:e|ing)(?:\\s+code)?|run\\s+self[- ]?upgrade)[:\\s]*', '', text, flags = re.I).strip()
    return text


def _slugify(text = None):
    if not text:
        text
    s = re.sub('[^\\w\\s-]', '', ''.lower())
    s = re.sub('[\\s_]+', '-', s).strip('-')
    if not s[:36]:
        s[:36]
    return 'upgrade'


def branch_name_for_task(task = None):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')
    return f'''aria/upgrade-{_slugify(task)}-{stamp}'''


def _abort_branch(base_branch = None, upgrade_branch = None):
    checkout_branch = checkout_branch
    delete_branch = delete_branch
    import jarvis.git_util
    notes = []
    (ok, out) = checkout_branch(base_branch)
    notes.append(out if ok else f'''checkout failed: {out}''')
    (ok, out) = delete_branch(upgrade_branch, force = True)
    if ok:
        notes.append(out)
        return notes
    None(f'''{out}''')
    return notes


def run_pipeline(assistant = None, task = None, *, max_steps):
    '''Create branch → propose → apply → commit → test → report (no merge).'''
    commit = commit
    create_branch = create_branch
    current_branch = current_branch
    has_local_changes = has_local_changes
    is_repo = is_repo
    import jarvis.git_util
    if not task:
        task
    task = ''.strip()
    if not task:
        return {
            'ok': False,
            'message': 'Describe the self-upgrade — e.g. `self upgrade: add /api/ping`.' }
    if not None():
        return {
            'ok': False,
            'message': 'Self-upgrade pipeline disabled (`JARVIS_SELF_UPGRADE_PIPELINE=0`).' }
    if not is_repo():
        return {
            'ok': False,
            'message': 'Self-upgrade pipeline needs a git repository. Initialize git or use manual **upgrade jarvis:** flow.' }
    if has_local_changes():
        return {
            'ok': False,
            'message': 'Working tree has uncommitted changes. Commit or stash before running self-upgrade.' }
    if not current_branch():
        current_branch()
    base_branch = 'main'
    upgrade_branch = branch_name_for_task(task)
    branch_msg = create_branch(upgrade_branch)
    if branch_msg.startswith('ERROR:'):
        return {
            'ok': False,
            'message': branch_msg }
# WARNING: Decompyle incomplete


def merge_pipeline(assistant = None, *, force):
    checkout_branch = checkout_branch
    current_branch = current_branch
    delete_branch = delete_branch
    merge_branch = merge_branch
    import jarvis.git_util
    if not get_session():
        get_session()
    session = { }
    if not session.get('pipeline'):
        return {
            'ok': False,
            'message': 'No self-upgrade pipeline session. Run **self upgrade: …** first.' }
    if not None.get('branch'):
        None.get('branch')
    branch = ''.strip()
    if not session.get('base_branch'):
        session.get('base_branch')
        if not current_branch():
            current_branch()
    base = 'main'.strip()
    if not branch:
        return {
            'ok': False,
            'message': 'Pipeline session missing upgrade branch.' }
    if not None.get('step') != 'awaiting_merge' and force:
        return {
            'ok': False,
            'message': f'''Upgrade is not ready to merge (step: `{session.get('step')}`). Tests must pass first, or say **merge upgrade anyway** to force.''' }
    if not None.get('verified') and force:
        return {
            'ok': False,
            'message': 'Tests did not pass. Say **merge upgrade anyway** to force merge.' }
    (ok, msg) = merge_branch(branch, base = base)
    if not ok:
        return {
            'ok': False,
            'message': f'''Merge failed: {msg}''' }
    delete_branch(branch, force = True)
    session['step'] = 'merged'
    session['merged'] = True
    save_session(session)
    restart = ''
    requires_jarvis_restart = requires_jarvis_restart
    import jarvis.upgrade_wizard
    if not assistant._upgrade_proposal(session.get('proposal_id')):
        assistant._upgrade_proposal(session.get('proposal_id'))
    proposal = { }
    if not proposal.get('files'):
        proposal.get('files')
    if requires_jarvis_restart([]):
        assistant_name = assistant_name
        import jarvis.branding
        restart = f'''\n\n**Restart {assistant_name()}** to load server/GUI changes.'''
    return {
        'ok': True,
        'message': f'''**Merged** `{branch}` → `{base}`.\n\n{msg}{restart}\n\nSnapshot `{session.get('snapshot_id', '')}` kept for rollback if needed.''',
        'type': 'self_upgrade_merged',
        'upgrade_wizard': True,
        'pipeline': True,
        'branch': branch,
        'base_branch': base }


def abort_pipeline(assistant = None):
    rollback_snapshot = rollback_snapshot
    import jarvis.upgrade_wizard
    if not get_session():
        get_session()
    session = { }
    if not session.get('pipeline'):
        return {
            'ok': False,
            'message': 'No active self-upgrade pipeline to abort.' }
    if not None.get('branch'):
        None.get('branch')
    branch = ''.strip()
    if not session.get('base_branch'):
        session.get('base_branch')
    base = 'main'.strip()
    notes = []
    if session.get('snapshot_id'):
        (ok, msg, _restored) = rollback_snapshot(session.get('snapshot_id'))
        if ok:
            notes.append(msg)
    if branch:
        notes.extend(_abort_branch(base, branch))
    session['step'] = 'aborted'
    session['aborted'] = True
    save_session(session)
    return {
        'ok': True,
        'message': '**Self-upgrade aborted.**\n\n' + '\n'.join(notes),
        'type': 'self_upgrade_aborted',
        'pipeline': True }


def is_merge_command(message = None):
    if not message:
        message
    lower = ''.lower()
    return bool(re.search('\\b(merge upgrade|approve upgrade|approve merge)\\b', lower))


def is_abort_command(message = None):
    if not message:
        message
    lower = ''.lower()
    return bool(re.search('\\b(abort upgrade|cancel upgrade|discard upgrade branch)\\b', lower))


def merge_force(message = None):
    if not message:
        message
    return bool(re.search('\\b(anyway|force)\\b', ''.lower()))

