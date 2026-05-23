from __future__ import annotations

from .effects import DecisionEffect
from .priority import priority
from .schemas import HarnessDecision


class DecisionAggregator:
    def merge(self, decisions: list[HarnessDecision], event_id: str) -> HarnessDecision:
        active = [d for d in decisions if not d.shadow]
        if not active:
            merged = HarnessDecision.allow(event_id)
            merged.contributing_decisions = [d.to_dict() for d in decisions]
            return merged
        winner = max(active, key=lambda d: priority(d.effect))
        merged = HarnessDecision.from_dict(winner.to_dict())
        merged.contributing_decisions = [d.to_dict() for d in decisions]
        return merged

    @staticmethod
    def is_terminal(effect: DecisionEffect) -> bool:
        return effect in {DecisionEffect.BLOCK, DecisionEffect.ABORT, DecisionEffect.FAIL_SAFE}
