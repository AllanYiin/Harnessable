from __future__ import annotations

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.core.errors import PolicyViolationError

from .context import GatewayContext
from .tool_gateway import ToolCallRequest, ToolGateway


class ActionGateway(ToolGateway):
    def __init__(self, kernel: object, tools: dict | None = None, capability: CapabilityProfile | None = None) -> None:
        super().__init__(
            kernel,
            tools=tools,
            capability=capability
            or CapabilityProfile(id="action.local", type=CapabilityType.EXTERNAL_ACTION, risk={"side_effect": True}),
        )

    async def execute(self, request: ToolCallRequest, context: GatewayContext):
        if self.capability.risk.get("side_effect") and not request.idempotency_key:
            raise PolicyViolationError("side-effect action requires idempotency_key")
        return await super().execute(request, context)
