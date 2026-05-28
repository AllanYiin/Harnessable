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


class ApprovalManager:
    def __init__(self) -> None:
        self.requests: dict[str, ApprovalRequest] = {}

    def create(self, run_id: str, event_id: str, reason: dict[str, Any] | None = None) -> ApprovalRequest:
        request = ApprovalRequest(run_id=run_id, event_id=event_id, reason=reason or {})
        self.requests[request.id] = request
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        return self.requests[approval_id]

    def approve(self, approval_id: str, evidence: dict[str, Any] | None = None) -> ApprovalRequest:
        request = self.requests[approval_id]
        if request.reason.get("requires_counter_evidence"):
            self._validate_counter_evidence(request, evidence or {})
        request.evidence = evidence or {}
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
        missing = [field for field in required if evidence.get(field) in (None, "", [], {}, False)]
        if missing:
            raise ValidationError(f"approval evidence missing: {', '.join(missing)}")
