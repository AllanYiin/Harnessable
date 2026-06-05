from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.core.serialization import to_plain


@dataclass(slots=True)
class SkillManifest:
    id: str
    name: str | None = None
    description: str = ""
    triggers: list[str] = field(default_factory=list)
    negative_triggers: list[str] = field(default_factory=list)
    language: str | None = None
    category: str | None = None
    priority: int = 100
    token_cost_estimate: int = 0
    path: str | None = None
    version: str | None = None
    root_priority: int = 100
    enabled: bool = True
    archived: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("skill manifest id is required")
        if self.name is None:
            self.name = self.id
        self.triggers = [_clean_text(item) for item in self.triggers if _clean_text(item)]
        self.negative_triggers = [_clean_text(item) for item in self.negative_triggers if _clean_text(item)]

    @property
    def normalized_id(self) -> str:
        return self.id.strip().lower()

    @property
    def resolved_path(self) -> Path | None:
        return Path(self.path) if self.path else None

    def to_prompt_metadata(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "triggers": self.triggers,
            "negative_triggers": self.negative_triggers,
            "language": self.language,
            "category": self.category,
            "priority": self.priority,
            "token_cost_estimate": self.token_cost_estimate,
            "version": self.version,
        }

    def to_capability(self) -> CapabilityProfile:
        return CapabilityProfile(
            id=f"skill.{self.id}",
            type=CapabilityType.RESOURCE,
            name=self.name,
            compatibility_class="skill",
            supports=["metadata", "progressive_hydration"],
            contracts={"skill_manifest": self.to_prompt_metadata()},
            enabled=self.enabled,
            archived=self.archived,
        )

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillManifest":
        return cls(**dict(data))


@dataclass(slots=True)
class SkillCandidate:
    manifest: SkillManifest
    score: float
    reasons: list[str] = field(default_factory=list)
    explicit: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest.to_prompt_metadata(),
            "score": self.score,
            "reasons": list(self.reasons),
            "explicit": self.explicit,
        }


@dataclass(slots=True)
class SkillSelectionResult:
    candidates: list[SkillCandidate]
    excluded: list[dict[str, Any]] = field(default_factory=list)
    metadata_tokens: int = 0
    budget_exceeded: bool = False

    @property
    def manifests(self) -> list[SkillManifest]:
        return [candidate.manifest for candidate in self.candidates]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "excluded": list(self.excluded),
            "metadata_tokens": self.metadata_tokens,
            "budget_exceeded": self.budget_exceeded,
        }


@dataclass(slots=True)
class HydratedSkill:
    manifest: SkillManifest
    content: str
    mode: str
    estimated_tokens: int
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest.to_prompt_metadata(),
            "content": self.content,
            "mode": self.mode,
            "estimated_tokens": self.estimated_tokens,
            "truncated": self.truncated,
        }


@dataclass(slots=True)
class SkillContext:
    selection: SkillSelectionResult
    hydrated: list[HydratedSkill] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    cache_key_hint: str | None = None
    routing_review: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "selection": self.selection.to_dict(),
            "hydrated": [item.to_dict() for item in self.hydrated],
            "warnings": list(self.warnings),
            "cache_key_hint": self.cache_key_hint,
            "routing_review": self.routing_review,
        }


def estimate_tokens(value: str) -> int:
    if not value:
        return 0
    return max(1, (len(value) + 3) // 4)


def _clean_text(value: Any) -> str:
    return str(value).strip()
