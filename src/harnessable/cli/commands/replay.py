import json

from harnessable import HarnessKernel, HarnessProject


def run(args) -> int:
    project = HarnessProject.open(args.project)
    report = HarnessKernel.from_project(project).replay(args.run_id)
    print(json.dumps(report.to_dict(), indent=2))
    return 0
