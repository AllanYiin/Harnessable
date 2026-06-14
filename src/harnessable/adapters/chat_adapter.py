from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from harnessable.decisions import HarnessDecision, RuntimeCommand, RuntimeCommandType
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import GatewayContext, ModelChunk, ModelGateway, ModelRequest

from .base import RuntimeAdapter


@dataclass(slots=True)
class ChatChunk:
    text: str
    command: RuntimeCommand | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


TERMINAL_CHAT_COMMANDS = {
    RuntimeCommandType.BLOCK,
    RuntimeCommandType.ABORT,
    RuntimeCommandType.FAIL_SAFE,
    RuntimeCommandType.REQUEST_APPROVAL,
    RuntimeCommandType.ROLLBACK,
}


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
        if command.command_type in TERMINAL_CHAT_COMMANDS:
            yield ChatChunk("", command=command, metadata={"stopped": True})
            return
        request, gateway_context, metadata = self._dispatch_request(user_input, event, decision, command)
        async for chunk in self.model_gateway.call_stream(request, gateway_context):
            yield ChatChunk(chunk.text if isinstance(chunk, ModelChunk) else str(chunk), command=command, metadata=metadata)

    def _dispatch_request(
        self,
        user_input: str,
        event: HarnessEvent,
        decision: HarnessDecision,
        command: RuntimeCommand,
    ) -> tuple[ModelRequest, GatewayContext, dict[str, Any]]:
        metadata: dict[str, Any] = {"runtime_command": command.command_type.value}
        prompt = user_input
        if command.command_type == RuntimeCommandType.MUTATE:
            mutation = decision.mutation or {}
            prompt = str(mutation.get("value", mutation.get("text", mutation.get("prompt", user_input))))
            metadata["mutation"] = mutation
        elif command.command_type == RuntimeCommandType.RETRY:
            retry = decision.retry or {}
            prompt = str(retry.get("value", retry.get("text", retry.get("prompt", user_input))))
            metadata["retry"] = retry
        elif command.command_type == RuntimeCommandType.ROUTE:
            metadata["route"] = decision.route or {}
        gateway_context = GatewayContext(run_id=event.run_id, runtime_type="chat", metadata=metadata)
        return ModelRequest(prompt), gateway_context, metadata
