from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SKILL_RESOURCE_POLICY_VERSION = 1
ALLOWED_RESOURCE_DIRS = ("references", "scripts", "assets")
MAX_LISTED_RESOURCES_PER_SKILL = 200
DEFAULT_READ_MAX_CHARS = 6000
MAX_READ_CHARS = 20000
MAX_TEXT_FILE_BYTES = 512 * 1024


class SkillResourcePolicyError(ValueError):
    pass


@dataclass(frozen=True)
class SkillResourceReadPolicy:
    schema_version: int = SKILL_RESOURCE_POLICY_VERSION
    allowed_dirs: tuple[str, ...] = ALLOWED_RESOURCE_DIRS
    default_read_max_chars: int = DEFAULT_READ_MAX_CHARS
    max_read_chars: int = MAX_READ_CHARS
    max_text_file_bytes: int = MAX_TEXT_FILE_BYTES

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "allowed_dirs": list(self.allowed_dirs),
            "default_read_max_chars": self.default_read_max_chars,
            "max_read_chars": self.max_read_chars,
            "max_text_file_bytes": self.max_text_file_bytes,
        }


@dataclass(frozen=True)
class SkillResourceAccessRequest:
    skill_id: str
    relative_path: str = ""
    selected_skill_ids: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = SKILL_RESOURCE_POLICY_VERSION


def assert_selected_skill(skill_id: str, selected_skill_ids: tuple[str, ...]) -> None:
    if skill_id not in selected_skill_ids:
        raise SkillResourcePolicyError(f"Skill is not activated for this turn: {skill_id}")


def normalize_read_max_chars(value: Any, *, policy: SkillResourceReadPolicy | None = None) -> int:
    policy = policy or SkillResourceReadPolicy()
    if value in (None, ""):
        return policy.default_read_max_chars
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise SkillResourcePolicyError("max_chars must be an integer.") from exc
    return max(1, min(policy.max_read_chars, integer))


def resolve_allowed_resource(
    root: Path,
    relative_path: str,
    *,
    policy: SkillResourceReadPolicy | None = None,
) -> Path:
    policy = policy or SkillResourceReadPolicy()
    candidate_path = Path(relative_path)
    if candidate_path.is_absolute():
        raise SkillResourcePolicyError("Skill resource path must be relative.")
    parts = candidate_path.parts
    if not parts or parts[0] not in policy.allowed_dirs:
        allowed = ", ".join(f"{directory}/" for directory in policy.allowed_dirs)
        raise SkillResourcePolicyError(f"Skill resource path must start with {allowed}.")
    if any(part in {"", ".", ".."} for part in parts):
        raise SkillResourcePolicyError("Skill resource path cannot contain empty, dot, or parent segments.")
    target = (root / candidate_path).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        raise SkillResourcePolicyError("Skill resource path escapes the skill directory.") from None
    return target


def is_likely_text_resource(data: bytes, *, size_bytes: int, policy: SkillResourceReadPolicy | None = None) -> bool:
    policy = policy or SkillResourceReadPolicy()
    return size_bytes <= policy.max_text_file_bytes and not looks_binary(data)


def looks_binary(data: bytes) -> bool:
    return b"\x00" in data
