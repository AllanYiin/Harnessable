import json
from pathlib import Path

from harnessable import HarnessKernel, HarnessProject
from harnessable.evals import EvalCase, EvalRunner


def run(args) -> int:
    project = HarnessProject.open(args.project)
    kernel = HarnessKernel.from_project(project)
    cases = []
    for file in sorted(Path(args.evals).glob("*.json")):
        data = json.loads(file.read_text(encoding="utf-8"))
        cases.append(EvalCase(**data))
    results = EvalRunner(kernel).run(cases)
    print(json.dumps(results, indent=2))
    return 0 if all(item["passed"] for item in results) else 1
