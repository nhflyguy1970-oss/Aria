# Source Generated with Decompyle++
# File: branches.cpython-312.pyc (Python 3.12)

'''Chat conversation branches.'''
import json
import threading
import uuid
from datetime import datetime, timezone
from jarvis.config import DATA_DIR
from jarvis.conversation import Conversation
from jarvis.session import SessionContext
BRANCHES_FILE = DATA_DIR / 'chat_branches.json'
_PERSIST_DEBOUNCE_SEC = 3

class BranchManager:
    
    def __init__(self):
        DATA_DIR.mkdir(parents = True, exist_ok = True)
        self._data = self._load()
        self.active_id = self._data.get('active', 'main')
        self._conversations = { }
        self._persist_timer = None
        self._persist_lock = threading.Lock()

    
    def _load(self = None):
        if BRANCHES_FILE.exists():
            
            try:
                return json.loads(BRANCHES_FILE.read_text(encoding = 'utf-8'))
                return {
                    'active': 'main',
                    'branches': {
                        'main': {
                            'name': 'Main',
                            'messages': [],
                            'created': '' } } }
            except (json.JSONDecodeError, OSError):
                continue


    
    def _save(self = None):
        for bid, conv in self._conversations.items():
            if not bid in self._data['branches']:
                continue
            self._data['branches'][bid]['messages'] = conv.messages
        assert_live_write_allowed = assert_live_write_allowed
        import jarvis.live_data_guard
        assert_live_write_allowed(BRANCHES_FILE)
        BRANCHES_FILE.write_text(json.dumps(self._data, indent = 2, ensure_ascii = False), encoding = 'utf-8')

    
    def _cancel_persist_timer(self = None):
        self._persist_lock
    # WARNING: Decompyle incomplete

    
    def _schedule_save(self = None, *, immediate):
        pass
    # WARNING: Decompyle incomplete

    
    def get_conversation(self = None, branch_id = None, system_prompt = None):
        if not branch_id:
            branch_id
            if not self.active_id:
                self.active_id
        bid = 'main'
        if bid not in self._data['branches']:
            self._data['branches'][bid] = {
                'name': bid,
                'messages': [],
                'created': datetime.now(timezone.utc).isoformat() }
        if bid not in self._conversations:
            conv = Conversation()
            conv.messages = list(self._data['branches'][bid].get('messages', []))
            if conv.messages or conv.messages[0].get('role') != 'system':
                conv.messages.insert(0, {
                    'role': 'system',
                    'content': system_prompt })
            self._conversations[bid] = conv
        return self._conversations[bid]

    
    def update_system_prompt(self = None, branch_id = None, system_prompt = None):
        if not branch_id:
            branch_id
            if not self.active_id:
                self.active_id
        bid = 'main'
        conv = self.get_conversation(bid, system_prompt)
        conv.set_system_content(system_prompt)
        if bid in self._data['branches']:
            self._data['branches'][bid]['messages'] = conv.messages
            return None

    
    def branch_name(self = None, branch_id = None):
        if not branch_id:
            branch_id
            if not self.active_id:
                self.active_id
        bid = 'main'
        return self._data.get('branches', { }).get(bid, { }).get('name', bid)

    
    def save_session(self = None, branch_id = None, session = None):
        if not branch_id:
            branch_id
            if not self.active_id:
                self.active_id
        bid = 'main'
        if bid in self._data['branches']:
            self._data['branches'][bid]['session'] = session.to_dict()
            return None

    
    def load_session(self = None, branch_id = None):
        if not branch_id:
            branch_id
            if not self.active_id:
                self.active_id
        bid = 'main'
        raw = self._data.get('branches', { }).get(bid, { }).get('session')
        return SessionContext.from_dict(raw)

    
    def list_branches(self = None):
        pass
    # WARNING: Decompyle incomplete

    
    def create_branch(self = None, name = None, from_branch = None, from_index = None, *, copy_session):
        bid = str(uuid.uuid4())[:8]
        messages = []
        if not from_branch:
            from_branch
        parent = self.active_id
    # WARNING: Decompyle incomplete

    
    def fork_at_display_index(self = None, name = None, display_index = None, from_branch = (None,)):
        '''Fork after the Nth user/assistant message (0-based, as shown in GUI).'''
        if not from_branch:
            from_branch
        parent = self.active_id
        if parent not in self._data['branches']:
            return self.create_branch(name)
        src = None._data['branches'][parent].get('messages', [])
        abs_index = None
        count = -1
        for i, m in enumerate(src):
            if not m.get('role') in ('user', 'assistant'):
                continue
            count += 1
            if not count == display_index:
                continue
            abs_index = i
            enumerate(src)
    # WARNING: Decompyle incomplete

    
    def switch(self = None, branch_id = None):
        if branch_id not in self._data['branches']:
            return False
        self.active_id = branch_id
        self._data['active'] = branch_id
        self._schedule_save(immediate = True)
        return True

    
    def persist(self = None, branch_id = None, session = None):
        if not branch_id:
            branch_id
        bid = self.active_id
        if bid in self._conversations:
            self._data['branches'][bid]['messages'] = self._conversations[bid].messages
    # WARNING: Decompyle incomplete

    
    def delete_branch(self = None, branch_id = None):
        '''Delete a branch. Main cannot be removed.'''
        if not branch_id:
            branch_id
        bid = ''.strip()
        if bid and bid == 'main' or bid not in self._data.get('branches', { }):
            return False
        self._data['branches'].pop(bid, None)
        self._conversations.pop(bid, None)
        if self.active_id == bid:
            self.active_id = 'main'
            self._data['active'] = 'main'
        self._schedule_save(immediate = True)
        return True

    
    def delete_branches(self = None, branch_ids = None):
        '''Delete multiple branches; returns deleted ids and active branch.'''
        deleted = []
        for bid in branch_ids:
            if not self.delete_branch(bid):
                continue
            deleted.append(bid)
        return {
            'deleted': deleted,
            'active': self.active_id }

    
    def clear_messages(self = None, branch_id = None, system_prompt = None):
        '''Clear user/assistant history for a branch (keeps branch id; resets session).'''
        if not branch_id:
            branch_id
        if not ''.strip():
            ''.strip()
        bid = 'main'
        if bid not in self._data.get('branches', { }):
            return False
        conv = Conversation()
        conv.messages = [
            {
                'role': 'system',
                'content': system_prompt }]
        self._conversations[bid] = conv
        self._data['branches'][bid]['messages'] = conv.messages
        self._data['branches'][bid]['session'] = SessionContext().to_dict()
        self._schedule_save(immediate = True)
        return True


