from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from harnessable.decisions import RuntimeCommandType
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import GatewayContext, ModelChunk, ModelGateway, ModelRequest

from .base import RuntimeAdapter


@dataclass(slots=True)
class ChatChunk:
    text: str


class ChatRuntimeAdapter(RuntimeAdapter):
    def __init__(self, kernel: object, model_gateway: ModelGateway | None = None) -> None:
        super().__init__(kernel)
        self.model_gateway = model_gateway or ModelGateway(kernel)

    def to_event(self, user_input: str, context: dict | None = None) -> HarnessEvent:
        context = context or {}
        return HarnessEvent(
            event_id=f"evt_{uuid4().hex}",
            run_id=context.get("run_id", f"run_{uuid4().hex}"),
            event_type=EventType.USER_INPUT_RECEIVED,
            runtime_type="chat",
            hook_point="before_input_accept",
            actor={"role": "user"},
            payload={"text": user_input},
            context=context,
        )

    async def run_stream(self, user_input: str, context: dict | None = None):
        event = self.to_event(user_input, context)
        decision = self.kernel.emit(event)
        command = self.apply_decision(decision)
        if command.command_type in {RuntimeCommandType.BLOCK, RuntimeCommandType.ABORT, RuntimeCommandType.FAIL_SAFE}:
            yield ChatChunk("")
            return
        gateway_context = GatewayContext(run_id=event.run_id, runtime_type="chat")
        async for chunk in self.model_gateway.call_stream(ModelRequest(user_input), gateway_context):
            yield ChatChunk(chunk.text if isinstance(chunk, ModelChunk) else str(chunk))
