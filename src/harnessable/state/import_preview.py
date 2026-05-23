from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class ImportPreview:
    preview_id: str
    source_path: str
    target_kind: str
    valid: bool
    summary: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "source_path": self.source_path,
            "target_kind": self.target_kind,
            "valid": self.valid,
            "summary": self.summary,
            "errors": self.errors,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportPreview":
        return cls(**dict(data))


@dataclass(slots=True)
class ImportResult:
    preview_id: str
    applied: bool
    target_path: str | None = None
    errors: list[str] = field(default_factory=list)


class ImportPreviewStore:
    def __init__(self, project_path: str | Path) -> None:
        self.project_path = Path(project_path)
        self.imports_path = self.project_path / "imports"
        self.imports_path.mkdir(parents=True, exist_ok=True)

    def preview(self, source_path: str | Path, target_kind: str = "rules") -> ImportPreview:
        source = Path(source_path)
        raw = source.read_text(encoding="utf-8")
        preview_id = "preview_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        errors: list[str] = []
        data: Any = None
        try:
            data = yaml.safe_load(raw) if source.suffix.lower() in {".yaml", ".yml"} else json.loads(raw)
        except Exception as exc:  # pragma: no cover - message varies by parser
            errors.append(str(exc))
        preview = ImportPreview(
            preview_id=preview_id,
            source_path=str(source),
            target_kind=target_kind,
            valid=not errors,
            summary={"item_type": target_kind, "source_name": source.name},
            errors=errors,
            data=data,
        )
        self._path(preview_id).write_text(json.dumps(preview.to_dict(), indent=2), encoding="utf-8")
        return preview

    def get(self, preview_id: str) -> ImportPreview:
        return ImportPreview.from_dict(json.loads(self._path(preview_id).read_text(encoding="utf-8")))

    def apply(self, preview_id: str) -> ImportResult:
        preview = self.get(preview_id)
        if not preview.valid:
            return ImportResult(preview_id=preview_id, applied=False, errors=preview.errors)
        target_dir = self.project_path / preview.target_kind
        target_dir.mkdir(exist_ok=True)
        source_name = Path(preview.source_path).name
        target = target_dir / source_name
        target.write_text(Path(preview.source_path).read_text(encoding="utf-8"), encoding="utf-8")
        return ImportResult(preview_id=preview_id, applied=True, target_path=str(target))

    def _path(self, preview_id: str) -> Path:
        return self.imports_path / f"{preview_id}.json"
