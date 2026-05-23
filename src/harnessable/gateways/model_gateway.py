from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.events import EventType

from .base import BaseGateway
from .context import GatewayContext


@dataclass(slots=True)
class ModelRequest:
    prompt: str


@dataclass(slots=True)
class ModelChunk:
    text: str


class ModelGateway(BaseGateway):
    before_event_type = EventType.MODEL_CALL_REQUESTED
    after_event_type = EventType.MODEL_CALL_COMPLETED
    failed_event_type = EventType.MODEL_CALL_FAILED

    def __init__(self, kernel: object, capability: CapabilityProfile | None = None) -> None:
        super().__init__(kernel, capability or CapabilityProfile(id="model.local.echo", type=CapabilityType.MODEL, supports=["streaming"]))

    async def execute(self, request: ModelRequest, context: GatewayContext) -> str:
        return request.prompt

    async def call_stream(self, request: ModelRequest, context: GatewayContext) -> AsyncIterator[ModelChunk]:
        result = await self.call(request, context)
        if not result.ok:
            yield ModelChunk("")
            return
        for token in str(result.value).split(" "):
            yield ModelChunk(token + " ")
