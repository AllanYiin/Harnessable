from __future__ import annotations

from uuid import uuid4

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.events import EventType, HarnessEvent
from harnessable.skills import SkillContextAssembler, SkillContextAssemblyRequest

from .base import BaseGateway
from .context import GatewayContext


class ContextAssemblyGateway(BaseGateway):
    before_event_type = EventType.CONTEXT_ASSEMBLY_REQUESTED
    after_event_type = EventType.CONTEXT_ASSEMBLED
    failed_event_type = EventType.RUN_FAILED

    def __init__(
        self,
        kernel: object,
        assembler: SkillContextAssembler,
        capability: CapabilityProfile | None = None,
    ) -> None:
        super().__init__(
            kernel,
            capability
            or CapabilityProfile(
                id="context.skill_assembly",
                type=CapabilityType.RESOURCE,
                compatibility_class="skill",
                supports=["metadata_selection", "progressive_hydration", "budget_events"],
            ),
        )
        self.assembler = assembler

    async def assemble(self, request: SkillContextAssemblyRequest, context: GatewayContext):
        return (await self.call(request, context)).value

    async def execute(self, request: SkillContextAssemblyRequest, context: GatewayContext):
        skill_context = self.assembler.assemble(request)
        for warning in skill_context.warnings:
            if str(warning.get("type", "")).endswith("budget_exceeded"):
                self.kernel.emit(
                    HarnessEvent(
                        event_id=f"evt_{uuid4().hex}",
                        run_id=context.run_id,
                        event_type=EventType.CONTEXT_BUDGET_EXCEEDED,
                        runtime_type=context.runtime_type,
                        actor={"role": context.actor_role},
                        capability=self.capability.to_dict(),
                        payload={"warning": warning, "selection": skill_context.selection.to_dict()},
                    )
                )
        return skill_context
