"""Chat conversation branches."""

import json
import uuid
from datetime import datetime, timezone

from jarvis.config import DATA_DIR
from jarvis.conversation import Conversation
from jarvis.session import SessionContext

BRANCHES_FILE = DATA_DIR / "chat_branches.json"


class BranchManager:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._data = self._load()
        self.active_id = self._data.get("active", "main")
        self._conversations: dict[str, Conversation] = {}
        self._ensure_default_branches()

    def _load(self) -> dict:
        if BRANCHES_FILE.exists():
            try:
                return json.loads(BRANCHES_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"active": "main", "branches": {"main": {"name": "Main", "messages": [], "created": ""}}}

    def _ensure_default_branches(self) -> None:
        branches = self._data.setdefault("branches", {})
        defaults = (
            ("main", "Main"),
            ("work", "Work"),
            ("personal", "Personal"),
        )
        added = False
        for bid, name in defaults:
            if bid not in branches:
                branches[bid] = {
                    "name": name,
                    "messages": [],
                    "created": datetime.now(timezone.utc).isoformat(),
                }
                added = True
        if added:
            self._save()

    def _save(self) -> None:
        for bid, conv in self._conversations.items():
            if bid in self._data["branches"]:
                self._data["branches"][bid]["messages"] = conv.messages
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(BRANCHES_FILE)
        BRANCHES_FILE.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_conversation(self, branch_id: str | None, system_prompt: str) -> Conversation:
        bid = branch_id or self.active_id or "main"
        if bid not in self._data["branches"]:
            self._data["branches"][bid] = {
                "name": bid,
                "messages": [],
                "created": datetime.now(timezone.utc).isoformat(),
            }
        if bid not in self._conversations:
            conv = Conversation()
            conv.messages = list(self._data["branches"][bid].get("messages", []))
            if not conv.messages or conv.messages[0].get("role") != "system":
                conv.messages.insert(0, {"role": "system", "content": system_prompt})
            self._conversations[bid] = conv
        return self._conversations[bid]

    def update_system_prompt(self, branch_id: str | None, system_prompt: str) -> None:
        bid = branch_id or self.active_id or "main"
        conv = self.get_conversation(bid, system_prompt)
        conv.set_system_content(system_prompt)
        if bid in self._data["branches"]:
            self._data["branches"][bid]["messages"] = conv.messages

    def branch_name(self, branch_id: str | None = None) -> str:
        bid = branch_id or self.active_id or "main"
        return self._data.get("branches", {}).get(bid, {}).get("name", bid)

    def save_session(self, branch_id: str | None, session: SessionContext) -> None:
        bid = branch_id or self.active_id or "main"
        if bid in self._data["branches"]:
            self._data["branches"][bid]["session"] = session.to_dict()

    def load_session(self, branch_id: str | None) -> SessionContext:
        bid = branch_id or self.active_id or "main"
        raw = self._data.get("branches", {}).get(bid, {}).get("session")
        return SessionContext.from_dict(raw)

    def list_branches(self) -> list[dict]:
        return [
            {
                "id": bid,
                "name": b.get("name", bid),
                "messages": sum(
                    1 for m in b.get("messages", []) if m.get("role") in ("user", "assistant")
                ),
            }
            for bid, b in self._data.get("branches", {}).items()
        ]

    def create_branch(
        self,
        name: str,
        from_branch: str | None = None,
        from_index: int | None = None,
        *,
        copy_session: bool = True,
    ) -> str:
        bid = str(uuid.uuid4())[:8]
        messages: list = []
        parent = from_branch or self.active_id
        if parent and parent in self._data["branches"]:
            src = self._data["branches"][parent].get("messages", [])
            messages = src[: from_index + 1] if from_index is not None else list(src)
        session_data = None
        if copy_session and parent and parent in self._data["branches"]:
            session_data = self._data["branches"][parent].get("session")
        self._data["branches"][bid] = {
            "name": name,
            "messages": messages,
            "created": datetime.now(timezone.utc).isoformat(),
            "forked_from": parent,
            "session": session_data,
        }
        self.active_id = bid
        self._data["active"] = bid
        self._conversations.pop(bid, None)
        self._save()
        return bid

    def fork_at_display_index(self, name: str, display_index: int, from_branch: str | None = None) -> str:
        """Fork after the Nth user/assistant message (0-based, as shown in GUI)."""
        parent = from_branch or self.active_id
        if parent not in self._data["branches"]:
            return self.create_branch(name)
        src = self._data["branches"][parent].get("messages", [])
        abs_index = None
        count = -1
        for i, m in enumerate(src):
            if m.get("role") in ("user", "assistant"):
                count += 1
                if count == display_index:
                    abs_index = i
                    break
        if abs_index is None and src:
            abs_index = len(src) - 1
        return self.create_branch(name, from_branch=parent, from_index=abs_index)

    def switch(self, branch_id: str) -> bool:
        if branch_id not in self._data["branches"]:
            return False
        self.active_id = branch_id
        self._data["active"] = branch_id
        self._save()
        return True

    def persist(self, branch_id: str | None = None, session: SessionContext | None = None) -> None:
        bid = branch_id or self.active_id
        if bid in self._conversations:
            self._data["branches"][bid]["messages"] = self._conversations[bid].messages
        if session is not None and bid in self._data["branches"]:
            self._data["branches"][bid]["session"] = session.to_dict()
        self._save()

    def delete_branch(self, branch_id: str) -> bool:
        """Delete a branch. Main cannot be removed."""
        bid = (branch_id or "").strip()
        if not bid or bid == "main" or bid not in self._data.get("branches", {}):
            return False
        self._data["branches"].pop(bid, None)
        self._conversations.pop(bid, None)
        if self.active_id == bid:
            self.active_id = "main"
            self._data["active"] = "main"
        self._save()
        return True

    def delete_branches(self, branch_ids: list[str]) -> dict:
        """Delete multiple branches; returns deleted ids and active branch."""
        deleted: list[str] = []
        for bid in branch_ids:
            if self.delete_branch(bid):
                deleted.append(bid)
        return {"deleted": deleted, "active": self.active_id}

    def clear_messages(self, branch_id: str, system_prompt: str) -> bool:
        """Clear user/assistant history for a branch (keeps branch id; resets session)."""
        bid = (branch_id or "").strip() or "main"
        if bid not in self._data.get("branches", {}):
            return False
        conv = Conversation()
        conv.messages = [{"role": "system", "content": system_prompt}]
        self._conversations[bid] = conv
        self._data["branches"][bid]["messages"] = conv.messages
        self._data["branches"][bid]["session"] = SessionContext().to_dict()
        self._save()
        return True
