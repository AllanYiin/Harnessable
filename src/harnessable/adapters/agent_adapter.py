from __future__ import annotations

from uuid import uuid4

from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import GatewayContext, ToolCallRequest, ToolGateway

from .base import RuntimeAdapter


class AgentRuntimeAdapter(RuntimeAdapter):
    def __init__(self, kernel: object, tool_gateway: ToolGateway | None = None) -> None:
        super().__init__(kernel)
        self.tool_gateway = tool_gateway or ToolGateway(kernel)

    def to_event(self, tool_name: str, context: dict | None = None) -> HarnessEvent:
        context = context or {}
        return HarnessEvent(
            event_id=f"evt_{uuid4().hex}",
            run_id=context.get("run_id", f"run_{uuid4().hex}"),
            event_type=EventType.TOOL_CALL_REQUESTED,
            runtime_type="agent",
            hook_point="before_tool_call",
            actor={"role": context.get("actor_role", "assistant")},
            capability={"type": "TOOL", "id": f"tool.{tool_name}"},
            payload={"tool": tool_name},
            context=context,
        )

    async def call_tool(self, name: str, args: dict | None = None, context: dict | None = None):
        event = self.to_event(name, context)
        decision = self.kernel.emit(event)
        command = self.apply_decision(decision)
        if command.command_type.value != "CONTINUE":
            return command
        return await self.tool_gateway.call(ToolCallRequest(name=name, args=args or {}), GatewayContext(run_id=event.run_id))
