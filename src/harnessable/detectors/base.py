from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from harnessable.events import HarnessEvent

from .results import DetectionResult


class HarnessDetector(ABC):
    detector_id: str

    @abstractmethod
    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        raise NotImplementedError


class StreamingDetector(HarnessDetector):
    async def evaluate_stream(self, event: HarnessEvent) -> AsyncIterator[str]:
        yield ""
