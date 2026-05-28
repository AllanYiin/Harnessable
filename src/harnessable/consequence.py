from __future__ import annotations

from harnessable.events import EventType
from harnessable.rules import HarnessRule


class ConsequenceGate:
    """Installs generalized release-risk rules without incident-specific blacklists."""

    RULE_PREFIX = "governance.consequence"

    @classmethod
    def install(cls, kernel: object, shadow: bool = False) -> list[HarnessRule]:
        rules = cls.rules(shadow=shadow)
        for rule in rules:
            kernel.register_rule(rule)
        return rules

    @classmethod
    def rules(cls, shadow: bool = False) -> list[HarnessRule]:
        draft_events = [
            EventType.BRIEF_PROPOSED.value,
            EventType.DRAFT_PROPOSED.value,
            EventType.ASSET_PROPOSED.value,
            EventType.RELEASE_SCHEDULED.value,
            EventType.FINAL_OUTPUT_PROPOSED.value,
        ]
        publication_events = [EventType.PUBLICATION_REQUESTED.value]
        return [
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.context_gap.draft.v1",
                name="Consequence context gaps on content lifecycle",
                shadow=shadow,
                applies_to={"event_types": draft_events, "runtimes": ["chat", "agent", "multi_agent"]},
                detector={"type": "context_gap_detector"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.context_gap.publication.v1",
                name="Consequence context gaps before publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "context_gap_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.context_gap.public_action.v1",
                name="Consequence context gaps before public external action",
                shadow=shadow,
                applies_to={"event_types": ["TOOL_CALL_REQUESTED"], "capability_types": ["EXTERNAL_ACTION"]},
                condition={"field": "capability.risk.public_impact", "equals": True},
                detector={"type": "context_gap_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.stakeholder.publication.v1",
                name="Stakeholder harm hypotheses before publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "stakeholder_harm_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.misread.publication.v1",
                name="Misread simulation before publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "misread_simulator"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.power_asymmetry.publication.v1",
                name="Power asymmetry commercialization guard",
                shadow=shadow,
                applies_to={"event_types": publication_events + [EventType.FINAL_OUTPUT_PROPOSED.value]},
                detector={"type": "power_asymmetry_detector"},
                action={"when_detected": {"type": "BLOCK"}, "when_clean": {"type": "ALLOW"}},
                severity="critical",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.release_pressure.publication.v1",
                name="Release pressure guard",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "release_pressure_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
        ]
