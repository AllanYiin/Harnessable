from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.events import EventType

from .base import BaseGateway
from .context import GatewayContext


@dataclass(slots=True)
class ToolCallRequest:
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False
    idempotency_key: str | None = None


@dataclass(slots=True)
class ToolCallResult:
    value: Any


class ToolGateway(BaseGateway):
    before_event_type = EventType.TOOL_CALL_REQUESTED
    after_event_type = EventType.TOOL_CALL_COMPLETED
    failed_event_type = EventType.TOOL_CALL_FAILED

    def __init__(self, kernel: object, tools: dict[str, Callable[..., Any]] | None = None, capability: CapabilityProfile | None = None) -> None:
        super().__init__(kernel, capability or CapabilityProfile(id="tool.local", type=CapabilityType.TOOL))
        self.tools = tools or {}

    async def execute(self, request: ToolCallRequest, context: GatewayContext) -> ToolCallResult:
        if request.dry_run:
            return ToolCallResult({"dry_run": True, "tool": request.name})
        func = self.tools.get(request.name)
        if not func:
            raise ValueError(f"tool not registered: {request.name}")
        return ToolCallResult(func(**request.args))
