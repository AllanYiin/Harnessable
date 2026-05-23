from __future__ import annotations

from harnessable.capabilities import CapabilityHealthMonitor, CapabilityProfile, CapabilityRegistry
from harnessable.decisions import ExecutionGovernor, HarnessDecision
from harnessable.detectors import HarnessDetector
from harnessable.events import EventBus, HarnessEvent
from harnessable.evals import ReplayEngine, ReplayReport
from harnessable.observability import AuditLogger, MetricsCollector, TraceRecorder
from harnessable.project import HarnessProject
from harnessable.rules import HarnessRule, RuleEngine, RuleRegistry
from harnessable.rules.rule_loader import load_rules


class HarnessKernel:
    def __init__(
        self,
        project: HarnessProject | None = None,
        rules: RuleRegistry | None = None,
        capabilities: CapabilityRegistry | None = None,
    ) -> None:
        self.project = project
        self.events = EventBus()
        self.rules = rules or RuleRegistry()
        self.capabilities = capabilities or CapabilityRegistry()
        self.health = CapabilityHealthMonitor()
        self.rule_engine = RuleEngine(self.rules)
        self.governor = ExecutionGovernor()
        self.traces = TraceRecorder()
        self.audit = AuditLogger()
        self.metrics = MetricsCollector()

    @classmethod
    def from_project(cls, project: HarnessProject) -> "HarnessKernel":
        kernel = cls(project=project)
        rules_path = project.path / "rules"
        if rules_path.exists():
            for rule in load_rules(rules_path):
                kernel.register_rule(rule)
        return kernel

    def emit(self, event: HarnessEvent) -> HarnessDecision:
        self.events.emit(event)
        self.traces.record("event", event.to_dict())
        decision = self.rule_engine.evaluate(event)
        self.traces.record("decision", decision.to_dict())
        self.audit.record("decision", decision.to_dict())
        self.metrics.increment(f"decision.{decision.effect.value}")
        if self.project:
            self.project.state.append_event(event.run_id, {"event": event.to_dict(), "decision": decision.to_dict()})
        return decision

    async def emit_async(self, event: HarnessEvent) -> HarnessDecision:
        return self.emit(event)

    def emit_from_dict(self, event: dict) -> HarnessDecision:
        return self.emit(HarnessEvent.from_dict(event))

    def register_rule(self, rule: HarnessRule) -> None:
        self.rules.add(rule)

    def register_detector(self, detector: HarnessDetector) -> None:
        self.rule_engine.detectors.register(detector)

    def register_capability(self, capability: CapabilityProfile) -> None:
        self.capabilities.add(capability)

    def replay(self, run_id: str, policy_profile: str | None = None) -> ReplayReport:
        if not self.project:
            return ReplayReport(run_id=run_id, decisions=[])
        records = self.project.state.read_events(run_id)
        events = [record["event"] for record in records]
        decisions = ReplayEngine(self).replay(events)
        return ReplayReport(run_id=run_id, decisions=decisions)
