from __future__ import annotations

from harnessable.decisions import DecisionAggregator, HarnessDecision
from harnessable.detectors.registry import DetectorRegistry
from harnessable.detectors.results import DetectionOutcome
from harnessable.events import HarnessEvent

from .condition_engine import ConditionEngine
from .rule_registry import RuleRegistry


class RuleEngine:
    def __init__(
        self,
        registry: RuleRegistry | None = None,
        detectors: DetectorRegistry | None = None,
        aggregator: DecisionAggregator | None = None,
    ) -> None:
        self.registry = registry or RuleRegistry()
        self.detectors = detectors or DetectorRegistry()
        self.conditions = ConditionEngine()
        self.aggregator = aggregator or DecisionAggregator()

    def evaluate(self, event: HarnessEvent) -> HarnessDecision:
        decisions: list[HarnessDecision] = []
        for rule in self.registry.match(event):
            if not self.conditions.evaluate(rule.condition, event):
                continue
            detector = self.detectors.create_from_config(rule.detector)
            result = detector.evaluate(event)
            outcome = result.outcome.value if isinstance(result.outcome, DetectionOutcome) else str(result.outcome)
            effect = rule.effect_for(outcome)
            if outcome == "clean" and "when_clean" not in rule.action:
                effect = rule.effect_for("clean")
            decision = HarnessDecision(
                event_id=event.event_id,
                rule_id=rule.id,
                effect=effect,
                severity=rule.severity,
                confidence=result.confidence,
                reason=result.reason,
                telemetry=rule.telemetry,
                shadow=rule.shadow,
            )
            decisions.append(decision)
            if self.aggregator.is_terminal(decision.effect) and not decision.shadow:
                break
        return self.aggregator.merge(decisions, event.event_id)
