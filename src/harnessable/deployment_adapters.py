from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class ProjectStoreAdapter(Protocol):
    adapter_id: str

    def read_manifest(self) -> dict[str, Any]: ...

    def dry_run_migration(self, target_version: str) -> "MigrationDryRunReport": ...


@dataclass(frozen=True)
class MigrationDryRunReport:
    adapter_id: str
    current_version: str
    target_version: str
    migration_required: bool
    planned_actions: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "current_version": self.current_version,
            "target_version": self.target_version,
            "migration_required": self.migration_required,
            "planned_actions": list(self.planned_actions),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class LocalProjectStoreAdapter:
    project_path: str | Path
    adapter_id: str = "local.project"
    manifest_name: str = "harnessable.project.json"

    def read_manifest(self) -> dict[str, Any]:
        path = Path(self.project_path) / self.manifest_name
        return json.loads(path.read_text(encoding="utf-8"))

    def dry_run_migration(self, target_version: str) -> MigrationDryRunReport:
        manifest = self.read_manifest()
        current_version = str(manifest.get("version") or "unknown")
        required = current_version != target_version
        actions = (f"update project manifest version from {current_version} to {target_version}",) if required else ()
        limitations = (
            "dry run only; no manifest or run artifact writes were performed",
            "remote database adapters must implement the same report shape before use",
        )
        return MigrationDryRunReport(
            adapter_id=self.adapter_id,
            current_version=current_version,
            target_version=target_version,
            migration_required=required,
            planned_actions=actions,
            limitations=limitations,
        )
