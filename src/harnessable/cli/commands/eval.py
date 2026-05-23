import json
from pathlib import Path

from harnessable import HarnessKernel, HarnessProject
from harnessable.evals import EvalCase, EvalRunner
from harnessable.validation import validate_payload


def run(args) -> int:
    project = HarnessProject.open(args.project)
    kernel = HarnessKernel.from_project(project)
    cases = []
    for file in sorted(Path(args.evals).glob("*.json")):
        data = json.loads(file.read_text(encoding="utf-8"))
        validation_errors = validate_payload("evals", data)
        if validation_errors:
            print(f"{file.name}:{'; '.join(validation_errors)}")
            return 1
        cases.append(EvalCase(**data))
    results = EvalRunner(kernel).run(cases)
    print(json.dumps(results, indent=2))
    return 0 if all(item["passed"] for item in results) else 1
