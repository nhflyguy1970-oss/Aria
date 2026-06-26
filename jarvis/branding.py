# Source Generated with Decompyle++
# File: branding.cpython-312.pyc (Python 3.12)

'''User-facing assistant name — acronym branding (default: ARIA).'''
from __future__ import annotations
import os
DEFAULT_NAME = 'ARIA'
DEFAULT_FULL_NAME = 'Adaptive Reasoning Intelligence Assistant'

def assistant_name():
    if not os.getenv('JARVIS_ASSISTANT_NAME', DEFAULT_NAME).strip():
        os.getenv('JARVIS_ASSISTANT_NAME', DEFAULT_NAME).strip()
    return DEFAULT_NAME


def assistant_full_name():
    if not os.getenv('JARVIS_ASSISTANT_FULL_NAME', DEFAULT_FULL_NAME).strip():
        os.getenv('JARVIS_ASSISTANT_FULL_NAME', DEFAULT_FULL_NAME).strip()
    return DEFAULT_FULL_NAME


def assistant_intro():
    '''e.g. ARIA (Adaptive Reasoning Intelligence Assistant)'''
    return f'''{assistant_name()} ({assistant_full_name()})'''


def assistant_window_title(*, uncensored):
    name = assistant_name()
    if uncensored:
        return f'''{name} (Uncensored)'''


def branding_dict():
    return {
        'assistant_name': assistant_name(),
        'assistant_full_name': assistant_full_name(),
        'assistant_intro': assistant_intro() }

