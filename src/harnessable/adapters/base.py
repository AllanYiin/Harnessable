from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from harnessable.events import HarnessEvent


class RuntimeAdapter(ABC):
    def __init__(self, kernel: object) -> None:
        self.kernel = kernel

    @abstractmethod
    def to_event(self, *args, **kwargs) -> HarnessEvent:
        raise NotImplementedError

    def apply_decision(self, decision):
        return self.kernel.governor.apply(decision)

    async def run_stream(self, *args, **kwargs) -> AsyncIterator[object]:
        raise NotImplementedError
