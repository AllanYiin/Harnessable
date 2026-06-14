from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from harnessable.capabilities import CONTRACT_KEY, CapabilityProfile
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
        plugins = getattr(self.kernel, "plugins", None)
        health_monitor = getattr(self.kernel, "health", None)
        if health_monitor is not None:
            snapshot = health_monitor.get(self.capability.id)
            if snapshot.status in {CapabilityHealth.OPEN_CIRCUIT, CapabilityHealth.DISABLED}:
                return GatewayResult(ok=False, error=RuntimeError(f"capability unavailable: {snapshot.status.value}"))
        if plugins is not None:
            request = plugins.run_before_gateway_call(request, context, self.capability)
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
        result = GatewayResult(ok=True, value=value, command=command)
        if plugins is not None:
            result = plugins.run_after_gateway_call(result, context, self.capability)
        self.kernel.emit(self._event(self.after_event_type, {"result": result.value}, context))
        return result

    @abstractmethod
    async def execute(self, request: Any, context: GatewayContext) -> Any:
        raise NotImplementedError

    def _event(self, event_type: EventType, payload: Any, context: GatewayContext) -> HarnessEvent:
        contract = self.capability.contracts.get(CONTRACT_KEY) or {}
        metadata = {
            "external_capability_contract": contract,
            "external_capability_warnings": list(contract.get("warnings") or []) if isinstance(contract, dict) else [],
        }
        if isinstance(payload, dict) and "usage" in payload:
            metadata["usage"] = payload["usage"]
        return HarnessEvent(
            event_id=f"evt_{uuid4().hex}",
            run_id=context.run_id,
            event_type=event_type,
            runtime_type=context.runtime_type,
            actor={"role": context.actor_role},
            capability=self.capability.to_dict(),
            payload={"request": payload} if event_type == self.before_event_type else payload,
            metadata=metadata,
        )
