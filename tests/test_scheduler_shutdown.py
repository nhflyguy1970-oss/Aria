"""Regression for graceful quit during a repository-indexing scheduler tick."""
import contextlib
import fcntl
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
from jarvis import proactive_scheduler as scheduler
from jarvis.knowledge import git_sync, repo_index

@pytest.mark.parametrize('incremental',[False,True])
def test_cancelled_batch_preserves_previous_index(tmp_path,monkeypatch,incremental):
    root=tmp_path/'repo';root.mkdir();(root/'a.py').write_text('print(1)')
    index=tmp_path/'index.json';before=b'[{"source":"old.py","embedding":[1]}]';index.write_bytes(before)
    cancel=threading.Event();calls=[]
    monkeypatch.setattr(repo_index.llm,'embed_session',contextlib.nullcontext)
    monkeypatch.setattr(repo_index,'_chunks',lambda *args:[{'text':'first'},{'text':'second'}])
    # Chunks are embedded in batches (one request per 32): the cancel is honoured before the next batch.
    def embed(texts):calls.append(list(texts));cancel.set();return [[1] for _ in texts]
    monkeypatch.setattr(repo_index.llm,'embed_batch',embed)
    monkeypatch.setattr(repo_index.llm,'embed_text',lambda t:pytest.fail('one request per chunk'))
    monkeypatch.setattr(repo_index,'EMBED_BATCH',1)
    with pytest.raises(InterruptedError):
        repo_index.build_repo_index(root,index_path=index,changed_files=['a.py'] if incremental else None,cancel_check=cancel.is_set)
    assert calls==[['first']];assert index.read_bytes()==before
    assert (root/'a.py').read_text()=='print(1)'


def test_cancel_after_last_chunk_does_not_commit(tmp_path,monkeypatch):
    (tmp_path/'a.py').write_text('print(1)');index=tmp_path/'index.json'
    monkeypatch.setattr(repo_index.llm,'embed_session',contextlib.nullcontext)
    cancel=threading.Event()
    monkeypatch.setattr(repo_index.llm,'embed_batch',lambda texts:(cancel.set() or [[1] for _ in texts]))
    with pytest.raises(InterruptedError):repo_index.build_repo_index(tmp_path,index_path=index,cancel_check=cancel.is_set)
    assert not index.exists()


def test_sync_cancel_stops_remaining_repositories_and_registry(monkeypatch):
    check=lambda:False
    monkeypatch.setattr(git_sync,'discover_repositories',lambda:[Path('/first'),Path('/second')])
    sync=Mock(side_effect=InterruptedError('stop'))
    monkeypatch.setattr(git_sync,'sync_repository',sync)
    from jarvis.knowledge import registry
    refresh=Mock(side_effect=AssertionError('must not refresh after cancellation'))
    monkeypatch.setattr(registry,'sync_registry',refresh)
    result=git_sync.sync_all(cancel_check=check)
    assert result['cancelled'] and not result['ok']
    sync.assert_called_once_with(Path('/first'),force=False,cancel_check=check);refresh.assert_not_called()


def test_cancelled_index_does_not_change_repository_metadata(tmp_path,monkeypatch):
    root=tmp_path/'repo';root.mkdir()
    monkeypatch.setattr(git_sync,'_load_state',lambda:{'repos':{}})
    for name in ['current_branch','_head_commit','_remote_url']:
        monkeypatch.setattr(git_sync,name,lambda *a:'test')
    monkeypatch.setattr(git_sync,'has_local_changes',lambda *a:False)
    monkeypatch.setattr(git_sync,'_open_pull_requests',lambda *a:[])
    index=Mock(side_effect=InterruptedError('stop'));save=Mock()
    monkeypatch.setattr(repo_index,'build_repo_index',index);monkeypatch.setattr(git_sync,'_save_state',save)
    with pytest.raises(InterruptedError):git_sync.sync_repository(root,cancel_check=lambda:True)
    save.assert_not_called()


def test_scheduler_passes_stop_event_into_sync(monkeypatch):
    monkeypatch.setenv('JARVIS_SCHEDULER_GIT_SYNC','1')
    monkeypatch.setattr(scheduler,'_last_git_sync_ts',0)
    sync=Mock(return_value={'ok':False,'cancelled':True})
    monkeypatch.setattr(git_sync,'sync_all',sync)
    scheduler._maybe_git_sync(None)
    assert sync.call_args.kwargs['cancel_check']==scheduler._stop.is_set


def test_quit_during_tick_prevents_following_jobs(monkeypatch):
    class Stop(threading.Event):
        def wait(self,timeout=None):return self.is_set()
    stop=Stop();monkeypatch.setattr(scheduler,'_stop',stop)
    calls=[]
    monkeypatch.setattr(scheduler,'_maybe_briefing',lambda now:(calls.append('briefing'),stop.set()))
    for name in ['_maybe_task_nudge','_maybe_git_sync','_maybe_auto_recover','_maybe_health_reminders','_maybe_integrity_scan']:
        monkeypatch.setattr(scheduler,name,Mock(side_effect=AssertionError('work after stop')))
    scheduler._loop();assert calls==['briefing']


def test_real_xorg_sigterm_stops_indexing_and_releases_database(tmp_path):
    # Actual idle Xorg loop + actual scheduler/index cancellation, no inference.
    harness=tmp_path/'tray_probe.py'
    harness.write_text('''import contextlib,fcntl,sqlite3,threading,os
from pathlib import Path
from jarvis import tray,proactive_scheduler as s
from jarvis.knowledge import repo_index
from jarvis.shutdown import close_acm
from aria_core import acm_bridge
from types import SimpleNamespace
p=Path(os.environ['PROBE_DATA']);p.mkdir(exist_ok=True)
conn=sqlite3.connect(p/'memory.db',check_same_thread=False)
conn.execute('pragma journal_mode=wal');conn.execute('create table records(v)')
conn.execute("insert into records values ('preserved')");conn.commit()
lock=(p/'launch.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX)
acm_bridge._ENGINE=SimpleNamespace(flush=lambda **kw:conn.commit(),durable=SimpleNamespace(close=conn.close))
(p/'a.py').write_text('print(1)');(p/'index.json').write_text('[]')
repo_index.llm.embed_session=contextlib.nullcontext
repo_index._chunks=lambda *a:[{'text':'first'},{'text':'second'}]
def embed(texts):
 (p/'indexing').touch();assert s._stop.wait(8);return [[1] for _ in texts]
repo_index.llm.embed_batch=embed
class Stop(threading.Event):
 def wait(self,timeout=None):
  if timeout==60:return self.is_set()
  return super().wait(timeout)
s._stop=Stop()
for name in ['_maybe_briefing','_maybe_task_nudge']:
 setattr(s,name,lambda now:None)
def index(now):
 try:repo_index.build_repo_index(p,index_path=p/'index.json',cancel_check=s._stop.is_set)
 except InterruptedError:pass
s._maybe_git_sync=index
for name in ['_maybe_auto_recover','_maybe_health_reminders','_maybe_integrity_scan']:
 setattr(s,name,lambda now:(_ for _ in ()).throw(AssertionError('work after quit')))
s._thread=threading.Thread(target=s._loop,name='jarvis-scheduler');s._thread.start()
def cleanup(*,complete):
 assert not complete;s.stop();assert not s._thread.is_alive()
 close_acm();fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
 (p/'closed').touch()
import pystray
orig=pystray.Icon.run
def run(icon,*a,**kw):
 (p/'ready').touch();return orig(icon,*a,**kw)
pystray.Icon.run=run
from PIL import Image
tray._create_icon_image=lambda:Image.new('RGBA',(16,16))
tray.run_tray_app('http://127.0.0.1',on_quit=cleanup)
''')
    out=(tmp_path/'xvfb.out').open('w+')
    xvfb=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x480x24'],stdout=out,stderr=subprocess.DEVNULL)
    proc=None
    try:
        deadline=time.monotonic()+5
        while True:
            out.seek(0);display=out.read().strip()
            if display:break
            assert xvfb.poll() is None and time.monotonic()<deadline;time.sleep(.02)
        private=tmp_path/'state';private.mkdir()
        env=dict(os.environ,DISPLAY=':'+display,PYSTRAY_BACKEND='xorg',JARVIS_DATA_DIR=str(private),DATA_ROOT=str(private/'platform'),APPLICATIONS_ROOT=str(private/'apps'),PROBE_DATA=str(private),PYTHONPATH=str(Path(__file__).parents[1]))
        log=(tmp_path/'tray.log').open('w+')
        proc=subprocess.Popen([sys.executable,str(harness)],env=env,stdout=log,stderr=log,cwd=Path(__file__).parents[1])
        deadline=time.monotonic()+10
        while not (private/'ready').exists() or not (private/'indexing').exists():
            assert proc.poll() is None and time.monotonic()<deadline;time.sleep(.02)
        time.sleep(.15);proc.send_signal(signal.SIGTERM)
        assert proc.wait(timeout=8)==0
        assert (private/'closed').exists() and (private/'index.json').read_text()=='[]'
        with (private/'launch.lock').open('r+') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with sqlite3.connect(private/'memory.db') as c:
            assert c.execute('pragma quick_check').fetchone()==('ok',)
            assert c.execute('select v from records').fetchall()==[('preserved',)]
    finally:
        if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
        xvfb.terminate();xvfb.wait(timeout=5);out.close()


def test_xorg_notification_failure_preserves_cleanup_error(monkeypatch,caplog):
    from types import SimpleNamespace
    from jarvis import tray
    calls=[];items=[];notified=threading.Event()
    class Item:
        def __init__(self,text,callback,**kw):self.text=text;self.callback=callback;items.append(self)
    class Menu:
        SEPARATOR=object()
        def __init__(self,*a):pass
    class Icon:
        def __init__(self,*a):pass
        def notify(self,*a):
            if str(a[0]).startswith('Quit failed:'):notified.set()
            raise NotImplementedError()
        def stop(self):calls.append('stop')
        def run(self):
            next(i for i in items if i.text=='Quit ARIA Completely').callback(self,None)
            assert notified.wait(2)
    monkeypatch.setitem(sys.modules,'pystray',SimpleNamespace(Menu=Menu,MenuItem=Item,Icon=Icon))
    monkeypatch.setattr(tray,'_create_icon_image',lambda:None)
    def cleanup(**kw):raise RuntimeError('scheduler did not stop')
    tray.run_tray_app('http://127.0.0.1',on_quit=cleanup)
    assert calls==[] and 'scheduler did not stop' in caplog.text
