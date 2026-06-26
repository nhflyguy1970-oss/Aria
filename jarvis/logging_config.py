# Source Generated with Decompyle++
# File: logging_config.cpython-312.pyc (Python 3.12)

'''Centralized logging setup for ARIA.'''
from __future__ import annotations
import logging
import os
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_DIR = PROJECT_ROOT / 'data' / 'logs'
_request_id: 'ContextVar[str]' = ContextVar('request_id', default = '')
_CONFIGURED = False
_QUIET_LOGGERS = ('httpcore', 'httpx', 'urllib3', 'uvicorn.access', 'onnxruntime')

class RequestIdFilter(logging.Filter):
    
    def filter(self = None, record = None):
        if not _request_id.get():
            _request_id.get()
        record.request_id = '-'
        return True



def set_request_id(request_id = None):
    if not request_id:
        request_id
    _request_id.set(''.strip())


def clear_request_id():
    _request_id.set('')


def get_request_id():
    if not _request_id.get():
        _request_id.get()
    return ''


def log_dir():
    return Path(os.getenv('JARVIS_LOG_DIR', str(DEFAULT_LOG_DIR)))


def log_file_path():
    explicit = os.getenv('JARVIS_LOG_FILE', '').strip()
    if explicit:
        return Path(explicit)
    return None() / 'jarvis.log'


def setup_logging(*, force):
    '''Configure root logging once per process (file + stderr, with rotation).'''
    pass
# WARNING: Decompyle incomplete


def get_logger(name = None):
    '''Return a named logger, ensuring setup ran at least once.'''
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)

