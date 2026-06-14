import json

from harnessable import AuditPackageExporter, HarnessProject


def run(args) -> int:
    project = HarnessProject.open(args.project)
    package = AuditPackageExporter(project).export_run(args.run_id)
    print(json.dumps(package.to_dict(), indent=2))
    return 0

