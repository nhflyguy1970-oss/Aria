# Source Generated with Decompyle++
# File: cursor_bridge.cpython-312.pyc (Python 3.12)

'''Cursor / IDE bridge — REST helpers and MCP tool definitions.'''
from __future__ import annotations
import re
from pathlib import Path
from typing import Any
from jarvis import fs
from jarvis.code_context import format_context, gather_context
from jarvis.code_index import build_index, invalidate_cache
from jarvis.code_index import search as code_search
from jarvis.lsp import check_any
from jarvis.syntax_check import diagnostics_to_dicts, format_diagnostics

def get_file_context(path = None, base = None, *, task):
    ctx = gather_context(path, base, task = task)
    return {
        'path': path,
        'primary': ctx.get('primary', ''),
        'related': ctx.get('related', []),
        'tests': ctx.get('tests', []),
        'formatted': format_context(ctx) }


def search_codebase(query = None, limit = None):
    return code_search(query, limit = limit)


def check_syntax(path = None, base = None, *, content):
    resolved = fs.resolve_path(path, base = base)
    diags = check_any(resolved, content = content, deep = True)
    return {
        'path': any,
        'ok': not (lambda .0: pass# WARNING: Decompyle incomplete
)(diags()),
        'diagnostics': diagnostics_to_dicts(diags),
        'summary': format_diagnostics(diags) }


def list_project_files(base = None, limit = None):
    (_, files) = fs.scan_project(base)
    return files[:limit]


def run_script_bridge(path = None, base = None):
    run_script = run_script
    runner_info = runner_info
    import jarvis.project_runner
    resolved = fs.resolve_path(path, base = base)
    result = run_script(resolved, base, timeout = 60)
    if not result.stdout:
        result.stdout
    if not result.stderr:
        result.stderr
    return {
        'ok': result.returncode == 0,
        'stdout': ''[:4000],
        'stderr': ''[:2000],
        'runner': runner_info(base) }


def build_code_index(root = None):
    invalidate_cache()
    chunks = build_index(root)
    return {
        'ok': True,
        'chunks': len(chunks) }

_assistant_inst = None

def _assistant():
    get_assistant = get_assistant
    import jarvis.assistant_instance
    return get_assistant()


def propose_fix(path = None, task = None, base = None, *, mode):
    '''Generate a fix/improve proposal without applying.'''
    _ = base
    a = _assistant()
    if mode == 'fix':
        if not task:
            task
        result = a._coding_fix({
            'path': path,
            'task': task }, f'''fix {path}''')
    elif not task:
        task
    result = a._coding_improve({
        'path': path }, f'''improve {path}''')
    return {
        'ok': result.get('ok', False),
        'proposal_id': result.get('proposal_id'),
        'message': result.get('message', ''),
        'syntax_ok': result.get('syntax_ok'),
        'diff': result.get('diff', '') }


def propose_create(description = None, path = None, base = None):
    _ = base
    a = _assistant()
    result = a._coding_create({
        'description': description,
        'path': path }, description)
    return {
        'ok': result.get('ok', False),
        'proposal_id': result.get('proposal_id'),
        'message': result.get('message', ''),
        'syntax_ok': result.get('syntax_ok') }


def apply_proposal_bridge(proposal_id = None, base = None, *, force):
    _ = base
    a = _assistant()
    if not proposal_id:
        proposal_id
    return a.apply_proposal(None, force = force)

MCP_TOOLS = [
    {
        'name': 'jarvis_read_file',
        'description': 'Read a file from the Jarvis project',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string' } },
            'required': [
                'path'] } },
    {
        'name': 'jarvis_search_code',
        'description': 'Semantic search over the Jarvis codebase',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string' },
                'limit': {
                    'type': 'integer' } },
            'required': [
                'query'] } },
    {
        'name': 'jarvis_check_syntax',
        'description': 'Run syntax/lint checks on a file',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string' },
                'content': {
                    'type': 'string' } },
            'required': [
                'path'] } },
    {
        'name': 'jarvis_code_context',
        'description': 'Gather related context for a file before editing',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string' },
                'task': {
                    'type': 'string' } },
            'required': [
                'path'] } },
    {
        'name': 'jarvis_run_script',
        'description': 'Run a Python script in the project sandbox',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string' } },
            'required': [
                'path'] } },
    {
        'name': 'jarvis_build_index',
        'description': 'Rebuild semantic code search index',
        'inputSchema': {
            'type': 'object',
            'properties': { } } },
    {
        'name': 'jarvis_list_files',
        'description': 'List project source files',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'limit': {
                    'type': 'integer' } } } },
    {
        'name': 'jarvis_propose_fix',
        'description': 'Generate a fix proposal for a Python file (returns proposal_id; use jarvis_apply_proposal to save)',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string' },
                'task': {
                    'type': 'string' } },
            'required': [
                'path'] } },
    {
        'name': 'jarvis_propose_create',
        'description': 'Generate a new Python script + pytest proposal',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'description': {
                    'type': 'string' },
                'path': {
                    'type': 'string' } },
            'required': [
                'description'] } },
    {
        'name': 'jarvis_apply_proposal',
        'description': 'Apply a pending Jarvis code proposal by proposal_id',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'proposal_id': {
                    'type': 'string' },
                'force': {
                    'type': 'boolean' } } } },
    {
        'name': 'jarvis_undo_apply',
        'description': 'Undo the last applied code proposal (restore backups / delete new files)',
        'inputSchema': {
            'type': 'object',
            'properties': { } } },
    {
        'name': 'jarvis_get_editor_context',
        'description': 'Active file and selection from Cursor (Jarvis Editor Bridge extension)',
        'inputSchema': {
            'type': 'object',
            'properties': { } } },
    {
        'name': 'jarvis_find_references',
        'description': 'Find grep-based references to a symbol in the codebase',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'symbol': {
                    'type': 'string' },
                'limit': {
                    'type': 'integer' } },
            'required': [
                'symbol'] } },
    {
        'name': 'jarvis_run_command',
        'description': 'Run an allowlisted project command (pytest, python, ruff, npm test, etc.)',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string' } },
            'required': [
                'command'] } },
    {
        'name': 'jarvis_write_file',
        'description': 'Write content to a file in the Jarvis project (creates parent dirs; backs up existing)',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string' },
                'content': {
                    'type': 'string' },
                'backup': {
                    'type': 'boolean' } },
            'required': [
                'path',
                'content'] } },
    {
        'name': 'jarvis_list_dir',
        'description': 'List files and subdirectories at a path',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string' },
                'limit': {
                    'type': 'integer' } } } },
    {
        'name': 'jarvis_run_tests',
        'description': 'Run pytest on a target path or tests/',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'target': {
                    'type': 'string' },
                'timeout': {
                    'type': 'integer' } } } },
    {
        'name': 'jarvis_propose_agent',
        'description': 'Run the multi-step coding agent and return a proposal (read/search/verify loop)',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'task': {
                    'type': 'string' },
                'path': {
                    'type': 'string' },
                'max_steps': {
                    'type': 'integer' },
                'mode': {
                    'type': 'string' } },
            'required': [
                'task'] } },
    {
        'name': 'jarvis_self_diagnose',
        'description': 'Quick ARIA health check: imports + pytest smoke',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'full': {
                    'type': 'boolean' } } } },
    {
        'name': 'jarvis_self_fix',
        'description': 'Diagnose ARIA, run coding agent on failures, optionally apply proposal',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'task': {
                    'type': 'string' },
                'apply': {
                    'type': 'boolean' },
                'max_steps': {
                    'type': 'integer' } } } },
    {
        'name': 'jarvis_self_upgrade_run',
        'description': 'Run git-branch self-upgrade pipeline (propose, apply, test, report)',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'task': {
                    'type': 'string' },
                'max_steps': {
                    'type': 'integer' } },
            'required': [
                'task'] } }]
_CODING_MCP_TOOL_NAMES = (lambda .0: pass# WARNING: Decompyle incomplete
)(MCP_TOOLS())
_MCP_SERVER_SCRIPT = Path(__file__).resolve().parent.parent / 'scripts' / 'jarvis-mcp-server.py'

def discover_mcp_server_tool_names():
    '''Tool names declared in scripts/jarvis-mcp-server.py (@mcp.tool).'''
    text = _MCP_SERVER_SCRIPT.read_text(encoding = 'utf-8')
    return frozenset(re.findall('@mcp\\.tool\\(\\)\\s*\\ndef\\s+(jarvis_\\w+)', text))


def _is_domain_mcp_tool(name = None):
    '''Domain tools: jarvis_* handlers in jarvis_mcp (not coding bridge).'''
    if name.startswith('jarvis_'):
        name.startswith('jarvis_')
    return name not in _CODING_MCP_TOOL_NAMES

_DOMAIN_MCP_TOOLS = discover_mcp_server_tool_names() - _CODING_MCP_TOOL_NAMES

def handle_mcp_tool(name = None, arguments = None, base = None):
    '''Dispatch MCP tool call.'''
    if _is_domain_mcp_tool(name):
        handle_jarvis_mcp_tool = handle_jarvis_mcp_tool
        import jarvis.jarvis_mcp
        return handle_jarvis_mcp_tool(name, arguments)
    if None == 'jarvis_read_file':
        path = arguments.get('path', '')
        content = fs.read_file(path, base = base)
        return {
            'path': path,
            'content': content }
    if None == 'jarvis_search_code':
        hits = search_codebase(arguments.get('query', ''), limit = int(arguments.get('limit', 8)))
        return {
            'results': hits }
    if None == 'jarvis_check_syntax':
        return check_syntax(arguments.get('path', ''), base, content = arguments.get('content'))
    if None == 'jarvis_code_context':
        return get_file_context(arguments.get('path', ''), base, task = arguments.get('task', ''))
    if None == 'jarvis_run_script':
        return run_script_bridge(arguments.get('path', ''), base)
    if None == 'jarvis_build_index':
        return build_code_index(base)
    if None == 'jarvis_list_files':
        return {
            'files': list_project_files(base, limit = int(arguments.get('limit', 100))) }
    if None == 'jarvis_propose_fix':
        return propose_fix(arguments.get('path', ''), arguments.get('task', ''), base, mode = 'fix')
    if None == 'jarvis_propose_create':
        return propose_create(arguments.get('description', ''), arguments.get('path', ''), base)
    if None == 'jarvis_apply_proposal':
        return apply_proposal_bridge(arguments.get('proposal_id', ''), base, force = bool(arguments.get('force')))
    if None == 'jarvis_undo_apply':
        perform_undo_apply = perform_undo_apply
        import jarvis.assistant
        return perform_undo_apply(_assistant())
    if None == 'jarvis_find_references':
        find_references = find_references
        import jarvis.code_context
        symbol = arguments.get('symbol', '')
        hits = find_references(symbol, base, limit = int(arguments.get('limit', 30)))
        return {
            'symbol': symbol,
            'references': hits }
    if None == 'jarvis_run_command':
        run_project_command = run_project_command
        import jarvis.project_runner
        cmd = arguments.get('command', '')
        
        try:
            result = run_project_command(cmd, base, timeout = 120)
            if not result.stdout:
                result.stdout
            if not result.stderr:
                result.stderr
            return {
                'ok': result.returncode == 0,
                'stdout': ''[:4000],
                'stderr': ''[:2000],
                'returncode': result.returncode }
            if name == 'jarvis_get_editor_context':
                DEFAULT_MAX_AGE_S = DEFAULT_MAX_AGE_S
                get_context = get_context
                load_context = load_context
                import jarvis.editor_context
                ctx = load_context()
                live = get_context()
                is_fresh = live is not None
                return {
                    'ok': True,
                    'is_fresh': is_fresh,
                    'fresh': is_fresh,
                    'updated_at': ctx.updated_at,
                    'max_age_s': DEFAULT_MAX_AGE_S,
                    'relative_file': ctx.relative_file,
                    'has_selection': ctx.has_selection(),
                    'formatted': ctx.format_for_prompt(),
                    'open_files': ctx.open_files }
            if None == 'jarvis_write_file':
                write_file_bridge = write_file_bridge
                import jarvis.aria_coder
                return write_file_bridge(arguments.get('path', ''), arguments.get('content', ''), base, backup = bool(arguments.get('backup', True)))
            if None == 'jarvis_list_dir':
                list_dir = list_dir
                import jarvis.aria_coder
                return {
                    'entries': list_dir(arguments.get('path', '.'), base, limit = int(arguments.get('limit', 200))) }
            if None == 'jarvis_run_tests':
                run_tests_bridge = run_tests_bridge
                import jarvis.aria_coder
                return run_tests_bridge(arguments.get('target', 'tests/'), base, timeout = int(arguments.get('timeout', 180)))
            if None == 'jarvis_propose_agent':
                propose_agent_bridge = propose_agent_bridge
                import jarvis.aria_coder
                return propose_agent_bridge(arguments.get('task', ''), arguments.get('path', ''), base, max_steps = int(arguments.get('max_steps', 5)), mode = arguments.get('mode', 'agent'))
            if None == 'jarvis_self_diagnose':
                aria_self_diagnose = aria_self_diagnose
                import jarvis.aria_coder
                return aria_self_diagnose(base, full = bool(arguments.get('full')))
            if None == 'jarvis_self_fix':
                self_fix_aria = self_fix_aria
                import jarvis.aria_coder
                return self_fix_aria(_assistant(), task = arguments.get('task', ''), apply = bool(arguments.get('apply')), max_steps = int(arguments.get('max_steps', 5)))
            if None == 'jarvis_self_upgrade_run':
                self_upgrade_bridge = self_upgrade_bridge
                import jarvis.aria_coder
                return self_upgrade_bridge(arguments.get('task', ''), max_steps = int(arguments.get('max_steps', 4)))
            return {
                None: f'''Unknown tool: {name}''' }
        except ValueError:
            e = None
            del e
            return None
            None = 
            del e


