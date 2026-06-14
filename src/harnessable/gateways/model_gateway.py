from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Callable

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.decisions import RuntimeCommandType
from harnessable.events import EventType

from .base import BaseGateway
from .context import GatewayContext


@dataclass(slots=True)
class ModelRequest:
    prompt: str


@dataclass(slots=True)
class ModelChunk:
    text: str
    usage: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelGateway(BaseGateway):
    before_event_type = EventType.MODEL_CALL_REQUESTED
    after_event_type = EventType.MODEL_CALL_COMPLETED
    failed_event_type = EventType.MODEL_CALL_FAILED

    def __init__(
        self,
        kernel: object,
        capability: CapabilityProfile | None = None,
        stream_provider: Callable[[ModelRequest, GatewayContext], AsyncIterator[ModelChunk]] | None = None,
    ) -> None:
        super().__init__(kernel, capability or CapabilityProfile(id="model.local.echo", type=CapabilityType.MODEL, supports=["streaming"]))
        self.stream_provider = stream_provider

    async def execute(self, request: ModelRequest, context: GatewayContext) -> str:
        return request.prompt

    async def call_stream(self, request: ModelRequest, context: GatewayContext) -> AsyncIterator[ModelChunk]:
        if self.stream_provider is not None:
            async for chunk in self._call_provider_stream(request, context):
                yield chunk
            return
        result = await self.call(request, context)
        if not result.ok:
            yield ModelChunk("")
            return
        for token in str(result.value).split(" "):
            yield ModelChunk(token + " ")

    async def _call_provider_stream(self, request: ModelRequest, context: GatewayContext) -> AsyncIterator[ModelChunk]:
        plugins = getattr(self.kernel, "plugins", None)
        if plugins is not None:
            request = plugins.run_before_gateway_call(request, context, self.capability)
        event = self._event(self.before_event_type, request, context)
        decision = self.kernel.emit(event)
        command = self.kernel.governor.apply(decision)
        if command.command_type in {RuntimeCommandType.BLOCK, RuntimeCommandType.ABORT, RuntimeCommandType.FAIL_SAFE, RuntimeCommandType.REQUEST_APPROVAL}:
            yield ModelChunk("")
            return
        if command.command_type == RuntimeCommandType.MUTATE and decision.mutation:
            request = decision.mutation.get("value", request)
        chunks: list[ModelChunk] = []
        try:
            async for chunk in self.stream_provider(request, context):
                chunks.append(chunk)
                yield chunk
        except Exception as exc:
            self.kernel.emit(self._event(self.failed_event_type, {"error": str(exc)}, context))
            yield ModelChunk("")
            return
        usage = {}
        for chunk in chunks:
            if chunk.usage:
                usage = dict(chunk.usage)
        self.kernel.emit(self._event(self.after_event_type, {"chunks": len(chunks), "usage": usage or {"status": "unknown"}}, context))
