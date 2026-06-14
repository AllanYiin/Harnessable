from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from harnessable.validation import validate_payload

IMPORT_POLICY_VERSION = 1
MAX_IMPORT_BYTES = 1024 * 1024
ALLOWED_IMPORT_SUFFIXES = {".json", ".yaml", ".yml"}


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
    def __init__(
        self,
        project_path: str | Path,
        *,
        allowed_roots: list[str | Path] | tuple[str | Path, ...] | None = None,
        max_bytes: int = MAX_IMPORT_BYTES,
    ) -> None:
        self.project_path = Path(project_path).resolve()
        self.allowed_roots = tuple(
            Path(root).resolve() for root in (allowed_roots or (self.project_path.parent,))
        )
        self.max_bytes = max_bytes
        self.imports_path = self.project_path / "imports"
        self.imports_path.mkdir(parents=True, exist_ok=True)

    def preview(self, source_path: str | Path, target_kind: str = "rules") -> ImportPreview:
        errors: list[str] = []
        source = Path(source_path).resolve()
        raw = ""
        raw_bytes = b""
        data: Any = None
        source_hash = ""
        errors.extend(self._guard_source(source))
        if not errors:
            raw_bytes = source.read_bytes()
            source_hash = hashlib.sha256(raw_bytes).hexdigest()
            raw = raw_bytes.decode("utf-8")
            try:
                data = yaml.safe_load(raw) if source.suffix.lower() in {".yaml", ".yml"} else json.loads(raw)
            except Exception as exc:  # pragma: no cover - message varies by parser
                errors.append(str(exc))
        if not errors:
            errors.extend(validate_payload(target_kind, data))
        preview_id_seed = source_hash or hashlib.sha256(str(source).encode("utf-8")).hexdigest()
        preview_id = "preview_" + preview_id_seed[:16]
        preview = ImportPreview(
            preview_id=preview_id,
            source_path=str(source),
            target_kind=target_kind,
            valid=not errors,
            summary={
                "schema_version": IMPORT_POLICY_VERSION,
                "item_type": target_kind,
                "source_name": source.name,
                "validated": not errors,
                "source_sha256": source_hash,
                "source_size_bytes": len(raw_bytes),
                "max_bytes": self.max_bytes,
            },
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
        source = Path(preview.source_path).resolve()
        errors = self._guard_source(source)
        if errors:
            return ImportResult(preview_id=preview_id, applied=False, errors=errors)
        source_bytes = source.read_bytes()
        expected_hash = str(preview.summary.get("source_sha256") or "")
        actual_hash = hashlib.sha256(source_bytes).hexdigest()
        if expected_hash and actual_hash != expected_hash:
            return ImportResult(
                preview_id=preview_id,
                applied=False,
                errors=["source changed after preview; create a new preview before apply"],
            )
        target_dir = self.project_path / preview.target_kind
        try:
            target_dir.resolve().relative_to(self.project_path)
        except ValueError:
            return ImportResult(preview_id=preview_id, applied=False, errors=["target kind escapes project"])
        target_dir.mkdir(exist_ok=True)
        source_name = source.name
        target = target_dir / source_name
        target.write_bytes(source_bytes)
        return ImportResult(preview_id=preview_id, applied=True, target_path=str(target))

    def _path(self, preview_id: str) -> Path:
        return self.imports_path / f"{preview_id}.json"

    def _guard_source(self, source: Path) -> list[str]:
        errors: list[str] = []
        if not self._is_allowed_source(source):
            errors.append("source path is outside allowed import roots")
            return errors
        if not source.exists() or not source.is_file():
            errors.append("source path is not a file")
            return errors
        if source.suffix.lower() not in ALLOWED_IMPORT_SUFFIXES:
            errors.append("unsupported import file extension")
        size_bytes = source.stat().st_size
        if size_bytes > self.max_bytes:
            errors.append("source file exceeds import size limit")
        sample = source.read_bytes()[:4096]
        if b"\x00" in sample:
            errors.append("source file appears to be binary")
        return errors

    def _is_allowed_source(self, source: Path) -> bool:
        for root in self.allowed_roots:
            try:
                source.relative_to(root)
                return True
            except ValueError:
                continue
        return False
