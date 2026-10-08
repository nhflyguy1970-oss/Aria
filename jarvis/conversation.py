from jarvis.config import MAX_CONTEXT_CHARS, MAX_MESSAGES


class Conversation:
    """The bounded context sent to models.

    `messages` is pruned to MAX_MESSAGES / MAX_CONTEXT_CHARS. When an `archive`
    is attached (branch conversations), every user/assistant turn is written
    to it before pruning, so pruning only ever narrows the model's context and
    never discards the source history.
    """

    def __init__(self, system_prompt: str | None = None, *, archive=None):
        self.messages: list[dict] = []
        self.archive = archive
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def _archive(self, role: str, content: str) -> None:
        if self.archive is not None:
            self.archive.record(role, content)

    def add_system(self, content: str) -> None:
        self.messages.append({"role": "system", "content": content})
        self._prune()

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self._archive("user", content)
        self._prune()

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self._archive("assistant", content)
        self._prune()

    def clear(self) -> None:
        system = [m for m in self.messages if m["role"] == "system"]
        self.messages = system[:1] if system else []
        if self.archive is not None:
            self.archive.mark("cleared")

    def pop_last_user(self) -> bool:
        if self.messages and self.messages[-1].get("role") == "user":
            removed = self.messages.pop()
            if self.archive is not None:
                # The turn was said; it is only withdrawn from the context.
                self.archive.mark("retracted", role="user", content=removed.get("content"))
            return True
        return False

    def truncate_last_assistant(self, *, mark: str = "\n\n[interrupted]") -> bool:
        """Cancel/recovery: shorten the last assistant turn and mark interruption."""
        if not self.messages or self.messages[-1].get("role") != "assistant":
            return False
        content = str(self.messages[-1].get("content") or "")
        # Keep a short prefix so context survives cancel without retaining a huge partial
        keep = content[:400].rstrip()
        if mark and mark.strip() not in keep:
            keep = f"{keep}{mark}" if keep else mark.strip()
        self.messages[-1]["content"] = keep
        if self.archive is not None:
            self.archive.mark("truncated", role="assistant", kept=keep)
        return True

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
