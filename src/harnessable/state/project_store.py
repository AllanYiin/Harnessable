from __future__ import annotations

import json
from pathlib import Path

from harnessable.core.errors import NotFoundError

from .schemas import ProjectManifest, ProjectStatus


PROJECT_DIRS = ["rules", "capabilities", "fallback", "evals", "runs", "artifacts", "imports", "reports"]


class ProjectStore:
    manifest_name = "harnessable.project.json"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.manifest_path = self.path / self.manifest_name

    def create(self, name: str, profile: str = "default") -> ProjectManifest:
        self.path.mkdir(parents=True, exist_ok=True)
        for dirname in PROJECT_DIRS:
            (self.path / dirname).mkdir(exist_ok=True)
        manifest = ProjectManifest(name=name, profile=profile, status=ProjectStatus.SAVED)
        self.write_manifest(manifest)
        return manifest

    def read_manifest(self) -> ProjectManifest:
        if not self.manifest_path.exists():
            raise NotFoundError(f"project manifest not found at {self.manifest_path}")
        return ProjectManifest.from_dict(json.loads(self.manifest_path.read_text(encoding="utf-8")))

    def write_manifest(self, manifest: ProjectManifest) -> None:
        self.manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

    def archive(self) -> ProjectManifest:
        manifest = self.read_manifest()
        manifest.status = ProjectStatus.ARCHIVED
        self.write_manifest(manifest)
        return manifest
