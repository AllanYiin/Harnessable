from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from harnessable.core.errors import ValidationError

from .schemas import CapabilityProfile, CapabilityType

CONTRACT_KEY = "external_capability"

_PROTOCOL_TO_TYPE = {
    "function": CapabilityType.TOOL,
    "mcp": CapabilityType.TOOL,
    "a2a": CapabilityType.AGENT,
    "http": CapabilityType.TOOL,
    "provider": CapabilityType.MODEL,
    "sandbox": CapabilityType.TOOL,
    "filesystem": CapabilityType.RESOURCE,
}

_DATA_CLASSIFICATION_RANK = {"public": 0, "internal": 1, "confidential": 2, "secret": 3, "unknown": 4}
_EXFILTRATION_RISK_RANK = {"low": 0, "medium": 1, "high": 2, "unknown": 3}
_NETWORK_SCOPE_RANK = {"none": 0, "allowlisted": 1, "internet": 2, "unknown": 3}
_DESTRUCTIVE_RANK = {"none": 0, "reversible": 1, "irreversible": 2, "unknown": 3}


@dataclass(slots=True)
class ExternalCapabilityContract:
    capability_id: str
    protocol: str
    schema_version: str = "1"
    descriptor_hash: str | None = None
    source_trust: str = "unknown"
    schema_ref: str | None = None
    input_schema_hash: str | None = None
    output_schema_hash: str | None = None
    risk_labels: list[str] = field(default_factory=list)
    risk: dict[str, Any] = field(default_factory=dict)
    approval_route: dict[str, Any] = field(default_factory=dict)
    tenant_constraints: dict[str, Any] = field(default_factory=dict)
    purpose_constraints: dict[str, Any] = field(default_factory=dict)
    cost_budget: dict[str, Any] = field(default_factory=dict)
    latency_budget: dict[str, Any] = field(default_factory=dict)
    data_access_scope: dict[str, Any] = field(default_factory=dict)
    side_effect_profile: dict[str, Any] = field(default_factory=dict)
    audit_required: bool = True
    fallback_allowed: bool = True
    observability: dict[str, Any] = field(default_factory=dict)
    raw_descriptor: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.capability_id:
            raise ValidationError("external capability contract id is required")
        if self.protocol not in _PROTOCOL_TO_TYPE:
            raise ValidationError(f"unsupported external capability protocol: {self.protocol}")
        self.risk_labels = [str(label) for label in self.risk_labels]
        self.warnings = sorted(set([*self.warnings, *self.validation_warnings()]))

    def validation_warnings(self) -> list[str]:
        warnings = []
        if not self.descriptor_hash:
            warnings.append("missing_descriptor_hash")
        if not self.input_schema_hash:
            warnings.append("missing_input_schema_hash")
        if self.protocol in {"mcp", "a2a", "provider", "http"} and not self.output_schema_hash:
            warnings.append("missing_output_schema_hash")
        if self.risk_labels and not self.approval_route:
            warnings.append("missing_approval_route")
        if not self.tenant_constraints:
            warnings.append("missing_tenant_constraints")
        if not self.purpose_constraints:
            warnings.append("missing_purpose_constraints")
        return warnings

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "protocol": self.protocol,
            "descriptor_hash": self.descriptor_hash,
            "source_trust": self.source_trust,
            "schema_ref": self.schema_ref,
            "input_schema_hash": self.input_schema_hash,
            "output_schema_hash": self.output_schema_hash,
            "risk_labels": list(self.risk_labels),
            "risk": dict(self.risk),
            "approval_route": dict(self.approval_route),
            "tenant_constraints": dict(self.tenant_constraints),
            "purpose_constraints": dict(self.purpose_constraints),
            "cost_budget": dict(self.cost_budget),
            "latency_budget": dict(self.latency_budget),
            "data_access_scope": dict(self.data_access_scope),
            "side_effect_profile": dict(self.side_effect_profile),
            "audit_required": self.audit_required,
            "fallback_allowed": self.fallback_allowed,
            "observability": dict(self.observability),
            "raw_descriptor": dict(self.raw_descriptor),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExternalCapabilityContract":
        return cls(**dict(data))

    def to_capability_profile(self, capability_type: CapabilityType | str | None = None) -> CapabilityProfile:
        cap_type = capability_type or _PROTOCOL_TO_TYPE[self.protocol]
        risk = {
            "protocol": self.protocol,
            "risk_labels": list(self.risk_labels),
            "source_trust": self.source_trust,
            "data_access_scope": dict(self.data_access_scope),
            "side_effect": bool(self.side_effect_profile.get("side_effect")),
            **self.risk,
        }
        permissions = {
            "allowed_tenant_ids": list(self.tenant_constraints.get("allowed_tenant_ids") or []),
            "denied_tenant_ids": list(self.tenant_constraints.get("denied_tenant_ids") or []),
            "allowed_purposes": list(self.purpose_constraints.get("allowed_purposes") or []),
            "denied_purposes": list(self.purpose_constraints.get("denied_purposes") or []),
        }
        profile = CapabilityProfile(
            id=self.capability_id,
            type=cap_type,
            contracts={CONTRACT_KEY: self.to_dict()},
            supports=[self.protocol],
            risk=risk,
            permissions={key: value for key, value in permissions.items() if value},
            approval=dict(self.approval_route),
            fallback={"allowed": self.fallback_allowed},
            observability={"audit_required": self.audit_required, **self.observability},
        )
        return profile


def normalize_function_contract(
    capability_id: str,
    *,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    **kwargs: Any,
) -> ExternalCapabilityContract:
    raw_descriptor = {"name": capability_id, "input_schema": input_schema or {}, "output_schema": output_schema or {}}
    return ExternalCapabilityContract(
        capability_id=capability_id,
        protocol="function",
        descriptor_hash=_hash_dict(raw_descriptor),
        input_schema_hash=_hash_dict(input_schema or {}),
        output_schema_hash=_hash_dict(output_schema or {}),
        raw_descriptor=raw_descriptor,
        **kwargs,
    )


def normalize_mcp_contract(descriptor: dict[str, Any], **kwargs: Any) -> ExternalCapabilityContract:
    input_schema = descriptor.get("inputSchema") or descriptor.get("input_schema") or {}
    output_schema = descriptor.get("outputSchema") or descriptor.get("output_schema") or {}
    return ExternalCapabilityContract(
        capability_id=str(kwargs.pop("capability_id", descriptor.get("name") or descriptor.get("id") or "")),
        protocol="mcp",
        descriptor_hash=_hash_dict(descriptor),
        input_schema_hash=_hash_dict(input_schema),
        output_schema_hash=_hash_dict(output_schema) if output_schema else None,
        raw_descriptor=dict(descriptor),
        **kwargs,
    )


def normalize_a2a_contract(descriptor: dict[str, Any], **kwargs: Any) -> ExternalCapabilityContract:
    capabilities = descriptor.get("capabilities") or {}
    security = descriptor.get("security") or {}
    schema_descriptor = {"capabilities": capabilities, "security": security}
    return ExternalCapabilityContract(
        capability_id=str(kwargs.pop("capability_id", descriptor.get("name") or descriptor.get("id") or "")),
        protocol="a2a",
        descriptor_hash=_hash_dict(descriptor),
        input_schema_hash=_hash_dict(schema_descriptor),
        output_schema_hash=_hash_dict(descriptor.get("skills") or descriptor.get("capabilities") or {}),
        raw_descriptor=dict(descriptor),
        **kwargs,
    )


def same_or_stricter_contract(source: ExternalCapabilityContract, target: ExternalCapabilityContract) -> bool:
    if not target.fallback_allowed:
        return False
    if source.approval_route.get("required") and not target.approval_route.get("required"):
        return False
    if not _set_subset(target.tenant_constraints.get("allowed_tenant_ids"), source.tenant_constraints.get("allowed_tenant_ids")):
        return False
    if not _set_subset(target.purpose_constraints.get("allowed_purposes"), source.purpose_constraints.get("allowed_purposes")):
        return False
    if not _rank_not_wider(
        target.data_access_scope.get("data_classification"),
        source.data_access_scope.get("data_classification"),
        _DATA_CLASSIFICATION_RANK,
    ):
        return False
    if not _rank_not_wider(target.risk.get("exfiltration_risk"), source.risk.get("exfiltration_risk"), _EXFILTRATION_RISK_RANK):
        return False
    if not _rank_not_wider(target.risk.get("network_scope"), source.risk.get("network_scope"), _NETWORK_SCOPE_RANK):
        return False
    if not _rank_not_wider(
        target.side_effect_profile.get("destructive_potential"),
        source.side_effect_profile.get("destructive_potential"),
        _DESTRUCTIVE_RANK,
    ):
        return False
    source_budget = source.cost_budget.get("max_call_cost_usd")
    target_budget = target.cost_budget.get("max_call_cost_usd")
    if source_budget is not None and target_budget is not None and float(target_budget) > float(source_budget):
        return False
    return True


def contract_from_capability(capability: CapabilityProfile) -> ExternalCapabilityContract | None:
    payload = capability.contracts.get(CONTRACT_KEY)
    if not payload:
        return None
    return ExternalCapabilityContract.from_dict(payload)


def _hash_dict(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _set_subset(candidate: Any, source: Any) -> bool:
    candidate_set = set(candidate or [])
    source_set = set(source or [])
    if not source_set:
        return not candidate_set
    return candidate_set.issubset(source_set)


def _rank_not_wider(candidate: Any, source: Any, ranks: dict[str, int]) -> bool:
    candidate_value = str(candidate or "unknown")
    source_value = str(source or "unknown")
    return ranks.get(candidate_value, ranks["unknown"]) <= ranks.get(source_value, ranks["unknown"])

