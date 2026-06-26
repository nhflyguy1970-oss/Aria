# Source Generated with Decompyle++
# File: lsp_bridge.cpython-312.pyc (Python 3.12)

'''LSP bridge helpers for API, assistant, and Cursor integration.'''
from __future__ import annotations
from pathlib import Path
from typing import Any
from jarvis import fs
from jarvis.lsp import check_any
from jarvis.lsp_client import completion, document_symbols, find_references, format_document, go_to_definition, hover, servers_status
from jarvis.lsp_protocol import LspError
from jarvis.syntax_check import diagnostics_to_dicts, format_diagnostics

def _resolve(path = None, base = None):
    return fs.resolve_path(path, base = base)


def lsp_status():
    return servers_status()


def lsp_diagnostics(path = None, base = None, *, deep):
    resolved = _resolve(path, base)
    if not resolved.is_file():
        return {
            'ok': False,
            'message': f'''File not found: {path}''' }
    diags = None(resolved, deep = deep)
    return {
        'ok': None,
        'path': any,
        'syntax_ok': not (lambda .0: pass# WARNING: Decompyle incomplete
)(diags()),
        'diagnostics': diagnostics_to_dicts(diags),
        'summary': format_diagnostics(diags) }


def lsp_definition(path = None, base = None, line = None, column = (1,)):
    resolved = _resolve(path, base)
    
    try:
        locations = go_to_definition(resolved, line, column)
        return {
            'ok': True,
            'path': path,
            'locations': locations }
    except LspError:
        e = None
        del e
        return None
        None = 
        del e



def lsp_references(path = None, base = None, line = None, column = (1,)):
    resolved = _resolve(path, base)
    
    try:
        locations = find_references(resolved, line, column)
        return {
            'ok': True,
            'path': path,
            'references': locations }
    except LspError:
        e = None
        del e
        return None
        None = 
        del e



def lsp_hover(path = None, base = None, line = None, column = (1,)):
    resolved = _resolve(path, base)
    
    try:
        text = hover(resolved, line, column)
        return {
            'ok': True,
            'path': path,
            'hover': text }
    except LspError:
        e = None
        del e
        return None
        None = 
        del e



def lsp_completion(path = None, base = None, line = None, column = (1,)):
    resolved = _resolve(path, base)
    
    try:
        items = completion(resolved, line, column)
        return {
            'ok': True,
            'path': path,
            'items': items }
    except LspError:
        e = None
        del e
        return None
        None = 
        del e



def lsp_symbols(path = None, base = None):
    resolved = _resolve(path, base)
    
    try:
        symbols = document_symbols(resolved)
        return {
            'ok': True,
            'path': path,
            'symbols': symbols }
    except LspError:
        e = None
        del e
        return None
        None = 
        del e



def lsp_format(path = None, base = None, *, write):
    resolved = _resolve(path, base)
    
    try:
        formatted = format_document(resolved)
        if write and formatted != resolved.read_text(encoding = 'utf-8', errors = 'replace'):
            resolved.write_text(formatted, encoding = 'utf-8')
        return {
            'ok': True,
            'path': path,
            'formatted': formatted,
            'written': write }
    except LspError:
        e = None
        del e
        return None
        None = 
        del e


