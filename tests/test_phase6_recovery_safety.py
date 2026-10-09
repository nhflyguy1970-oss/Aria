"""Regression gates found while recovering Phase 6; only fake agents and temp repos."""
# ruff: noqa: F811
# Imported pytest fixtures are intentionally also named in test parameters.
import os
from pathlib import Path

import pytest
from test_phase5_coding_agents import _register, _run, agents, repo  # noqa: F401

from jarvis.coding_agents import contract, discovery, promotion, runs, workspace


@pytest.mark.parametrize('agent', ['codex', 'claude_code', 'antigravity'])
def test_each_cli_process_cannot_read_or_write_outside(agent, agents, repo, tmp_path):
    secret = tmp_path / 'outside.txt'
    secret.write_text('private\n')
    read_secret = tmp_path / 'private.txt'
    read_secret.write_text('private\n')
    proj = _register(repo, protected=[str(secret)])
    agents.behave(read_outside=str(read_secret), write_outside=str(secret),
                  edits={'calc.py': 'def add(a, b):\n    return a + b  # safe\n'})
    run = _run(agent, proj, 'fix')
    assert run['status'] == contract.VERIFIED
    assert run['result']['agent_report'].startswith('READFAIL')
    assert secret.read_text() == 'private\n'
    assert 'private PID/IPC' in run['receipt']['sandbox']
    assert run['receipt']['protected_before'] == run['receipt']['protected_after']


@pytest.mark.parametrize('agent', ['codex', 'claude_code', 'antigravity'])
def test_read_only_is_enforced_for_each_cli(agent, agents, repo):
    agents.behave(edits={'calc.py': 'compromised\n'})
    run = _run(agent, _register(repo), 'explain', mode=discovery.READ_ONLY)
    assert not run['result']['success']
    assert not run['result']['changed']['files']
    assert (Path(run['workspace']) / 'calc.py').read_bytes() == (repo / 'calc.py').read_bytes()


def test_host_process_root_is_invisible(agents, repo, tmp_path):
    secret = tmp_path / 'outside.txt'
    secret.write_text('private\n')
    agents.behave(read_outside=f'/proc/{os.getpid()}/root{secret}')
    run = _run('codex', _register(repo), 'explain', mode=discovery.READ_ONLY)
    assert run['result']['agent_report'].startswith('READFAIL')


@pytest.mark.parametrize('agent', ['codex', 'claude_code', 'antigravity'])
def test_agent_cannot_contact_host_loopback(agent, agents, repo):
    import socket
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        agents.behave(connect_host=list(listener.getsockname()))
        run = _run(agent, _register(repo), 'look', mode=discovery.READ_ONLY)
    assert run['result']['agent_report'].startswith('NETFAIL')


@pytest.mark.parametrize('agent,auth', [('codex', 'auth.json'), ('claude_code', '.credentials.json'),
                                      ('antigravity', 'oauth_creds.json')])
def test_agent_state_is_private_and_owner_history_is_hidden(agent, auth, agents, repo, monkeypatch):
    state = agents.tmp / 'owner-state'
    state.mkdir()
    (state / auth).write_text('fake sign-in fixture\n')
    history = state / 'history.jsonl'
    history.write_text('other project private history\n')
    monkeypatch.setattr(workspace, 'agent_state_dirs', lambda a: [str(state)])
    agents.behave(read_outside=str(history), touch_config=str(state / auth))
    run = _run(agent, _register(repo), 'look', mode=discovery.READ_ONLY)
    assert run['result']['agent_report'].startswith('READFAIL')
    assert history.read_text() == 'other project private history\n'
    assert (state / auth).read_text() == 'fake sign-in fixture\n'
    copied = Path(run['workspace']).parent / f"run-{run['id']}.out" / 'state/0' / auth
    assert 'agent was here' in copied.read_text()
    assert copied.stat().st_mode & 0o777 == 0o600


def test_missing_bwrap_refuses_codex_without_launch(agents, repo, monkeypatch):
    def refuse(*a, **k):
        raise workspace.WorkspaceError('sandbox unavailable')
    monkeypatch.setattr(workspace, 'sandbox_argv', refuse)
    run = _run('codex', _register(repo), 'explain', mode=discovery.READ_ONLY)
    assert run['status'] == contract.REFUSED
    assert not run['result']['success']


def test_parser_failure_finishes_run_and_preserves_launch_evidence(agents, repo, monkeypatch):
    original = runs.adapters.parse
    def broken(*a, **k):
        raise ValueError('damaged output parser')
    monkeypatch.setattr(runs.adapters, 'parse', broken)
    proj = _register(repo)
    run = _run('codex', proj, 'look', mode=discovery.READ_ONLY)
    assert run['status'] == contract.FAILED
    assert run['receipt']['plan_hash']
    assert run['receipt']['sandbox']
    assert Path(run['receipt']['output_logs']['stdout']).is_file()
    assert Path(run['receipt']['output_logs']['stderr']).is_file()
    monkeypatch.setattr(runs.adapters, 'parse', original)
    assert _run('codex', proj, 'look', mode=discovery.READ_ONLY)['status'] == contract.COMPLETED


def test_verification_toolchain_is_available_and_read_only(agents, repo):
    import shlex
    import sys
    venv = repo / 'venv/bin'
    venv.mkdir(parents=True)
    (venv / 'python').symlink_to(sys.executable)
    marker = repo / 'venv/marker'
    marker.write_text('owner toolchain\n')
    ws = workspace.prepare(str(repo), 'toolchain-check')
    python = Path(ws['workspace']) / 'venv/bin/python'
    check = workspace.run_tests(ws['workspace'], shlex.join([str(python), '-c', 'from calc import add; assert add(2, 2) == 4']))
    assert check['passed']
    code = f'from pathlib import Path; Path({str(marker)!r}).write_text("changed")'
    check = workspace.run_tests(ws['workspace'], shlex.join([str(python), '-c', code]))
    assert not check['passed']
    assert marker.read_text() == 'owner toolchain\n'
    assert not workspace.collect_changes(ws['workspace'], ws['base_commit'])['files']


@pytest.mark.parametrize('in_place', [False, True])
def test_verification_cannot_read_another_project(in_place, tmp_path):
    import shlex
    root = Path(__file__).resolve().parents[1]
    secret = root / 'scratch' / f'verification-private-{tmp_path.name}.txt'
    secret.parent.mkdir(parents=True, exist_ok=True)
    secret.write_text('private verification data\n')
    clone = tmp_path / 'clone'
    clone.mkdir()
    try:
        runner = promotion.run_tests_in_place if in_place else workspace.run_tests
        result = runner(str(clone), f'test ! -r {shlex.quote(str(secret))}')
        assert result['passed'], result
    finally:
        secret.unlink()


def test_agent_modified_toolchain_symlink_does_not_authorize_new_reads(agents, repo):
    import shlex
    root = Path(__file__).resolve().parents[1]
    ws = workspace.prepare(str(repo), 'untrusted-toolchain')
    # This agent-controlled symlink used to expose all of ARIA's source/data.
    (Path(ws['workspace']) / 'venv').symlink_to(root, target_is_directory=True)
    result = workspace.run_tests(ws['workspace'], f'test ! -r {shlex.quote(str(root / "jarvis/config.py"))}')
    assert result['passed'], result


def test_approved_plan_tampering_never_executes(agents, repo):
    p = runs.create_plan(agent='codex', project=_register(repo)['slug'], mode=discovery.READ_ONLY, task='look')
    runs.approve(p['id'], token=runs.approval_token(p['id']), via='test')
    with runs._conn() as c:
        c.execute('UPDATE plans SET task=? WHERE id=?', ('unauthorized', p['id']))
    with pytest.raises(runs.AgentRunError, match='changed after approval'):
        runs.start(p['id'], background=False)
    assert not runs.list_runs()


def test_normalized_task_can_be_approved(agents, repo):
    p = runs.create_plan(agent='codex', project=_register(repo)['slug'], mode=discovery.READ_ONLY, task=' look \n')
    assert runs.approve(p['id'], token=runs.approval_token(p['id']), via='test')['task'] == 'look'


@pytest.mark.parametrize('field,value', [
    ('path', '/tmp/different-authorized-source'),
    ('test_command', 'changed-command'),
    ('protected_paths', ['additional-protected']),
    ('allowed_agents', ['claude_code']),
])
@pytest.mark.parametrize('approved', [False, True])
def test_project_registration_changes_invalidate_run_approval(agents, repo, monkeypatch, field, value, approved):
    from jarvis.coding_agents import projects
    proj = _register(repo)
    plan = runs.create_plan(agent='codex', project=proj['slug'], mode=discovery.READ_ONLY, task='look')
    if approved:
        runs.approve(plan['id'], token=runs.approval_token(plan['id']), via='test')
    original = projects.get
    monkeypatch.setattr(projects, 'get', lambda slug: {**original(slug), field: value})
    with pytest.raises(runs.AgentRunError, match='project scope changed'):
        if approved:
            runs.start(plan['id'], background=False)
        else:
            runs.approve(plan['id'], token=runs.approval_token(plan['id']), via='test')
    assert not runs.list_runs()


def test_legacy_unbound_approval_cannot_execute(agents, repo):
    plan = runs.create_plan(agent='codex', project=_register(repo)['slug'], mode=discovery.READ_ONLY, task='look')
    runs.approve(plan['id'], token=runs.approval_token(plan['id']), via='test')
    with runs._conn() as conn:
        conn.execute('UPDATE plans SET project_scope=NULL WHERE id=?', (plan['id'],))
    with pytest.raises(runs.AgentRunError):
        runs.start(plan['id'], background=False)
    assert not runs.list_runs()


def test_legacy_schema_migration_preserves_approval_without_granting_scope(agents, repo):
    plan = runs.create_plan(agent='codex', project=_register(repo)['slug'], mode=discovery.READ_ONLY, task='legacy')
    runs.approve(plan['id'], token=runs.approval_token(plan['id']), via='test')
    with runs._conn() as conn:
        conn.execute('ALTER TABLE plans DROP COLUMN project_scope')
    restored = runs.get_plan(plan['id'])
    assert restored['task'] == 'legacy' and restored['status'] == runs.APPROVED
    assert restored['project_scope'] is None
    with pytest.raises(runs.AgentRunError):
        runs.start(plan['id'], background=False)
    assert not runs.list_runs()


def test_project_scope_rechecked_after_reservation_before_clone(agents, repo, monkeypatch):
    from jarvis.coding_agents import projects
    from jarvis.missions import engine
    proj = _register(repo)
    plan = runs.create_plan(agent='codex', project=proj['slug'], mode=discovery.READ_ONLY, task='look')
    runs.approve(plan['id'], token=runs.approval_token(plan['id']), via='test')
    reserved = runs._reserve_run(plan['id'], engine)
    original = projects.get
    monkeypatch.setattr(projects, 'get', lambda slug: {**original(slug), 'path': '/tmp/changed-after-reservation'})
    monkeypatch.setattr(workspace, 'prepare', lambda *a, **k: pytest.fail('unapproved source cloned'))
    try:
        result = runs._execute(runs.get_run(reserved['run_id']))
        assert result['status'] == contract.REFUSED
        assert 'project scope changed' in result['reason']
        assert runs.get_run(reserved['run_id'])['receipt']['plan_hash']
    finally:
        runs._owned.discard(reserved['run_id'])


def test_detected_live_boundary_failure_persistently_quarantines_adapter(agents, repo, monkeypatch):
    import json

    from jarvis.coding_agents import runtime
    monkeypatch.setattr(runtime, 'FILE', agents.tmp / 'runtime.json')
    original = workspace.sandbox_argv
    def deliberately_broken_readonly_boundary(*args, **kwargs):
        # Inject a failed boundary only in a disposable fixture. Actual edits
        # violate the requested read-only contract and must disable the adapter.
        return original(*args, **{**kwargs, 'read_only': False})
    monkeypatch.setattr(workspace, 'sandbox_argv', deliberately_broken_readonly_boundary)
    agents.behave(edits={'calc.py': 'def add(a,b): return a+b # unauthorized\n'})
    run = _run('codex', _register(repo), 'review only', mode=discovery.READ_ONLY)
    assert run['status'] == contract.VIOLATION
    record = json.loads(runtime.FILE.read_text())['codex']
    assert record['state'] == 'disabled' and run['id'] in record['reason']
    assert (repo / 'calc.py').read_text() == 'def add(a, b):\n    return a + b\n'


@pytest.mark.parametrize('broken_database', [False, True])
def test_durable_violation_or_unreadable_history_refuses_otherwise_valid_certificate(tmp_path, monkeypatch, broken_database):
    import hashlib
    import json
    import sqlite3

    from jarvis.coding_agents import runtime
    monkeypatch.setattr(runtime, 'FILE', tmp_path / 'runtime.json')
    monkeypatch.setattr(runtime, 'DATA_DIR', tmp_path)
    binary = tmp_path / 'binary'
    binary.write_text('fixture executable, never launched')
    record = {'state':'verified', 'backend':'oci', 'version':'1',
              'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
              'policy_sha256':runtime.policy_hash(), 'boundary_history_reviewed':True}
    runtime.FILE.write_text(json.dumps({'codex':record}))
    assert runtime.compatibility('codex', str(binary), '1')['state'] == 'verified'
    database = tmp_path / 'coding_agents.db'
    if broken_database:
        database.write_bytes(b'broken durable history')
    else:
        with sqlite3.connect(database) as conn:
            conn.execute('CREATE TABLE runs (id TEXT, agent TEXT, status TEXT)')
            conn.execute('INSERT INTO runs VALUES (?,?,?)', ('unreviewed-run', 'codex', contract.VIOLATION))
    assert runtime.compatibility('codex', str(binary), '1')['state'] == 'disabled'


def _promotion(agents, repo):
    agents.behave(edits={'calc.py': 'def add(a, b):\n    return a + b  # reviewed\n'})
    r = _run('codex', _register(repo), 'tidy')
    return promotion.propose(r['id'])


def test_verification_unavailable_after_apply_restores_original(agents, repo, monkeypatch):
    p = _promotion(agents, repo)
    monkeypatch.setattr(promotion, 'run_tests_in_place', lambda *a, **k: {'ran': False, 'reason': 'missing sandbox'})
    out = promotion.apply(p['id'], token=promotion.approval_token(p['id']), via='test')
    assert out['status'] == promotion.ROLLED_BACK
    assert (repo / 'calc.py').read_text() == 'def add(a, b):\n    return a + b\n'


def test_verification_exception_has_durable_rollback_receipt(agents, repo, monkeypatch):
    p = _promotion(agents, repo)
    def broken(*a, **k):
        raise OSError('test process unavailable')
    monkeypatch.setattr(promotion, 'run_tests_in_place', broken)
    out = promotion.apply(p['id'], token=promotion.approval_token(p['id']), via='test')
    assert out['status'] == promotion.ROLLED_BACK
    assert 'verification unavailable' in out['result']['tests_after_apply']['error']
    assert (repo / 'calc.py').read_text() == 'def add(a, b):\n    return a + b\n'


def test_destination_symlink_created_after_review_is_refused(agents, repo, tmp_path):
    p = _promotion(agents, repo)
    outside = tmp_path / 'owner-file'
    outside.write_text('mine\n')
    (repo / 'calc.py').unlink()
    (repo / 'calc.py').symlink_to(outside)
    out = promotion.apply(p['id'], token=promotion.approval_token(p['id']), via='test')
    assert out['status'] == promotion.FAILED
    assert outside.read_text() == 'mine\n'


def test_automatic_rollback_preserves_owner_edit_during_tests(agents, repo, monkeypatch):
    p = _promotion(agents, repo)
    def edit_and_fail(*a, **k):
        (repo / 'calc.py').write_text('owner edit during verification\n')
        return {'ran': True, 'passed': False}
    monkeypatch.setattr(promotion, 'run_tests_in_place', edit_and_fail)
    out = promotion.apply(p['id'], token=promotion.approval_token(p['id']), via='test')
    assert out['status'] == promotion.FAILED
    assert 'owner edit left untouched' in out['result']['reason']
    assert (repo / 'calc.py').read_text() == 'owner edit during verification\n'


def test_recovery_does_not_take_over_another_live_process(agents, repo):
    p = _promotion(agents, repo)
    promotion._update(p['id'], status=promotion.APPLYING, owner_pid=os.getpid())
    assert p['id'] not in promotion.recover_interrupted()
    assert promotion.get(p['id'])['status'] == promotion.APPLYING


def test_run_recovery_does_not_interrupt_live_supervisor(agents, repo):
    proj = _register(repo)
    p = runs.create_plan(agent='codex', project=proj['slug'], mode=discovery.READ_ONLY, task='x')
    with runs._conn() as c:
        c.execute("INSERT INTO runs (id, plan_id, agent, project, mode, task, status, owner_pid, pid) "
                  "VALUES ('live', ?, 'codex', ?, 'read_only', 'x', 'running', ?, 999999)",
                  (p['id'], proj['slug'], os.getpid()))
    assert 'live' not in runs.recover_interrupted()
    assert runs.get_run('live')['status'] == runs.RUNNING


def test_launch_reservation_prevents_two_concurrent_agents(agents, repo, monkeypatch):
    import threading

    from jarvis.missions import engine
    proj = _register(repo)
    plans = [runs.create_plan(agent='codex', project=proj['slug'], mode=discovery.READ_ONLY, task='x') for _ in range(2)]
    for p in plans:
        runs.approve(p['id'], token=runs.approval_token(p['id']), via='test')
    entered, proceed = threading.Event(), threading.Event()
    original = engine.create_mission
    def delayed(*a, **k):
        entered.set()
        assert proceed.wait(5)
        return original(*a, **k)
    monkeypatch.setattr(engine, 'create_mission', delayed)
    result = []
    thread = threading.Thread(target=lambda: result.append(runs.start(plans[0]['id'], background=False)))
    thread.start()
    try:
        assert entered.wait(5)
        with pytest.raises(runs.AgentRunError, match='in progress'):
            runs.start(plans[1]['id'], background=False)
    finally:
        proceed.set()
        thread.join(10)
    assert len(result) == 1 and len(runs.list_runs()) == 1


def test_agent_last_message_symlink_cannot_read_host_data(tmp_path):
    from jarvis.coding_agents import adapters
    secret = tmp_path / 'secret.txt'
    secret.write_text('PRIVATE_OWNER_VALUE')
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'last_message.txt').symlink_to(secret)
    report = adapters.parse('codex', '{"type":"item.completed","item":{"type":"agent_message","text":"SAFE"}}', '', str(output))
    assert report.final_message == 'SAFE'


def test_agent_git_filter_cannot_escape_during_evidence_collection(agents, repo, tmp_path, monkeypatch):
    import subprocess

    from test_phase5_coding_agents import _register

    from jarvis.coding_agents import workspace
    proj = _register(repo)
    ws = workspace.prepare(proj['path'], 'hostile_git')
    target = tmp_path / 'outside-filter.txt'
    target.write_text('KEEP')
    clone = Path(ws['workspace'])
    # Simulate a hostile agent-generated clean filter. The supervisor must
    # never execute it on the unrestricted host when staging the diff.
    subprocess.run(['git','config','filter.escape.clean',f'echo BAD > {target}; cat'],cwd=clone,check=True)
    (clone/'.gitattributes').write_text('calc.py filter=escape\n')
    (clone/'calc.py').write_text('def add(a,b): return a+b\n')
    # Receipts can outlive a change to the configured workspace root.
    monkeypatch.setenv("JARVIS_AGENT_WORKSPACES", str(tmp_path / "new-workspace-root"))
    workspace.collect_changes(str(clone),ws['base_commit'])
    assert target.read_text()=='KEEP'


def test_antigravity_actual_oauth_filename_is_copied_without_shared_profile(tmp_path):
    import json
    source = tmp_path / 'source'
    source.mkdir()
    auth = source / 'antigravity-cli' / 'antigravity-oauth-token'
    auth.parent.mkdir()
    auth.write_text(json.dumps({'access_token': 'fixture-token-is-private'}))
    (source / 'history.json').write_text('owner history')
    output = tmp_path / 'output'
    output.mkdir()
    bindings = workspace.private_agent_state('antigravity', output, [str(source)])
    copied = Path(bindings[0][0])
    assert (copied / 'antigravity-cli/antigravity-oauth-token').is_file()
    assert not (copied / 'history.json').exists()
    assert runs._private_tokens(bindings) == {'fixture-token-is-private'}


def test_private_token_scan_rejects_agent_replaced_state_symlink(tmp_path):
    import json
    original = tmp_path / 'original'
    original.mkdir()
    (original / 'auth.json').write_text(json.dumps({'access_token': 'OWNER_PRIVATE_TOKEN'}))
    replaced = tmp_path / 'replaced'
    replaced.symlink_to(original, target_is_directory=True)
    assert runs._private_tokens([(str(replaced), '/home/fixture/.codex')]) == set()


def test_promotion_capture_disables_agent_external_diff(agents, repo):
    import subprocess
    agents.behave(edits={'calc.py': 'def add(a, b):\n    return a + b  # repaired\n'})
    run = _run('codex', _register(repo), 'fixture')
    assert run['status'] == contract.VERIFIED
    clone = Path(run['workspace'])
    helper = clone / 'external-diff.sh'
    helper.write_text('#!/bin/sh\ntouch external-diff-executed\necho fake_patch\n')
    subprocess.run(['git', 'config', 'diff.external', f'sh {helper}'], cwd=clone, check=True)
    patch, manifest = promotion.capture(run)
    assert not (clone / 'external-diff-executed').exists()
    assert patch.startswith(b'diff --git ') and any(f['path']=='calc.py' for f in manifest)
