from __future__ import annotations

from harnessable.events import EventType
from harnessable.rules import HarnessRule


class ConsequenceGate:
    """Installs generalized release-risk rules without incident-specific blacklists."""

    RULE_PREFIX = "governance.consequence"
    PREVIEW_CONDITION = {"field": "metadata.consequence_gate_enabled", "equals": True}

    @classmethod
    def install(cls, kernel: object, shadow: bool = False) -> list[HarnessRule]:
        rules = cls.rules(shadow=shadow)
        for rule in rules:
            kernel.register_rule(rule)
        return rules

    @classmethod
    def install_preview(cls, kernel: object, shadow: bool = False) -> list[HarnessRule]:
        rules = cls.preview_rules(shadow=shadow)
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
        public_action_events = ["TOOL_CALL_REQUESTED"]
        publication_context_fields = cls.publication_context_fields()
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
                detector={"type": "context_gap_detector", "required_fields": publication_context_fields},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.context_gap.public_action.v1",
                name="Consequence context gaps before public external action",
                shadow=shadow,
                applies_to={"event_types": public_action_events, "capability_types": ["EXTERNAL_ACTION"]},
                condition={"field": "capability.risk.public_impact", "equals": True},
                detector={"type": "context_gap_detector", "required_fields": publication_context_fields},
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
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.claim_evidence.publication.v1",
                name="Claim evidence guard before publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "claim_evidence_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.claim_evidence.public_action.v1",
                name="Claim evidence guard before public external action",
                shadow=shadow,
                applies_to={"event_types": public_action_events, "capability_types": ["EXTERNAL_ACTION"]},
                condition={"field": "capability.risk.public_impact", "equals": True},
                detector={"type": "claim_evidence_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.offer_disclosure.publication.v1",
                name="Offer disclosure guard before publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "offer_disclosure_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.provenance.publication.v1",
                name="Provenance and rights metadata guard before publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "provenance_metadata_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.provenance.public_action.v1",
                name="Provenance and rights metadata guard before public external action",
                shadow=shadow,
                applies_to={"event_types": public_action_events, "capability_types": ["EXTERNAL_ACTION"]},
                condition={"field": "capability.risk.public_impact", "equals": True},
                detector={"type": "provenance_metadata_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.scanner_coverage.asset_lifecycle.v1",
                name="Scanner coverage preview for high-risk assets",
                shadow=shadow,
                applies_to={"event_types": [EventType.ASSET_PROPOSED.value, EventType.FINAL_OUTPUT_PROPOSED.value]},
                detector={"type": "scanner_coverage_detector"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.scanner_coverage.publication.v1",
                name="Required scanner coverage before publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "scanner_coverage_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.scanner_coverage.public_action.v1",
                name="Required scanner coverage before public external action",
                shadow=shadow,
                applies_to={"event_types": public_action_events, "capability_types": ["EXTERNAL_ACTION"]},
                condition={"field": "capability.risk.public_impact", "equals": True},
                detector={"type": "scanner_coverage_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.scanner_result.publication.v1",
                name="External scanner result guard before publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "scanner_result_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.scanner_result.public_action.v1",
                name="External scanner result guard before public external action",
                shadow=shadow,
                applies_to={"event_types": public_action_events, "capability_types": ["EXTERNAL_ACTION"]},
                condition={"field": "capability.risk.public_impact", "equals": True},
                detector={"type": "scanner_result_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.rollback.publication.v1",
                name="Rollback readiness guard before high exposure publication",
                shadow=shadow,
                applies_to={"event_types": publication_events, "capability_types": ["EXTERNAL_ACTION"]},
                detector={"type": "rollback_readiness_detector"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"gate": "consequence"},
            ),
        ]

    @classmethod
    def preview_rules(
        cls,
        shadow: bool = False,
        *,
        event_types: list[str] | None = None,
        runtimes: list[str] | None = None,
        condition: dict | None = None,
    ) -> list[HarnessRule]:
        preview_events = event_types or [EventType.FINAL_OUTPUT_PROPOSED.value]
        preview_runtimes = runtimes or ["chat"]
        enabled_condition = condition or cls.PREVIEW_CONDITION
        applies_to = {"event_types": preview_events, "runtimes": preview_runtimes}
        return [
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.preview.context_gap.v1",
                name="Consequence publishing context preview",
                shadow=shadow,
                applies_to=applies_to,
                condition=enabled_condition,
                detector={"type": "context_gap_detector", "required_fields": cls.publication_context_fields()},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence", "preview": True},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.preview.claim_evidence.v1",
                name="Consequence claim evidence preview",
                shadow=shadow,
                applies_to=applies_to,
                condition=enabled_condition,
                detector={"type": "claim_evidence_detector"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence", "preview": True},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.preview.offer_disclosure.v1",
                name="Consequence offer disclosure preview",
                shadow=shadow,
                applies_to=applies_to,
                condition=enabled_condition,
                detector={"type": "offer_disclosure_detector"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence", "preview": True},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.preview.provenance.v1",
                name="Consequence provenance preview",
                shadow=shadow,
                applies_to=applies_to,
                condition=enabled_condition,
                detector={"type": "provenance_metadata_detector"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence", "preview": True},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.preview.scanner_coverage.v1",
                name="Consequence scanner coverage preview",
                shadow=shadow,
                applies_to=applies_to,
                condition=enabled_condition,
                detector={"type": "scanner_coverage_detector"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence", "preview": True},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.preview.scanner_result.v1",
                name="Consequence scanner result preview",
                shadow=shadow,
                applies_to=applies_to,
                condition=enabled_condition,
                detector={"type": "scanner_result_detector"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence", "preview": True},
            ),
            HarnessRule(
                id=f"{cls.RULE_PREFIX}.preview.rollback.v1",
                name="Consequence rollback readiness preview",
                shadow=shadow,
                applies_to=applies_to,
                condition=enabled_condition,
                detector={"type": "rollback_readiness_detector"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"gate": "consequence", "preview": True},
            ),
        ]

    @staticmethod
    def publication_context_fields() -> list[str]:
        return [
            "jurisdiction",
            "market",
            "locale",
            "release_at",
            "publish_window",
            "audience",
            "channel",
            "intent",
            "asset_hash",
            "artifact_refs",
            "ai_generated",
        ]
