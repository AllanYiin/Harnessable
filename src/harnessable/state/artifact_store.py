from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4


class ArtifactStore:
    def __init__(self, project_path: str | Path) -> None:
        self.root = Path(project_path) / "artifacts"
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, payload: Any, metadata: dict[str, Any] | None = None) -> str:
        artifact_id = f"artifact_{uuid4().hex}"
        path = self.root / f"{artifact_id}.json"
        path.write_text(json.dumps({"versions": [{"payload": payload, "metadata": metadata or {}}], "archived": False}, indent=2), encoding="utf-8")
        return artifact_id

    def read(self, artifact_id: str, version: int = -1) -> Any:
        data = self._load(artifact_id)
        return data["versions"][version]["payload"]

    def version(self, artifact_id: str, payload: Any, metadata: dict[str, Any] | None = None) -> int:
        data = self._load(artifact_id)
        data["versions"].append({"payload": payload, "metadata": metadata or {}})
        self._save(artifact_id, data)
        return len(data["versions"]) - 1

    def archive(self, artifact_id: str) -> None:
        data = self._load(artifact_id)
        data["archived"] = True
        self._save(artifact_id, data)

    def redact_metadata(self, artifact_id: str, keys: list[str]) -> None:
        data = self._load(artifact_id)
        for version in data["versions"]:
            metadata = version.get("metadata") or {}
            for key in keys:
                if key in metadata:
                    metadata[key] = "[REDACTED]"
        self._save(artifact_id, data)

    def purge(self, artifact_id: str) -> None:
        self._path(artifact_id).unlink(missing_ok=True)

    def _path(self, artifact_id: str) -> Path:
        return self.root / f"{artifact_id}.json"

    def _load(self, artifact_id: str) -> dict[str, Any]:
        return json.loads(self._path(artifact_id).read_text(encoding="utf-8"))

    def _save(self, artifact_id: str, data: dict[str, Any]) -> None:
        self._path(artifact_id).write_text(json.dumps(data, indent=2), encoding="utf-8")
