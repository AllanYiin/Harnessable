from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.events import EventType

from .base import BaseGateway
from .context import GatewayContext


@dataclass(slots=True)
class MemoryReadRequest:
    key: str


@dataclass(slots=True)
class MemoryWriteRequest:
    key: str
    value: Any
    consent: bool = False


class MemoryGateway(BaseGateway):
    before_event_type = EventType.MEMORY_READ_REQUESTED
    after_event_type = EventType.MEMORY_READ_COMPLETED
    failed_event_type = EventType.MEMORY_READ_FAILED

    def __init__(self, kernel: object, capability: CapabilityProfile | None = None) -> None:
        super().__init__(kernel, capability or CapabilityProfile(id="memory.local", type=CapabilityType.MEMORY))
        self.store: dict[str, Any] = {}

    async def read(self, request: MemoryReadRequest, context: GatewayContext) -> Any:
        return (await self.call(request, context)).value

    async def write(self, request: MemoryWriteRequest, context: GatewayContext) -> Any:
        event_type = self.before_event_type
        self.before_event_type = EventType.MEMORY_WRITE_REQUESTED
        self.after_event_type = EventType.MEMORY_WRITE_COMPLETED
        self.failed_event_type = EventType.MEMORY_WRITE_FAILED
        try:
            return (await self.call(request, context)).value
        finally:
            self.before_event_type = event_type
            self.after_event_type = EventType.MEMORY_READ_COMPLETED
            self.failed_event_type = EventType.MEMORY_READ_FAILED

    async def execute(self, request: MemoryReadRequest | MemoryWriteRequest, context: GatewayContext) -> Any:
        if isinstance(request, MemoryWriteRequest):
            if not request.consent:
                raise PermissionError("memory write requires consent")
            self.store[request.key] = request.value
            return {"written": request.key}
        return self.store.get(request.key)
