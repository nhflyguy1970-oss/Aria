"""Working buffer — capacity-limited focus with designed interference."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass
class BufferItem:
    kind: str  # concept | goal | percept | hypothesis | dialogue
    ref_id: str
    label: str
    attention: float = 0.5
    importance: float = 0.5
    entered: float = field(default_factory=time)
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkingBuffer:
    def __init__(self, capacity: int = 7) -> None:
        self.capacity = max(1, capacity)
        self._items: deque[BufferItem] = deque()

    def __len__(self) -> int:
        return len(self._items)

    def items(self) -> list[BufferItem]:
        return list(self._items)

    def push(self, item: BufferItem) -> list[BufferItem]:
        """Push item; return displaced items (interference)."""
        displaced: list[BufferItem] = []
        # Replace same ref
        self._items = deque(i for i in self._items if i.ref_id != item.ref_id)
        self._items.appendleft(item)
        while len(self._items) > self.capacity:
            # Dislodge lowest attention*importance from the back half
            victim_idx = min(
                range(len(self._items)),
                key=lambda i: self._items[i].attention * self._items[i].importance,
            )
            victim = self._items[victim_idx]
            del self._items[victim_idx]
            displaced.append(victim)
        return displaced

    def clear(self) -> None:
        self._items.clear()
