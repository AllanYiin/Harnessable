from pathlib import Path

import yaml

from harnessable import HarnessProject
from harnessable.validation import validate_payload
from harnessable.resilience import FallbackPolicy


def run(args) -> int:
    project = HarnessProject.open(args.project)
    if args.fallback_command == "validate":
        errors = []
        for file in sorted((project.path / "fallback").glob("*.y*ml")):
            try:
                data = yaml.safe_load(file.read_text(encoding="utf-8"))
                validation_errors = validate_payload("fallback", data)
                if validation_errors:
                    raise ValueError("; ".join(validation_errors))
                FallbackPolicy.from_dict(data)
            except Exception as exc:
                errors.append(f"{file.name}:{exc}")
        if errors:
            print("\n".join(errors))
            return 1
        print("fallback:ok")
        return 0
    return 1
