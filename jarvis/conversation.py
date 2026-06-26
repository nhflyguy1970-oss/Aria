# Source Generated with Decompyle++
# File: conversation.cpython-312.pyc (Python 3.12)

from jarvis.config import MAX_CONTEXT_CHARS, MAX_MESSAGES

class Conversation:
    
    def __init__(self = None, system_prompt = None):
        self.messages = []
        if system_prompt:
            self.messages.append({
                'role': 'system',
                'content': system_prompt })
            return None

    
    def add_system(self = None, content = None):
        self.messages.append({
            'role': 'system',
            'content': content })
        self._prune()

    
    def add_user(self = None, content = None):
        self.messages.append({
            'role': 'user',
            'content': content })
        self._prune()

    
    def add_assistant(self = None, content = None):
        self.messages.append({
            'role': 'assistant',
            'content': content })
        self._prune()

    
    def clear(self = None):
        pass
    # WARNING: Decompyle incomplete

    
    def pop_last_user(self = None):
        if self.messages and self.messages[-1].get('role') == 'user':
            self.messages.pop()
            return True
        return False

    
    def truncate_last_assistant(self = None, *, partial_note):
        if self.messages or self.messages[-1].get('role') != 'assistant':
            return False
        if not self.messages[-1].get('content'):
            self.messages[-1].get('content')
        content = ''
        if partial_note and partial_note not in content:
            self.messages[-1]['content'] = content.rstrip() + f'''\n\n{partial_note}'''
            return True
        self.messages.pop()
        return True

    
    def set_system_content(self = None, content = None):
        if self.messages and self.messages[0].get('role') == 'system':
            self.messages[0]['content'] = content
            return None
        self.messages.insert(0, {
            'role': 'system',
            'content': content })

    
    def _prune(self = None):
        if len(self.messages) > MAX_MESSAGES:
            for i, msg in enumerate(self.messages):
                if not msg['role'] in ('user', 'assistant'):
                    continue
                del self.messages[i]
                enumerate(self.messages)
        elif len(self.messages) > MAX_MESSAGES:
            continue
        total = (lambda .0: pass# WARNING: Decompyle incomplete
)(self.messages())
        if total > MAX_CONTEXT_CHARS:
            if len(self.messages) > 2:
                for i, msg in enumerate(self.messages):
                    if not msg['role'] in ('user', 'assistant'):
                        continue
                    total -= len(msg['content'])
                    del self.messages[i]
                    enumerate(self.messages)
                return None
                if total > MAX_CONTEXT_CHARS:
                    if len(self.messages) > 2:
                        continue
                    return None
                return None
            return None


