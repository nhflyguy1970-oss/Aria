# Source Generated with Decompyle++
# File: test_background_jobs.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Background job dispatch (learn_about, document_summarize).'''
import builtins as @py_builtins

rewrite
from types import SimpleNamespace
import _pytest.assertion.rewrite, assertion
from unittest.mock import MagicMock
import pytest

class _FakeAssistant:
    
    def __init__(self):
        self.learn_calls = []

    
    def _learn_about(self, params, message):
        self.learn_calls.append((dict(params), message))
        return {
            'ok': True,
            'type': 'knowledge_learned',
            'message': 'Learned' }



def test_submit_action_learn_about_uses_assistant_handler(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_submit_action_uses_registry_handler_when_present(monkeypatch):
    pass
# WARNING: Decompyle incomplete

