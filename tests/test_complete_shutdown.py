"""Focused lifecycle coverage using real disposable SQLite/flock processes."""
import fcntl
import os
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from jarvis import shutdown

@pytest.fixture
def lifecycle(tmp_path, monkeypatch):
    root = tmp_path/'aria'; root.mkdir(); data=root/'data'; data.mkdir()
    main=root/'main.py'
    main.write_text('''import fcntl,os,signal,sqlite3,sys,time
from pathlib import Path
root=Path(__file__).parent; data=root/'data'; role=sys.argv[1]
lock=(data/(role+'.lock')).open('a+');fcntl.flock(lock,fcntl.LOCK_EX)
conn=sqlite3.connect(data/(role+'.db'));conn.execute('pragma journal_mode=wal')
conn.execute('create table if not exists preserved(v text)');conn.execute("insert into preserved values ('existing memory')");conn.commit()
def close(*args):
 conn.close();fcntl.flock(lock,fcntl.LOCK_UN);lock.close();sys.exit(0)
signal.signal(signal.SIGTERM,close)
(data/(role+'.ready')).touch()
while True:time.sleep(.05)
''')
    monkeypatch.setattr(shutdown,'PROJECT_ROOT',root)
    monkeypatch.setattr(shutdown,'DATA_DIR',data)
    monkeypatch.setattr(shutdown,'QUIT_FLAG',data/'quit_aria.request')
    processes=[]
    def spawn(role):
        ready=data/(role+'.ready');ready.unlink(missing_ok=True)
        p=subprocess.Popen([sys.executable,str(main),role],cwd=root)
        processes.append(p)
        deadline=time.monotonic()+5
        while not ready.exists():
            assert p.poll() is None
            assert time.monotonic()<deadline
            time.sleep(.02)
        return p
    yield root,data,spawn,processes
    for p in processes:
        if p.poll() is None:p.terminate()
        p.wait(timeout=5)


def test_complete_quit_closes_sqlite_and_locks_then_explicit_restart(lifecycle,monkeypatch):
    from jarvis import launch_ownership
    root,data,spawn,processes=lifecycle
    tray=spawn('tray');server=spawn('serve')
    monkeypatch.setattr(launch_ownership,'systemd_unit_installed',lambda:True)
    def stop_unit():
        assert tray.poll() is not None  # Watchdog owner stops first.
        server.terminate();server.wait(timeout=5);return True
    monkeypatch.setattr(launch_ownership,'systemd_stop',stop_unit)
    assert shutdown.quit_completely()['ok']
    assert shutdown.quit_requested()
    for role in ('tray','serve'):
        with (data/(role+'.lock')).open('r+') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        conn=sqlite3.connect(data/(role+'.db'))
        assert conn.execute('pragma quick_check').fetchone()==('ok',)
        assert conn.execute('select v from preserved').fetchall()==[('existing memory',)]
        conn.close()
    # Explicit startup clears the fence and the preserved DB remains writable.
    shutdown.clear_quit();assert not shutdown.quit_requested()
    restarted=spawn('serve');restarted.terminate();restarted.wait(timeout=5)
    conn=sqlite3.connect(data/'serve.db')
    assert conn.execute('select count(*) from preserved').fetchone()==(2,)
    conn.close()


def test_intentional_quit_suppresses_watchdog_and_systemd_restart(lifecycle,monkeypatch):
    from jarvis.watchdog import ServerWatchdog
    from jarvis import launch_ownership
    callback=Mock();control=Mock(return_value=SimpleNamespace(returncode=0,stdout=''))
    monkeypatch.setattr(launch_ownership,'_systemctl',control)
    shutdown.mark_quit()
    watchdog=ServerWatchdog(on_restart=callback)
    for _ in range(4):watchdog._restart_server()
    callback.assert_not_called()
    assert not launch_ownership.systemd_start()
    assert not launch_ownership.systemd_restart()
    control.assert_not_called()
    shutdown.clear_quit()
    assert launch_ownership.systemd_start()
    assert launch_ownership.systemd_restart()
    assert control.call_count==2


def test_pid_reuse_or_foreign_process_is_not_signalled(lifecycle,monkeypatch):
    _,_,spawn,_=lifecycle;p=spawn('tray')
    identity=shutdown.process_identity(p.pid)
    assert identity and identity[0]=='tray'
    shutdown.stop_processes({p.pid:('tray','wrong-start-time')},timeout=.05)
    assert p.poll() is None
    assert shutdown.process_identity(os.getpid()) is None


def test_uncooperative_process_fails_without_sigkill(lifecycle,monkeypatch):
    monkeypatch.setattr(shutdown,'process_identity',lambda pid:('tray','123'))
    signals=[];monkeypatch.setattr(shutdown.os,'kill',lambda pid,sig:signals.append(sig))
    with pytest.raises(RuntimeError,match='no forced termination'):
        shutdown.stop_processes({999999:('tray','123')},timeout=.01)
    assert signals==[signal.SIGTERM]
    assert signal.SIGKILL not in signals


def test_open_database_is_a_shutdown_failure(lifecycle):
    _,data,_,_=lifecycle
    conn=sqlite3.connect(data/'held.db')
    try:
        with pytest.raises(RuntimeError,match='Database handle remains'):
            shutdown.verify_closed()
    finally:conn.close()
    shutdown.verify_closed()


def test_owner_security_and_origin_gate_fail_closed(monkeypatch):
    from jarvis.security.owner import provider_credentials
    owner=SimpleNamespace(authorize=Mock(return_value={'ok':False,'reason':'locked'}))
    monkeypatch.setattr(provider_credentials,'bound_owner_service',lambda:owner)
    assert not shutdown.authorize_quit('192.0.2.1','','http://127.0.0.1:8765')['ok']
    assert not shutdown.authorize_quit('127.0.0.1','https://evil.test','http://127.0.0.1:8765')['ok']
    owner.authorize.assert_not_called()
    assert not shutdown.authorize_quit('127.0.0.1','http://127.0.0.1:8765','http://127.0.0.1:8765')['ok']
    owner.authorize.return_value={'ok':True}
    assert shutdown.authorize_quit('127.0.0.1','','http://127.0.0.1:8765')['ok']


def test_acm_cleanup_flushes_then_closes_without_creating_engine(monkeypatch):
    from aria_core import acm_bridge
    calls=[]
    durable=SimpleNamespace(close=lambda:calls.append('close'))
    eng=SimpleNamespace(durable=durable,flush=lambda **kw:calls.append(kw['kind']))
    monkeypatch.setattr(acm_bridge,'_ENGINE',eng)
    monkeypatch.setattr(acm_bridge,'get_engine',Mock(side_effect=AssertionError('must not create engine')))
    shutdown.close_acm()
    assert calls==['shutdown','close']
    assert acm_bridge._ENGINE is None
    shutdown.close_acm();assert calls==['shutdown','close']


@pytest.mark.parametrize('via_signal',[False,True])
def test_tray_quit_and_sigterm_clean_up_before_icon_stops(monkeypatch,via_signal):
    from jarvis import tray
    calls=[];menu_items=[];handlers={};completed=[]
    class Item:
        def __init__(self,title,callback,**kw):self.title=title;self.callback=callback;menu_items.append(self)
    class Icon:
        def __init__(self,*args):pass
        def notify(self,*args):pass
        def stop(self):calls.append('stop');completed.append(True)
        def run(self):
            if via_signal:handlers[signal.SIGTERM](signal.SIGTERM,None)
            else:next(i for i in menu_items if i.title=='Quit ARIA Completely').callback(self,None)
            deadline=time.monotonic()+2
            while not completed:
                assert time.monotonic()<deadline;time.sleep(.01)
    class Menu:
        SEPARATOR=object()
        def __init__(self,*args):pass
    monkeypatch.setitem(sys.modules,'pystray',SimpleNamespace(Menu=Menu,MenuItem=Item,Icon=Icon))
    monkeypatch.setattr(tray,'_create_icon_image',lambda:None)
    monkeypatch.setattr(tray.signal,'signal',lambda sig,handler:handlers.setdefault(sig,handler))
    def cleanup(*,complete):calls.append(('cleanup',complete))
    tray.run_tray_app('http://127.0.0.1',on_quit=cleanup)
    assert calls==[('cleanup',not via_signal),'stop']


def test_quit_coordinator_failure_is_not_reported_as_success(lifecycle,monkeypatch):
    monkeypatch.setattr(shutdown.subprocess,'run',lambda *a,**kw:SimpleNamespace(returncode=1))
    with pytest.raises(RuntimeError,match='independent quit coordinator'):
        shutdown.request_quit()
    assert not shutdown.quit_requested()


def test_real_acm_flush_close_preserves_durable_snapshot(tmp_path,monkeypatch):
    from aria_core import acm_bridge
    from aria_acm.acm.api.engine import CognitiveEngine
    path=tmp_path/'acm.db'
    eng=CognitiveEngine(agent_id='shutdown-fixture',persist_path=str(path),auto_persist=False)
    monkeypatch.setattr(acm_bridge,'_ENGINE',eng)
    shutdown.close_acm()
    with pytest.raises(sqlite3.ProgrammingError):eng.durable.backend._conn.execute('select 1')
    conn=sqlite3.connect(path)
    assert conn.execute('pragma quick_check').fetchone()==('ok',)
    assert conn.execute("select count(*) from snapshots where kind='shutdown'").fetchone()[0]>=1
    conn.close()


def test_desktop_quit_endpoint_security_and_scheduling(monkeypatch):
    # Execute the actual registered endpoint without starting other products.
    import ast
    from fastapi import FastAPI,Request
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient
    source=Path(__file__).parents[1]/'jarvis/gui/extra_routes.py'
    tree=ast.parse(source.read_text())
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='jarvis_quit_completely')
    app=FastAPI();scope={'app':app,'Request':Request,'JSONResponse':JSONResponse}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope)
    client=TestClient(app)
    quit_call=Mock(return_value={'ok':True})
    monkeypatch.setattr(shutdown,'request_quit',quit_call)
    monkeypatch.setattr(shutdown,'authorize_quit',lambda *a:{'ok':False,'reason':'locked'})
    assert client.post('/api/jarvis/quit-completely').status_code==403
    quit_call.assert_not_called()
    monkeypatch.setattr(shutdown,'authorize_quit',lambda *a:{'ok':True})
    assert client.post('/api/jarvis/quit-completely').json()=={'ok':True}
    quit_call.side_effect=RuntimeError('coordinator unavailable')
    assert client.post('/api/jarvis/quit-completely').status_code==503


def test_daemon_restart_callback_refuses_intentional_quit(lifecycle,monkeypatch):
    from jarvis import daemon
    shutdown.mark_quit()
    start=Mock();monkeypatch.setattr(daemon,'start_server',start)
    assert daemon.restart_server() is None
    start.assert_not_called()


@pytest.mark.parametrize('command',['quit','stop'])
def test_terminal_exit_uses_targeted_coordinator(tmp_path,command):
    import shutil
    root=tmp_path/'app';(root/'scripts').mkdir(parents=True);(root/'venv/bin').mkdir(parents=True)
    source=Path(__file__).parents[1]/'scripts'
    shutil.copy2(source/'jarvis-ctl.sh',root/'scripts/jarvis-ctl.sh')
    shutil.copy2('/media/jeff/AI/jarvis/scripts/_jarvis-launch-lib.sh',root/'scripts/_jarvis-launch-lib.sh')
    fake=root/'venv/bin/python';fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n');fake.chmod(0o700)
    result=subprocess.run(['bash',str(root/'scripts/jarvis-ctl.sh'),command],capture_output=True,text=True)
    assert result.returncode==0
    assert result.stdout.splitlines()==['-m','jarvis.shutdown','quit']
