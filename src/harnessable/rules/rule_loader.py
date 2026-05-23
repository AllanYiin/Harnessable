from __future__ import annotations

from pathlib import Path

import yaml

from harnessable.core import ValidationError
from harnessable.validation import validate_payload

from .schemas import HarnessRule


def load_rule(path: str | Path) -> HarnessRule:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    errors = validate_payload("rules", data)
    if errors:
        raise ValidationError(f"{path}: {'; '.join(errors)}")
    return HarnessRule.from_dict(data)


def load_rules(path: str | Path) -> list[HarnessRule]:
    root = Path(path)
    files = [root] if root.is_file() else sorted(root.glob("*.y*ml"))
    return [load_rule(file) for file in files]
