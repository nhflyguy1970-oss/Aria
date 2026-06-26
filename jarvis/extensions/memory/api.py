# Source Generated with Decompyle++
# File: api.cpython-312.pyc (Python 3.12)

'''Memory, cheatsheet, and profile REST API routes.'''
from __future__ import annotations
from fastapi import Request
from fastapi.responses import JSONResponse

def _memory_settings_payload(assistant = None):
    load_auto_checkpoint = load_auto_checkpoint
    load_auto_correction_mode = load_auto_correction_mode
    load_auto_document_learn = load_auto_document_learn
    load_auto_journal_learn = load_auto_journal_learn
    load_auto_memory_mode = load_auto_memory_mode
    load_auto_namespace = load_auto_namespace
    load_brain_mode = load_brain_mode
    load_memory_in_system_prompt = load_memory_in_system_prompt
    load_memory_namespace = load_memory_namespace
    import jarvis.config
    brain_mode_status = brain_mode_status
    import jarvis.brain_memory
    status = {
        'ok': True,
        'namespace': load_memory_namespace(),
        'session_namespace': assistant.session.memory_namespace,
        'auto_memory_mode': load_auto_memory_mode(),
        'auto_correction_mode': load_auto_correction_mode(),
        'auto_checkpoint': load_auto_checkpoint(),
        'auto_namespace': load_auto_namespace(),
        'memory_in_system_prompt': load_memory_in_system_prompt(),
        'brain_mode': load_brain_mode(),
        'auto_journal_learn': load_auto_journal_learn(),
        'auto_document_learn': load_auto_document_learn(),
        'brain_learning': brain_mode_status() }
    
    try:
        confidence_snapshot = snapshot
        import jarvis.action_confidence
        reflection_status = reflection_status
        import jarvis.reflection_loop
        status['reflection'] = reflection_status()
        status['action_confidence'] = confidence_snapshot()
        return status
    except Exception:
        return status



def register_routes(app = None, assistant = None):
    pass
# WARNING: Decompyle incomplete

