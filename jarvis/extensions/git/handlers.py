# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Git action handlers.'''
from __future__ import annotations
import re
from jarvis import git_util, llm
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok

def _base(assistant):
    return assistant.coding._base()

git_status = (lambda assistant = None, params = None, message = register_action('git_status', module = 'coding', extension = 'git', description = 'Git working tree status'): ok(f'''```\n{git_util.status()}\n```''', module = 'coding'))()
git_diff = (lambda assistant = None, params = None, message = register_action('git_diff', module = 'coding', extension = 'git', description = 'Git diff for file or repo'): f = params.get('file', '')if not f:
fd = git_util.diff(file = None)ok(f'''```diff\n{d[:8000]}\n```''', module = 'coding'))()
git_commit = (lambda assistant = None, params = None, message = register_action('git_commit', module = 'coding', extension = 'git', description = 'Git commit staged changes'): if not params.get('message'):
params.get('message')msg = ''if not msg:
m = re.search('commit(?:\\s+with\\s+message)?[:\\s]+(.+)', message, re.I)msg = m.group(1).strip() if m else ''if not msg:
err('Provide a commit message, e.g. "commit: fix hello world script"')files = None.get('files')if isinstance(files, str):
files = [
files]result = git_util.commit(msg, path = _base(assistant), files = files)if result.startswith('ERROR:'):
err(result)None(f'''```\n{result}\n```''', module = 'coding'))()
git_branch = (lambda assistant = None, params = None, message = register_action('git_branch', module = 'coding', extension = 'git', description = 'Create and switch git branch'): if not params.get('name'):
params.get('name')name = ''if not name:
m = re.search('(?:create\\s+)?branch\\s+[`\'\\"]?([\\w./-]+)', message, re.I)name = m.group(1) if m else ''if not name:
err('Provide a branch name, e.g. "create branch feature/coding-agent"')result = None.create_branch(name, path = _base(assistant))if result.startswith('ERROR:'):
err(result)None(result, module = 'coding'))()
git_summarize = (lambda assistant = None, params = None, message = register_action('git_summarize', module = 'coding', extension = 'git', description = 'Summarize git diff in plain English'): f = params.get('file', '')if not f:
fdiff_text = git_util.summarize_diff(path = _base(assistant), file = None)if diff_text in ('No changes.', 'Not a git repository.'):
ok(diff_text, module = 'coding')summary = None.ask(llm.general_model(), [
{
'role': 'user',
'content': f'''Summarize this git diff in plain English (bullet points):\n\n```diff\n{diff_text[:12000]}\n```''' }])ok(f'''**Changes summary:**\n\n{summary}''', module = 'coding'))()
git_pr = (lambda assistant = None, params = None, message = register_action('git_pr', module = 'coding', extension = 'git', description = 'Create a GitHub pull request'): title = params.get('title', '')body = params.get('body', '')if not title:
m = re.search('\\bcreate (?:a )?pull request[:\\s]+(.+)', message, re.I)title = m.group(1).strip() if m else 'Jarvis coding changes'result = git_util.create_pull_request(title, body, path = _base(assistant))if result.startswith('ERROR'):
err(result)None(f'''**Pull request:** {result}''', module = 'coding'))()
