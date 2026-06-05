from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any

import yaml

from .schemas import SkillManifest


class SkillIndex:
    def __init__(self, manifests: Iterable[SkillManifest] | None = None) -> None:
        self._manifests: dict[str, SkillManifest] = {}
        for manifest in manifests or []:
            self.add(manifest)

    def add(self, manifest: SkillManifest) -> None:
        current = self._manifests.get(manifest.normalized_id)
        if current is None or _wins_precedence(manifest, current):
            self._manifests[manifest.normalized_id] = manifest

    def list(self, include_archived: bool = False) -> list[SkillManifest]:
        values = list(self._manifests.values())
        if not include_archived:
            values = [item for item in values if item.enabled and not item.archived]
        return sorted(values, key=lambda item: (item.priority, item.root_priority, item.id))

    def get(self, skill_id: str) -> SkillManifest | None:
        return self._manifests.get(skill_id.strip().lower())

    @classmethod
    def from_paths(cls, paths: Iterable[str | Path]) -> "SkillIndex":
        index = cls()
        for root_priority, path in enumerate(paths):
            candidate = Path(path)
            if candidate.is_file():
                index.add(load_manifest(candidate, root_priority=root_priority))
                continue
            if candidate.is_dir():
                for skill_file in sorted(candidate.rglob("SKILL.md")):
                    index.add(load_manifest(skill_file, root_priority=root_priority))
        return index


def load_manifest(path: str | Path, root_priority: int = 100) -> SkillManifest:
    skill_path = Path(path)
    text = skill_path.read_text(encoding="utf-8")
    frontmatter = _frontmatter(text)
    metadata = frontmatter.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    skill_id = str(frontmatter.get("name") or skill_path.parent.name)
    category = frontmatter.get("category") or metadata.get("category")
    language = frontmatter.get("language") or metadata.get("language")
    return SkillManifest(
        id=skill_id,
        name=str(frontmatter.get("name") or skill_id),
        description=str(frontmatter.get("description") or ""),
        triggers=_list_field(frontmatter, "triggers"),
        negative_triggers=_list_field(frontmatter, "negative_triggers"),
        language=str(language) if language else None,
        category=str(category) if category else None,
        priority=int(frontmatter.get("priority") or metadata.get("priority") or 100),
        token_cost_estimate=int(frontmatter.get("token_cost_estimate") or metadata.get("token_cost_estimate") or 0),
        path=str(skill_path),
        version=str(frontmatter.get("version")) if frontmatter.get("version") else None,
        root_priority=root_priority,
        enabled=bool(frontmatter.get("enabled", True)),
        archived=bool(frontmatter.get("archived", False)),
        metadata=metadata,
    )


def _frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    parsed = yaml.safe_load(parts[1]) or {}
    return parsed if isinstance(parsed, dict) else {}


def _list_field(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _wins_precedence(candidate: SkillManifest, current: SkillManifest) -> bool:
    if candidate.root_priority != current.root_priority:
        return candidate.root_priority < current.root_priority
    if candidate.priority != current.priority:
        return candidate.priority < current.priority
    return str(candidate.path or "") < str(current.path or "")
