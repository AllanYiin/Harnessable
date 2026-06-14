from __future__ import annotations

import shutil
from pathlib import Path

from .evals import TracePromotionStore
from .compliance import VerticalPackStore
from .state.artifact_store import ArtifactStore
from .state.import_preview import ImportPreview, ImportPreviewStore, ImportResult
from .state.project_store import ProjectStore
from .state.schemas import ProjectManifest, ProjectStatus
from .state.state_store import StateStore


class HarnessProject:
    def __init__(self, path: str | Path, manifest: ProjectManifest) -> None:
        self.path = Path(path)
        self.manifest = manifest
        self.store = ProjectStore(self.path)
        self.artifacts = ArtifactStore(self.path)
        self.state = StateStore(self.path)
        self.imports = ImportPreviewStore(self.path)
        self.trace_promotions = TracePromotionStore(self.path)
        self.vertical_packs = VerticalPackStore(self.path)

    @classmethod
    def create(cls, path: str, name: str, profile: str = "default") -> "HarnessProject":
        store = ProjectStore(path)
        manifest = store.create(name, profile)
        return cls(path, manifest)

    @classmethod
    def open(cls, path: str) -> "HarnessProject":
        store = ProjectStore(path)
        manifest = store.read_manifest()
        manifest.status = ProjectStatus.OPEN
        store.write_manifest(manifest)
        return cls(path, manifest)

    def save(self) -> None:
        self.manifest.status = ProjectStatus.SAVED
        self.store.write_manifest(self.manifest)

    def mark_dirty(self) -> None:
        self.manifest.status = ProjectStatus.DIRTY
        self.store.write_manifest(self.manifest)

    def update_metadata(self, **metadata: object) -> None:
        self.manifest.metadata.update(metadata)
        self.mark_dirty()

    def archive(self) -> None:
        self.manifest = self.store.archive()

    def export_bundle(self, target_path: str) -> None:
        target = Path(target_path)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(self.path, target)

    def import_bundle_preview(self, source_path: str) -> ImportPreview:
        return self.imports.preview(source_path)

    def apply_import(self, preview_id: str) -> ImportResult:
        result = self.imports.apply(preview_id)
        if result.applied:
            self.mark_dirty()
        return result
