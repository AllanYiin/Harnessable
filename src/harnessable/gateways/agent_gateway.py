from __future__ import annotations

from dataclasses import dataclass

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.events import EventType

from .base import BaseGateway
from .context import GatewayContext


@dataclass(slots=True)
class AgentHandoffRequest:
    target_agent: str
    message: str


class AgentGateway(BaseGateway):
    before_event_type = EventType.AGENT_HANDOFF_REQUESTED
    after_event_type = EventType.AGENT_HANDOFF_COMPLETED
    failed_event_type = EventType.AGENT_HANDOFF_FAILED

    def __init__(self, kernel: object, capability: CapabilityProfile | None = None) -> None:
        super().__init__(kernel, capability or CapabilityProfile(id="agent.local", type=CapabilityType.AGENT))

    async def execute(self, request: AgentHandoffRequest, context: GatewayContext):
        return {"target_agent": request.target_agent, "message": request.message}
