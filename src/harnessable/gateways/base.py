from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from harnessable.capabilities import CapabilityProfile
from harnessable.capabilities.health import CapabilityHealth
from harnessable.decisions import RuntimeCommandType
from harnessable.events import EventType, HarnessEvent

from .context import GatewayContext


@dataclass(slots=True)
class GatewayResult:
    ok: bool
    value: Any = None
    command: object | None = None
    error: Exception | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseGateway(ABC):
    before_event_type: EventType
    after_event_type: EventType
    failed_event_type: EventType

    def __init__(self, kernel: object, capability: CapabilityProfile) -> None:
        self.kernel = kernel
        self.capability = capability

    async def call(self, request: Any, context: GatewayContext) -> GatewayResult:
        health_monitor = getattr(self.kernel, "health", None)
        if health_monitor is not None:
            snapshot = health_monitor.get(self.capability.id)
            if snapshot.status in {CapabilityHealth.OPEN_CIRCUIT, CapabilityHealth.DISABLED}:
                return GatewayResult(ok=False, error=RuntimeError(f"capability unavailable: {snapshot.status.value}"))
        event = self._event(self.before_event_type, request, context)
        decision = self.kernel.emit(event)
        command = self.kernel.governor.apply(decision)
        if command.command_type in {RuntimeCommandType.BLOCK, RuntimeCommandType.ABORT, RuntimeCommandType.FAIL_SAFE, RuntimeCommandType.REQUEST_APPROVAL}:
            return GatewayResult(ok=False, command=command)
        if command.command_type == RuntimeCommandType.MUTATE and decision.mutation:
            request = decision.mutation.get("value", request)
        try:
            value = await self.execute(request, context)
        except Exception as exc:
            self.kernel.emit(self._event(self.failed_event_type, {"error": str(exc)}, context))
            return GatewayResult(ok=False, error=exc)
        self.kernel.emit(self._event(self.after_event_type, {"result": value}, context))
        return GatewayResult(ok=True, value=value, command=command)

    @abstractmethod
    async def execute(self, request: Any, context: GatewayContext) -> Any:
        raise NotImplementedError

    def _event(self, event_type: EventType, payload: Any, context: GatewayContext) -> HarnessEvent:
        return HarnessEvent(
            event_id=f"evt_{uuid4().hex}",
            run_id=context.run_id,
            event_type=event_type,
            runtime_type=context.runtime_type,
            actor={"role": context.actor_role},
            capability=self.capability.to_dict(),
            payload={"request": payload} if event_type == self.before_event_type else payload,
        )
