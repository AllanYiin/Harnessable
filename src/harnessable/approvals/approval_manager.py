from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from harnessable.core.errors import ValidationError


class ApprovalStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


@dataclass(slots=True)
class ApprovalRequest:
    run_id: str
    event_id: str
    reason: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"approval_{uuid4().hex}")
    status: ApprovalStatus = ApprovalStatus.REQUESTED
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ApprovalEvidence:
    opened_artifacts: bool = False
    risk_card_reviewed: bool = False
    counter_evidence: str | None = None
    reviewer_role: str | None = None
    approval_reason: str | None = None
    override_expiry: str | None = None
    alternate_version_reviewed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "opened_artifacts": self.opened_artifacts,
            "risk_card_reviewed": self.risk_card_reviewed,
            "counter_evidence": self.counter_evidence,
            "reviewer_role": self.reviewer_role,
            "approval_reason": self.approval_reason,
            "override_expiry": self.override_expiry,
            "alternate_version_reviewed": self.alternate_version_reviewed,
            **self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalEvidence":
        fields = {
            "opened_artifacts",
            "risk_card_reviewed",
            "counter_evidence",
            "reviewer_role",
            "approval_reason",
            "override_expiry",
            "alternate_version_reviewed",
        }
        metadata = {key: value for key, value in data.items() if key not in fields}
        values = {key: data.get(key) for key in fields if key in data}
        return cls(**values, metadata=metadata)


class ApprovalManager:
    def __init__(self) -> None:
        self.requests: dict[str, ApprovalRequest] = {}

    def create(self, run_id: str, event_id: str, reason: dict[str, Any] | None = None) -> ApprovalRequest:
        request = ApprovalRequest(run_id=run_id, event_id=event_id, reason=reason or {})
        self.requests[request.id] = request
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        return self.requests[approval_id]

    def approve(self, approval_id: str, evidence: dict[str, Any] | ApprovalEvidence | None = None) -> ApprovalRequest:
        request = self.requests[approval_id]
        evidence_dict = evidence.to_dict() if isinstance(evidence, ApprovalEvidence) else evidence or {}
        if request.reason.get("requires_counter_evidence"):
            self._validate_counter_evidence(request, evidence_dict)
        request.evidence = evidence_dict
        return self._set(approval_id, ApprovalStatus.APPROVED)

    def reject(self, approval_id: str) -> ApprovalRequest:
        return self._set(approval_id, ApprovalStatus.REJECTED)

    def expire(self, approval_id: str) -> ApprovalRequest:
        return self._set(approval_id, ApprovalStatus.EXPIRED)

    def cancel(self, approval_id: str) -> ApprovalRequest:
        return self._set(approval_id, ApprovalStatus.CANCELLED)

    def _set(self, approval_id: str, status: ApprovalStatus) -> ApprovalRequest:
        request = self.requests[approval_id]
        request.status = status
        return request

    def _validate_counter_evidence(self, request: ApprovalRequest, evidence: dict[str, Any]) -> None:
        required = request.reason.get("required_evidence") or ["opened_artifacts", "approval_reason"]
        if request.reason.get("high_risk_override"):
            required = [
                "opened_artifacts",
                "risk_card_reviewed",
                "counter_evidence",
                "reviewer_role",
                "approval_reason",
                "override_expiry",
            ]
        missing = [field for field in required if evidence.get(field) in (None, "", [], {}, False)]
        if missing:
            raise ValidationError(f"approval evidence missing: {', '.join(missing)}")
