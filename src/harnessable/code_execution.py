from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.rules import HarnessRule


CODE_EXECUTION_COMPATIBILITY_CLASS = "code_execution"
CODE_EXECUTION_RULE_PREFIX = "governance.code_execution"


@dataclass(slots=True)
class CodeExecutionContract:
    backend: str
    filesystem: dict[str, Any] = field(default_factory=dict)
    network: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=lambda: {"mode": "one_shot"})
    trust_level: str = "preview"
    enforcement_gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "filesystem": dict(self.filesystem),
            "network": dict(self.network),
            "resources": dict(self.resources),
            "state": dict(self.state),
            "trust_level": self.trust_level,
            "enforcement_gaps": list(self.enforcement_gaps),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeExecutionContract":
        return cls(
            backend=str(data.get("backend") or ""),
            filesystem=dict(data.get("filesystem") or {}),
            network=dict(data.get("network") or {}),
            resources=dict(data.get("resources") or {}),
            state=dict(data.get("state") or {"mode": "one_shot"}),
            trust_level=str(data.get("trust_level") or "preview"),
            enforcement_gaps=list(data.get("enforcement_gaps") or []),
        )


def code_execution_capability(
    *,
    capability_id: str,
    backend: str,
    filesystem: dict[str, Any] | None = None,
    network: dict[str, Any] | None = None,
    resources: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    trust_level: str = "preview",
    enforcement_gaps: list[str] | None = None,
    supports: list[str] | None = None,
) -> CapabilityProfile:
    contract = CodeExecutionContract(
        backend=backend,
        filesystem=filesystem or {},
        network=network or {},
        resources=resources or {},
        state=state or {"mode": "one_shot"},
        trust_level=trust_level,
        enforcement_gaps=enforcement_gaps or [],
    )
    return CapabilityProfile(
        id=capability_id,
        type=CapabilityType.TOOL,
        compatibility_class=CODE_EXECUTION_COMPATIBILITY_CLASS,
        contracts={"code_execution": contract.to_dict()},
        supports=supports or ["code_execution", "one_shot"],
        risk={"side_effect": False, "untrusted_code": True},
        permissions={"allowed_roles": ["agent", "assistant"]},
        fallback={"same_or_stricter_data_policy_required": True},
    )


class CodeExecutionHarness:
    @classmethod
    def install(cls, kernel: object, shadow: bool = False) -> list[HarnessRule]:
        rules = cls.rules(shadow=shadow)
        for rule in rules:
            kernel.register_rule(rule)
        return rules

    @classmethod
    def rules(cls, shadow: bool = False) -> list[HarnessRule]:
        applies = {
            "event_types": ["TOOL_CALL_REQUESTED"],
            "runtimes": ["chat", "agent", "multi_agent"],
            "capability_types": ["TOOL"],
        }
        condition = {"field": "capability.compatibility_class", "equals": CODE_EXECUTION_COMPATIBILITY_CLASS}
        return [
            HarnessRule(
                id=f"{CODE_EXECUTION_RULE_PREFIX}.block_secret_or_broad_write.v1",
                name="Code execution secret and broad write guard",
                applies_to=applies,
                condition=condition,
                detector={"type": "code_execution_policy_detector", "bucket": "block"},
                action={"when_detected": {"type": "BLOCK"}, "when_clean": {"type": "ALLOW"}},
                severity="high",
                telemetry={"module": "code_execution"},
                shadow=shadow,
            ),
            HarnessRule(
                id=f"{CODE_EXECUTION_RULE_PREFIX}.approval_for_open_network_or_missing_limits.v1",
                name="Code execution approval guard",
                applies_to=applies,
                condition=condition,
                detector={"type": "code_execution_policy_detector", "bucket": "approval"},
                action={"when_detected": {"type": "REQUIRE_APPROVAL"}, "when_clean": {"type": "ALLOW"}},
                severity="medium",
                telemetry={"module": "code_execution"},
                shadow=shadow,
            ),
            HarnessRule(
                id=f"{CODE_EXECUTION_RULE_PREFIX}.warn_preview_gaps.v1",
                name="Code execution preview enforcement gap warning",
                applies_to=applies,
                condition=condition,
                detector={"type": "code_execution_policy_detector", "bucket": "warn"},
                action={"when_detected": {"type": "WARN"}, "when_clean": {"type": "ALLOW"}},
                severity="low",
                telemetry={"module": "code_execution"},
                shadow=shadow,
            ),
        ]
