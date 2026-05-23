from __future__ import annotations

from dataclasses import dataclass, field

from harnessable.decisions import DecisionEffect, HarnessDecision
from harnessable.events import HarnessEvent

from .degradation_budget import DegradationBudget
from .failure_signal import FailureCategory, FailureSignal
from .fallback_graph import FallbackGraphPlanner, FallbackStep
from .fallback_policy_registry import FallbackPolicyRegistry


@dataclass(slots=True)
class FallbackPlan:
    steps: list[FallbackStep] = field(default_factory=list)
    decision: HarnessDecision | None = None
    disclosure_required: bool = False
    blocked_reason: str | None = None


class FallbackManager:
    def __init__(self, policies: FallbackPolicyRegistry | None = None) -> None:
        self.policies = policies or FallbackPolicyRegistry()
        self.planner = FallbackGraphPlanner()

    def plan(self, event: HarnessEvent, signal: FailureSignal, budget: DegradationBudget | None = None) -> FallbackPlan:
        budget = budget or DegradationBudget()
        if signal.category == FailureCategory.SIDE_EFFECT_UNKNOWN:
            return FallbackPlan(decision=HarnessDecision(event_id=event.event_id, effect=DecisionEffect.REQUIRE_APPROVAL))
        if budget.exhausted():
            return FallbackPlan(decision=HarnessDecision(event_id=event.event_id, effect=DecisionEffect.FAIL_SAFE))
        matched = self.policies.match(event, signal)
        if not matched:
            return FallbackPlan(decision=HarnessDecision(event_id=event.event_id, effect=DecisionEffect.FAIL_SAFE))
        policy = matched[0]
        steps = self.planner.plan(policy.fallback_graph)
        never_degrade = set((policy.constraints or {}).get("never_degrade") or [])
        for step in steps:
            selector = step.selector or {}
            if selector.get("same_or_stricter_data_policy") is False or selector.get("same_or_stricter_permission_boundary") is False:
                return FallbackPlan(
                    decision=HarnessDecision(
                        event_id=event.event_id,
                        effect=DecisionEffect.BLOCK,
                        reason={"code": "UNSAFE_FALLBACK_TARGET"},
                    ),
                    blocked_reason="unsafe fallback target",
                )
            if "tool_permission" in never_degrade and selector.get("permission_boundary") == "wider":
                return FallbackPlan(
                    decision=HarnessDecision(event_id=event.event_id, effect=DecisionEffect.BLOCK, reason={"code": "FALLBACK_WOULD_DEGRADE_PERMISSION"}),
                    blocked_reason="permission boundary cannot be degraded",
                )
        disclosure_required = any(step.disclosure and step.disclosure.get("required") for step in steps)
        return FallbackPlan(steps=steps, disclosure_required=disclosure_required)
