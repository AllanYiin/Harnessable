from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.consequence import ConsequenceGate
from harnessable.core.errors import PolicyViolationError
from harnessable.events import EventType
from harnessable.risk import RiskContext

from .base import BaseGateway
from .context import GatewayContext


@dataclass(slots=True)
class PublicationRequest:
    name: str
    content: str | dict[str, Any] = ""
    destination: str | None = None
    risk_context: RiskContext | dict[str, Any] | None = None
    risk_evidence: dict[str, Any] = field(default_factory=dict)
    args: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False
    idempotency_key: str | None = None


class PublicationGateway(BaseGateway):
    before_event_type = EventType.PUBLICATION_REQUESTED
    after_event_type = EventType.PUBLICATION_COMPLETED
    failed_event_type = EventType.PUBLICATION_FAILED

    def __init__(
        self,
        kernel: object,
        publishers: dict[str, Callable[..., Any]] | None = None,
        capability: CapabilityProfile | None = None,
        install_consequence_gate: bool = True,
    ) -> None:
        super().__init__(
            kernel,
            capability
            or CapabilityProfile(
                id="publication.local",
                type=CapabilityType.EXTERNAL_ACTION,
                supports=["publication"],
                risk={"side_effect": True, "public_impact": True},
            ),
        )
        self.publishers = publishers or {}
        if install_consequence_gate:
            ConsequenceGate.install(kernel)

    async def execute(self, request: PublicationRequest, context: GatewayContext) -> Any:
        if self.capability.risk.get("side_effect") and not request.idempotency_key:
            raise PolicyViolationError("publication action requires idempotency_key")
        if request.dry_run:
            return {"dry_run": True, "publisher": request.name, "destination": request.destination}
        publisher = self.publishers.get(request.name)
        if not publisher:
            raise ValueError(f"publisher not registered: {request.name}")
        return publisher(content=request.content, destination=request.destination, **request.args)
