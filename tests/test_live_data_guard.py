# Source Generated with Decompyle++
# File: test_live_data_guard.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Live data guard blocks pytest writes to project data/.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.config import PROJECT_ROOT
from jarvis.live_data_guard import assert_live_write_allowed, enable_test_guard
from jarvis.modules.memory import MemoryStore
LIVE_MEMORY_FILE = PROJECT_ROOT / 'data' / 'memory.json'

def test_guard_blocks_live_memory_path():
    enable_test_guard()
    pytest.raises(RuntimeError, match = 'live Jarvis data')
    assert_live_write_allowed(LIVE_MEMORY_FILE)
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_guard_allows_temp_path(data_dir):
    enable_test_guard()
    assert_live_write_allowed(data_dir / 'memory.json')


def test_store_writes_under_temp(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: [
1]))
    store = MemoryStore(path = data_dir / 'memory.json')
    store.add('fact', 'Safe fact for tests.')

