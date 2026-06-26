# Source Generated with Decompyle++
# File: api.cpython-312.pyc (Python 3.12)

'''Fly-tying REST API.'''
from __future__ import annotations
import json
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from jarvis.flytying import bridge
from jarvis.flytying.chat import chat_turn, chat_turn_stream, get_model_setting, set_model_setting
from jarvis.flytying.knowledge import seed_memory, sync_library, sync_status

def register_routes(app = None, assistant = None):
    pass
# WARNING: Decompyle incomplete

