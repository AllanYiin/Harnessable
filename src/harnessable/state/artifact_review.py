from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

ARTIFACT_REVIEW_SCHEMA_VERSION = 1

_EXTERNAL_SCRIPT_RE = re.compile(r"<script\b[^>]*\bsrc\s*=", re.IGNORECASE)
_HTML_OPEN_RE = re.compile(r"<html\b", re.IGNORECASE)
_HTML_CLOSE_RE = re.compile(r"</html\s*>", re.IGNORECASE)


@dataclass(frozen=True)
class ArtifactReviewIssue:
    code: str
    message: str
    severity: str = "error"
    field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.field is not None:
            payload["field"] = self.field
        return payload


@dataclass
class ArtifactUpdateReviewRequest:
    artifact_id: str
    profile_id: str
    base_version: int
    content: str
    content_type: str
    current_artifact_id: str | None = None
    current_profile_id: str | None = None
    current_version: int | None = None
    verification_claimed: bool = False
    execution_evidence_refs: list[str] = field(default_factory=list)
    allow_external_scripts: bool = False
    schema_version: int = ARTIFACT_REVIEW_SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_id": self.artifact_id,
            "profile_id": self.profile_id,
            "base_version": self.base_version,
            "content": self.content,
            "content_type": self.content_type,
            "current_artifact_id": self.current_artifact_id,
            "current_profile_id": self.current_profile_id,
            "current_version": self.current_version,
            "verification_claimed": self.verification_claimed,
            "execution_evidence_refs": list(self.execution_evidence_refs),
            "allow_external_scripts": self.allow_external_scripts,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ArtifactUpdateReviewRequest":
        content_type = payload.get("content_type", payload.get("kind", ""))
        evidence_refs = payload.get("execution_evidence_refs") or []
        if isinstance(evidence_refs, str):
            evidence_refs = [evidence_refs]
        return cls(
            schema_version=int(payload.get("schema_version", ARTIFACT_REVIEW_SCHEMA_VERSION)),
            artifact_id=str(payload.get("artifact_id", "")),
            profile_id=str(payload.get("profile_id", "")),
            base_version=int(payload.get("base_version", -1)),
            content=str(payload.get("content", "")),
            content_type=str(content_type),
            current_artifact_id=_optional_str(payload.get("current_artifact_id")),
            current_profile_id=_optional_str(payload.get("current_profile_id")),
            current_version=_optional_int(payload.get("current_version")),
            verification_claimed=bool(payload.get("verification_claimed", False)),
            execution_evidence_refs=[str(ref) for ref in evidence_refs],
            allow_external_scripts=bool(payload.get("allow_external_scripts", False)),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(frozen=True)
class ArtifactReviewResult:
    ok: bool = True
    issues: list[ArtifactReviewIssue] = field(default_factory=list)
    schema_version: int = ARTIFACT_REVIEW_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def review_artifact_update(request: ArtifactUpdateReviewRequest) -> ArtifactReviewResult:
    issues: list[ArtifactReviewIssue] = []

    if not request.artifact_id.strip():
        issues.append(_issue("missing_artifact_id", "Artifact update must include artifact_id.", "artifact_id"))
    if not request.profile_id.strip():
        issues.append(_issue("missing_profile_id", "Artifact update must include profile_id.", "profile_id"))
    if request.base_version < 0:
        issues.append(_issue("missing_base_version", "Artifact update must include a non-negative base_version.", "base_version"))

    if request.current_artifact_id is not None and request.artifact_id != request.current_artifact_id:
        issues.append(_issue("wrong_artifact_id", "Artifact update targets a different artifact_id.", "artifact_id"))
    if request.current_profile_id is not None and request.profile_id != request.current_profile_id:
        issues.append(_issue("wrong_profile_id", "Artifact update targets a different profile_id.", "profile_id"))
    if request.current_version is not None and request.base_version != request.current_version:
        issues.append(_issue("stale_base_version", "Artifact update base_version is stale.", "base_version"))

    if request.content_type == "single_page_html":
        if not _HTML_OPEN_RE.search(request.content) or not _HTML_CLOSE_RE.search(request.content):
            issues.append(
                _issue(
                    "incomplete_single_page_html",
                    "single_page_html content must be a complete HTML document.",
                    "content",
                )
            )
        if not request.allow_external_scripts and _EXTERNAL_SCRIPT_RE.search(request.content):
            issues.append(
                _issue(
                    "external_script_not_allowed",
                    "single_page_html content must not load external scripts unless explicitly allowed.",
                    "content",
                )
            )

    if request.verification_claimed and not request.execution_evidence_refs:
        issues.append(
            _issue(
                "missing_execution_evidence",
                "Verification claims must reference execution evidence.",
                "execution_evidence_refs",
            )
        )

    return ArtifactReviewResult(ok=not any(issue.severity == "error" for issue in issues), issues=issues)


def _issue(code: str, message: str, field_name: str) -> ArtifactReviewIssue:
    return ArtifactReviewIssue(code=code, message=message, field=field_name)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
