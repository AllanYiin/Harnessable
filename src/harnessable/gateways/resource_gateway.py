from __future__ import annotations

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.events import EventType

from .base import BaseGateway
from .context import GatewayContext


class ResourceGateway(BaseGateway):
    before_event_type = EventType.RESOURCE_READ_REQUESTED
    after_event_type = EventType.RESOURCE_READ_COMPLETED
    failed_event_type = EventType.RUN_FAILED

    def __init__(self, kernel: object, resources: dict | None = None, capability: CapabilityProfile | None = None) -> None:
        super().__init__(kernel, capability or CapabilityProfile(id="resource.local", type=CapabilityType.RESOURCE))
        self.resources = resources or {}

    async def execute(self, request: dict, context: GatewayContext):
        return self.resources.get(request.get("key"))
