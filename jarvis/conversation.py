from jarvis.config import MAX_CONTEXT_CHARS, MAX_MESSAGES


class Conversation:
    def __init__(self, system_prompt: str | None = None):
        self.messages: list[dict] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def add_system(self, content: str) -> None:
        self.messages.append({"role": "system", "content": content})
        self._prune()

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self._prune()

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self._prune()

    def clear(self) -> None:
        system = [m for m in self.messages if m["role"] == "system"]
        self.messages = system[:1] if system else []

    def pop_last_user(self) -> bool:
        if self.messages and self.messages[-1].get("role") == "user":
            self.messages.pop()
            return True
        return False

    def set_system_content(self, content: str) -> None:
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0]["content"] = content
        else:
            self.messages.insert(0, {"role": "system", "content": content})

    def _prune(self) -> None:
        while len(self.messages) > MAX_MESSAGES:
            for i, msg in enumerate(self.messages):
                if msg["role"] in ("user", "assistant"):
                    del self.messages[i]
                    break
            else:
                break

        total = sum(len(m["content"]) for m in self.messages)
        while total > MAX_CONTEXT_CHARS and len(self.messages) > 2:
            for i, msg in enumerate(self.messages):
                if msg["role"] in ("user", "assistant"):
                    total -= len(msg["content"])
                    del self.messages[i]
                    break
            else:
                break
