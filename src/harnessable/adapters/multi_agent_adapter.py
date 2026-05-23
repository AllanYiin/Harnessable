from __future__ import annotations

from uuid import uuid4

from harnessable.events import EventType, HarnessEvent

from .base import RuntimeAdapter


class MultiAgentRuntimeAdapter(RuntimeAdapter):
    def to_event(self, target_agent: str, message: str = "", context: dict | None = None) -> HarnessEvent:
        context = context or {}
        return HarnessEvent(
            event_id=f"evt_{uuid4().hex}",
            run_id=context.get("run_id", f"run_{uuid4().hex}"),
            event_type=EventType.AGENT_HANDOFF_REQUESTED,
            runtime_type="multi_agent",
            hook_point="before_agent_handoff",
            actor={"role": context.get("actor_role", "coordinator")},
            capability={"type": "AGENT", "id": target_agent},
            payload={"target_agent": target_agent, "message": message},
            context=context,
        )

    def handoff(self, target_agent: str, message: str = "", context: dict | None = None):
        event = self.to_event(target_agent, message, context)
        return self.kernel.emit(event)
