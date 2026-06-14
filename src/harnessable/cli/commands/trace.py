import json

from harnessable import HarnessProject


def run(args) -> int:
    project = HarnessProject.open(args.project)
    if args.trace_command == "promote-preview":
        preview = project.trace_promotions.preview(args.run_id, project.state.read_events(args.run_id))
        print(json.dumps(preview.to_dict(), indent=2))
        return 0 if preview.candidate_cases else 1
    if args.trace_command == "promote-apply":
        preview = project.trace_promotions.get(args.preview_id)
        result = project.trace_promotions.apply(args.preview_id, project.state.read_events(preview.source_run_id))
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.applied else 1
    records = project.state.read_events(args.run_id)
    print(json.dumps(records, indent=2))
    return 0
