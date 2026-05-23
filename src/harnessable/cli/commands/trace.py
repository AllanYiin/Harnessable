import json

from harnessable import HarnessProject


def run(args) -> int:
    project = HarnessProject.open(args.project)
    records = project.state.read_events(args.run_id)
    print(json.dumps(records, indent=2))
    return 0
